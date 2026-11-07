/**
 * Archivo:           GpioDriver.h
 * Descripcion:       Driver de GPIO: configuracion de pines como salida y
 *                    como entrada sin resistencias internas, con validacion del pin.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef GPIO_DRIVER_H
#define GPIO_DRIVER_H

#include "esp_err.h"

esp_err_t ConfigGpioAsOutput(int pin, int level);
esp_err_t ConfigGpioAsInput(int pin);
esp_err_t SetGpioLevel(int pin, int level);

#endif /* GPIO_DRIVER_H */
