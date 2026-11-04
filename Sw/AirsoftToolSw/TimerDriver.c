/**
 * Archivo:           TimerDriver.c
 * Descripcion:       Driver del timer periodico de hardware (GPTimer) que genera
 *                    la interrupcion de C_TIMER_PERIOD_MS (5 ms) con la que
 *                    avanza el ciclo principal.
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
#include "TimerDriver.h"
#define C_RAM_EXPOSE_GLOBALS  /* violacion de R1 pendiente: la ISR escribe variables de Ram; se quita en el refactor */
#include "Ram.h"

static const char *TAG = "TimerDriver";

static gptimer_handle_t sPeriodicTimer = NULL;
static TaskHandle_t sTaskToWake = NULL;

/**
 * Nombre:      PeriodicTimerAlarmIsr
 * Descripcion: Rutina de interrupcion del timer. Se ejecuta cada
 *              C_TIMER_PERIOD_MS: suma ese periodo al contador global
 *              gSystemTickMs y enciende la bandera bf_5MsMainLoopFlag de
 *              u8MainFlag. Si la bandera todavia estaba encendida, el ciclo
 *              principal no termino el periodo anterior y se suma uno a
 *              gTickOverrunCount. Despierta la tarea del ciclo principal con
 *              una notificacion. Corre en IRAM y no usa funciones bloqueantes.
 * Entradas:    timer    - handle del timer que disparo la alarma.
 *              eventData - datos de la alarma (no se usan).
 *              userData - dato del usuario (no se usa).
 * Salidas:     true si hay que ceder el procesador a una tarea de mayor
 *              prioridad al salir de la interrupcion, false en otro caso.
 */
static bool IRAM_ATTR PeriodicTimerAlarmIsr(gptimer_handle_t timer,
                                            const gptimer_alarm_event_data_t *eventData,
                                            void *userData)
{
  BaseType_t higherPriorityTaskWoken = pdFALSE;

  gSystemTickMs += C_TIMER_PERIOD_MS;

  if(u8MainFlag.bf_5MsMainLoopFlag == C_TRUE)
  {
    gTickOverrunCount++;
  }
  else
  {
    u8MainFlag.bf_5MsMainLoopFlag = C_TRUE;
  }

  vTaskNotifyGiveFromISR(sTaskToWake, &higherPriorityTaskWoken);

  return (higherPriorityTaskWoken == pdTRUE);
}

/**
 * Nombre:      ConfigPeriodicTimer
 * Descripcion: Crea y configura el GPTimer a C_TIMER_RESOLUTION_HZ (1 us por
 *              cuenta), con alarma cada C_TIMER_PERIOD_MS en recarga
 *              automatica, y registra la rutina de interrupcion. No arranca
 *              el timer; para eso se llama a StartPeriodicTimer.
 * Entradas:    taskToWake - tarea que la interrupcion despierta en cada
 *                           periodo (normalmente la del ciclo principal).
 * Salidas:     ESP_OK si se configuro bien.
 *              ESP_ERR_INVALID_ARG si taskToWake es NULL.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t ConfigPeriodicTimer(TaskHandle_t taskToWake)
{
  if(taskToWake == NULL)
  {
    ESP_LOGE(TAG, "taskToWake es NULL");
    return ESP_ERR_INVALID_ARG;
  }
  sTaskToWake = taskToWake;

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
 * Nombre:      StartPeriodicTimer
 * Descripcion: Arranca el timer periodico. A partir de aqui la interrupcion se
 *              dispara cada C_TIMER_PERIOD_MS. Requiere haber llamado antes a
 *              ConfigPeriodicTimer.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si arranco bien.
 *              ESP_ERR_INVALID_STATE si el timer no esta configurado.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t StartPeriodicTimer(void)
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
