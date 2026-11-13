/**
 * Archivo:           DisplayDriver.h
 * Descripcion:       Driver de la pantalla TFT sobre el bus paralelo i80 de
 *                    esp_lcd. Su API no depende del controlador: el modelo
 *                    (ILI9486 o ST7796U) se elige al compilar con la opcion
 *                    AIRSOFT_LCD_CONTROLLER y su secuencia de inicio vive en
 *                    PanelIli9486Driver / PanelSt7796Driver.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef DISPLAY_DRIVER_H
#define DISPLAY_DRIVER_H

#include <stdint.h>
#include "esp_err.h"

esp_err_t DisplayInit(void);
esp_err_t DisplayFillColor(uint16_t color565);
esp_err_t DisplayDrawBitmap(int xStart, int yStart, int xEnd, int yEnd, const uint16_t *pixels);
const char *DisplayGetControllerName(void);

#endif /* DISPLAY_DRIVER_H */
