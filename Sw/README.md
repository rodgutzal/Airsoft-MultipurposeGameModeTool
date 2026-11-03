# Sw

Firmware de la herramienta, con ESP-IDF v6.1 para el ESP32-S3-DevKitC-1 N16R8.

Por ahora es un proyecto base: al arrancar inicializa la RAM y los puertos simples, imprime por el monitor serie el chip, la flash y la PSRAM, y no hace nada más.

## Estructura

El código vive en `AirsoftToolSw/` (declarada como componente en `CMakeLists.txt` con `EXTRA_COMPONENT_DIRS`, en lugar de la carpeta `main` por defecto).

| Archivo | Contenido |
| --- | --- |
| `main.c` | `app_main`: llama a `InitRam` y `InitMainProcess`. |
| `GlobalDefine.h` | Definiciones globales: pines (de [`../Hw/esquematico_v1/README.md`](../Hw/esquematico_v1/README.md)), cuentas y constantes. |
| `Ram.c` / `Ram.h` | Variables globales (prefijo `g`) e `InitRam`, que las inicializa. |
| `MainProcess.c` / `MainProcess.h` | Procesos base: `InitClock`, `InitPorts` e `InitMainProcess`. |
| `[nombre]Driver.c` / `.h` | Un par por cada driver (por ejemplo `PwmDriver`). Todavía no hay ninguno; al agregar uno se suma a `SRCS` en `AirsoftToolSw/CMakeLists.txt`. |

## Configuración

`sdkconfig.defaults` fija el target `esp32s3`, flash de 16 MB, PSRAM octal de 8 MB a 80 MHz y CPU a 240 MHz. El `sdkconfig` generado no se versiona.

## Compilar

Desde una terminal con ESP-IDF activado (terminal de la extensión de VS Code, o PowerShell con `C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1`), dentro de `Sw`:

```
idf.py set-target esp32s3
idf.py build
idf.py -p COMx flash monitor
```

Usar el puerto USB marcado como **UART** de la placa. Si el perfil de PowerShell falla con "MSys/Mingw is no longer supported", vaciar la variable con `$env:MSYSTEM = $null` antes de activarlo (aparece cuando la terminal se abre desde Git Bash).

No se ha flasheado en la placa todavía: solo se comprobó que compila.
