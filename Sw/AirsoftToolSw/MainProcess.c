/**
 * Archivo:           MainProcess.c
 * Descripcion:       Procesos base del micro: arranque del reloj, inicializacion
 *                    y configuracion de los puertos GPIO simples.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include <stdio.h>
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "esp_flash.h"
#include "esp_chip_info.h"
#include "MainProcess.h"
#include "Ram.h"
#include "ClockDriver.h"
#include "DisplayDriver.h"
#include "FlashDriver.h"
#include "GpioDriver.h"
#include "HeartbeatDriver.h"
#include "TimerDriver.h"

static const char *TAG = "MainProcess";

/**
 * Nombre:      InitSimpleGpioPorts
 * Descripcion: Configura los puertos simples: dato de la tira LED en bajo
 *              (hasta que exista el driver RMT). El teclado, los switches y el
 *              push button estan en el expansor MCP23017 (hardware v0.8) y
 *              los configurara su driver; no se tocan sus antiguos GPIO porque
 *              ahora son el bus de la pantalla y el SPI del touch. Los pines
 *              de LCD, I2S y ADC los configura su propio driver. Si el pin no
 *              se puede configurar, el firmware aborta (ESP_ERROR_CHECK).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void InitSimpleGpioPorts(void)
{
  /* Datos de la tira LED en bajo (hardware v0.8: una sola linea para las dos tiras) */
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_TIRA_LED_1, 0));

  /* El teclado, los switches y el push button ya no estan en GPIO directos:
   * en el hardware v0.8 viven en el expansor MCP23017 (pendiente de driver) y
   * sus antiguos GPIO son el bus de la pantalla y el SPI del touch. */
}

/**
 * Nombre:      InitMainProcess
 * Descripcion: Imprime los datos del chip (nucleos, revision, flash, PSRAM) y
 *              ejecuta la secuencia de arranque: reloj (ClockDriver), puertos
 *              simples, almacenamiento en flash (FlashInit; si falla solo se
 *              avisa y el firmware sigue sin guardar datos), LED de heartbeat
 *              (HeartbeatInit; si falla solo se avisa), pantalla (DisplayInit;
 *              si falla solo se avisa y el firmware sigue sin display) y timer periodico
 *              (TimerInit y TimerStart).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (escribe en el log).
 */
void InitMainProcess(void)
{
  esp_chip_info_t info;
  esp_chip_info(&info);

  uint32_t flashSize = 0;
  esp_flash_get_size(NULL, &flashSize);

  ESP_LOGI(TAG, "Chip: %s, %d nucleos, rev %d", CONFIG_IDF_TARGET, info.cores, info.revision);
  ESP_LOGI(TAG, "Flash: %lu MB", (unsigned long)(flashSize / C_BYTES_PER_MB));
  ESP_LOGI(TAG, "PSRAM: %u KB", (unsigned)(heap_caps_get_total_size(MALLOC_CAP_SPIRAM) / C_BYTES_PER_KB));

  ESP_ERROR_CHECK(ConfigCpuClock());
  InitSimpleGpioPorts();

  if(FlashInit() != ESP_OK)
  {
    ESP_LOGE(TAG, "Sin almacenamiento en flash: los datos no se guardaran");
  }

  if(HeartbeatInit() != ESP_OK)
  {
    ESP_LOGE(TAG, "Sin LED de heartbeat: el firmware sigue sin indicador");
  }

  if(DisplayInit() != ESP_OK)
  {
    ESP_LOGE(TAG, "Sin pantalla: el firmware sigue sin display");
  }
  else if(DisplayFillColor(C_LCD_COLOR_BLACK) != ESP_OK)
  {
    ESP_LOGE(TAG, "La pantalla se inicio pero no se pudo pintar: revisar el cableado del bus");
  }

  ESP_ERROR_CHECK(TimerInit());
  ESP_ERROR_CHECK(TimerStart());
}
