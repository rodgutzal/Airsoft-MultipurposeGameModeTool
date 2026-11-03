#include "Ram.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "MainProcess.h"

void app_main(void)
{
    InitRam();
    InitMainProcess();

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
