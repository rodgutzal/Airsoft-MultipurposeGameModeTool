#ifndef RAM_H
#define RAM_H

#include <stdint.h>
#include <stdbool.h>
#include "GlobalDefine.h"

/* Variables globales. Se definen en Ram.c y se inicializan en InitRam(). */

extern uint8_t  gTeam;                       /* TEAM_RED o TEAM_BLUE */
extern bool     gArmed;                      /* interruptor de llave */
extern bool     gActionButton;               /* push button de accion */
extern uint8_t  gKeyPressed;                 /* 0xFF = ninguna tecla */
extern uint32_t gSystemTickMs;               /* contador de milisegundos */

extern void InitRam(void);

#endif /* RAM_H */
