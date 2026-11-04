idf_component_register(SRCS "main.c" "Ram.c" "MainProcess.c" "ClockDriver.c" "GpioDriver.c" "TimerDriver.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES esp_driver_gpio esp_driver_gptimer esp_hw_support esp_psram esp_pm spi_flash)
