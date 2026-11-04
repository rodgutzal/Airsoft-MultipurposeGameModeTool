/**
 * Archivo:           main.c
 * Descripcion:       Punto de entrada del firmware. Inicializa la RAM y los
 *                    procesos base, y despues queda en el ciclo principal.
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
#include "MainProcess.h"
#include "TimerDriver.h"

/**
 * Nombre:      app_main
 * Descripcion: Funcion que ESP-IDF llama al terminar el arranque. Inicializa
 *              las variables globales y los procesos base (reloj, puertos y
 *              timer periodico), y luego ejecuta el ciclo principal: espera el
 *              siguiente periodo del timer (TimerWaitMainTick), ejecuta las
 *              subrutinas del ciclo y marca el periodo como atendido
 *              (TimerEndMainTick). Si las subrutinas tardan mas de
 *              C_TIMER_PERIOD_MS, el timer lo cuenta y se consulta con
 *              TimerGetOverrunCount.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (no regresa).
 */
void app_main(void)
{
  InitRam();
  InitMainProcess();

  while(C_TRUE)
  {
    TimerWaitMainTick();

    /* Aqui van las subrutinas del ciclo principal, una vez cada C_TIMER_PERIOD_MS. */

    TimerEndMainTick();
  }
}
