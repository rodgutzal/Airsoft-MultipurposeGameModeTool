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

#include "Ram.h"

uint8_t  gTeam;
bool     gArmed;
bool     gActionButton;
uint8_t  gKeyPressed;
uint32_t gSystemTickMs;

/**
 * Nombre:      InitRam
 * Descripcion: Deja todas las variables globales en su valor inicial: equipo
 *              rojo, bomba sin armar, boton sin pulsar, ninguna tecla
 *              presionada (0xFF) y contador de milisegundos en cero.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (modifica las variables globales de Ram.h).
 */
void InitRam(void)
{
  gTeam         = TEAM_RED;
  gArmed        = false;
  gActionButton = false;
  gKeyPressed   = 0xFF;
  gSystemTickMs = 0;
}
