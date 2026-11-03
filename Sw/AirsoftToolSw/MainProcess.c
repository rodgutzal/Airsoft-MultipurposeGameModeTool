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
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "esp_flash.h"
#include "esp_chip_info.h"
#include "esp_clk_tree.h"
#include "soc/clk_tree_defs.h"
#include "MainProcess.h"
#include "GlobalDefine.h"

static const char *TAG = "MainProcess";

/**
 * Nombre:      ConfigGpioAsOutput
 * Descripcion: Configura un GPIO como salida sin resistencias internas y le
 *              asigna un nivel inicial.
 * Entradas:    pin   - numero de GPIO.
 *              level - nivel inicial (0 = bajo, 1 = alto).
 * Salidas:     Ninguna.
 */
static void ConfigGpioAsOutput(int pin, int level)
{
  gpio_config_t cfg =
  {
    .pin_bit_mask = 1ULL << pin,
    .mode         = GPIO_MODE_OUTPUT,
    .pull_up_en   = GPIO_PULLUP_DISABLE,
    .pull_down_en = GPIO_PULLDOWN_DISABLE,
    .intr_type    = GPIO_INTR_DISABLE,
  };
  gpio_config(&cfg);
  gpio_set_level(pin, level);
}

/**
 * Nombre:      ConfigGpioAsInputWithPullUp
 * Descripcion: Configura un GPIO como entrada con resistencia pull-up interna
 *              y sin interrupciones.
 * Entradas:    pin - numero de GPIO.
 * Salidas:     Ninguna.
 */
static void ConfigGpioAsInputWithPullUp(int pin)
{
  gpio_config_t cfg =
  {
    .pin_bit_mask = 1ULL << pin,
    .mode         = GPIO_MODE_INPUT,
    .pull_up_en   = GPIO_PULLUP_ENABLE,
    .pull_down_en = GPIO_PULLDOWN_DISABLE,
    .intr_type    = GPIO_INTR_DISABLE,
  };
  gpio_config(&cfg);
}

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
 *              como entradas con pull-up. Los pines de LCD, I2S y ADC los
 *              configura su propio driver.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
void InitSimpleGpioPorts(void)
{
  /* LEDs apagados */
  ConfigGpioAsOutput(PIN_LED_ROJO, 0);
  ConfigGpioAsOutput(PIN_LED_AZUL, 0);

  /* Filas del teclado en alto, columnas con pull-up */
  ConfigGpioAsOutput(PIN_KEY_F1, 1);
  ConfigGpioAsOutput(PIN_KEY_F2, 1);
  ConfigGpioAsOutput(PIN_KEY_F3, 1);
  ConfigGpioAsOutput(PIN_KEY_F4, 1);
  ConfigGpioAsInputWithPullUp(PIN_KEY_C1);
  ConfigGpioAsInputWithPullUp(PIN_KEY_C2);
  ConfigGpioAsInputWithPullUp(PIN_KEY_C3);
  ConfigGpioAsInputWithPullUp(PIN_KEY_C4);

  /* Switches y push button */
  ConfigGpioAsInputWithPullUp(PIN_SW_EQUIPO);
  ConfigGpioAsInputWithPullUp(PIN_SW_ARMADO);
  ConfigGpioAsInputWithPullUp(PIN_BTN_ACCION);
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
