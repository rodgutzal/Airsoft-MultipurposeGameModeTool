/**
 * Archivo:           Ram.c
 * Descripcion:       Definicion de las variables globales del firmware y de
 *                    la subrutina que las inicializa.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#define C_RAM_EXPOSE_GLOBALS
#include "Ram.h"

/* Definicion de las variables declaradas en Ram.h (ahi estan sus significados
 * y el responsable de escritura de cada una). Sus valores iniciales los fija
 * InitRam, no el inicializador de C, para que el reinicio sea explicito. */
uint8_t  gTeam;
bool     gArmed;
bool     gActionButton;
uint8_t  gKeyPressed;

/**
 * Nombre:      InitRam
 * Descripcion: Deja todas las variables globales en su valor inicial: equipo
 *              rojo, bomba sin armar, boton sin pulsar, ninguna tecla
 *              presionada (C_KEY_NONE).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (modifica las variables globales de Ram.h).
 */
void InitRam(void)
{
  gTeam         = C_TEAM_RED;
  gArmed        = false;
  gActionButton = false;
  gKeyPressed   = C_KEY_NONE;
}
