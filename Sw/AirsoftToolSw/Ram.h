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

/* Interruptor C_RAM_EXPOSE_GLOBALS.
 * Ram.h es el header comun: siempre entrega las constantes y los tipos de
 * GlobalDefine.h. Las variables globales y InitRam() solo se declaran si el
 * archivo define C_RAM_EXPOSE_GLOBALS antes de incluir Ram.h. Los drivers no lo
 * definen, asi que si intentan usar una variable global no compila (R1).
 * Lo definen: main.c y Ram.c. */
#ifdef C_RAM_EXPOSE_GLOBALS

/* Modelo de la aplicacion. Se define en Ram.c y se inicializa en InitRam().
 * Cada variable tiene un solo responsable de escritura (R6); los demas la leen.
 * El estado interno de un driver (banderas, contadores del timer) no va aqui:
 * es privado del driver y se consulta con sus funciones. */

extern uint8_t  gTeam;                       /* C_TEAM_RED o C_TEAM_BLUE. Responsable de escritura (previsto): InputDriver */
extern bool     gArmed;                      /* interruptor de llave. Responsable de escritura (previsto): InputDriver */
extern bool     gActionButton;               /* push button de accion. Responsable de escritura (previsto): InputDriver */
extern uint8_t  gKeyPressed;                 /* C_KEY_NONE = ninguna tecla. Responsable de escritura (previsto): KeypadDriver */

void InitRam(void);

#endif /* C_RAM_EXPOSE_GLOBALS */

#endif /* RAM_H */
