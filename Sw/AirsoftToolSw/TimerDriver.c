/**
 * Archivo:           TimerDriver.c
 * Descripcion:       Driver del timer periodico de hardware (GPTimer) que genera
 *                    la interrupcion de C_TIMER_PERIOD_MS (5 ms) con la que
 *                    avanza el ciclo principal. El consumidor solo espera el
 *                    periodo y consulta los contadores; la bandera, la
 *                    notificacion y la interrupcion son internas del driver.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "driver/gptimer.h"
#include "esp_attr.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "TimerDriver.h"
#include "Ram.h"

static const char *TAG = "TimerDriver";

/* Banderas internas del driver. Regla de escritura: cada bit lo escribe un solo
 * contexto a la vez (la ISR lo enciende solo cuando esta apagado y
 * TimerEndMainTick lo apaga solo cuando esta encendido), porque modificar un
 * bit es una lectura-modificacion-escritura del byte completo y no es atomica. */
#define bf_5MsMainLoopFlag  Bits.Bit0  /* la ISR lo enciende cada C_TIMER_PERIOD_MS */

static volatile Union8_t u8MainFlag;
static volatile uint32_t sSystemTickMs = 0;
static volatile uint32_t sTickOverrunCount = 0;
static volatile TaskHandle_t sWaitingTask = NULL;
static gptimer_handle_t sPeriodicTimer = NULL;

/**
 * Nombre:      PeriodicTimerAlarmIsr
 * Descripcion: Rutina de interrupcion del timer. Se ejecuta cada
 *              C_TIMER_PERIOD_MS: suma ese periodo al contador de milisegundos
 *              y enciende la bandera bf_5MsMainLoopFlag de u8MainFlag. Si la
 *              bandera todavia estaba encendida, el consumidor no termino el
 *              periodo anterior y se suma uno al contador de periodos
 *              perdidos. Despierta con una notificacion a la tarea que espera
 *              en TimerWaitMainTick, si hay una. Corre en IRAM y no usa
 *              funciones bloqueantes.
 * Entradas:    timer     - handle del timer que disparo la alarma.
 *              eventData - datos de la alarma (no se usan).
 *              userData  - dato del usuario (no se usa).
 * Salidas:     true si hay que ceder el procesador a una tarea de mayor
 *              prioridad al salir de la interrupcion, false en otro caso.
 */
static bool IRAM_ATTR PeriodicTimerAlarmIsr(gptimer_handle_t timer,
                                            const gptimer_alarm_event_data_t *eventData,
                                            void *userData)
{
  BaseType_t higherPriorityTaskWoken = pdFALSE;
  TaskHandle_t waitingTask = sWaitingTask;

  sSystemTickMs += C_TIMER_PERIOD_MS;

  if(u8MainFlag.bf_5MsMainLoopFlag == C_TRUE)
  {
    sTickOverrunCount++;
  }
  else
  {
    u8MainFlag.bf_5MsMainLoopFlag = C_TRUE;
  }

  if(waitingTask != NULL)
  {
    vTaskNotifyGiveFromISR(waitingTask, &higherPriorityTaskWoken);
  }

  return (higherPriorityTaskWoken == pdTRUE);
}

/**
 * Nombre:      TimerInit
 * Descripcion: Crea y configura el GPTimer a C_TIMER_RESOLUTION_HZ (1 us por
 *              cuenta), con alarma cada C_TIMER_PERIOD_MS en recarga
 *              automatica, y registra la rutina de interrupcion. Deja en cero
 *              la bandera y los contadores. No arranca el timer; para eso se
 *              llama a TimerStart.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si se configuro bien.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t TimerInit(void)
{
  u8MainFlag.Byte = 0;
  sSystemTickMs = 0;
  sTickOverrunCount = 0;
  sWaitingTask = NULL;

  gptimer_config_t timerConfig =
  {
    .clk_src       = GPTIMER_CLK_SRC_DEFAULT,
    .direction     = GPTIMER_COUNT_UP,
    .resolution_hz = C_TIMER_RESOLUTION_HZ,
  };
  esp_err_t err = gptimer_new_timer(&timerConfig, &sPeriodicTimer);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "gptimer_new_timer fallo (%s)", esp_err_to_name(err));
    return err;
  }

  gptimer_event_callbacks_t callbacks =
  {
    .on_alarm = PeriodicTimerAlarmIsr,
  };
  err = gptimer_register_event_callbacks(sPeriodicTimer, &callbacks, NULL);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "gptimer_register_event_callbacks fallo (%s)", esp_err_to_name(err));
    return err;
  }

  err = gptimer_enable(sPeriodicTimer);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "gptimer_enable fallo (%s)", esp_err_to_name(err));
    return err;
  }

  gptimer_alarm_config_t alarmConfig =
  {
    .alarm_count = C_TIMER_ALARM_COUNT,
    .reload_count = 0,
    .flags.auto_reload_on_alarm = true,
  };
  err = gptimer_set_alarm_action(sPeriodicTimer, &alarmConfig);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "gptimer_set_alarm_action fallo (%s)", esp_err_to_name(err));
    return err;
  }

  ESP_LOGI(TAG, "Timer periodico configurado: %d ms", C_TIMER_PERIOD_MS);
  return ESP_OK;
}

/**
 * Nombre:      TimerStart
 * Descripcion: Arranca el timer periodico. A partir de aqui la interrupcion se
 *              dispara cada C_TIMER_PERIOD_MS. Requiere haber llamado antes a
 *              TimerInit.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si arranco bien.
 *              ESP_ERR_INVALID_STATE si el timer no esta configurado.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t TimerStart(void)
{
  if(sPeriodicTimer == NULL)
  {
    ESP_LOGE(TAG, "El timer no esta configurado");
    return ESP_ERR_INVALID_STATE;
  }

  esp_err_t err = gptimer_start(sPeriodicTimer);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "gptimer_start fallo (%s)", esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      TimerWaitMainTick
 * Descripcion: Bloquea a la tarea que la llama hasta que empieza un nuevo
 *              periodo del timer (la bandera bf_5MsMainLoopFlag esta
 *              encendida) y regresa sin apagarla. Mientras espera la tarea
 *              duerme y no consume CPU. Si el periodo ya habia empezado,
 *              regresa de inmediato. La tarea que llama queda registrada para
 *              que la ISR la despierte. Al terminar el trabajo del periodo se
 *              debe llamar a TimerEndMainTick.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void TimerWaitMainTick(void)
{
  sWaitingTask = xTaskGetCurrentTaskHandle();

  while(u8MainFlag.bf_5MsMainLoopFlag == C_FALSE)
  {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
  }
}

/**
 * Nombre:      TimerEndMainTick
 * Descripcion: Marca el periodo actual como atendido: apaga la bandera
 *              bf_5MsMainLoopFlag. Debe llamarse al terminar el trabajo del
 *              periodo; si el trabajo tarda mas de C_TIMER_PERIOD_MS, la
 *              siguiente interrupcion encuentra la bandera encendida y suma
 *              un periodo perdido (TimerGetOverrunCount).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void TimerEndMainTick(void)
{
  u8MainFlag.bf_5MsMainLoopFlag = C_FALSE;
}

/**
 * Nombre:      TimerGetSystemTickMs
 * Descripcion: Devuelve los milisegundos transcurridos desde TimerInit, en
 *              pasos de C_TIMER_PERIOD_MS. Se desborda a los 49.7 dias.
 * Entradas:    Ninguna.
 * Salidas:     Milisegundos desde el arranque del timer.
 */
uint32_t TimerGetSystemTickMs(void)
{
  return sSystemTickMs;
}

/**
 * Nombre:      TimerGetOverrunCount
 * Descripcion: Devuelve cuantos periodos del timer encontraron la bandera
 *              todavia encendida, es decir, cuantas veces el trabajo del
 *              ciclo principal tardo mas de C_TIMER_PERIOD_MS.
 * Entradas:    Ninguna.
 * Salidas:     Numero de periodos perdidos desde TimerInit.
 */
uint32_t TimerGetOverrunCount(void)
{
  return sTickOverrunCount;
}
