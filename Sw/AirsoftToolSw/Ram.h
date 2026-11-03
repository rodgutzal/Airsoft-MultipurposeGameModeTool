/**
 * Archivo:           Ram.h
 * Descripcion:       Declaracion de las variables globales del firmware y de
 *                    la subrutina que las inicializa (InitRam, en Ram.c).
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef RAM_H
#define RAM_H

#include <stdint.h>
#include <stdbool.h>
#include "GlobalDefine.h"

/* Variables globales. Se definen en Ram.c y se inicializan en InitRam(). */

extern uint8_t  gTeam;                       /* C_TEAM_RED o C_TEAM_BLUE */
extern bool     gArmed;                      /* interruptor de llave */
extern bool     gActionButton;               /* push button de accion */
extern uint8_t  gKeyPressed;                 /* C_KEY_NONE = ninguna tecla */
extern volatile uint32_t gSystemTickMs;      /* contador de milisegundos (lo suma la ISR del timer) */
extern uint32_t gTickOverrunCount;           /* periodos del timer que el ciclo principal no alcanzo a atender */
extern volatile Union8_t u8MainFlag;     /* banderas del ciclo principal */

/* Nombres de bit de u8MainFlag: cada bf_ es un alias de un bit y se usa como
 * u8MainFlag.bf_5MsMainLoopFlag.
 * Regla de escritura: cada bit lo escribe un solo contexto a la vez, porque
 * modificar un bit es una lectura-modificacion-escritura del byte completo
 * y no es atomica. */
#define bf_5MsMainLoopFlag  Bits.Bit0  /* la ISR lo enciende cada C_TIMER_PERIOD_MS */

void InitRam(void);

#endif /* RAM_H */
