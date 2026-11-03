# Sw

Firmware de la herramienta, con ESP-IDF v6.1 para el ESP32-S3-DevKitC-1 N16R8.

Por ahora es un proyecto base: al arrancar imprime por el monitor serie el chip, el tamaño de la flash y el de la PSRAM, y no hace nada más. Los pines están en `main/pines.h` y salen de la asignación de [`../Hw/esquematico_v1/README.md`](../Hw/esquematico_v1/README.md).

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
