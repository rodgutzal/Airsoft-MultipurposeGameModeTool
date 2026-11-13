idf_component_register(SRCS "main.c" "Ram.c" "MainProcess.c" "ClockDriver.c" "DisplayDriver.c" "FlashDriver.c" "GpioDriver.c" "HeartbeatDriver.c" "PanelIli9486Driver.c" "PanelSt7796Driver.c" "TimerDriver.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES esp_driver_gpio esp_driver_gptimer esp_hw_support esp_lcd esp_psram esp_pm nvs_flash spi_flash)
