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
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "MainProcess.h"
#include "TimerDriver.h"

/**
 * Nombre:      app_main
 * Descripcion: Funcion que ESP-IDF llama al terminar el arranque. Inicializa
 *              las variables globales, los procesos base y el timer
 *              periodico, y luego ejecuta el ciclo principal: la tarea duerme
 *              hasta que la interrupcion del timer (cada C_TIMER_PERIOD_MS)
 *              la despierta. Si la bandera bf_5MsMainLoopFlag de u8MainFlag
 *              es verdadera, ejecuta las subrutinas del ciclo y al terminar
 *              apaga la bandera. Si la ISR encuentra la bandera todavia
 *              encendida (las subrutinas tardaron mas de C_TIMER_PERIOD_MS),
 *              se cuenta en gTickOverrunCount.
 * Entradas:    Ninguna.
 * Salidas:     Ninguna (no regresa).
 */
void app_main(void)
{
  InitRam();
  InitMainProcess();

  ESP_ERROR_CHECK(ConfigPeriodicTimer(xTaskGetCurrentTaskHandle()));
  ESP_ERROR_CHECK(StartPeriodicTimer());

  while(C_TRUE)
  {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    if(u8MainFlag.bf_5MsMainLoopFlag == C_TRUE)
    {
      /* Aqui van las subrutinas del ciclo principal, una vez cada C_TIMER_PERIOD_MS. */

      u8MainFlag.bf_5MsMainLoopFlag = C_FALSE;
    }
  }
}
