#include <stdio.h>
#include "esp_chip_info.h"
#include "esp_heap_caps.h"
#include "esp_flash.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "pines.h"

static const char *TAG = "airsoft_tool";

void app_main(void)
{
    esp_chip_info_t info;
    esp_chip_info(&info);

    uint32_t flash_size = 0;
    esp_flash_get_size(NULL, &flash_size);

    ESP_LOGI(TAG, "Chip: %s, %d nucleos, rev %d", CONFIG_IDF_TARGET, info.cores, info.revision);
    ESP_LOGI(TAG, "Flash: %lu MB", (unsigned long)(flash_size / (1024 * 1024)));
    ESP_LOGI(TAG, "PSRAM: %u KB", (unsigned)(heap_caps_get_total_size(MALLOC_CAP_SPIRAM) / 1024));

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
