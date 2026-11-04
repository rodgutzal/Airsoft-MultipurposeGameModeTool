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
#include "GpioDriver.h"

static const char *TAG = "MainProcess";

/**
 * Nombre:      InitSimpleGpioPorts
 * Descripcion: Configura los puertos simples: datos de las tiras LED en
 *              bajo (hasta que exista el driver RMT), filas del
 *              teclado en alto, columnas del teclado, switches y push button
 *              como entradas sin pull interno (el pull-up es externo). Los
 *              pines de LCD, I2S y ADC los configura su propio driver. Si
 *              algun pin no se puede configurar, el firmware aborta con el
 *              error (ESP_ERROR_CHECK).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void InitSimpleGpioPorts(void)
{
  /* Datos de las tiras LED en bajo */
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_TIRA_LED_1, 0));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_TIRA_LED_2, 0));

  /* Filas del teclado en alto, columnas como entradas (pull-up externo) */
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_KEY_F1, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_KEY_F2, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_KEY_F3, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(C_PIN_KEY_F4, 1));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_KEY_C1));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_KEY_C2));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_KEY_C3));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_KEY_C4));

  /* Switches y push button */
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_SW_EQUIPO));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_SW_ARMADO));
  ESP_ERROR_CHECK(ConfigGpioAsInput(C_PIN_BTN_ACCION));
}

/**
 * Nombre:      InitMainProcess
 * Descripcion: Imprime los datos del chip (nucleos, revision, flash, PSRAM) y
 *              ejecuta los procesos base: configuracion del reloj (ClockDriver)
 *              y de los puertos simples.
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
}
