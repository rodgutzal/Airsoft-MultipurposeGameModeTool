# Uso de memoria

Se actualiza antes de cada commit que toque `Sw/`, después de compilar y correr `idf.py size`. ESP-IDF v6.1, target esp32s3 (16 MB de flash, 8 MB de PSRAM octal).

## Estado actual

Branch `b#10_FlashDriver`, 2026-11-04.

```
ROM (Flash)
  Partición ota_0 de la app (3 MB)  [█░░░░░░░░░░░░░░░░░░░]   6.9 %   usado 218,384 B   libre 2,927,344 B
  Flash asignada a particiones      [█████████████░░░░░░░]  63.3 %   asignado 10.1 MB de 16 MB   reserva 5.9 MB

RAM interna
  DIRAM (datos + código)   [███░░░░░░░░░░░░░░░░░]  17.5 %   usado  59,710 B   libre 282,050 B
     .text  42,511 B (12.4 %)   .data 14,207 B (4.2 %)   .bss 2,992 B (0.9 %)
  IRAM (código rápido)     [████████████████████] 100.0 %   usado  16,384 B   libre       0 B
  RTC SLOW                 [░░░░░░░░░░░░░░░░░░░░]   0.4 %   usado      36 B   libre   8,156 B
  RTC FAST                 [░░░░░░░░░░░░░░░░░░░░]   0.3 %   usado      24 B   libre   8,168 B

RAM externa
  PSRAM (8 MB)             [░░░░░░░░░░░░░░░░░░░░]   0.0 %   sin uso estático; solo se ve en ejecución
```

Notas:
- La IRAM al 100% es normal en el ESP32-S3: son 16 KB fijos de caché de instrucciones que el sistema reserva completos.
- El uso de PSRAM no se conoce al compilar, porque el tamaño se detecta al arrancar. Se medirá con las trazas de arranque cuando se flashee.
- Desde el PR de `FlashDriver` la app vive en una partición `ota_0` de 3 MB (tabla propia en `Sw/partitions.csv`); antes eran 1 MB con la tabla por defecto. Por eso el porcentaje de la columna "Flash app (%)" del historial baja aunque el firmware crece: los porcentajes anteriores están sobre 1 MB.
- El `FlashDriver` (NVS) y `CONFIG_GPTIMER_ISR_IRAM_SAFE` suman unos 14.6 KB de ROM y 2.1 KB de DIRAM.
## Historial

| Fecha | Commit | Flash app (B) | Flash app (%) | DIRAM (B) | DIRAM (%) | Observación |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-02 | `a3b0e4a` | 188,016 | 17.9 | 54,890 | 16.1 | Proyecto base con GlobalDefine, Ram y MainProcess |
| 2026-11-02 | `5393c27` | 188,016 | 17.9 | 54,890 | 16.1 | Formato Allman, headers de archivo y funcion, nombres descriptivos; sin cambio de tamano |
| 2026-11-02 | `fb8cd28` | 189,424 | 18.1 | 54,890 | 16.1 | Driver GpioDriver (validacion de pin, esp_err_t); entradas sin pull interno |
| 2026-11-03 | `def49dd` | 203,824 | 19.4 | 57,578 | 16.9 | TimerInitialization (reloj 240 MHz con esp_pm), constantes C_, timer periodico de 5 ms con u8MainFlag, uniones, reglas de formato |
| 2026-11-03 | `6a4793f` | 203,840 | 19.4 | 57,578 | 16.9 | ClockDriver (reloj movido fuera de MainProcess); sin cambio de tamano relevante |
| 2026-11-04 | `1a59c69` | 203,840 | 19.4 | 57,578 | 16.9 | Los archivos incluyen Ram.h en lugar de GlobalDefine.h (R8) y interruptor C_RAM_EXPOSE_GLOBALS (R1); sin cambio de tamano |
| 2026-11-04 | `a8a1155` | 203,728 | 19.4 | 57,586 | 16.9 | Refactor de encapsulamiento: TimerDriver con estado privado y API TimerWaitMainTick/TimerEndMainTick; secuencia de arranque unica |
| 2026-11-04 | este commit (sobre `f79165c`) | 218,384 | 6.9 (de 3 MB) | 59,710 | 17.5 | FlashDriver (NVS), tabla de particiones propia (ota_0 de 3 MB) y CONFIG_GPTIMER_ISR_IRAM_SAFE |
