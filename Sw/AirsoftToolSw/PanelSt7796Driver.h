/**
 * Archivo:           PanelSt7796Driver.h
 * Descripcion:       Panel del controlador ST7796U: entrega el descriptor con su
 *                    secuencia de inicio, orientacion y reloj maximo.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef PANEL_ST7796_DRIVER_H
#define PANEL_ST7796_DRIVER_H

#include "PanelDriver.h"

const PanelDescriptor_t *PanelSt7796GetDescriptor(void);

#endif /* PANEL_ST7796_DRIVER_H */
