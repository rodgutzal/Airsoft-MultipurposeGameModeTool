/**
 * Archivo:           TimerDriver.h
 * Descripcion:       Driver del timer periodico de hardware (GPTimer) que genera
 *                    la interrupcion de C_TIMER_PERIOD_MS (5 ms) con la que
 *                    avanza el ciclo principal.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef TIMER_DRIVER_H
#define TIMER_DRIVER_H

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

esp_err_t ConfigPeriodicTimer(TaskHandle_t taskToWake);
esp_err_t StartPeriodicTimer(void);

#endif /* TIMER_DRIVER_H */
