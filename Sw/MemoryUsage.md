# Uso de memoria

Se actualiza antes de cada commit que toque `Sw/`, después de compilar y correr `idf.py size`. ESP-IDF v6.1, target esp32s3 (16 MB de flash, 8 MB de PSRAM octal).

## Estado actual

Branch `b#4_RelojCpu240MHz`, 2026-11-03.

```
ROM (Flash)
  Partición de app (1 MB)  [████░░░░░░░░░░░░░░░░]  19.4 %   usado 203,824 B   libre 844,752 B
  Flash total (16 MB)      [░░░░░░░░░░░░░░░░░░░░]   1.2 %   usado 203,824 B   libre ≈ 16.6 MB

RAM interna
  DIRAM (datos + código)   [███░░░░░░░░░░░░░░░░░]  16.9 %   usado  57,578 B   libre 284,182 B
     .text  40,619 B (11.9 %)   .data 13,999 B (4.1 %)   .bss 2,960 B (0.9 %)
  IRAM (código rápido)     [████████████████████] 100.0 %   usado  16,384 B   libre       0 B
  RTC SLOW                 [░░░░░░░░░░░░░░░░░░░░]   0.4 %   usado      36 B   libre   8,156 B
  RTC FAST                 [░░░░░░░░░░░░░░░░░░░░]   0.3 %   usado      24 B   libre   8,168 B

RAM externa
  PSRAM (8 MB)             [░░░░░░░░░░░░░░░░░░░░]   0.0 %   sin uso estático; solo se ve en ejecución
```

Notas:
- La IRAM al 100% es normal en el ESP32-S3: son 16 KB fijos de caché de instrucciones que el sistema reserva completos.
- El uso de PSRAM no se conoce al compilar, porque el tamaño se detecta al arrancar. Se medirá con las trazas de arranque cuando se flashee.
- La partición de app de 1 MB es la de la tabla de particiones por defecto. Si el firmware crece (pantalla, WiFi, audio), habrá que definir una tabla propia para aprovechar los 16 MB.
- Desde el commit del timer de 5 ms y la gestión de energía (`CONFIG_PM_ENABLE`) el firmware pesa unos 14 KB más de ROM y 2.7 KB más de DIRAM.

## Historial

| Fecha | Commit | Flash app (B) | Flash app (%) | DIRAM (B) | DIRAM (%) | Observación |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-02 | `a3b0e4a` | 188,016 | 17.9 | 54,890 | 16.1 | Proyecto base con GlobalDefine, Ram y MainProcess |
| 2026-11-02 | `5393c27` | 188,016 | 17.9 | 54,890 | 16.1 | Formato Allman, headers de archivo y funcion, nombres descriptivos; sin cambio de tamano |
| 2026-11-02 | `fb8cd28` | 189,424 | 18.1 | 54,890 | 16.1 | Driver GpioDriver (validacion de pin, esp_err_t); entradas sin pull interno |
| 2026-11-03 | este commit (sobre `5ef4950`) | 203,824 | 19.4 | 57,578 | 16.9 | TimerInitialization (reloj 240 MHz con esp_pm), constantes C_, timer periodico de 5 ms con u8MainFlag, uniones, reglas de formato |
