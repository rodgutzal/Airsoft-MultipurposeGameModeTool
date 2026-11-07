/**
 * Archivo:           HeartbeatDriver.h
 * Descripcion:       Driver del LED de heartbeat: indica que el ciclo principal
 *                    sigue ejecutandose. El LED cambia de estado cada
 *                    C_HEARTBEAT_HALF_TICKS periodos del ciclo principal, es
 *                    decir, un ciclo completo (encendido y apagado) dura
 *                    C_HEARTBEAT_PERIOD_MS (1 s). Si el ciclo se atasca, el
 *                    LED se queda fijo.
 * Fecha de creacion: 2026-11-07
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef HEARTBEAT_DRIVER_H
#define HEARTBEAT_DRIVER_H

#include "esp_err.h"

esp_err_t HeartbeatInit(void);
void HeartbeatTick(void);

#endif /* HEARTBEAT_DRIVER_H */
