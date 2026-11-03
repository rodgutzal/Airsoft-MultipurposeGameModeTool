/**
 * Archivo:           MainProcess.c
 * Descripcion:       Procesos base del micro: reporte del reloj, inicializacion
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
#include "esp_clk_tree.h"
#include "soc/clk_tree_defs.h"
#include "MainProcess.h"
#include "GlobalDefine.h"
#include "GpioDriver.h"

static const char *TAG = "MainProcess";

/**
 * Nombre:      ReportCpuClockFrequency
 * Descripcion: Lee la frecuencia del CPU y la imprime por el monitor serie.
 *              El reloj en si se fija en sdkconfig.defaults (240 MHz).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (escribe en el log).
 */
void ReportCpuClockFrequency(void)
{
  uint32_t cpuHz = 0;
  esp_clk_tree_src_get_freq_hz(SOC_MOD_CLK_CPU, ESP_CLK_TREE_SRC_FREQ_PRECISION_CACHED, &cpuHz);
  ESP_LOGI(TAG, "CPU: %lu MHz", (unsigned long)(cpuHz / 1000000UL));
}

/**
 * Nombre:      InitSimpleGpioPorts
 * Descripcion: Configura los puertos simples: LEDs apagados, filas del
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
  /* LEDs apagados */
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_LED_ROJO, 0));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_LED_AZUL, 0));

  /* Filas del teclado en alto, columnas como entradas (pull-up externo) */
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_KEY_F1, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_KEY_F2, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_KEY_F3, 1));
  ESP_ERROR_CHECK(ConfigGpioAsOutput(PIN_KEY_F4, 1));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_KEY_C1));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_KEY_C2));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_KEY_C3));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_KEY_C4));

  /* Switches y push button */
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_SW_EQUIPO));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_SW_ARMADO));
  ESP_ERROR_CHECK(ConfigGpioAsInput(PIN_BTN_ACCION));
}

/**
 * Nombre:      InitMainProcess
 * Descripcion: Imprime los datos del chip (nucleos, revision, flash, PSRAM) y
 *              ejecuta los procesos base: reporte del reloj y configuracion
 *              de los puertos simples.
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
  ESP_LOGI(TAG, "Flash: %lu MB", (unsigned long)(flashSize / (1024 * 1024)));
  ESP_LOGI(TAG, "PSRAM: %u KB", (unsigned)(heap_caps_get_total_size(MALLOC_CAP_SPIRAM) / 1024));

  ReportCpuClockFrequency();
  InitSimpleGpioPorts();
}
