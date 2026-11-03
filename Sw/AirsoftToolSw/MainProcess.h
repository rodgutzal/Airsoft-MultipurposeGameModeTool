/**
 * Archivo:           MainProcess.h
 * Descripcion:       Declaracion de los procesos base del micro: reloj,
 *                    inicializacion y configuracion de puertos.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef MAIN_PROCESS_H
#define MAIN_PROCESS_H

void ReportCpuClockFrequency(void);
void InitSimpleGpioPorts(void);
void InitMainProcess(void);

#endif /* MAIN_PROCESS_H */
