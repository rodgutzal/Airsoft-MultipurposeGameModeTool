# Sw

Firmware de la herramienta, con ESP-IDF v6.1 para el ESP32-S3-DevKitC-1 N16R8.

Documentación: [`GuiaDesarrollo.md`](GuiaDesarrollo.md) (reglas y flujo de trabajo, empezar por ahí), [`ReferenciaApi.md`](ReferenciaApi.md) (funciones de cada driver), [`MapaPines.md`](MapaPines.md) (pines contra hardware), [`Arquitectura.md`](Arquitectura.md) (diseño objetivo), [`MemoryUsage.md`](MemoryUsage.md) y [`Warnings.md`](Warnings.md) (seguimiento).

Estado actual: proyecto base. Al arrancar inicializa la RAM, fija el reloj del CPU a 240 MHz con el `ClockDriver`, configura los puertos simples e inicia un timer de 5 ms que gobierna el ciclo principal. La única subrutina del ciclo es el heartbeat (LED en GPIO43, ciclo de 1 s); las demás todavía no existen y su espacio está marcado en `main.c`. La consola va por el puerto USB (USB-Serial-JTAG), no por el UART. El pinout de `GlobalDefine.h` es el de v0.7 y el hardware ya es v0.8 o posterior; las diferencias están en [`MapaPines.md`](MapaPines.md). No se ha flasheado en la placa: solo se comprobó que compila.

## Arquitectura

El firmware se organiza en capas. Cada capa solo usa a la de abajo. El diseño objetivo (reglas de encapsulamiento, catálogo de drivers, tareas y núcleos, memoria y plan de PRs) está en [`Arquitectura.md`](Arquitectura.md); esta sección y las siguientes describen el código **actual**.

```mermaid
flowchart TB
  subgraph APP["Aplicación (Sw/AirsoftToolSw)"]
    MAIN["main.c<br/>app_main y ciclo principal"]
    MP["MainProcess<br/>procesos base"]
    RAM["Ram<br/>variables globales"]
    DRV["Drivers propios<br/>ClockDriver, DisplayDriver, FlashDriver, GpioDriver, HeartbeatDriver, PanelIli9486Driver, PanelSt7796Driver, TimerDriver"]
    GD["GlobalDefine.h<br/>constantes y tipos"]
  end
  subgraph IDF["ESP-IDF v6.1"]
    FR["FreeRTOS"]
    GPIO["esp_driver_gpio"]
    GPT["esp_driver_gptimer"]
    PM["esp_pm / esp_clk_tree"]
    NVS["nvs_flash"]
  end
  HW["ESP32-S3: GPIO, GPTimer, PLL 240 MHz, flash"]
  MAIN --> MP
  MAIN --> RAM
  MAIN --> DRV
  MP --> DRV
  DRV -. "solo constantes y tipos" .-> RAM
  MP --> RAM
  RAM --> GD
  DRV --> PM
  DRV --> GPIO
  DRV --> GPT
  DRV --> NVS
  NVS --> HW
  MAIN --> FR
  GPIO --> HW
  GPT --> HW
  PM --> HW
```

Los drivers incluyen `Ram.h` solo para obtener constantes y tipos (flecha punteada); no leen ni escriben sus variables, y el compilador lo hace cumplir. El estado interno del `TimerDriver` (bandera, contadores) es privado del driver. Los pendientes frente al diseño objetivo están en [`Arquitectura.md`](Arquitectura.md#10-estado-actual-frente-al-objetivo).

Reglas de la arquitectura:
- Las constantes (`C_*`), los tipos y las uniones viven solo en `GlobalDefine.h`.
- Ningún archivo incluye `GlobalDefine.h` directamente: se incluye solo desde `Ram.h`, y el resto de los archivos incluye `Ram.h` para obtener las constantes y los tipos (R8 de [`Arquitectura.md`](Arquitectura.md)).
- Las variables globales de `Ram.h` solo se declaran si el archivo define `C_RAM_EXPOSE_GLOBALS` antes de incluirlo. Lo definen `main.c` y `Ram.c`. Un driver que no lo define y usa una variable global no compila (R1).
- Las variables globales y los alias de bit (`bf_*`) viven en `Ram.c` / `Ram.h`.
- Cada periférico tiene su driver `[nombre]Driver.c` / `.h`. Un driver valida sus argumentos y devuelve `esp_err_t`; no decide qué hacer ante un error.
- `MainProcess` agrupa el arranque del micro (reloj y puertos). Quien llama a un driver decide si un error es fatal (`ESP_ERROR_CHECK`).

## Estructura de archivos

El código vive en `AirsoftToolSw/` (declarado como componente en `CMakeLists.txt` con `EXTRA_COMPONENT_DIRS`, en lugar de la carpeta `main` por defecto).

| Archivo | Contenido |
| --- | --- |
| `main.c` | `app_main`: inicializa, arranca el timer y ejecuta el ciclo principal. |
| `GlobalDefine.h` | Constantes `C_*` (pines de [`../Hw/esquematico_v1/README.md`](../Hw/esquematico_v1/README.md), tiempos, conversiones, `C_TRUE` / `C_FALSE`) y las uniones `Union8_t`, `Union16_t`, `Union32_t`. |
| `Ram.c` / `Ram.h` | Modelo de la aplicación (`gTeam`, `gArmed`, `gActionButton`, `gKeyPressed`) e `InitRam`. |
| `MainProcess.c` / `.h` | Secuencia de arranque: `InitMainProcess` (reloj, puertos simples, almacenamiento en flash y timer) e `InitSimpleGpioPorts`. |
| `ClockDriver.c` / `.h` | Reloj del CPU: `ConfigCpuClock` (240 MHz por PLL con `esp_pm`) y `VerifyCpuClockFrequency`. |
| `GpioDriver.c` / `.h` | `ConfigGpioAsOutput`, `ConfigGpioAsInput` y `SetGpioLevel`, con validación de pin. |
| `DisplayDriver.c` / `.h` | Pantalla TFT sobre el bus i80 de `esp_lcd` (16 bits). API independiente del controlador: `DisplayInit`, `DisplayFillColor`, `DisplayDrawBitmap`, `DisplayGetControllerName`. El controlador (ILI9486 o ST7796U) se elige en `menuconfig` > Airsoft Tool (`AIRSOFT_LCD_CONTROLLER`). Transferencias bloqueantes; no se llama desde el ciclo de 5 ms. **Sin validar en hardware.** |
| `PanelDriver.h` | Tipos comunes de la capa de panel: `PanelInitCommand_t` y `PanelDescriptor_t` (secuencia de inicio, MADCTL, reloj máximo). |
| `PanelIli9486Driver.c` / `.h` | Descriptor del ILI9486: `PanelIli9486GetDescriptor`. Solo datos, no toca el hardware. Valores de la comunidad, sin validar. |
| `PanelSt7796Driver.c` / `.h` | Descriptor del ST7796U: `PanelSt7796GetDescriptor`. Solo datos, no toca el hardware. Valores del ST7796 de la comunidad, sin confirmar para la variante U. |
| `Kconfig.projbuild` | Opción `AIRSOFT_LCD_CONTROLLER` (ILI9486 por omisión, o ST7796U). |
| `HeartbeatDriver.c` / `.h` | LED de heartbeat en `C_PIN_LED_ESTADO` (GPIO43): `HeartbeatInit` y `HeartbeatTick`. Se llama una vez por periodo de 5 ms y el LED cambia cada `C_HEARTBEAT_HALF_TICKS` (100 periodos = 0.5 s), así que el ciclo completo dura `C_HEARTBEAT_PERIOD_MS` (1 s). Si el ciclo principal se atasca, el LED se queda fijo. No escribe en el log. |
| `FlashDriver.c` / `.h` | Almacenamiento persistente en flash (NVS) bajo el espacio de nombres `C_FLASH_NAMESPACE`: `FlashInit`, `FlashReadU32` / `FlashWriteU32`, `FlashReadBlob` / `FlashWriteBlob` y `FlashEraseAll`. Las escrituras son bloqueantes (decenas de ms): no se llaman dentro de las subrutinas del ciclo de 5 ms. |
| `partitions.csv` | Tabla de particiones propia (ver Configuración). |
| `GuiaDesarrollo.md` | Guía para mantener el firmware: reglas de código, cómo agregar un driver, flujo de Git y qué documentación actualizar. |
| `ReferenciaApi.md` | Funciones públicas de cada driver, con su contexto de uso y sus códigos de error. |
| `MapaPines.md` | Pines del hardware contra las constantes `C_PIN_*`, con las diferencias abiertas. |
| `TimerDriver.c` / `.h` | Timer periódico de 5 ms (GPTimer): `TimerInit`, `TimerStart`, `TimerWaitMainTick`, `TimerEndMainTick`, `TimerGetSystemTickMs` y `TimerGetOverrunCount`. La bandera `u8MainFlag` (bit `bf_5MsMainLoopFlag`), los contadores, la notificación y la ISR son privados del driver. |

Para agregar un driver nuevo: crear `[nombre]Driver.c` / `.h` y sumarlo a `SRCS` en `AirsoftToolSw/CMakeLists.txt` (y su componente de ESP-IDF a `PRIV_REQUIRES`).

## Relación entre archivos

Cada flecha es un `#include` de un archivo propio.

```mermaid
flowchart LR
  main_c["main.c"] --> Ram_h["Ram.h"]
  main_c --> MainProcess_h["MainProcess.h"]
  main_c --> TimerDriver_h["TimerDriver.h"]
  main_c --> HeartbeatDriver_h["HeartbeatDriver.h"]
  Ram_h --> GlobalDefine_h["GlobalDefine.h"]
  Ram_c["Ram.c"] --> Ram_h
  MainProcess_c["MainProcess.c"] --> MainProcess_h
  MainProcess_c --> Ram_h
  MainProcess_c --> ClockDriver_h["ClockDriver.h"]
  ClockDriver_c["ClockDriver.c"] --> ClockDriver_h
  ClockDriver_c --> Ram_h
  MainProcess_c --> FlashDriver_h["FlashDriver.h"]
  FlashDriver_c["FlashDriver.c"] --> FlashDriver_h
  FlashDriver_c --> Ram_h
  MainProcess_c --> GpioDriver_h["GpioDriver.h"]
  GpioDriver_c["GpioDriver.c"] --> GpioDriver_h
  GpioDriver_c --> Ram_h
  MainProcess_c --> HeartbeatDriver_h
  HeartbeatDriver_c["HeartbeatDriver.c"] --> HeartbeatDriver_h
  HeartbeatDriver_c --> Ram_h
  HeartbeatDriver_c --> GpioDriver_h
  TimerDriver_c["TimerDriver.c"] --> TimerDriver_h
  TimerDriver_c --> Ram_h
  MainProcess_c --> DisplayDriver_h["DisplayDriver.h"]
  DisplayDriver_c["DisplayDriver.c"] --> DisplayDriver_h
  DisplayDriver_c --> Ram_h
  DisplayDriver_c --> PanelIli9486Driver_h["PanelIli9486Driver.h"]
  DisplayDriver_c --> PanelSt7796Driver_h["PanelSt7796Driver.h"]
  PanelIli9486Driver_h --> PanelDriver_h["PanelDriver.h"]
  PanelSt7796Driver_h --> PanelDriver_h
  PanelDriver_h --> Ram_h
  PanelIli9486Driver_c["PanelIli9486Driver.c"] --> PanelIli9486Driver_h
  PanelSt7796Driver_c["PanelSt7796Driver.c"] --> PanelSt7796Driver_h
```

Ningún driver usa variables de `Ram`: `ClockDriver`, `FlashDriver`, `GpioDriver`, `HeartbeatDriver` y `TimerDriver` incluyen `Ram.h` solo para las constantes `C_*` y las uniones. `main.c` y `Ram.c` definen `C_RAM_EXPOSE_GLOBALS` para ver las variables.

## Diagrama de clases UML

Cada archivo `.c` / `.h` se modela como un módulo (clase estática). Los miembros con `-` son privados (`static`).

```mermaid
classDiagram
  class GlobalDefine {
    <<header>>
    C_PIN_xxx pines
    C_TIMER_PERIOD_MS
    C_CPU_CLOCK_TARGET_MHZ
    C_TRUE / C_FALSE
    C_GPIO_RESERVED_MASK
  }
  class Union8_t {
    <<union>>
    +uint8_t Byte
    +Bits Bit0..Bit7
  }
  class Union16_t {
    <<union>>
    +uint16_t Word
    +uint8_t Bytes_2
    +Bits Bit0..Bit15
  }
  class Union32_t {
    <<union>>
    +uint32_t Dword
    +uint16_t Words_2
    +uint8_t Bytes_4
    +Bits Bit0..Bit31
  }
  class Ram {
    <<module>>
    +uint8_t gTeam
    +bool gArmed
    +bool gActionButton
    +uint8_t gKeyPressed
    +InitRam() void
  }
  class MainProcess {
    <<module>>
    +InitMainProcess() void
    +InitSimpleGpioPorts() void
  }
  class ClockDriver {
    <<module>>
    +ConfigCpuClock() esp_err_t
    +VerifyCpuClockFrequency() esp_err_t
  }
  class FlashDriver {
    <<module>>
    +FlashInit() esp_err_t
    +FlashReadU32(key, value) esp_err_t
    +FlashWriteU32(key, value) esp_err_t
    +FlashReadBlob(key, buffer, length) esp_err_t
    +FlashWriteBlob(key, data, length) esp_err_t
    +FlashEraseAll() esp_err_t
    -IsFlashKeyValid(key) bool
    -OpenFlashNamespace(mode, handle) esp_err_t
  }
  class GpioDriver {
    <<module>>
    +ConfigGpioAsOutput(pin, level) esp_err_t
    +ConfigGpioAsInput(pin) esp_err_t
    +SetGpioLevel(pin, level) esp_err_t
    -IsGpioPinUsable(pin) bool
  }
  class HeartbeatDriver {
    <<module>>
    +HeartbeatInit() esp_err_t
    +HeartbeatTick() void
    -sTickCount uint32_t
    -sLedLevel int
  }
  class DisplayDriver {
    <<module>>
    +DisplayInit() esp_err_t
    +DisplayFillColor(color565) esp_err_t
    +DisplayDrawBitmap(xStart, yStart, xEnd, yEnd, pixels) esp_err_t
    +DisplayGetControllerName() char*
    -DisplayWriteWindow() esp_err_t
    -DisplayColorTransferDoneIsr() bool
    -sPanel PanelDescriptor_t*
  }
  class PanelIli9486Driver {
    <<module>>
    +PanelIli9486GetDescriptor() PanelDescriptor_t*
  }
  class PanelSt7796Driver {
    <<module>>
    +PanelSt7796GetDescriptor() PanelDescriptor_t*
  }
  class TimerDriver {
    <<module>>
    +TimerInit() esp_err_t
    +TimerStart() esp_err_t
    +TimerWaitMainTick() void
    +TimerEndMainTick() void
    +TimerGetSystemTickMs() uint32_t
    +TimerGetOverrunCount() uint32_t
    -u8MainFlag Union8_t
    -PeriodicTimerAlarmIsr() bool
  }
  class Main {
    <<module>>
    +app_main() void
  }
  Union8_t ..> GlobalDefine : definido en
  Union16_t ..> GlobalDefine : definido en
  Union32_t ..> GlobalDefine : definido en
  TimerDriver --> Union8_t : u8MainFlag privado
  Main ..> Ram : usa
  Main ..> MainProcess : usa
  Main ..> TimerDriver : espera el periodo
  Main ..> HeartbeatDriver : HeartbeatTick cada 5 ms
  MainProcess ..> ClockDriver : usa
  MainProcess ..> FlashDriver : usa
  MainProcess ..> GpioDriver : usa
  MainProcess ..> HeartbeatDriver : HeartbeatInit
  HeartbeatDriver ..> GpioDriver : ConfigGpioAsOutput / SetGpioLevel
  HeartbeatDriver ..> Ram : usa constantes
  MainProcess ..> DisplayDriver : DisplayInit
  DisplayDriver ..> PanelIli9486Driver : descriptor (si Kconfig = ILI9486)
  DisplayDriver ..> PanelSt7796Driver : descriptor (si Kconfig = ST7796U)
  DisplayDriver ..> Ram : usa constantes
  FlashDriver ..> Ram : usa constantes
  MainProcess ..> TimerDriver : usa
  MainProcess ..> Ram : usa constantes
  GpioDriver ..> Ram : usa constantes
  ClockDriver ..> Ram : usa constantes
  TimerDriver ..> Ram : usa constantes
```

## Secuencia de arranque

```mermaid
sequenceDiagram
  participant IDF as ESP-IDF
  participant Main as app_main
  participant Ram
  participant MP as MainProcess
  participant Clk as ClockDriver
  participant Gpio as GpioDriver
  participant Fl as FlashDriver
  participant Hb as HeartbeatDriver
  participant Tim as TimerDriver
  IDF->>Main: arranque, CPU a 240 MHz
  Main->>Ram: InitRam()
  Main->>MP: InitMainProcess()
  MP->>MP: imprime chip, flash y PSRAM
  MP->>Clk: ConfigCpuClock()
  Note over Clk: esp_pm_configure fija 240 MHz y<br/>VerifyCpuClockFrequency lo comprueba
  Clk-->>MP: esp_err_t
  MP->>Gpio: InitSimpleGpioPorts(): ConfigGpioAsOutput / ConfigGpioAsInput
  Gpio-->>MP: esp_err_t
  MP->>Fl: FlashInit()
  Note over Fl: nvs_flash_init; si la particion esta llena<br/>o es de otra version, la borra y la crea
  Fl-->>MP: esp_err_t (si falla solo se avisa)
  MP->>Hb: HeartbeatInit()
  Note over Hb: configura GPIO43 como salida, LED apagado
  Hb-->>MP: esp_err_t (si falla solo se avisa)
  MP->>Tim: TimerInit()
  MP->>Tim: TimerStart()
  Tim-->>MP: esp_err_t
  Note over Main: entra al ciclo principal
```

## Interrupción de 5 ms y ciclo principal

```mermaid
sequenceDiagram
  participant T as GPTimer (hardware)
  participant ISR as PeriodicTimerAlarmIsr
  participant S as Estado interno de TimerDriver
  participant L as Ciclo principal (app_main)
  loop cada 5 ms
    T->>ISR: alarma
    ISR->>S: tick de milisegundos += 5
    alt bf_5MsMainLoopFlag == C_TRUE
      ISR->>S: periodos perdidos++
    else bf_5MsMainLoopFlag == C_FALSE
      ISR->>S: bf_5MsMainLoopFlag = C_TRUE
    end
    ISR->>L: notificación a la tarea que espera
    L->>L: TimerWaitMainTick() regresa
    L->>L: ejecuta las subrutinas (HeartbeatTick)
    L->>S: TimerEndMainTick() apaga bf_5MsMainLoopFlag
  end
```

Flujo del ciclo principal:

```mermaid
flowchart TD
  A(["Inicio del ciclo"]) --> B["TimerWaitMainTick: la tarea duerme<br/>hasta el siguiente periodo de 5 ms"]
  B --> D["Subrutinas del ciclo, una vez cada 5 ms<br/>HeartbeatTick invierte el LED cada 100 periodos"]
  D --> E["TimerEndMainTick"]
  E --> B
```

Si las subrutinas tardan más de 5 ms, la siguiente interrupción encuentra la bandera todavía en `C_TRUE`: no la vuelve a escribir y suma un periodo perdido, que se consulta con `TimerGetOverrunCount()`. Ese contador mide si el trabajo del ciclo cabe en el periodo. `TimerGetSystemTickMs()` devuelve los milisegundos desde el arranque del timer.

La bandera es un bit de un byte, y modificarlo es una lectura-modificación-escritura que no es atómica. Por eso cada bit lo escribe un solo contexto a la vez: la ISR lo enciende solo cuando está apagado y `TimerEndMainTick()` lo apaga solo cuando está encendido. Todo esto es interno del driver; el ciclo principal solo llama a `TimerWaitMainTick()` y `TimerEndMainTick()`.

## Configuración

`sdkconfig.defaults` fija:
- target `esp32s3`, flash de 16 MB y PSRAM octal de 8 MB a 80 MHz;
- CPU a 240 MHz (PLL sobre el cristal de 40 MHz; el oscilador interno RC_FAST de unos 17.5 MHz no se usa como fuente del CPU);
- `CONFIG_PM_ENABLE`, necesario para `esp_pm_configure` en `ConfigCpuClock`;
- la tabla de particiones propia `partitions.csv` (`CONFIG_PARTITION_TABLE_CUSTOM`);
- `CONFIG_GPTIMER_ISR_IRAM_SAFE`: la ISR del timer de 5 ms sigue viva mientras se escribe o borra la flash;
- consola por el USB-Serial-JTAG (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG`) y log de la ROM apagado (`CONFIG_BOOT_ROM_LOG_ALWAYS_OFF`): así GPIO43 (TX del UART0) queda libre para el LED de heartbeat y no parpadea con los mensajes. Los logs se ven por el puerto USB de la tarjeta, no por el puerto UART.

### Tabla de particiones

La flash es de 16 MB. `Sw/partitions.csv` asigna 10.1 MB y deja 5.9 MB de reserva:

| Partición | Offset | Tamaño | Uso |
| --- | --- | --- | --- |
| `nvs` | `0x9000` | 24 KB | Datos de `FlashDriver` |
| `otadata` | `0xF000` | 8 KB | Control de actualización OTA |
| `phy_init` | `0x11000` | 4 KB | Calibración de radio |
| `ota_0` | `0x20000` | 3 MB | Firmware (`idf.py flash` escribe aquí) |
| `ota_1` | `0x320000` | 3 MB | Segundo slot para actualización OTA |
| `storage` | `0x620000` | 4 MB | Sonidos y recursos gráficos (sin uso todavía) |

No hay partición `factory`: el arranque usa `ota_0`. Cambiar la tabla exige reflashear todo el chip.
El `sdkconfig` generado no se versiona. Los archivos generados del firmware (`build/`, `sdkconfig`, `sdkconfig.old`, `managed_components/`, `dependencies.lock`, `.cache/` y `.clangd`) están en `Sw/.gitignore`; la configuración local de editor, Python, KiCad, Excel y el sistema operativo está en el `.gitignore` de la raíz.

## Reglas de formato del código

- Llave de apertura en la línea de abajo, indentación de 2 espacios y cuerpo un nivel adentro.
- Cada archivo lleva un header (descripción, fecha, micro, compilador, IDE, ADE y licencia) y cada función un header con entradas y salidas.
- Nombres de funciones descriptivos.
- Constantes solo en `GlobalDefine.h`, con formato `C_[NOMBRE]`. Los archivos incluyen `Ram.h`, no `GlobalDefine.h`; `GlobalDefine.h` solo se incluye desde `Ram.h`. El interruptor `C_RAM_EXPOSE_GLOBALS` se define en cada `.c` que necesita las variables globales (no va en `GlobalDefine.h`, porque entonces lo verían todos).
- Uniones con nombre `[tamaño][Nombre]` (por ejemplo `u8MainFlag`, privada de `TimerDriver`) y bits con alias `bf_[nombre descriptivo]`, definido junto a la instancia.
- Condiciones con comparación explícita (`if(x == C_TRUE)`) y paréntesis pegados a la condicional. Los ciclos infinitos se escriben `while(C_TRUE)`.
- Los inputs no usan pull-ups internos: si hacen falta, van en el esquemático.

## Compilar

Desde una terminal con ESP-IDF activado (terminal de la extensión de VS Code, o PowerShell con `C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1`), dentro de `Sw`:

```
idf.py set-target esp32s3
idf.py build
idf.py -p COMx flash monitor
```

Usar el puerto USB marcado como **UART** de la placa. Si el perfil de PowerShell falla con "MSys/Mingw is no longer supported", vaciar la variable con `$env:MSYSTEM = $null` antes de activarlo (aparece cuando la terminal se abre desde Git Bash).

Antes de cada commit se compila, se actualizan [`Warnings.md`](Warnings.md) (warnings de compilación) y [`MemoryUsage.md`](MemoryUsage.md) (uso de ROM y RAM).
