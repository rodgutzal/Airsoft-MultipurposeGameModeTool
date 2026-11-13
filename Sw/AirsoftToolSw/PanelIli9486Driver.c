/**
 * Archivo:           PanelIli9486Driver.c
 * Descripcion:       Panel del controlador ILI9486. Contiene la secuencia de
 *                    inicio (formato RGB565, potencia, VCOM y gamma) y los
 *                    parametros propios del controlador. No accede al hardware:
 *                    DisplayDriver envia los comandos por el bus i80.
 *                    SIN VALIDAR EN HARDWARE: los valores siguen los
 *                    inicializadores habituales de la comunidad (por ejemplo
 *                    TFT_eSPI) y hay que contrastarlos con la hoja de datos y
 *                    la pantalla real.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "PanelIli9486Driver.h"

/* Secuencia de inicio. Despues de ella DisplayDriver envia MADCTL y DISPON. */
static const PanelInitCommand_t sInitCommands[] =
{
  { 0x01, { 0 },                                  0,  120 },  /* SWRESET: el RST de la pantalla va a EN, no hay GPIO */
  { 0x11, { 0 },                                  0,  120 },  /* SLPOUT */
  { 0x3A, { 0x55 },                               1,  0   },  /* COLMOD: 16 bits por pixel (RGB565) */
  { 0xC0, { 0x0D, 0x0D },                         2,  0   },  /* Power control 1 */
  { 0xC1, { 0x43, 0x00 },                         2,  0   },  /* Power control 2 */
  { 0xC2, { 0x00 },                               1,  0   },  /* Power control 3 */
  { 0xC5, { 0x00, 0x48 },                         2,  0   },  /* VCOM control */
  { 0xE0, { 0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98,
            0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00 }, 15, 0 },  /* Gamma positivo */
  { 0xE1, { 0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75,
            0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00 }, 15, 0 },  /* Gamma negativo */
};

/* Descriptor del ILI9486. MADCTL 0x28 = MV (intercambiar ejes, horizontal) + BGR. */
static const PanelDescriptor_t sDescriptor =
{
  .name             = "ILI9486",
  .initCommands     = sInitCommands,
  .initCommandCount = sizeof(sInitCommands) / sizeof(sInitCommands[0]),
  .madctlLandscape  = 0x28,
  .maxPclkHz        = 10000000,  /* Hz. Valor prudente sin validar; el ILI9486 acepta ciclos de escritura de decenas de ns */
};

/**
 * Nombre:      PanelIli9486GetDescriptor
 * Descripcion: Devuelve el descriptor del controlador ILI9486.
 * Entradas:    Ninguna.
 * Salidas:     Puntero al descriptor constante (nunca es NULL).
 */
const PanelDescriptor_t *PanelIli9486GetDescriptor(void)
{
  return &sDescriptor;
}
