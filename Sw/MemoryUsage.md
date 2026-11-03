# Uso de memoria

Se actualiza antes de cada commit que toque `Sw/`, después de compilar y correr `idf.py size`. ESP-IDF v6.1, target esp32s3 (16 MB de flash, 8 MB de PSRAM octal).

## Estado actual

Branch `b#2_ProyectoBaseEspIdf`, 2026-11-02.

```
ROM (Flash)
  Partición de app (1 MB)  [████░░░░░░░░░░░░░░░░]  17.9 %   usado 188,016 B   libre 860,560 B
  Flash total (16 MB)      [░░░░░░░░░░░░░░░░░░░░]   1.1 %   usado 188,016 B   libre ≈ 16.6 MB

RAM interna
  DIRAM (datos + código)   [███░░░░░░░░░░░░░░░░░]  16.1 %   usado  54,890 B   libre 286,870 B
     .text  38,223 B (11.2 %)   .data 13,891 B (4.1 %)   .bss 2,776 B (0.8 %)
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

## Historial

| Fecha | Commit | Flash app (B) | Flash app (%) | DIRAM (B) | DIRAM (%) | Observación |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-02 | posterior a `5523a4e` | 188,016 | 17.9 | 54,890 | 16.1 | Proyecto base con GlobalDefine, Ram y MainProcess |
