# Guía de desarrollo del firmware

Para quien va a darle mantenimiento o seguimiento al firmware: dónde leer primero, cómo compilar, qué reglas sigue el código y cómo agregar un driver o hacer un cambio sin romper la arquitectura.

## 1. Por dónde empezar

Lee en este orden:

1. [`../README.md`](../README.md): qué es el proyecto y qué hardware usa.
2. [`README.md`](README.md): cómo está organizado el firmware **hoy**: archivos, diagramas de relación, UML y secuencias.
3. [`Arquitectura.md`](Arquitectura.md): cómo debe quedar al final (capas, reglas R1 a R8, catálogo de drivers, tareas y núcleos, plan de PRs).
4. [`MapaPines.md`](MapaPines.md): qué pin hace qué y dónde el firmware todavía no sigue al hardware.
5. [`ReferenciaApi.md`](ReferenciaApi.md): las funciones públicas de cada driver, con su contexto de uso.
6. Este documento, para las reglas de trabajo.

Archivos de seguimiento que se actualizan en cada cambio:

| Archivo | Qué lleva |
| --- | --- |
| [`MemoryUsage.md`](MemoryUsage.md) | Uso de flash y RAM con gráficas, y una fila de historial por commit. |
| [`Warnings.md`](Warnings.md) | Lista de warnings de compilación con su causa y su estado. |

## 2. Estado actual

- El firmware arranca, fija el CPU a 240 MHz, inicia la flash (NVS), el heartbeat y un timer de 5 ms que gobierna el ciclo principal.
- La única subrutina del ciclo es el heartbeat. Pantalla, audio, tiras LED, teclado, entradas y batería todavía no tienen driver.
- Nada se ha probado en la placa; solo se sabe que compila. La guía para probarlo en hardware está en el PR de `GuiaDepuracion.md` (si ya se mergeó, está en `Sw/GuiaDepuracion.md`).
- El pinout del firmware es el de v0.7 y el hardware ya es v0.8 o posterior (ver [`MapaPines.md`](MapaPines.md)).

## 3. Preparar el entorno y compilar

ESP-IDF v6.1 para el ESP32-S3. En Windows, desde PowerShell, dentro de `Sw/`:

```powershell
$env:MSYSTEM = $null
. C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1
idf.py build
idf.py size
```

- `$env:MSYSTEM = $null` es necesario: si queda definido, el perfil de ESP-IDF falla con "MSys/Mingw is no longer supported".
- `idf.py size` imprime el uso de memoria. El resultado se vuelca en `MemoryUsage.md`.
- Si cambias `sdkconfig.defaults`, borra `Sw/sdkconfig` antes de compilar. `sdkconfig` lo genera ESP-IDF, no está en el repositorio, y mientras exista manda sobre los defaults.
- Los 5 warnings de CMake sobre `esp_wifi` y `wpa_supplicant` son del propio ESP-IDF y están en `Warnings.md` (W-001 a W-005). Cualquier warning nuevo debe agregarse ahí.

## 4. Mapa del código

Todo el código vive en `AirsoftToolSw/`, declarado como componente en `Sw/CMakeLists.txt` (`EXTRA_COMPONENT_DIRS`).

| Capa | Archivos | Para qué |
| --- | --- | --- |
| Entrada | `main.c` | `app_main`: inicializa y corre el ciclo principal de 5 ms. |
| Arranque | `MainProcess.c/.h` | Secuencia de arranque: reloj, puertos, flash, heartbeat, timer. |
| Datos | `Ram.c/.h`, `GlobalDefine.h` | Variables globales de la aplicación, constantes `C_*`, tipos y uniones. |
| Drivers | `ClockDriver`, `GpioDriver`, `FlashDriver`, `HeartbeatDriver`, `TimerDriver` | Un periférico o función por driver. |

El ciclo principal, en una línea: el `TimerDriver` genera una interrupción cada 5 ms que enciende una bandera y despierta a la tarea principal; esa tarea ejecuta las subrutinas y apaga la bandera. Si no termina a tiempo, el driver cuenta un "periodo perdido". Los diagramas de secuencia están en [`README.md`](README.md#interrupción-de-5-ms-y-ciclo-principal).

## 5. Reglas de código

Estas reglas son obligatorias; el código existente ya las cumple.

**Formato**
- Llave de apertura en su propia línea (estilo Allman), también en inicializadores de `struct`. Sangría de 2 espacios, sin tabuladores; el cuerpo va un nivel adentro de las llaves.
- Sin espacio entre `if`, `while`, `for` o `switch` y el paréntesis: `if(`, `while(`.
- Ciclos infinitos con `while(C_TRUE)`.
- Los comentarios en el código se escriben sin acentos ni eñe.

**Encabezados y comentarios**
- Cada archivo empieza con un encabezado: archivo, descripción, fecha de creación, microcontrolador, compilador, IDE, ADE y licencia. Copia el de un archivo existente.
- Cada función lleva un comentario con **Nombre**, **Descripción**, **Entradas** y **Salidas**. Incluye los códigos de error que puede devolver.
- Cada variable `static` (salvo `TAG`) y cada constante con unidad lleva un comentario de una línea con su significado y su unidad.
- Los nombres de función dicen qué hacen (`ConfigGpioAsOutput`, `FlashWriteU32`). Excepciones: `app_main` (lo exige ESP-IDF) e `InitRam`.

**Constantes y tipos**
- Las constantes viven solo en `GlobalDefine.h`, con el formato `C_[NOMBRE]` (por ejemplo `C_PIN_LCD_RS`). No se escriben números mágicos en los `.c`. Quedan fuera `static const char *TAG` y las guardas de inclusión.
- Booleanos: `C_TRUE` y `C_FALSE`.
- Las uniones de banderas se nombran `[tamaño][Nombre]` (por ejemplo `u8MainFlag`), con un alias por bit `bf_[nombre descriptivo]` definido junto a la instancia (por ejemplo `#define bf_5MsMainLoopFlag Bits.Bit0`). Cada bit lo escribe un solo contexto a la vez, porque modificar un bit no es una operación atómica.

**Condiciones**
- Siempre comparaciones explícitas: `if(u8MainFlag.bf_5MsMainLoopFlag == C_TRUE)`. Nunca `if(flag)` ni `if(!flag)` (se escribe `== C_FALSE`).

**Inclusión y encapsulamiento**
- Los archivos incluyen `Ram.h`, nunca `GlobalDefine.h` directamente; `Ram.h` es el único que lo incluye (R8).
- Las variables globales de `Ram.h` solo se ven si el archivo define `C_RAM_EXPOSE_GLOBALS` antes de incluirlo. Solo lo definen `main.c` y `Ram.c`. Un driver que use una variable global no compila (R1).
- Un driver no lee ni escribe variables de `Ram`. Su estado interno es `static` dentro del driver y se consulta con sus funciones.
- Cada driver valida sus argumentos y devuelve `esp_err_t`. Quien lo llama decide si el error es fatal (`ESP_ERROR_CHECK`) o se tolera, como pasa con `FlashInit`.

**Hardware**
- Sin resistencias pull-up o pull-down internas. Si una entrada necesita pull-up, se agrega en el esquemático (resistencia externa de 10k a 3.3 V).
- Antes de usar un GPIO, revisa [`MapaPines.md`](MapaPines.md): GPIO19 y 20 (USB), 26 a 32 (flash) y 35 a 37 (PSRAM) están reservados, y GPIO0, 3, 45 y 46 son pines de arranque.

**Tiempo real**
- Dentro de las subrutinas del ciclo de 5 ms no se llama nada que bloquee: ni escrituras a flash (`FlashWriteU32` y similares tardan decenas de ms), ni `ESP_LOGx` largos, ni esperas.
- Lo que corre en una interrupción lleva `IRAM_ATTR` y no usa funciones bloqueantes ni de log.

## 6. Cómo agregar un driver

1. Crea la branch desde `develop` actualizado (sección 7).
2. Crea `AirsoftToolSw/[Nombre]Driver.c` y `.h` copiando el encabezado de un driver existente. El `.h` solo declara las funciones públicas, sin `extern`.
3. Escribe la API pública con prefijo del driver (`HeartbeatInit`, `HeartbeatTick`) y devuelve `esp_err_t` donde pueda fallar. Valida todos los argumentos.
4. Si el driver usa constantes, defínelas en `GlobalDefine.h` con `C_`; en el `.c` incluye `Ram.h`.
5. Todo estado interno es `static` y está comentado. No toques variables de `Ram`.
6. Súmalo a `SRCS` en `AirsoftToolSw/CMakeLists.txt` y su componente de ESP-IDF a `PRIV_REQUIRES` si hace falta.
7. Si arranca algo, llama a su `Init` desde `InitMainProcess` (en `MainProcess.c`); decide ahí si un error es fatal.
8. Si tiene trabajo periódico, llama a su `Tick` desde el ciclo de `main.c`, respetando los 5 ms.
9. Actualiza la documentación (sección 8) y el catálogo de drivers de `Arquitectura.md`.

## 7. Flujo de trabajo con Git

- **Antes de cualquier cambio:** actualiza `develop` (`git checkout develop`, `git pull --ff-only origin develop`) y crea desde ahí la branch nueva. Nunca se edita sobre `develop` ni sobre una branch que ya tiene un PR abierto o mergeado.
- **Nombres:** branch `b#[N]_[Nombre]` (el nombre va junto y cada palabra empieza con mayúscula, por ejemplo `b#12_Heartbeat`). El PR se titula `PR#[N]_[Nombre]`, con el mismo número y nombre, y va hacia `develop`. Usa el siguiente número libre.
- **Antes del commit, si tocaste `Sw/`:**
  1. Compila y corrige los errores.
  2. Anota los warnings nuevos en `Warnings.md`.
  3. Corre `idf.py size` y actualiza `MemoryUsage.md` (barras y una fila del historial).
  4. Actualiza la documentación (sección 8).
- **Revisión con Codex antes de subir:** con el commit hecho, corre `codex review --base develop` desde la raíz del repositorio. Corrige los hallazgos y repite hasta que Codex no reporte nada. Solo entonces se hace `git push` y se crea el PR.
- **Pull request:** `gh pr create --base develop --head "b#N_Nombre" --title "PR#N_Nombre"`. La descripción dice qué cambió, cómo se verificó y qué no se probó en hardware.

## 8. Qué documentación actualizar con cada cambio

| Si cambias... | Actualiza |
| --- | --- |
| Un archivo, driver, función pública, variable global, constante o unión | `README.md` de `Sw`: tabla de archivos, diagrama de inclusiones y diagrama UML. |
| El orden de arranque o el ciclo principal | Las secuencias de `README.md`. |
| La API pública de un driver | [`ReferenciaApi.md`](ReferenciaApi.md). |
| Un `C_PIN_*` o el pinout del hardware | [`MapaPines.md`](MapaPines.md) y el aviso al inicio de `GlobalDefine.h`. |
| Algo del diseño objetivo (tareas, núcleos, particiones, plan de PRs) | [`Arquitectura.md`](Arquitectura.md). |
| La memoria usada o los warnings | `MemoryUsage.md` y `Warnings.md`. |
| Un parámetro de `sdkconfig.defaults` o `partitions.csv` | La sección "Configuración" de `README.md`. |

## 9. Problemas conocidos

| Síntoma | Causa | Qué hacer |
| --- | --- | --- |
| El perfil de ESP-IDF falla con "MSys/Mingw is no longer supported" | `MSYSTEM` está definido en la sesión. | `$env:MSYSTEM = $null` y volver a cargar el perfil. |
| Un cambio de `sdkconfig.defaults` no surte efecto | Ya existe `Sw/sdkconfig`. | Borrarlo y compilar de nuevo. |
| No salen logs por el puerto UART de la tarjeta | La consola va por el USB (GPIO43 es el LED de estado). | Conectar el puerto USB de la tarjeta (USB-Serial-JTAG). |
| Git avisa "LF will be replaced by CRLF" | Los archivos del repositorio están en LF y Windows convierte al escribirlos. | Es solo un aviso; no hace falta corregir nada. |

## 10. Glosario

| Término | Significado |
| --- | --- |
| Ciclo principal | El `while(C_TRUE)` de `main.c`, que corre una vez por periodo de 5 ms. |
| Periodo / tick | Cada interrupción del timer, cada `C_TIMER_PERIOD_MS` (5 ms). |
| Periodo perdido (overrun) | Un tick que encontró la bandera todavía encendida porque el ciclo anterior no terminó. `TimerGetOverrunCount` los cuenta. |
| Heartbeat | LED de estado que cambia cada 0.5 s (ciclo de 1 s) mientras el ciclo principal corre. |
| `C_*` | Constante definida en `GlobalDefine.h`. |
| `bf_*` | Alias de un bit dentro de una unión de banderas. |
| `Ram.h` | Header común: entrega constantes y tipos, y las variables globales solo a quien define `C_RAM_EXPOSE_GLOBALS`. |
| NVS | Almacenamiento clave-valor en flash de ESP-IDF; lo usa `FlashDriver`. |
| `ota_0` / `ota_1` | Las dos particiones de firmware; `idf.py flash` escribe en `ota_0`. |
| DIRAM / IRAM | RAM interna de datos y código / RAM interna de código rápido. |
| MCP23017 | Expansor de GPIO por I2C (U6 en el hardware v0.8) donde van el teclado, los switches y el botón. |
