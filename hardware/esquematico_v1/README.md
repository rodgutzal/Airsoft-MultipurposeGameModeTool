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
| 40 | I2S_BCLK | reloj de bit del MAX98357A |
| 45 | I2S_LRC | selección de canal; pin de arranque, solo carga una entrada de alta impedancia |
| 0 | I2S_DIN | datos de audio; pin de arranque (botón BOOT de la tarjeta), solo carga una entrada de alta impedancia |
| 10 | VBAT_ADC | ADC1, divisor 1:2 |

Libres: GPIO43/44 (UART de depuración). Se evitó usarlos para I2S porque el puente USB-UART de la tarjeta maneja GPIO44 y chocaría con la salida de datos. No usar: GPIO19/20 (USB nativo) ni GPIO35 a 37 (PSRAM octal).

LCD_RD queda fijo en alto con R1. Si hace falta leer el ID del controlador (ILI9486 o ST7796U, cambia según el lote) se mueve a un pin libre.

## Alimentación

Dos celdas 18650 en paralelo, cargador TP4056 con protección y USB-C, interruptor de encendido y un elevador con el circuito integrado MT3608 (SOT-23-6) y sus componentes mínimos: capacitor de entrada C5 de 22 µF, inductor L1 de 22 µH y 3 A de saturación, diodo Schottky D4 (SS34), capacitor de salida C6 de 22 µF y el divisor de realimentación R15 de 100k y R16 de 13k. EN va a VIN. La salida es 0.6 V × (1 + 100k / 13k) = 5.2 V. La realimentación se toma después de D4, así que la caída del diodo queda compensada. El riel de 5 V alimenta la pantalla, los LEDs, el amplificador de audio y el pin 5V del DevKit, cuyo regulador da los 3.3 V. D4 también bloquea el retorno desde el USB del DevKit hacia el inductor.

El consumo estimado es de 400 mA desde la batería con WiFi encendido, pantalla con retroiluminación completa y un LED prendido. Con 6000 mAh nominales salen unas 10 horas, el doble de las 5 horas pedidas. Hay que medirlo en el prototipo.

## Audio

El buzzer pasivo del borrador inicial (unos 85 dB a 10 cm) quedaría en unos 40 dB a 15 m, por debajo del ruido de un campo. Se cambió por un módulo MAX98357A (I2S, clase D, 3.2 W en 4 Ω a 5 V) con una bocina de 4 Ω y 3 a 5 W. La estimación es de unos 95 dB a 1 m y unos 70 dB a 15 m, sin medir. Si la bocina elegida rinde menos de 90 dB a 1 W y 1 m, el alcance baja en la misma proporción.

En picos el amplificador puede pedir unos 0.8 A a 5 V. Con la batería baja, el MT3608 (interruptor interno de 2 A, unos 1 A de salida a 5.2 V con 3.3 V de batería) puede ser el cuello de botella, por eso C3 de 470 µF va junto al amplificador. Conviene limitar el volumen por firmware a la mitad y medir la caída de 5 V con el volumen máximo antes de cerrar el diseño.

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
| 1 | U3 | Circuito integrado MT3608 (SOT-23-6) | 8 (estimado) |
| 1 | L1 | Inductor de potencia 22 µH, saturación de 3 A o más, blindado | 12 (estimado) |
| 2 | C5, C6 | Capacitor cerámico 22 µF 10 V (0805 o 1206) | 5 (estimado) |
| 1 | SW4 | Interruptor de encendido | 15 |
| 1 | SW1 | Interruptor de palanca (selector de equipo) | 25 |
| 1 | SW2 | Interruptor de llave (armado de bomba) | 80 |
| 1 | SW3 | Push button de panel 16 a 22 mm | 40 |
| 1 | D1 | LED rojo 10 mm | 5 |
| 1 | D2 | LED azul 10 mm | 5 |
| 1 | U4 | Módulo amplificador I2S MAX98357A | 90 (estimado) |
| 1 | LS1 | Bocina 4 Ω, 3 a 5 W, cono de 40 a 57 mm | 60 (estimado) |
| 2 | Q1, Q2 | MOSFET N AO3400A (SOT-23); en perfboard sirve 2N7000 TO-92 | 5 |
| 1 | D4 | SS34 | 5 |
| 4 | R1, R2, R3, R4 | 10k | 1 |
| 3 | R5, R8, R10 | 100 Ω | 1 |
| 5 | R6, R9, R13, R14, R15 | 100k | 1 |
| 1 | R16 | 13k | 1 |
| 1 | R7 | 150 Ω | 1 |
| 3 | C1, C2, C4 | 100 nF | 2 |
| 1 | C3 | 470 µF 10 V electrolítico | 8 |

Total aproximado: 1,343 MXN por unidad sin gabinete.

Precios confirmados para comparar: ESP32 DevKit V1 (WROOM-32) a 199 en Steren y 130 + IVA en Teknomovo; Raspberry Pi Pico 2 W a 208 en 330ohms. El análisis completo de la elección del micro está en el documento del paso 1.

## Pendientes

- El MT3608, el inductor y los capacitores del elevador son componentes SMD. Para soldarlos hace falta una PCB propia o una placa adaptadora SOT-23-6; en perfboard no se pueden montar directo.
- Verificar con el prototipo que el riel quede entre 5.1 y 5.3 V, la tolerancia de las resistencias de 1% del divisor da unos 3% de variación.
- Confirmar qué líneas de datos usa el touch en la pantalla que llegue (sketch de diagnóstico de MCUFRIEND_kbv).
- Medir el consumo real y la corriente de la retroiluminación.
- Decidir gabinete y conectores para LEDs y switches de panel.
