/**
 * Archivo:           FlashDriver.h
 * Descripcion:       Driver de almacenamiento persistente en flash (NVS):
 *                    guarda y lee valores y bloques de datos por clave dentro de
 *                    un espacio de nombres propio (C_FLASH_NAMESPACE). Las
 *                    escrituras borran y escriben flash: son bloqueantes y
 *                    pueden tardar decenas de milisegundos, por lo que no deben
 *                    llamarse dentro de las subrutinas del ciclo de 5 ms.
 * Fecha de creacion: 2026-11-04
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef FLASH_DRIVER_H
#define FLASH_DRIVER_H

#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

esp_err_t FlashInit(void);
esp_err_t FlashReadU32(const char *key, uint32_t *value);
esp_err_t FlashWriteU32(const char *key, uint32_t value);
esp_err_t FlashReadBlob(const char *key, void *buffer, size_t *length);
esp_err_t FlashWriteBlob(const char *key, const void *data, size_t length);
esp_err_t FlashEraseAll(void);

#endif /* FLASH_DRIVER_H */
