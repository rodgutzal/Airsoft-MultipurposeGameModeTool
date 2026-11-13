# Referencia de la API de los drivers

Lista de las funciones públicas de cada módulo de `AirsoftToolSw/`: qué hacen, qué reciben, qué devuelven y desde dónde se pueden llamar. El detalle fino está en el comentario de cada función dentro del `.c`; este documento es el índice para no tener que abrir cada archivo.

Convenciones:
- `esp_err_t` es el código de error de ESP-IDF. `ESP_OK` es éxito; el resto se imprime con `esp_err_to_name`.
- Todos los drivers validan sus argumentos y devuelven `ESP_ERR_INVALID_ARG` si algo no es válido. No deciden qué hacer ante un error: lo decide quien llama.
- **Tarea principal** es la tarea de `app_main`, que corre el ciclo de 5 ms. **Ciclo de 5 ms** son las subrutinas dentro del `while(C_TRUE)` de `main.c`.

Resumen:

| Módulo | Archivos | Se llama desde | Bloquea |
| --- | --- | --- | --- |
| [`MainProcess`](#mainprocess) | `MainProcess.c/.h` | `app_main` | Sí, durante el arranque |
| [`Ram`](#ram) | `Ram.c/.h` | `app_main` | No |
| [`ClockDriver`](#clockdriver) | `ClockDriver.c/.h` | `InitMainProcess` | Breve |
| [`GpioDriver`](#gpiodriver) | `GpioDriver.c/.h` | Arranque y ciclo de 5 ms | No |
| [`FlashDriver`](#flashdriver) | `FlashDriver.c/.h` | Arranque y fuera del ciclo de 5 ms | **Sí, decenas de ms al escribir** |
| [`HeartbeatDriver`](#heartbeatdriver) | `HeartbeatDriver.c/.h` | Arranque y ciclo de 5 ms | No |
| [`DisplayDriver`](#displaydriver) | `DisplayDriver.c/.h`, `PanelDriver.h`, `PanelIli9486Driver.c/.h`, `PanelSt7796Driver.c/.h` | Arranque y fuera del ciclo de 5 ms | **Sí, hasta que termina el DMA** |
| [`TimerDriver`](#timerdriver) | `TimerDriver.c/.h` | Arranque y ciclo de 5 ms | `TimerWaitMainTick` duerme hasta el siguiente periodo |

## MainProcess

Secuencia de arranque del micro. Solo la llama `app_main`.

| Función | Descripción |
| --- | --- |
| `void InitMainProcess(void)` | Imprime los datos del chip (núcleos, revisión, flash, PSRAM) y arranca en orden: reloj, puertos simples, flash, heartbeat y timer periódico. Si el reloj, los puertos o el timer fallan, el firmware aborta (`ESP_ERROR_CHECK`). Si la flash o el heartbeat fallan, solo avisa en el log y sigue. |
| `void InitSimpleGpioPorts(void)` | Configura los GPIO simples: hoy solo el dato de la tira LED en bajo. El teclado, los switches y el botón ya no se configuran aquí: en v0.8 están en el MCP23017 (sin driver aún) y sus antiguos GPIO son el bus de la pantalla y el SPI del touch; ver [`MapaPines.md`](MapaPines.md). Aborta si el pin no se puede configurar. |

## Ram

Variables globales de la aplicación. Solo son visibles si el archivo define `C_RAM_EXPOSE_GLOBALS` antes de incluir `Ram.h` (hoy, `main.c` y `Ram.c`).

| Elemento | Descripción |
| --- | --- |
| `void InitRam(void)` | Deja las variables en su valor inicial. Se llama una vez, antes que cualquier otra cosa. |
| `uint8_t gTeam` | `C_TEAM_RED` (0) o `C_TEAM_BLUE` (1). Inicial: rojo. Escritor previsto: `InputDriver`. |
| `bool gArmed` | Interruptor de llave de la bomba. Inicial: `false`. Escritor previsto: `InputDriver`. |
| `bool gActionButton` | Push button de acción. Inicial: `false`. Escritor previsto: `InputDriver`. |
| `uint8_t gKeyPressed` | Tecla del teclado, o `C_KEY_NONE` (0xFF) si no hay. Escritor previsto: `KeypadDriver`. |

Cada variable debe tener un solo escritor (R6 de [`Arquitectura.md`](Arquitectura.md)). Hoy nadie las escribe después de `InitRam`.

## ClockDriver

Reloj del CPU. Lo llama `InitMainProcess`.

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t ConfigCpuClock(void)` | Fija el CPU a `C_CPU_CLOCK_TARGET_MHZ` (240 MHz, desde el PLL sobre el cristal de 40 MHz), sin escalado de frecuencia ni light sleep, con `esp_pm_configure`. Informa la fuente del reloj y verifica la frecuencia. Requiere `CONFIG_PM_ENABLE=y`. | `ESP_OK`; el error de `esp_pm_configure`; o el de la verificación. |
| `esp_err_t VerifyCpuClockFrequency(void)` | Lee la frecuencia real del CPU y la compara con la objetivo. | `ESP_OK`; `ESP_FAIL` si es distinta (también avisa en el log); u otro error si no se pudo leer. |

## GpioDriver

Configuración y escritura de pines. Valida que el pin exista y no esté en `C_GPIO_RESERVED_MASK` (GPIO19/20, 26 a 32, 35 a 37). Nunca activa pull-up ni pull-down internos.

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t ConfigGpioAsOutput(int pin, int level)` | Pone el pin como salida y le fija el nivel inicial (0 bajo, distinto de 0 alto). | `ESP_OK`; `ESP_ERR_INVALID_ARG` si el pin no existe o está reservado; u otro error de ESP-IDF. |
| `esp_err_t ConfigGpioAsInput(int pin)` | Pone el pin como entrada sin resistencias internas. El nivel en reposo lo fija el hardware (pull-up externo). | Igual que la anterior. |
| `esp_err_t SetGpioLevel(int pin, int level)` | Fija el nivel de un pin que ya es salida. No escribe en el log, así que se puede usar en el ciclo de 5 ms. | `ESP_OK`; `ESP_ERR_INVALID_ARG` si el pin no existe o está reservado. |

## FlashDriver

Almacenamiento persistente en NVS, dentro del espacio de nombres `C_FLASH_NAMESPACE` ("airsoft"). Las claves tienen de 1 a `C_FLASH_KEY_MAX_LENGTH` (15) caracteres.

**Las escrituras y el borrado son bloqueantes y tardan decenas de milisegundos. No llamarlas desde el ciclo de 5 ms ni desde una interrupción.** El timer sigue funcionando mientras la flash se escribe porque su ISR corre en IRAM (`CONFIG_GPTIMER_ISR_IRAM_SAFE`), pero la tarea que escribe queda detenida.

Todas, menos `FlashInit`, devuelven `ESP_ERR_INVALID_STATE` si `FlashInit` no se ejecutó.

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t FlashInit(void)` | Inicializa NVS. Si la partición está llena o es de otra versión, **la borra y la crea de nuevo** (se pierden los datos). | `ESP_OK`; o el error de NVS. |
| `esp_err_t FlashReadU32(const char *key, uint32_t *value)` | Lee un entero de 32 bits. | `ESP_OK`; `ESP_ERR_NVS_NOT_FOUND` si la clave no existe todavía (usa un valor por omisión); `ESP_ERR_INVALID_ARG` si la clave no es válida o `value` es NULL. |
| `esp_err_t FlashWriteU32(const char *key, uint32_t value)` | Guarda un entero de 32 bits y confirma la escritura. Bloqueante. | `ESP_OK`; `ESP_ERR_INVALID_ARG` si la clave no es válida. |
| `esp_err_t FlashReadBlob(const char *key, void *buffer, size_t *length)` | Lee un bloque de bytes. `length` entra con el tamaño de `buffer` y sale con el tamaño guardado. | `ESP_OK`; `ESP_ERR_NVS_NOT_FOUND`; `ESP_ERR_NVS_INVALID_LENGTH` si `buffer` es más chico que el bloque; `ESP_ERR_INVALID_ARG`. |
| `esp_err_t FlashWriteBlob(const char *key, const void *data, size_t length)` | Guarda un bloque y confirma la escritura. Bloqueante. | `ESP_OK`; `ESP_ERR_INVALID_ARG` si la clave no es válida, `data` es NULL o `length` es 0. |
| `esp_err_t FlashEraseAll(void)` | Borra todas las claves de `C_FLASH_NAMESPACE`. Bloqueante. | `ESP_OK`; o el error de NVS. |

Uso típico:

```c
uint32_t score = 0;
if(FlashReadU32("score", &score) == ESP_ERR_NVS_NOT_FOUND)
{
  score = 0;                       /* primera vez: valor por omision */
}
...
FlashWriteU32("score", score);     /* fuera del ciclo de 5 ms */
```

## HeartbeatDriver

LED de estado en `C_PIN_LED_ESTADO` (GPIO43). Indica que el ciclo principal sigue corriendo: cambia de estado cada `C_HEARTBEAT_HALF_TICKS` (100) periodos, es decir, un ciclo completo cada `C_HEARTBEAT_PERIOD_MS` (1 s). Si el ciclo se atasca, el LED se queda fijo.

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t HeartbeatInit(void)` | Configura el pin como salida con el LED apagado y reinicia la cuenta. Una vez, antes de llamar `HeartbeatTick`. | `ESP_OK`; o el error de `ConfigGpioAsOutput`. |
| `void HeartbeatTick(void)` | Avanza un periodo. Se llama **una vez por cada periodo de 5 ms** desde el ciclo principal. No escribe en el log. | Nada. |

## DisplayDriver

Pantalla TFT sobre el bus i80 de `esp_lcd` (16 bits, `C_LCD_BUS_WIDTH`). La API no depende del controlador: el modelo (ILI9486 por omisión, o ST7796U) se elige en `menuconfig` > Airsoft Tool > `AIRSOFT_LCD_CONTROLLER` y su secuencia de inicio está en `PanelIli9486Driver.c` o `PanelSt7796Driver.c` (cada uno solo entrega un `PanelDescriptor_t`, no toca el hardware). RST va a EN y CS a GND, por eso no hay GPIO para ellos. **Las transferencias son bloqueantes (esperan al DMA): no llamarlas desde el ciclo de 5 ms.** No maneja la retroiluminación (U6 GPB4, pendiente del driver I2C). **Sin validar en hardware.**

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t DisplayInit(void)` | Crea el bus, la interfaz del panel y el buffer DMA (`C_LCD_H_RES` × `C_LCD_BUFFER_LINES` × 2 bytes), ejecuta la secuencia de inicio, fija la orientación horizontal (480x320) y enciende la pantalla. Una sola vez. | `ESP_OK`; `ESP_ERR_INVALID_STATE` si ya se inicializó; `ESP_ERR_NO_MEM`; u otro error de `esp_lcd`. |
| `esp_err_t DisplayFillColor(uint16_t color565)` | Llena toda la pantalla con un color RGB565 (`C_LCD_COLOR_*`). | `ESP_OK`; `ESP_ERR_INVALID_STATE` si falta `DisplayInit`; `ESP_ERR_TIMEOUT`; u otro error de `esp_lcd`. |
| `esp_err_t DisplayDrawBitmap(int xStart, int yStart, int xEnd, int yEnd, const uint16_t *pixels)` | Dibuja un rectángulo RGB565 (esquinas inclusivas). Debe caber en `C_LCD_BUFFER_LINES` líneas y estar en memoria apta para DMA. | Igual que la anterior; `ESP_ERR_INVALID_ARG` si el rectángulo no es válido o `pixels` es NULL. |
| `const char *DisplayGetControllerName(void)` | Nombre del controlador elegido. | `"ILI9486"`, `"ST7796U"` o `"sin inicializar"`. |

Para agregar otro controlador: crear `Panel[Nombre]Driver.c/.h` con su `PanelDescriptor_t`, añadir la opción en `Kconfig.projbuild` y el caso en `DisplaySelectPanel`.

## TimerDriver

Timer periódico de hardware (GPTimer) que genera la interrupción de `C_TIMER_PERIOD_MS` (5 ms) y marca el paso del ciclo principal. La bandera, la notificación a la tarea y la ISR son internas del driver.

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `esp_err_t TimerInit(void)` | Crea el timer (1 µs por cuenta, alarma cada 5 ms con recarga automática) y registra la ISR. Pone en cero la bandera y los contadores. No lo arranca. | `ESP_OK`; o el error de ESP-IDF. |
| `esp_err_t TimerStart(void)` | Arranca el timer. Requiere `TimerInit`. | `ESP_OK`; `ESP_ERR_INVALID_STATE` si el timer no está configurado. |
| `void TimerWaitMainTick(void)` | Duerme la tarea que la llama hasta que empieza un nuevo periodo. Si el periodo ya empezó, regresa de inmediato. Solo la debe llamar **una** tarea: la del ciclo principal. | Nada. |
| `void TimerEndMainTick(void)` | Marca el periodo como atendido. Se llama al terminar las subrutinas. | Nada. |
| `uint32_t TimerGetSystemTickMs(void)` | Milisegundos desde `TimerInit`, en pasos de 5 ms. Se desborda a los 49.7 días. | Milisegundos. |
| `uint32_t TimerGetOverrunCount(void)` | Cuántos periodos encontraron el ciclo anterior sin terminar. Si crece, las subrutinas tardan más de 5 ms en total. | Periodos perdidos desde `TimerInit`. |

Forma del ciclo principal (`main.c`):

```c
while(C_TRUE)
{
  TimerWaitMainTick();   /* duerme hasta el siguiente periodo de 5 ms */

  HeartbeatTick();       /* subrutinas del ciclo, una vez cada 5 ms */

  TimerEndMainTick();    /* periodo atendido */
}
```

## Qué falta

Estos módulos están en el plan de [`Arquitectura.md`](Arquitectura.md) pero todavía no existen, así que no tienen API: `WatchdogDriver`, `DmaDriver`, `LedStripDriver`, touch y LVGL de la pantalla, `AudioDriver`, `KeypadDriver` / `InputDriver` y `AdcDriver`. Cuando se agreguen, su API se documenta aquí en el mismo PR.
