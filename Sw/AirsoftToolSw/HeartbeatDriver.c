/**
 * Archivo:           HeartbeatDriver.c
 * Descripcion:       Driver del LED de heartbeat: indica que el ciclo principal
 *                    sigue ejecutandose. El LED cambia de estado cada
 *                    C_HEARTBEAT_HALF_TICKS periodos del ciclo principal, es
 *                    decir, un ciclo completo (encendido y apagado) dura
 *                    C_HEARTBEAT_PERIOD_MS (1 s). Si el ciclo se atasca, el
 *                    LED se queda fijo.
 * Fecha de creacion: 2026-11-07
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include <stdint.h>
#include "esp_log.h"
#include "HeartbeatDriver.h"
#include "Ram.h"
#include "GpioDriver.h"

static const char *TAG = "HeartbeatDriver";

static uint32_t sTickCount = 0;
static int sLedLevel = C_FALSE;

/**
 * Nombre:      HeartbeatInit
 * Descripcion: Configura el pin del LED como salida y lo deja apagado. Debe
 *              llamarse una vez, antes de empezar a llamar HeartbeatTick.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si el pin se configuro bien.
 *              Otro codigo de esp_err_t si ConfigGpioAsOutput falla.
 */
esp_err_t HeartbeatInit(void)
{
  sTickCount = 0;
  sLedLevel = C_FALSE;

  esp_err_t err = ConfigGpioAsOutput(C_PIN_LED_ESTADO, sLedLevel);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "No se pudo configurar el LED de heartbeat en GPIO%d", C_PIN_LED_ESTADO);
    return err;
  }

  ESP_LOGI(TAG, "Heartbeat en GPIO%d, ciclo de %d ms", C_PIN_LED_ESTADO, C_HEARTBEAT_PERIOD_MS);
  return ESP_OK;
}

/**
 * Nombre:      HeartbeatTick
 * Descripcion: Avanza el heartbeat un periodo del ciclo principal. Cada
 *              C_HEARTBEAT_HALF_TICKS llamadas invierte el LED. No escribe en
 *              el log para no alargar el ciclo de 5 ms. Se llama una vez por
 *              periodo desde el ciclo principal.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void HeartbeatTick(void)
{
  sTickCount++;

  if(sTickCount >= C_HEARTBEAT_HALF_TICKS)
  {
    sTickCount = 0;
    sLedLevel = (sLedLevel == C_FALSE) ? C_TRUE : C_FALSE;
    SetGpioLevel(C_PIN_LED_ESTADO, sLedLevel);
  }
}
