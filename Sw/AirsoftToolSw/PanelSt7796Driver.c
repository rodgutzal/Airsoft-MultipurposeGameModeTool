/**
 * Archivo:           PanelSt7796Driver.c
 * Descripcion:       Panel del controlador ST7796U. Contiene la secuencia de
 *                    inicio (habilitar comandos, formato RGB565, potencia,
 *                    inversion y gamma) y los parametros propios del
 *                    controlador. No accede al hardware: DisplayDriver envia
 *                    los comandos por el bus i80.
 *                    SIN VALIDAR EN HARDWARE: los valores siguen los
 *                    inicializadores habituales del ST7796 (comunidad y
 *                    componente esp_lcd_st7796) y no se ha confirmado que
 *                    sirvan tal cual para la variante U.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "PanelSt7796Driver.h"

/* Secuencia de inicio. Despues de ella DisplayDriver envia MADCTL y DISPON. */
static const PanelInitCommand_t sInitCommands[] =
{
  { 0x01, { 0 },                                  0,  120 },  /* SWRESET: el RST de la pantalla va a EN, no hay GPIO */
  { 0x11, { 0 },                                  0,  120 },  /* SLPOUT */
  { 0xF0, { 0xC3 },                               1,  0   },  /* Habilitar comandos extendidos, parte 1 */
  { 0xF0, { 0x96 },                               1,  0   },  /* Habilitar comandos extendidos, parte 2 */
  { 0x3A, { 0x55 },                               1,  0   },  /* COLMOD: 16 bits por pixel (RGB565) */
  { 0xB4, { 0x01 },                               1,  0   },  /* Inversion de columnas */
  { 0xB6, { 0x80, 0x02, 0x3B },                   3,  0   },  /* Display function control */
  { 0xE8, { 0x40, 0x8A, 0x00, 0x00, 0x29, 0x19,
            0xA5, 0x33 },                         8,  0   },  /* Display output ctrl adjust */
  { 0xC1, { 0x06 },                               1,  0   },  /* Power control 2 */
  { 0xC2, { 0xA7 },                               1,  0   },  /* Power control 3 */
  { 0xC5, { 0x18 },                               1,  120 },  /* VCOM control */
  { 0xE0, { 0xF0, 0x09, 0x0B, 0x06, 0x04, 0x15, 0x2F,
            0x54, 0x42, 0x3C, 0x17, 0x14, 0x18, 0x1B }, 14, 0 },  /* Gamma positivo */
  { 0xE1, { 0xE0, 0x09, 0x0B, 0x06, 0x04, 0x03, 0x2B,
            0x43, 0x42, 0x3B, 0x16, 0x14, 0x17, 0x1B }, 14, 120 },  /* Gamma negativo */
  { 0xF0, { 0x3C },                               1,  0   },  /* Deshabilitar comandos extendidos, parte 1 */
  { 0xF0, { 0x69 },                               1,  120 },  /* Deshabilitar comandos extendidos, parte 2 */
};

/* Descriptor del ST7796U. MADCTL 0x28 = MV (intercambiar ejes, horizontal) + BGR. */
static const PanelDescriptor_t sDescriptor =
{
  .name             = "ST7796U",
  .initCommands     = sInitCommands,
  .initCommandCount = sizeof(sInitCommands) / sizeof(sInitCommands[0]),
  .madctlLandscape  = 0x28,
  .maxPclkHz        = 10000000,  /* Hz. Valor prudente sin validar; consultar el ciclo de escritura de la hoja de datos */
};

/**
 * Nombre:      PanelSt7796GetDescriptor
 * Descripcion: Devuelve el descriptor del controlador ST7796U.
 * Entradas:    Ninguna.
 * Salidas:     Puntero al descriptor constante (nunca es NULL).
 */
const PanelDescriptor_t *PanelSt7796GetDescriptor(void)
{
  return &sDescriptor;
}
