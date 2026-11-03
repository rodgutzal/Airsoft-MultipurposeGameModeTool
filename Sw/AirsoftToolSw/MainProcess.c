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

static void ConfigOutput(int pin, int level)
{
    gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << pin,
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
    gpio_set_level(pin, level);
}

static void ConfigInputPullUp(int pin)
{
    gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << pin,
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
}

/* El reloj se fija en sdkconfig.defaults (CPU a 240 MHz). Aqui solo se informa. */
void InitClock(void)
{
    uint32_t cpuHz = 0;
    esp_clk_tree_src_get_freq_hz(SOC_MOD_CLK_CPU, ESP_CLK_TREE_SRC_FREQ_PRECISION_CACHED, &cpuHz);
    ESP_LOGI(TAG, "CPU: %lu MHz", (unsigned long)(cpuHz / 1000000UL));
}

/* Solo los puertos simples. Los pines de LCD, I2S y ADC los configura su driver. */
void InitPorts(void)
{
    /* LEDs apagados */
    ConfigOutput(PIN_LED_ROJO, 0);
    ConfigOutput(PIN_LED_AZUL, 0);

    /* Filas del teclado en alto, columnas con pull-up */
    ConfigOutput(PIN_KEY_F1, 1);
    ConfigOutput(PIN_KEY_F2, 1);
    ConfigOutput(PIN_KEY_F3, 1);
    ConfigOutput(PIN_KEY_F4, 1);
    ConfigInputPullUp(PIN_KEY_C1);
    ConfigInputPullUp(PIN_KEY_C2);
    ConfigInputPullUp(PIN_KEY_C3);
    ConfigInputPullUp(PIN_KEY_C4);

    /* Switches y push button */
    ConfigInputPullUp(PIN_SW_EQUIPO);
    ConfigInputPullUp(PIN_SW_ARMADO);
    ConfigInputPullUp(PIN_BTN_ACCION);
}

void InitMainProcess(void)
{
    esp_chip_info_t info;
    esp_chip_info(&info);

    uint32_t flashSize = 0;
    esp_flash_get_size(NULL, &flashSize);

    ESP_LOGI(TAG, "Chip: %s, %d nucleos, rev %d", CONFIG_IDF_TARGET, info.cores, info.revision);
    ESP_LOGI(TAG, "Flash: %lu MB", (unsigned long)(flashSize / (1024 * 1024)));
    ESP_LOGI(TAG, "PSRAM: %u KB", (unsigned)(heap_caps_get_total_size(MALLOC_CAP_SPIRAM) / 1024));

    InitClock();
    InitPorts();
}
