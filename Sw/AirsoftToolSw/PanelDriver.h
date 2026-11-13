/**
 * Archivo:           PanelDriver.h
 * Descripcion:       Tipos comunes de la capa de panel: describen un controlador
 *                    de pantalla (secuencia de inicio, orientacion y reloj
 *                    maximo) sin tocar el hardware. PanelIli9486Driver y
 *                    PanelSt7796Driver entregan cada uno su descriptor y
 *                    DisplayDriver lo ejecuta sobre el bus i80.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef PANEL_DRIVER_H
#define PANEL_DRIVER_H

#include <stddef.h>
#include <stdint.h>
#include "Ram.h"

/* Un comando de la secuencia de inicio: codigo, parametros y espera posterior. */
typedef struct
{
  uint8_t  command;                       /* codigo del comando */
  uint8_t  params[C_LCD_INIT_PARAMS_MAX]; /* parametros, en orden */
  uint8_t  paramCount;                    /* cuantos parametros son validos */
  uint16_t delayMs;                       /* ms de espera despues del comando */
} PanelInitCommand_t;

/* Descripcion completa de un controlador. */
typedef struct
{
  const char               *name;              /* nombre para el log */
  const PanelInitCommand_t *initCommands;      /* secuencia de inicio (sin MADCTL ni DISPON) */
  size_t                    initCommandCount;  /* cuantos comandos tiene la secuencia */
  uint8_t                   madctlLandscape;   /* valor de MADCTL para 480x320 y orden de color BGR */
  uint32_t                  maxPclkHz;         /* reloj de escritura maximo, en Hz */
} PanelDescriptor_t;

#endif /* PANEL_DRIVER_H */
