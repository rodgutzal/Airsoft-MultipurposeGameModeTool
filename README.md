# Airsoft-MultipurposeGameModeTool

Herramienta multipropósito para partidas de airsoft, con hardware y software propios. Un mismo dispositivo cubre cinco modos de juego: captura la bandera, control de zona, rey de la colina, desactivación de bomba y extracción de paquete.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `Hw` | Hardware: esquemático en KiCad, PDF, lista de materiales, asignación de pines y propuesta de PCB (`Hw/pcb`). |
| `Sw` | Firmware en ESP-IDF, con su documentación. |

## Estado

Hardware en versión 0.8, en [`Hw/esquematico_v1`](Hw/esquematico_v1/README.md). Usa un ESP32-S3-DevKitC-1 N16R8 con pantalla TFT de 3.5 pulgadas (480x320, bus paralelo de 16 bits y touch resistivo XPT2046 por SPI), un expansor I2C MCP23017 para el teclado 4x4, dos switches y un push button, dos tiras LED RGB direccionables WS2812B, y audio por I2S con un amplificador MAX98357A y una bocina de 4 Ω. La alimentación tiene dos opciones y se construye una sola: un módulo LUORNG V8 para dos celdas 18650 (opción A) o TP4056 con MT3608 discretos (opción B). Todas las entradas digitales tienen pull-up externo de 10k.

La opción C (v0.9, en [`Hw/esquematico_v1/opcion_c`](Hw/esquematico_v1/opcion_c/README.md)) quita los módulos comprados para armar todo en una PCB propia: módulo ESP32-S3-WROOM-1 N16R8 sin tarjeta de desarrollo, cargador TP4056 con protección DW01A y FS8205A, elevador TPS61022, regulador AP7361C, MAX98357A suelto y USB-C al USB nativo para grabar, depurar y cargar.

El firmware está en `Sw` (ESP-IDF). Hoy arranca, fija el CPU a 240 MHz, inicia la flash y un ciclo principal de 5 ms con un LED de heartbeat; pantalla, audio, tiras LED, teclado y entradas todavía no tienen driver, y nada se ha probado en la placa. Su pinout es el de v0.7 y falta migrarlo a v0.8 (ver [`Sw/MapaPines.md`](Sw/MapaPines.md)).

## Documentación

Dónde leer según lo que necesites:

| Si quieres... | Lee |
| --- | --- |
| Entender el hardware y su pinout | [`Hw/esquematico_v1/README.md`](Hw/esquematico_v1/README.md) |
| Ver la variante para PCB propia | [`Hw/esquematico_v1/opcion_c/README.md`](Hw/esquematico_v1/opcion_c/README.md) y [`Hw/pcb/pcb_propuesta_v0.3.md`](Hw/pcb/pcb_propuesta_v0.3.md) |
| Entender cómo está organizado el firmware | [`Sw/README.md`](Sw/README.md) |
| Trabajar en el firmware (reglas, flujo de Git, cómo agregar un driver) | [`Sw/GuiaDesarrollo.md`](Sw/GuiaDesarrollo.md) |
| Saber qué hace cada función de cada driver | [`Sw/ReferenciaApi.md`](Sw/ReferenciaApi.md) |
| Saber qué pin del micro hace qué | [`Sw/MapaPines.md`](Sw/MapaPines.md) |
| Conocer el diseño objetivo del firmware | [`Sw/Arquitectura.md`](Sw/Arquitectura.md) |
| Ver el uso de memoria y los warnings | [`Sw/MemoryUsage.md`](Sw/MemoryUsage.md) y [`Sw/Warnings.md`](Sw/Warnings.md) |

## Requisitos de diseño

La autonomía mínima es de 5 horas, en periodos de uso de unos 30 minutos. El audio debe oírse a 15 metros al aire libre. El microcontrolador debe poder comprarse fácilmente en México y los precios se calculan en pesos mexicanos.
