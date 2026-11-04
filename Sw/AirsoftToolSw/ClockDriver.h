/**
 * Archivo:           ClockDriver.h
 * Descripcion:       Driver del reloj del CPU: lo fija a la frecuencia objetivo
 *                    (C_CPU_CLOCK_TARGET_MHZ) y verifica que se logro.
 * Fecha de creacion: 2026-11-03
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef CLOCK_DRIVER_H
#define CLOCK_DRIVER_H

#include "esp_err.h"

esp_err_t ConfigCpuClock(void);
esp_err_t VerifyCpuClockFrequency(void);

#endif /* CLOCK_DRIVER_H */
