idf_component_register(SRCS "main.c" "Ram.c" "MainProcess.c" "ClockDriver.c" "FlashDriver.c" "GpioDriver.c" "HeartbeatDriver.c" "TimerDriver.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES esp_driver_gpio esp_driver_gptimer esp_hw_support esp_psram esp_pm nvs_flash spi_flash)
