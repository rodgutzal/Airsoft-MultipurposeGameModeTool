# Sw

Firmware de la herramienta, con ESP-IDF v6.1 para el ESP32-S3-DevKitC-1 N16R8.

Estado actual: proyecto base. Al arrancar inicializa la RAM, fija el reloj del CPU a 240 MHz con el `ClockDriver`, configura los puertos simples e inicia un timer de 5 ms que gobierna el ciclo principal. Las subrutinas del ciclo todavía no existen; el espacio está marcado en `main.c`. No se ha flasheado en la placa: solo se comprobó que compila.

## Arquitectura

El firmware se organiza en capas. Cada capa solo usa a la de abajo. El diseño objetivo (reglas de encapsulamiento, catálogo de drivers, tareas y núcleos, memoria y plan de PRs) está en [`Arquitectura.md`](Arquitectura.md); esta sección y las siguientes describen el código **actual**.

```mermaid
flowchart TB
  subgraph APP["Aplicación (Sw/AirsoftToolSw)"]
    MAIN["main.c<br/>app_main y ciclo principal"]
    MP["MainProcess<br/>procesos base"]
    RAM["Ram<br/>variables globales"]
    DRV["Drivers propios<br/>ClockDriver, GpioDriver, TimerDriver"]
    GD["GlobalDefine.h<br/>constantes y tipos"]
  end
  subgraph IDF["ESP-IDF v6.1"]
    FR["FreeRTOS"]
    GPIO["esp_driver_gpio"]
    GPT["esp_driver_gptimer"]
    PM["esp_pm / esp_clk_tree"]
  end
  HW["ESP32-S3: GPIO, GPTimer, PLL 240 MHz"]
  MAIN --> MP
  MAIN --> RAM
  MAIN --> DRV
  MP --> DRV
  DRV -. "escribe (viola R1)" .-> RAM
  MP --> RAM
  RAM --> GD
  DRV --> PM
  DRV --> GPIO
  DRV --> GPT
  MAIN --> FR
  GPIO --> HW
  GPT --> HW
  PM --> HW
```

El código actual **todavía no cumple** la regla de capas en un punto: la ISR de `TimerDriver` escribe variables de `Ram` (flecha punteada). Está registrado en [`Arquitectura.md`](Arquitectura.md#10-estado-actual-frente-al-objetivo) y se corrige en el PR de refactor de encapsulamiento.

Reglas de la arquitectura:
- Las constantes (`C_*`), los tipos y las uniones viven solo en `GlobalDefine.h`.
- Ningún archivo incluye `GlobalDefine.h` directamente: se incluye solo desde `Ram.h`, y el resto de los archivos incluye `Ram.h` para obtener las constantes y los tipos (R8 de [`Arquitectura.md`](Arquitectura.md)).
- Las variables globales de `Ram.h` solo se declaran si el archivo define `C_RAM_EXPOSE_GLOBALS` antes de incluirlo. Lo definen `main.c`, `Ram.c` y, hasta el refactor, `TimerDriver.c`. Un driver que no lo define y usa una variable global no compila (R1).
- Las variables globales y los alias de bit (`bf_*`) viven en `Ram.c` / `Ram.h`.
- Cada periférico tiene su driver `[nombre]Driver.c` / `.h`. Un driver valida sus argumentos y devuelve `esp_err_t`; no decide qué hacer ante un error.
- `MainProcess` agrupa el arranque del micro (reloj y puertos). Quien llama a un driver decide si un error es fatal (`ESP_ERROR_CHECK`).

## Estructura de archivos

El código vive en `AirsoftToolSw/` (declarado como componente en `CMakeLists.txt` con `EXTRA_COMPONENT_DIRS`, en lugar de la carpeta `main` por defecto).

| Archivo | Contenido |
| --- | --- |
| `main.c` | `app_main`: inicializa, arranca el timer y ejecuta el ciclo principal. |
| `GlobalDefine.h` | Constantes `C_*` (pines de [`../Hw/esquematico_v1/README.md`](../Hw/esquematico_v1/README.md), tiempos, conversiones, `C_TRUE` / `C_FALSE`) y las uniones `Union8_t`, `Union16_t`, `Union32_t`. |
| `Ram.c` / `Ram.h` | Variables globales (`gTeam`, `gArmed`, `gActionButton`, `gKeyPressed`, `gSystemTickMs`, `gTickOverrunCount`, `u8MainFlag`), el alias `bf_5MsMainLoopFlag` e `InitRam`. |
| `MainProcess.c` / `.h` | Procesos base: `InitMainProcess` e `InitSimpleGpioPorts`. |
| `ClockDriver.c` / `.h` | Reloj del CPU: `ConfigCpuClock` (240 MHz por PLL con `esp_pm`) y `VerifyCpuClockFrequency`. |
| `GpioDriver.c` / `.h` | `ConfigGpioAsOutput` y `ConfigGpioAsInput`, con validación de pin. |
| `TimerDriver.c` / `.h` | Timer periódico (GPTimer): `ConfigPeriodicTimer`, `StartPeriodicTimer` y la ISR de 5 ms. |

Para agregar un driver nuevo: crear `[nombre]Driver.c` / `.h` y sumarlo a `SRCS` en `AirsoftToolSw/CMakeLists.txt` (y su componente de ESP-IDF a `PRIV_REQUIRES`).

## Relación entre archivos

Cada flecha es un `#include` de un archivo propio.

```mermaid
flowchart LR
  main_c["main.c"] --> Ram_h["Ram.h"]
  main_c --> MainProcess_h["MainProcess.h"]
  main_c --> TimerDriver_h["TimerDriver.h"]
  Ram_h --> GlobalDefine_h["GlobalDefine.h"]
  Ram_c["Ram.c"] --> Ram_h
  MainProcess_c["MainProcess.c"] --> MainProcess_h
  MainProcess_c --> Ram_h
  MainProcess_c --> ClockDriver_h["ClockDriver.h"]
  ClockDriver_c["ClockDriver.c"] --> ClockDriver_h
  ClockDriver_c --> Ram_h
  MainProcess_c --> GpioDriver_h["GpioDriver.h"]
  GpioDriver_c["GpioDriver.c"] --> GpioDriver_h
  GpioDriver_c --> Ram_h
  TimerDriver_c["TimerDriver.c"] --> TimerDriver_h
  TimerDriver_c --> Ram_h
```

`TimerDriver.c` usa `Ram.h` porque la ISR escribe `u8MainFlag`, `gSystemTickMs` y `gTickOverrunCount`. `GpioDriver` no depende de `Ram`.

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
    +uint32_t gSystemTickMs
    +uint32_t gTickOverrunCount
    +Union8_t u8MainFlag
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
  class GpioDriver {
    <<module>>
    +ConfigGpioAsOutput(pin, level) esp_err_t
    +ConfigGpioAsInput(pin) esp_err_t
    -IsGpioPinUsable(pin) bool
  }
  class TimerDriver {
    <<module>>
    +ConfigPeriodicTimer(taskToWake) esp_err_t
    +StartPeriodicTimer() esp_err_t
    -PeriodicTimerAlarmIsr() bool
  }
  class Main {
    <<module>>
    +app_main() void
  }
  Union8_t ..> GlobalDefine : definido en
  Union16_t ..> GlobalDefine : definido en
  Union32_t ..> GlobalDefine : definido en
  Ram --> Union8_t : u8MainFlag
  Main ..> Ram : usa
  Main ..> MainProcess : usa
  Main ..> TimerDriver : usa
  MainProcess ..> ClockDriver : usa
  MainProcess ..> GpioDriver : usa
  MainProcess ..> Ram : usa constantes
  GpioDriver ..> Ram : usa constantes
  ClockDriver ..> Ram : usa constantes
  TimerDriver ..> Ram : usa constantes y escribe
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
  Main->>Tim: ConfigPeriodicTimer(tarea actual)
  Main->>Tim: StartPeriodicTimer()
  Note over Main: entra al ciclo principal
```

## Interrupción de 5 ms y ciclo principal

```mermaid
sequenceDiagram
  participant T as GPTimer (hardware)
  participant ISR as PeriodicTimerAlarmIsr
  participant R as Ram
  participant L as Ciclo principal (app_main)
  loop cada 5 ms
    T->>ISR: alarma
    ISR->>R: gSystemTickMs += 5
    alt bf_5MsMainLoopFlag == C_TRUE
      ISR->>R: gTickOverrunCount++
    else bf_5MsMainLoopFlag == C_FALSE
      ISR->>R: bf_5MsMainLoopFlag = C_TRUE
    end
    ISR->>L: vTaskNotifyGiveFromISR
    L->>L: ulTaskNotifyTake despierta
    L->>R: lee bf_5MsMainLoopFlag
    L->>L: ejecuta las subrutinas
    L->>R: bf_5MsMainLoopFlag = C_FALSE
  end
```

Flujo del ciclo principal:

```mermaid
flowchart TD
  A(["Inicio del ciclo"]) --> B["ulTaskNotifyTake: la tarea duerme<br/>hasta la notificación de la ISR"]
  B --> C{"bf_5MsMainLoopFlag<br/>== C_TRUE"}
  C -- no --> B
  C -- sí --> D["Subrutinas del ciclo<br/>una vez cada 5 ms"]
  D --> E["bf_5MsMainLoopFlag = C_FALSE"]
  E --> B
```

Si las subrutinas tardan más de 5 ms, la siguiente interrupción encuentra la bandera todavía en `C_TRUE`: no la vuelve a escribir y suma uno a `gTickOverrunCount`. Ese contador mide si el trabajo del ciclo cabe en el periodo.

La bandera es un bit de un byte, y modificarlo es una lectura-modificación-escritura que no es atómica. Por eso cada bit lo escribe un solo contexto a la vez: la ISR lo enciende solo cuando está apagado y el ciclo lo apaga solo cuando está encendido.

## Configuración

`sdkconfig.defaults` fija:
- target `esp32s3`, flash de 16 MB y PSRAM octal de 8 MB a 80 MHz;
- CPU a 240 MHz (PLL sobre el cristal de 40 MHz; el oscilador interno RC_FAST de unos 17.5 MHz no se usa como fuente del CPU);
- `CONFIG_PM_ENABLE`, necesario para `esp_pm_configure` en `ConfigCpuClock`.

El `sdkconfig` generado no se versiona. Los archivos generados del firmware (`build/`, `sdkconfig`, `sdkconfig.old`, `managed_components/`, `dependencies.lock`, `.cache/` y `.clangd`) están en `Sw/.gitignore`; la configuración local de editor, Python, KiCad, Excel y el sistema operativo está en el `.gitignore` de la raíz.

## Reglas de formato del código

- Llave de apertura en la línea de abajo, indentación de 2 espacios y cuerpo un nivel adentro.
- Cada archivo lleva un header (descripción, fecha, micro, compilador, IDE, ADE y licencia) y cada función un header con entradas y salidas.
- Nombres de funciones descriptivos.
- Constantes solo en `GlobalDefine.h`, con formato `C_[NOMBRE]`. Los archivos incluyen `Ram.h`, no `GlobalDefine.h`; `GlobalDefine.h` solo se incluye desde `Ram.h`. El interruptor `C_RAM_EXPOSE_GLOBALS` se define en cada `.c` que necesita las variables globales (no va en `GlobalDefine.h`, porque entonces lo verían todos).
- Uniones con nombre `[tamaño][Nombre]` (por ejemplo `u8MainFlag`) y bits con alias `bf_[nombre descriptivo]`.
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
