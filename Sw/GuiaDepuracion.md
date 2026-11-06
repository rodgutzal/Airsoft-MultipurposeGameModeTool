# Guía: cargar el firmware en la tarjeta y depurar

Paso a paso para grabar el firmware en el ESP32-S3-DevKitC-1 N16R8 y tener una sesión de depuración. Se basa en la configuración real del proyecto (`Sw/sdkconfig.defaults`, `Sw/partitions.csv`) y en la documentación de ESP-IDF v6.1, que queda en tu equipo al instalarlo (`C:\esp\v6.1\esp-idf\docs\en\api-guides\jtag-debugging\`).

> **Estado:** esta guía todavía **no se ha ejecutado en la tarjeta**. Los comandos y rutas salen de la configuración y de la documentación local; los mensajes de arranque esperados salen del código. El paso 6.4 (depuración desde VS Code) depende de la versión de la extensión y sus comandos pueden variar de nombre. Al ejecutarla por primera vez, anota qué difiere y se corrige aquí.

## 1. Qué programa usar

| Para qué | Programa | Dónde queda tras instalarlo (rutas por omisión) |
| --- | --- | --- |
| Compilar, grabar y ver mensajes | **ESP-IDF** (`idf.py`) en una terminal de PowerShell | `C:\esp\v6.1\esp-idf` |
| Editor y depuración gráfica | **Visual Studio Code** con la extensión **ESP-IDF** | Se abre la carpeta `Sw` |
| Puente de depuración (JTAG) | **OpenOCD** de Espressif | `C:\Espressif\tools\openocd-esp32` |
| Depurador | **GDB** de Xtensa (`xtensa-esp-elf-gdb`) | `C:\Espressif\tools\xtensa-esp-elf-gdb` |

ESP-IDF, OpenOCD y GDB se instalan juntos con un solo instalador (el paso 2.4). Las rutas de la tabla son las que usa el instalador por omisión; si eliges otra, adapta las de esta guía.

Hay dos niveles de sesión, de menos a más complejo:
- **Nivel A, cargar y ver mensajes:** `idf.py flash monitor`. Es suficiente para casi todo.
- **Nivel B, depurar con puntos de interrupción:** OpenOCD + GDB por el JTAG integrado del chip. No necesita ningún programador externo.

## 2. Prerrequisitos: instalación desde cero

Esta sección supone un equipo **sin nada instalado**. Sigue los pasos en orden. Cada paso termina con un comando para comprobarlo.

### 2.1 Qué necesitas
- **Equipo:** Windows 10 u 11 de 64 bits, con PowerShell 5.1 o superior y conexión a Internet. Los comandos de esta guía son de PowerShell.
- **Espacio en disco:** en la PC donde se probó el proyecto, ESP-IDF y sus herramientas ocupan unos 11.4 GB (la mayor parte son las herramientas y los archivos descargados que deja el instalador en `C:\Espressif`). Deja al menos **15 GB libres**.
- **Winget:** viene con Windows 11 y con las versiones recientes de Windows 10. Comprueba con `winget --version`. Si no existe, instala "App Installer" desde Microsoft Store.
- **Permiso de scripts de PowerShell:** más adelante se ejecuta un script `.ps1`. Si PowerShell responde *"running scripts is disabled on this system"*, ejecuta una vez:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- **Hardware:** la tarjeta ESP32-S3-DevKitC-1 N16R8 y **dos cables USB de datos** (no solo de carga), uno por cada puerto de la tarjeta. Para el Nivel A basta uno.

### 2.2 Git
```powershell
winget install --id Git.Git -e
```
Cierra y vuelve a abrir PowerShell y comprueba: `git --version`.

### 2.3 Visual Studio Code
```powershell
winget install --id Microsoft.VisualStudioCode -e
```
Cierra y vuelve a abrir PowerShell y comprueba: `code --version`.

### 2.4 ESP-IDF v6.1 (incluye compilador, OpenOCD y GDB)
ESP-IDF se instala con el **EIM** (*ESP-IDF Installation Manager*), que descarga el framework, el compilador de Xtensa, CMake, Ninja, OpenOCD, GDB y Python. Si falta Git o Python, el instalador avisa. Requiere Python 3.11 o superior; el instalador lo gestiona.

1. Instala el EIM:
   ```powershell
   winget install Espressif.EIM
   ```
2. Instala la versión del proyecto con la línea de comandos del EIM, que permite fijarla:
   ```powershell
   eim install -i v6.1
   ```
   La instalación fácil de la interfaz gráfica (*Start Installation → Start Easy Installation*) instala la **última versión estable**, que puede ser distinta de la v6.1; úsala solo si aceptas esa diferencia.
3. Espera a la pantalla *Installation Complete*. Si falla, revisa el registro (*Logs*) que muestra el instalador, corrige y pulsa *Try Again*.

El proyecto se compila y se ha comprobado con **ESP-IDF v6.1**, compilador `xtensa-esp-elf` 15.2.0, GDB 17.1 y OpenOCD `v0.12.0-esp32-20260703`. Con otras versiones puede haber diferencias.

Comprobación (abre una terminal nueva y activa el entorno como en el paso 4):
```powershell
Test-Path C:\Espressif\tools\eim_idf.json      # debe responder True
idf.py --version                                # debe mostrar ESP-IDF v6.1
```

### 2.5 Extensión ESP-IDF de VS Code
```powershell
code --install-extension espressif.esp-idf-extension
```
Luego, en VS Code:
1. Paleta de comandos (`Ctrl+Shift+P`) → `ESP-IDF: Select Current ESP-IDF Version` y elige la v6.1 instalada en el paso 2.4. La extensión detecta las instalaciones del EIM leyendo `C:\Espressif\tools\eim_idf.json`; si lo instalaste en otra ruta, indícala en el ajuste `idf.eimIdfJsonPath`.
2. Paleta de comandos → `ESP-IDF: Doctor Command` para verificar la instalación.

La extensión crea en el proyecto la carpeta `.vscode/` con rutas de tu equipo; está ignorada por Git y no se sube al repositorio.

### 2.6 Drivers USB
1. **Puerto UART de la tarjeta (CP2102N).** Windows 11 suele instalarlo solo. Conecta la tarjeta por el puerto marcado **UART** y mira el Administrador de dispositivos → *Puertos (COM y LPT)*: debe aparecer un puerto `COMx`. Si no aparece, instala el *CP210x Universal Windows Driver* de Silicon Labs (búscalo en silabs.com) y vuelve a conectar.
2. **JTAG por USB (solo para el Nivel B).** Según la documentación de ESP-IDF, en Windows puede aparecer el error `LIBUSB_ERROR_NOT_FOUND` si falta el driver. Se instala con cualquiera de estas dos formas:
   - En PowerShell: `eim install-drivers`.
   - En la interfaz del EIM: *Manage Installations → Open Dashboard → Install Drivers*.

### 2.7 Obtener el código del proyecto
```powershell
cd C:\Users\<tu_usuario>\Documents\Proyects
git clone https://github.com/rodgutzal/Airsoft-MultipurposeGameModeTool.git
cd Airsoft-MultipurposeGameModeTool
git checkout develop
```
Si el repositorio es privado, Git pide iniciar sesión con tu cuenta de GitHub. La carpeta del firmware es `Sw`. Las rutas de esta guía usan `C:\Users\rodgu\Documents\Proyects\Airsoft-MultipurposeGameModeTool`; sustitúyela por la tuya.

### 2.8 Lista de verificación antes de seguir

| Comprobación | Comando o acción | Resultado esperado |
| --- | --- | --- |
| Git | `git --version` | Muestra una versión |
| VS Code | `code --version` | Muestra una versión |
| ESP-IDF | `Test-Path C:\Espressif\tools\eim_idf.json` | `True` |
| ESP-IDF activado | Pasos del apartado 4 y luego `idf.py --version` | ESP-IDF v6.1 |
| Extensión | `code --list-extensions` | Aparece `espressif.esp-idf-extension` |
| Código | `Test-Path .\Sw\CMakeLists.txt` dentro del repositorio | `True` |
| Puerto UART | Conectar la tarjeta y mirar *Puertos (COM y LPT)* | Aparece un `COMx` |

### Advertencia de alimentación (léela antes de conectar la tarjeta)
El README de hardware deja pendiente confirmar si la DevKitC-1 tiene un diodo entre su USB y el pin 5V, y dice: *"Si no lo tiene, no se debe conectar USB al DevKit con M1 encendido."*

**Regla para cargar y depurar:** mientras no se confirme el diodo, conecta el USB **solo con el módulo de baterías M1 apagado o desconectado**, es decir, con la tarjeta de desarrollo alimentada únicamente por el USB. Así se evita contraalimentar el módulo de baterías.
## 3. Conexión de la tarjeta

La DevKitC-1 tiene **dos puertos micro/USB-C**. Cada uno sirve para algo distinto:

| Puerto (serigrafía) | Chip | Se usa para |
| --- | --- | --- |
| **UART** | Puente CP2102N | Grabar el firmware y ver mensajes (aparece como `COMx`). Reinicio automático con DTR/RTS. |
| **USB** | USB nativo del ESP32-S3 | JTAG para depurar (y consola secundaria; el proyecto la tiene activa con `CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG`). |

- **Nivel A:** basta conectar el puerto **UART**.
- **Nivel B:** conecta **los dos**. El UART graba y muestra mensajes; el USB lleva el JTAG.

Para saber qué `COM` se asignó:

```powershell
Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Description
```

## 4. Abrir un entorno con ESP-IDF activado

En PowerShell, dentro de la carpeta del proyecto:

```powershell
cd C:\Users\rodgu\Documents\Proyects\Airsoft-MultipurposeGameModeTool\Sw
$env:MSYSTEM = $null
. C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1
```

- La línea `$env:MSYSTEM = $null` evita el error *"MSys/Mingw is no longer supported"*, que aparece cuando la terminal viene de Git Bash.
- El nombre del script incluye la versión instalada (`Microsoft.v6.1.PowerShell_profile.ps1` para la v6.1) y lo crea el EIM en la carpeta de herramientas (`C:\Espressif\tools`). Si instalaste otra versión o ruta, busca el archivo `*PowerShell_profile.ps1` en esa carpeta.
- Alternativa: en VS Code, abre la carpeta `Sw` y usa la terminal que ofrece la extensión ESP-IDF (`ESP-IDF: Open ESP-IDF Terminal`), que ya trae el entorno.

## 5. Nivel A: grabar y ver mensajes

### 5.1 Compilar
```powershell
idf.py set-target esp32s3   # solo la primera vez, o si borras sdkconfig
idf.py build
```
Debe terminar con `Project build complete`. Los 5 warnings de CMake sobre `esp_wifi` y `wpa_supplicant` son externos y conocidos (ver `Warnings.md`).

### 5.2 Grabar
```powershell
idf.py -p COMx flash
```
Cambia `COMx` por el puerto UART del paso 3. Esto escribe cuatro archivos, según `build/flasher_args.json`:

| Offset | Archivo | Qué es |
| --- | --- | --- |
| `0x0` | `bootloader.bin` | Bootloader |
| `0x8000` | `partition-table.bin` | Tabla de particiones (`Sw/partitions.csv`) |
| `0xF000` | `ota_data_initial.bin` | Control de arranque OTA |
| `0x20000` | `airsoft_tool.bin` | El firmware (partición `ota_0`) |

Si la tarjeta ya traía otro firmware, borra primero toda la flash **una sola vez** para empezar limpio (incluida la partición `nvs`):
```powershell
idf.py -p COMx erase-flash
```

### 5.3 Ver los mensajes
```powershell
idf.py -p COMx monitor        # salir con Ctrl+]
idf.py -p COMx flash monitor  # grabar y abrir el monitor de una vez
```
La velocidad es de 115200 baudios (`CONFIG_ESPTOOLPY_MONITOR_BAUD`).

### 5.4 Qué debe imprimir el arranque
Según el código, el arranque escribe estas líneas (cada una empieza con `I (milisegundos) Etiqueta:`). Los valores entre corchetes son los esperados para la N16R8; **no están comprobados en la tarjeta**.

| Etiqueta | Mensaje | Valor esperado |
| --- | --- | --- |
| `MainProcess` | `Chip: esp32s3, 2 nucleos, rev ...` | 2 núcleos |
| `MainProcess` | `Flash: 16 MB` | 16 MB |
| `MainProcess` | `PSRAM: ... KB` | Cerca de 8192 KB (8 MB) |
| `ClockDriver` | `Fuente del CPU: PLL, ...` | PLL |
| `ClockDriver` | `CPU: 240 MHz (objetivo 240 MHz)` | 240 MHz |
| `FlashDriver` | `Almacenamiento en flash listo` | Si no aparece, sale un `E (...)` con el motivo |
| `TimerDriver` | `Timer periodico configurado: 5 ms` | 5 ms |

Después de esas líneas el programa queda en el ciclo principal sin imprimir nada más, es lo normal por ahora.

### 5.5 Si algo falla

| Síntoma | Qué revisar |
| --- | --- |
| No aparece ningún `COMx` | Cable de solo carga; driver CP210x; usar el puerto marcado **UART**. |
| `Failed to connect to ESP32-S3` | Entrar a modo descarga a mano: mantener **BOOT** (GPIO0), pulsar **RST**, soltar RST y luego BOOT, y repetir `flash`. |
| Se reinicia en bucle | Alimentación insuficiente (probar otro cable o puerto); revisar la línea `rst:` del mensaje de arranque. |
| `E (...) FlashDriver: ...` | La partición `nvs` está dañada: `idf.py -p COMx erase-flash` y volver a grabar. |
| `CPU: ... MHz` distinto de 240 | Avisa con un `W (...)`; revisar `sdkconfig.defaults`. |
| El monitor no muestra nada | Revisar el puerto, o pulsar RST. El mensaje de arranque ocurre antes de que abras el monitor. |

Nota: GPIO0 (BOOT) y los GPIO 3, 45 y 46 son pines de arranque. En la tarjeta completa, los dispositivos conectados a ellos (audio y tiras LED) no deben forzar un nivel al reiniciar. En la DevKitC-1 sola no hay problema.

## 6. Nivel B: depuración con puntos de interrupción

### 6.1 Antes de empezar
- Conecta **los dos** puertos (paso 3) y completa el driver USB del paso 2.3.
- El proyecto compila con `CONFIG_COMPILER_OPTIMIZATION_DEBUG` (`-Og`), adecuado para depurar. No necesitas cambiar la configuración.
- No quemes eFuses de JTAG (`DIS_USB_JTAG`, `STRAP_JTAG_SEL`): por defecto el chip ya usa el JTAG por USB. Solo con `STRAP_JTAG_SEL` quemado importaría el nivel del GPIO3, que en este diseño lleva la tira LED 1.
- Graba antes el firmware actual (paso 5.2).

### 6.2 Ruta por línea de comandos (la documentada en ESP-IDF)

Usa **dos terminales** con el entorno del paso 4, ambas dentro de `Sw`.

**Terminal 1: OpenOCD (déjala abierta):**
```powershell
idf.py openocd
```
Esto ejecuta OpenOCD con `-f board/esp32s3-builtin.cfg` (la configuración que usa el proyecto, según `build/project_description.json`). Debe terminar en algo como `Listening on port 3333 for gdb connections`. Si dice `LIBUSB_ERROR_NOT_FOUND`, falta el driver del paso 2.3.

**Terminal 2: GDB:**
```powershell
idf.py gdb
```
Carga los símbolos, se conecta a OpenOCD, reinicia el chip y se detiene en un punto de interrupción temporal en `app_main` (lo configura el archivo `build/gdbinit/connect`). Verás el prompt `(gdb)`.

### 6.3 Comandos de GDB útiles

| Comando | Qué hace |
| --- | --- |
| `c` | Continuar la ejecución |
| `n` / `s` | Siguiente línea / entrar a la función |
| `bt` | Pila de llamadas |
| `thb nombre_función` | Punto de interrupción de hardware temporal |
| `hb archivo.c:línea` | Punto de interrupción de hardware |
| `info breakpoints` | Listar puntos de interrupción |
| `p variable` | Imprimir una variable |
| `p 'TimerDriver.c'::sSystemTickMs` | Variable `static` de un archivo |
| `watch variable` | Detener cuando una variable cambia (usa un watchpoint de hardware) |
| `info threads` | Tareas de FreeRTOS (la extensión se carga con `idf.py gdb`) |
| `mon reset halt` | Reiniciar y dejar el CPU detenido |
| `maintenance flush register-cache` | Después de un `mon reset`, refrescar el estado que ve GDB |
| `q` | Salir (cierra también la conexión) |

El chip dispone de pocos puntos de interrupción y watchpoints de hardware, así que conviene mantener pocos activos a la vez. Para salir, `Ctrl+C` detiene el CPU y `q` termina GDB; luego cierra OpenOCD con `Ctrl+C` en la terminal 1.

### 6.4 Ruta desde VS Code (alternativa)
1. Abre la carpeta `Sw` (no la raíz del repositorio) en VS Code.
2. Barra de estado de la extensión ESP-IDF: elige el puerto `COMx` y el target `esp32s3`.
3. Paleta de comandos (`Ctrl+Shift+P`): `ESP-IDF: Select OpenOCD Board Configuration` y elige `ESP32-S3 chip (via builtin USB-JTAG)`; en la lista debe corresponder a `board/esp32s3-builtin.cfg`.
4. Compila y graba (`ESP-IDF: Build, Flash and Monitor`).
5. Abre *Run and Debug* (`Ctrl+Shift+D`) y lanza la configuración de depuración que genera la extensión en `.vscode/launch.json` (carpeta ignorada por Git). Coloca puntos de interrupción con clic en el margen.

Los nombres exactos de los comandos y de la configuración pueden cambiar según la versión de la extensión (hoy 2.3.0).

## 7. Precauciones al depurar este firmware

- **Watchdogs.** Mientras el CPU está detenido, el watchdog de tareas (5 s) y el de interrupciones (800 ms) podrían reiniciar el chip. Si se reinicia solo en pleno punto de interrupción, es eso. Según recuerdo, OpenOCD suspende los watchdogs al detener el CPU, pero no está comprobado aquí.
- **Timer de 5 ms.** Al reanudar tras una pausa larga, `TimerGetOverrunCount()` puede haber subido: es la pausa, no un error del código.
- **Escrituras en flash (`FlashDriver`).** Tardan decenas de milisegundos; no las llames dentro del ciclo de 5 ms, ni las pruebes con puntos de interrupción activos dentro de ellas.
- **Puntos de interrupción en flash.** GDB puede escribir en la flash para ponerlos y eso cambia el contenido del programa. Prefiere los de hardware (`thb`, `hb`).

## 8. Sesión sugerida: validar lo que aún no se ha medido

Es el primer uso real de la tarjeta. Esta lista cubre lo que hasta hoy solo se comprobó compilando:

| # | Qué se valida | Cómo | Resultado esperado |
| --- | --- | --- | --- |
| 1 | Reloj del CPU | Monitor, línea `CPU: ...` | 240 MHz, sin `W (...)` |
| 2 | Flash y PSRAM | Monitor, líneas `Flash:` y `PSRAM:` | 16 MB y unos 8 MB |
| 3 | Arranque del `FlashDriver` | Monitor, `Almacenamiento en flash listo` | Aparece, sin errores |
| 4 | Tabla de particiones | Monitor: el bootloader imprime `Partition Table:` con la lista y los offsets | Offsets como en `partitions.csv` (`nvs` `0x9000`, `ota_0` `0x20000`, `ota_1` `0x320000`, `storage` `0x620000`) |
| 5 | Periodo de 5 ms | En GDB: `p 'TimerDriver.c'::sSystemTickMs`, esperar un tiempo conocido, repetir | La diferencia coincide con el tiempo, en pasos de 5 |
| 6 | Sin periodos perdidos | En GDB: `p 'TimerDriver.c'::sTickOverrunCount` tras unos segundos con el ciclo vacío | 0 |
| 7 | Pila y reinicios | Dejar corriendo unos minutos | Sin reinicios ni `panic` |
| 8 | Escritura/lectura en NVS | Requiere un código de prueba que llame a `FlashWriteU32` y `FlashReadU32` | El valor sobrevive a un reinicio. Aún no existe ese código de prueba. |

Anota los resultados en esta guía o en el PR correspondiente; los puntos 1, 3, 5 y 6 son los que más valor tienen antes de seguir con más drivers.

## 9. Referencias

- Depuración con JTAG (queda en tu equipo tras instalar ESP-IDF): `C:\esp\v6.1\esp-idf\docs\en\api-guides\jtag-debugging\index.rst` (y `configure-builtin-jtag.rst`, `using-debugger.rst`, `tips-and-quirks.rst`).
- Arquitectura y particiones del proyecto: [`Arquitectura.md`](Arquitectura.md) y [`README.md`](README.md).
- Warnings conocidos: [`Warnings.md`](Warnings.md). Uso de memoria: [`MemoryUsage.md`](MemoryUsage.md).
