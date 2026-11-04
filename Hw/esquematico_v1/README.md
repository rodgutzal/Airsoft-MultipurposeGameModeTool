# Esquemático v0.6

Esquemático de la herramienta, pensado para armarse con módulos comerciales. Todo es igual en las dos variantes menos la alimentación.

La opción A usa el módulo LUORNG V8 para dos celdas 18650 (archivo `airsoft_tool.kicad_sch`, vista rápida en `airsoft_tool.pdf`). La opción B es el diseño anterior con TP4056 y MT3608 discretos (archivo `opcion_b/airsoft_tool_opcion_B.kicad_sch`, vista rápida en `opcion_b/airsoft_tool_opcion_B.pdf`). Se construye una sola de las dos.

Las conexiones se hacen por etiqueta de red. Dos etiquetas con el mismo nombre son el mismo nodo. Los dos esquemáticos se generan con `gen_sch.py salida.kicad_sch bom.csv A` (o `B`; necesita la librería de símbolos de KiCad en `/usr/share/kicad/symbols`); se puede editar a mano en KiCad sin problema, pero si se vuelve a correr el script se sobrescriben esos cambios.

## Asignación de pines del ESP32-S3-DevKitC-1 N16R8

| GPIO | Señal | Notas |
| --- | --- | --- |
| 1 | LCD_RS | ADC1, lectura del touch |
| 2 | LCD_WR | ADC1, lectura del touch |
| 4, 5, 6, 7, 15, 16, 17, 18 | LCD_D0 a LCD_D7 | bus de 8 bits |
| 41 | LCD_RST | |
| 42 | LCD_CS | |
| 11, 12, 13, 14 | KEY_F1 a KEY_F4 | filas del teclado, salidas |
| 8, 9, 38, 39 | KEY_C1 a KEY_C4 | columnas del teclado, entradas con pull-up externo (R17 a R20) |
| 21 | SW_EQUIPO | selector de equipo, abierto = rojo; pull-up R2 |
| 47 | SW_ARMADO | interruptor de llave de la bomba; pull-up R3 |
| 48 | BTN_ACCION | push button (push and hold); pull-up R4 y filtro C1; comparte línea con el LED RGB de la tarjeta |
| 3 | LED_TIRA1 | datos de la tira 1 (DS2) a través de U5; pull-down R6 |
| 46 | LED_TIRA2 | datos de la tira 2 (DS3) a través de U5; pin de arranque, pull-down R9 |
| 40 | I2S_BCLK | reloj de bit del MAX98357A |
| 45 | I2S_LRC | selección de canal; pin de arranque, solo carga una entrada de alta impedancia |
| 0 | I2S_DIN | datos de audio; pin de arranque (botón BOOT de la tarjeta), solo carga una entrada de alta impedancia |
| 10 | VBAT_ADC | ADC1, divisor 1:2 |

Libres: GPIO43/44 (UART de depuración). Se evitó usarlos para I2S porque el puente USB-UART de la tarjeta maneja GPIO44 y chocaría con la salida de datos. No usar: GPIO19/20 (USB nativo) ni GPIO35 a 37 (PSRAM octal).

LCD_RD queda fijo en alto con R1. Si hace falta leer el ID del controlador (ILI9486 o ST7796U, cambia según el lote) se mueve a un pin libre.

## Pull-ups

Todas las entradas digitales tienen pull-up externo de 10k a 3.3 V y el firmware las configura sin resistencias internas (`ConfigGpioAsInput` en `Sw/AirsoftToolSw/GpioDriver.c`). Son R2 (SW_EQUIPO), R3 (SW_ARMADO), R4 (BTN_ACCION) y R17 a R20 (columnas KEY_C1 a KEY_C4, nuevas en v0.5). Con un contacto cerrado cada una consume 0.33 mA.

No llevan pull-up las filas del teclado, porque son salidas. Tampoco GPIO1 y GPIO2: además de LCD_RS y LCD_WR leen el touch por ADC, y una resistencia a 3.3 V movería la medición. Las demás líneas de la pantalla, el I2S y los datos de las tiras LED son salidas. De los pines de arranque, GPIO0 es salida (I2S_DIN) y la tarjeta ya trae el botón BOOT en esa línea; GPIO46 lleva pull-down (R9) a propósito, igual que GPIO3 (R6), para que las tiras no reciban basura mientras arranca el micro; GPIO45 no debe llevar pull-up, porque en alto durante el arranque fija el voltaje de la flash en 1.8 V y la N16R8 trabaja a 3.3 V. RST de la tarjeta ya tiene su pull-up y su capacitor en el DevKit.

Al escanear el teclado conviene que las filas no seleccionadas queden en alta impedancia o en open-drain. Si quedan en alto push-pull, dos teclas de la misma columna presionadas a la vez ponen en corto una fila en alto con la fila en bajo.

## Alimentación

Opción A, la principal. El módulo LUORNG V8 (M1) aloja dos celdas 18650 en paralelo (BT1 y BT2), las carga por USB-C o micro USB, tiene botón ON/OFF y entrega 5 V a 2.2 A nominales (3 A de emergencia) y 3 V a 1 A. Se usa solo la salida de 5 V, que va al riel +5V que alimenta la pantalla, las tiras LED, el amplificador de audio y el pin 5V del DevKit, cuyo regulador da los 3.3 V. R13 y R14 leen el voltaje de la batería desde el contacto positivo del portapilas. Los datos salen de la publicación en Amazon MX tal como se ve en las capturas de Roy del 2 de noviembre de 2026, no pude abrir la página.

Cosas por confirmar al recibir el módulo: que BAT- y GND sean comunes, que el contacto positivo del portapilas se pueda tomar para el divisor, qué interruptor de modo trae (hay que dejarlo en encendido continuo, porque en el modo automático se apaga con poca carga) y si el DevKit tiene diodo entre su USB y el pin 5V. Si no lo tiene, no se debe conectar USB al DevKit con M1 encendido. El proveedor es extranjero, la publicación avisa que puede diferir de la versión mexicana y solo quedaban 4 piezas.

Opción B, alternativa. Dos celdas 18650 en paralelo, cargador TP4056 con protección y USB-C, interruptor de encendido y un elevador con el circuito integrado MT3608 (SOT-23-6) y sus componentes mínimos: capacitor de entrada C5 de 22 µF, inductor L1 de 22 µH y 3 A de saturación, diodo Schottky D4 (SS34), capacitor de salida C6 de 22 µF y el divisor de realimentación R15 de 100k y R16 de 13k. EN va a VIN. La salida es 0.6 V × (1 + 100k / 13k) = 5.2 V, con la realimentación después de D4 para compensar su caída. D4 también bloquea el retorno desde el USB del DevKit. Es SMD, así que requiere PCB propia o una placa adaptadora SOT-23-6. Cuesta unos 156 MXN menos que la opción A.

El consumo estimado sin las tiras es de unos 370 mA desde la batería con WiFi encendido y la pantalla con retroiluminación completa. Las tiras lo cambian bastante; el cálculo está en la sección siguiente. Con las tiras en un color al 50 % salen unas 6.8 horas nominales con 6000 mAh. Hay que medirlo en el prototipo.

## Tiras LED RGB

Los LEDs rojo y azul de 10 mm (D1, D2, con Q1, Q2, R5, R7, R8 y R10) se cambiaron por dos tiras RGB direccionables WS2812B de 5 V, DS2 y DS3. Cada tira tiene su propia línea de datos, GPIO3 y GPIO46, así el firmware las maneja por separado con dos canales RMT del ESP32-S3. Con tiras direccionables cada LED toma su propio color, lo que permite mostrar el equipo con cualquier color, una barra que se vacía como contador de la bomba, el avance de captura de una zona o parpadeos de alerta, todo por firmware.

Se descartaron las tiras RGB analógicas (las de 4 hilos, 12 V). Pintan toda la tira de un solo color, necesitan un elevador a 12 V y tres MOSFET con PWM por tira, seis en total. Las WS2812B ocupan los mismos dos GPIO que ya usaban los LEDs y van directo al riel de 5 V.

El WS2812B alimentado a 5 V pide un alto de al menos 0.7 × VDD, 3.5 V, y el ESP32 da 3.3 V. U5 es un 74AHCT125 alimentado a 5 V, con entradas TTL (alto desde 2 V), que sube las dos señales; sus otros dos buffers quedan con la entrada y el habilitador a GND. Cada dato pasa por una resistencia de 330 Ω (R5 y R8) puesta junto a la entrada DIN de la tira, para amortiguar reflexiones en el cable. C8 de 1000 µF va en la entrada de 5 V de las tiras y C7 de 100 nF junto a U5. R6 y R9 de 100k mantienen los datos en bajo durante el arranque. Conviene un conector JST SM de 3 hilos en cada tira para poder sacarlas del gabinete.

Supuesto, falta que Roy lo confirme: 15 LEDs por tira, unos 25 cm de tira de 60 LEDs/m, 30 LEDs en total. Un rollo de 1 m alcanza para las dos.

| Caso (las dos tiras, 30 LEDs) | Corriente a 5 V | Desde la batería |
| --- | --- | --- |
| Apagadas (consumo propio del WS2812B, ~1 mA por LED) | 30 mA | 45 mA |
| Un color al 50 % (rojo o azul) | 330 mA | 0.5 A |
| Un color al 100 %, tope fijado por firmware | 630 mA | 0.97 A |
| Blanco al 100 %, ~60 mA por LED, no permitido | 1.8 A | 2.8 A |

La columna de batería supone 3.7 V y 88 % de eficiencia del elevador, y 20 mA por color por LED (la hoja de datos de Worldsemi da 12 mA; los clones suelen pedir más). Sumando los 370 mA del resto, la autonomía nominal con 6000 mAh queda en unas 6.8 h con un color al 50 % y en unas 4.5 h con un color al 100 % todo el tiempo. Para cumplir las 5 h hay que usar brillo moderado o encender las tiras solo en los eventos. El firmware debe limitar las dos tiras a 600 mA en total (FastLED y la biblioteca led_strip de ESP-IDF permiten calcular la corriente por cuadro y escalar el brillo).

Pico en el riel de 5 V con la opción A: 0.8 A del amplificador, 0.63 A de las tiras y unos 0.25 A del resto, cerca de 1.7 A contra los 2.2 A nominales de M1. Con la opción B no alcanza: el MT3608 entrega alrededor de 1 A a 5.2 V con la batería en 3.3 V, así que hay que bajar el tope de las tiras a 300 mA y el volumen a la mitad, o poner un segundo elevador solo para las tiras.

## Audio

El buzzer pasivo del borrador inicial (unos 85 dB a 10 cm) quedaría en unos 40 dB a 15 m, por debajo del ruido de un campo. Se cambió por un módulo MAX98357A (I2S, clase D, 3.2 W en 4 Ω a 5 V) con una bocina de 4 Ω y 3 a 5 W. La estimación es de unos 95 dB a 1 m y unos 70 dB a 15 m, sin medir. Si la bocina elegida rinde menos de 90 dB a 1 W y 1 m, el alcance baja en la misma proporción.

En picos el amplificador puede pedir unos 0.8 A a 5 V. Con la opción A el módulo da 2.2 A nominales y no debería ser problema. Con la opción B, con la batería baja, el MT3608 (interruptor interno de 2 A, unos 1 A de salida a 5.2 V con 3.3 V de batería) puede ser el cuello de botella. C3 de 470 µF va junto al amplificador en ambos casos. Conviene limitar el volumen por firmware a la mitad y medir la caída de 5 V con el volumen máximo antes de cerrar el diseño.

## Lista de materiales

Lista de la opción A. El Excel `lista_materiales_v0.6.xlsx` trae las dos opciones en hojas separadas, con subtotales y totales calculados. Precios aproximados en MXN y sin verificar en tienda, salvo el de M1 ($278.10 en la captura de Roy). Mercado Libre y Amazon MX no permiten lectura automática.

| Cant. | Referencia | Pieza | Precio aprox. c/u |
| --- | --- | --- | --- |
| 1 | U1 | ESP32-S3-DevKitC-1 N16R8 | 300 |
| 1 | DS1 | Pantalla TFT 3.5" 480x320 ILI9486/ST7796U shield UNO/MEGA, variante con touch | 300 |
| 1 | KP1 | Teclado de membrana 4x4 | 40 |
| 2 | BT1, BT2 | Celda 18650 3000 mAh de marca (Samsung 30Q, LG HG2 o similar) | 120 |
| 1 | M1 | Módulo LUORNG V8 para 2 celdas 18650, carga USB-C y micro USB, salida 5 V y 3 V | 278.10 (captura de Roy) |
| 1 | SW1 | Interruptor de palanca (selector de equipo) | 25 |
| 1 | SW2 | Interruptor de llave (armado de bomba) | 80 |
| 1 | SW3 | Push button de panel 16 a 22 mm | 40 |
| 1 | DS2, DS3 | Tira WS2812B 5 V, 60 LEDs/m, IP65, rollo de 1 m (dos tramos de 15 LEDs) | 180 (estimado) |
| 1 | U5 | 74AHCT125 DIP-14 (SN74AHCT125N); el 74HCT125 también sirve | 30 (estimado) |
| 2 | sin ref. | Par de conectores JST SM de 3 pines con cable | 10 |
| 1 | U4 | Módulo amplificador I2S MAX98357A | 90 (estimado) |
| 1 | LS1 | Bocina 4 Ω, 3 a 5 W, cono de 40 a 57 mm | 60 (estimado) |
| 8 | R1, R2, R3, R4, R17, R18, R19, R20 | 10k | 1 |
| 2 | R5, R8 | 330 Ω | 1 |
| 4 | R6, R9, R13, R14 | 100k | 1 |
| 4 | C1, C2, C4, C7 | 100 nF | 2 |
| 1 | C3 | 470 µF 10 V electrolítico | 8 |
| 1 | C8 | 1000 µF 10 V electrolítico | 12 |

Total aproximado de la opción A: 1,725 MXN por unidad sin gabinete.

La opción B cambia M1 por portapilas (35), TP4056 (35), interruptor de encendido (15), MT3608 (8), L1 (12), C5 y C6 (10), D4 (5), R15 (1) y R16 (1), para un total aproximado de 1,569 MXN. En las dos opciones el cambio a tiras suma unos 222 MXN.

Precios confirmados para comparar: ESP32 DevKit V1 (WROOM-32) a 199 en Steren y 130 + IVA en Teknomovo; Raspberry Pi Pico 2 W a 208 en 330ohms. El análisis completo de la elección del micro está en el documento del paso 1.

## Pendientes

- Confirmar al recibir M1 los puntos listados en Alimentación.
- Opción B: el MT3608, el inductor y los capacitores son SMD, y el riel debe quedar entre 5.1 y 5.3 V con resistencias de 1%.
- Confirmar qué líneas de datos usa el touch en la pantalla que llegue (sketch de diagnóstico de MCUFRIEND_kbv).
- Medir el consumo real y la corriente de la retroiluminación.
- Decidir gabinete y conectores para las tiras y los switches de panel.
- Confirmar longitud y número de LEDs de cada tira (supuesto: 15 LEDs, 25 cm).
- Medir la corriente real de las tiras compradas al 50 % y al 100 % de un color.
