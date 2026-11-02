# Esquemático v0.1

Primera versión del esquemático de la herramienta, pensada para armarse en perfboard con módulos comerciales. El archivo de KiCad 7 es `airsoft_tool.kicad_sch` y la vista rápida está en `airsoft_tool.pdf`.

Las conexiones se hacen por etiqueta de red. Dos etiquetas con el mismo nombre son el mismo nodo. El esquemático se genera con `gen_sch.py` (necesita la librería de símbolos de KiCad en `/usr/share/kicad/symbols`); se puede editar a mano en KiCad sin problema, pero si se vuelve a correr el script se sobrescriben esos cambios.

## Asignación de pines del ESP32-S3-DevKitC-1 N16R8

| GPIO | Señal | Notas |
| --- | --- | --- |
| 1 | LCD_RS | ADC1, lectura del touch |
| 2 | LCD_WR | ADC1, lectura del touch |
| 4, 5, 6, 7, 15, 16, 17, 18 | LCD_D0 a LCD_D7 | bus de 8 bits |
| 41 | LCD_RST | |
| 42 | LCD_CS | |
| 11, 12, 13, 14 | KEY_F1 a KEY_F4 | filas del teclado, salidas |
| 8, 9, 38, 39 | KEY_C1 a KEY_C4 | columnas del teclado, entradas con pull-up |
| 21 | SW_EQUIPO | selector de equipo, abierto = rojo |
| 47 | SW_ARMADO | interruptor de llave de la bomba |
| 48 | BTN_ACCION | push button (push and hold); comparte línea con el LED RGB de la tarjeta |
| 3 | LED_ROJO | compuerta de Q1 |
| 46 | LED_AZUL | compuerta de Q2, pin de arranque con pull-down de 100k |
| 40 | BUZZER | PWM a la compuerta de Q3 |
| 10 | VBAT_SENSE | ADC1, divisor 1:2 |

Libres: GPIO0 (botón BOOT), GPIO45 (arranque), GPIO43/44 (UART de depuración). No usar: GPIO19/20 (USB nativo) ni GPIO35 a 37 (PSRAM octal).

LCD_RD queda fijo en alto con R1. Si hace falta leer el ID del controlador (ILI9486 o ST7796U, cambia según el lote) se mueve a un pin libre.

## Alimentación

Dos celdas 18650 en paralelo, cargador TP4056 con protección y USB-C, interruptor de encendido y elevador MT3608 ajustado a 5.1 V. El riel de 5 V alimenta la pantalla, los LEDs, el buzzer y el pin 5V del DevKit, cuyo regulador da los 3.3 V. D4 evita que el USB del DevKit empuje corriente hacia el elevador.

El consumo estimado es de 400 mA desde la batería con WiFi encendido, pantalla con retroiluminación completa y un LED prendido. Con 6000 mAh nominales salen unas 10 horas, el doble de las 5 horas pedidas. Hay que medirlo en el prototipo.

## Lista de materiales

Precios aproximados en MXN, sin verificar en tienda (Mercado Libre y Amazon MX no permiten lectura automática). Los únicos confirmados al 2 de noviembre de 2026 son los de las notas.

| Cant. | Referencia | Pieza | Precio aprox. c/u |
| --- | --- | --- | --- |
| 1 | U1 | ESP32-S3-DevKitC-1 N16R8 | 300 |
| 1 | DS1 | Pantalla TFT 3.5" 480x320 ILI9486/ST7796U shield UNO/MEGA, variante con touch | 300 |
| 1 | KP1 | Teclado de membrana 4x4 | 40 |
| 2 | BT1, BT2 | Celda 18650 3000 mAh de marca (Samsung 30Q, LG HG2 o similar) | 120 |
| 1 | | Portapilas 2x18650 | 35 |
| 1 | U2 | Módulo TP4056 USB-C con protección (DW01) | 35 |
| 1 | U3 | Módulo elevador MT3608 | 35 |
| 1 | SW4 | Interruptor de encendido | 15 |
| 1 | SW1 | Interruptor de palanca (selector de equipo) | 25 |
| 1 | SW2 | Interruptor de llave (armado de bomba) | 80 |
| 1 | SW3 | Push button de panel 16 a 22 mm | 40 |
| 1 | D1 | LED rojo 10 mm | 5 |
| 1 | D2 | LED azul 10 mm | 5 |
| 1 | BZ1 | Buzzer pasivo 5 V | 15 |
| 3 | Q1, Q2, Q3 | MOSFET N AO3400A (SOT-23); en perfboard sirve 2N7000 TO-92 | 5 |
| 1 | D3 | 1N4148 | 2 |
| 1 | D4 | SS34 | 5 |
| 4 | R1, R2, R3, R4 | 10k | 1 |
| 4 | R5, R8, R10, R11 | 100 Ω | 1 |
| 5 | R6, R9, R12, R13, R14 | 100k | 1 |
| 1 | R7 | 150 Ω | 1 |
| 2 | C1, C2 | 100 nF | 2 |

Total aproximado: 1,250 MXN por unidad sin gabinete.

Precios confirmados para comparar: ESP32 DevKit V1 (WROOM-32) a 199 en Steren y 130 + IVA en Teknomovo; Raspberry Pi Pico 2 W a 208 en 330ohms. El análisis completo de la elección del micro está en el documento del paso 1.

## Pendientes

- Confirmar qué líneas de datos usa el touch en la pantalla que llegue (sketch de diagnóstico de MCUFRIEND_kbv).
- Medir el consumo real y la corriente de la retroiluminación.
- Decidir gabinete y conectores para LEDs y switches de panel.
