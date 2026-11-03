idf_component_register(SRCS "main.c" "Ram.c" "MainProcess.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES esp_driver_gpio esp_hw_support esp_psram spi_flash)
