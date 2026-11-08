# Esquemático v0.8

Esquemático de la herramienta, pensado para armarse con módulos comerciales. Todo es igual en las dos variantes menos la alimentación.

La opción A usa el módulo LUORNG V8 para dos celdas 18650 (archivo `airsoft_tool.kicad_sch`, vista rápida en `airsoft_tool.pdf`). La opción B es el diseño anterior con TP4056 y MT3608 discretos (archivo `opcion_b/airsoft_tool_opcion_B.kicad_sch`, vista rápida en `opcion_b/airsoft_tool_opcion_B.pdf`). Se construye una sola de las dos.

La opción C (v0.9) cambia los módulos comprados por componentes discretos para una PCB propia: módulo ESP32-S3-WROOM-1 N16R8 sin DevKit, alimentación discreta, MAX98357A suelto y USB-C para grabar y depurar. Está en `opcion_c/`, con su propio README y la lista `lista_materiales_v0.9_opcionC.xlsx`.

Las conexiones se hacen por etiqueta de red. Dos etiquetas con el mismo nombre son el mismo nodo. Los dos esquemáticos se generan con `gen_sch.py salida.kicad_sch bom.csv A` (o `B`; necesita la librería de símbolos de KiCad en `/usr/share/kicad/symbols`); se puede editar a mano en KiCad sin problema, pero si se vuelve a correr el script se sobrescriben esos cambios.

## Asignación de pines del ESP32-S3-DevKitC-1 N16R8

| GPIO | Señal | Notas |
| --- | --- | --- |
| 1 | LCD_RS | pin 2 de la pantalla |
| 2 | LCD_WR | pin 3 de la pantalla |
| 4, 5, 6, 7, 15, 16, 17, 18 | LCD_D0 a LCD_D7 | DB0 a DB7, pines 6 a 13 de la pantalla |
| 8, 9, 11, 12, 13, 14, 21, 47 | LCD_D8 a LCD_D15 | DB8 a DB15, pines 14 a 21 de la pantalla |
| 38 | TOUCH_CLK | CLK del XPT2046, pin 34; en v1.1 de la tarjeta también va al LED RGB |
| 46 | TOUCH_MOSI | pin 30; pin de arranque, pull-down R9 |
| 48 | TOUCH_MISO | pin 29 |
| 41 | TOUCH_CS | T_CS, pin 33 |
| 39 | I2C_SDA | expansor U6, pull-up R10 |
| 42 | I2C_SCL | expansor U6, pull-up R11 |
| 3 | LED_TIRA | dato de las dos tiras encadenadas, a través de U5; pull-down R6 |
| 40 | I2S_BCLK | reloj de bit del MAX98357A |
| 45 | I2S_LRC | selección de canal; pin de arranque, solo carga una entrada de alta impedancia |
| 0 | I2S_DIN | datos de audio; pin de arranque (botón BOOT de la tarjeta), solo carga una entrada de alta impedancia |
| 10 | VBAT_ADC | ADC1, divisor 1:2 |
| 43 | LED_ESTADO | LED verde D5 con R21 a GND; es U0TXD, ver la sección LED de estado |
| EN (pin RST de J1) | ESP_EN | va también al RST de la pantalla (pin 5) |

Libre: GPIO44 (U0RXD). El puente USB-UART de la tarjeta lo maneja como salida, por eso no se usa. No usar: GPIO19/20 (USB nativo) ni GPIO35 a 37 (PSRAM octal). No queda ningún GPIO libre en la tarjeta; lo que se agregue después va al expansor U6, que tiene GPB5 a GPB7 libres.

## Expansor U6 (MCP23017)

| Pin de U6 | Señal |
| --- | --- |
| GPA0 a GPA3 | KEY_F1 a KEY_F4, filas del teclado |
| GPA4 a GPA7 | KEY_C1 a KEY_C4, columnas del teclado, pull-ups R17 a R20 |
| GPB0 | SW_EQUIPO, pull-up R2 |
| GPB1 | SW_ARMADO, pull-up R3 |
| GPB2 | BTN_ACCION, pull-up R4 y filtro C1 |
| GPB3 | TOUCH_PEN (PEN de la pantalla, bajo al tocar) |
| GPB4 | LCD_BL (alto = retroiluminación encendida) |
| GPB5 a GPB7 | libres |

U6 es un MCP23017-E/SP en DIP-28, alimentado a 3.3 V, en la dirección 0x20 (A0 a A2 a GND). RESET va a 3.3 V con R7 de 10k, C9 de 100 nF va junto a VDD. INTA e INTB quedan sin conectar porque no sobra GPIO; el firmware lee el expansor por sondeo. Un barrido completo del teclado son 4 escrituras y 4 lecturas por I2C, menos de 1 ms a 400 kHz.

Al arrancar U6 deja todas sus líneas como entradas. GPB4 queda flotando y la base del transistor de la retroiluminación tiene su resistencia a GND en el módulo, así que la pantalla arranca apagada hasta que el firmware ponga GPB4 en alto.

## Pull-ups

Todas las entradas digitales tienen pull-up externo de 10k a 3.3 V y el firmware no activa las resistencias internas del MCP23017 (registro GPPU en 0). Son R2 (SW_EQUIPO), R3 (SW_ARMADO), R4 (BTN_ACCION) y R17 a R20 (columnas KEY_C1 a KEY_C4). Desde v0.8 todas están en el expansor U6. Con un contacto cerrado cada una consume 0.33 mA. TOUCH_PEN no lleva resistencia externa porque el XPT2046 trae su pull-up.

El bus I2C lleva R10 y R11 de 4.7k a 3.3 V. Las líneas de la pantalla, el SPI del touch, el I2S y el dato de las tiras son salidas. De los pines de arranque, GPIO0 es salida (I2S_DIN) y la tarjeta ya trae el botón BOOT en esa línea; GPIO46 (TOUCH_MOSI) lleva pull-down R9 y no debe llevar pull-up, porque GPIO46 en alto junto con GPIO0 en bajo es una combinación de arranque inválida y no se podría grabar por UART; GPIO3 lleva R6 para que las tiras no reciban basura al arrancar; GPIO45 no debe llevar pull-up, porque en alto durante el arranque fija el voltaje de la flash en 1.8 V y la N16R8 trabaja a 3.3 V. RST de la tarjeta ya tiene su pull-up y su capacitor en el DevKit.

Al escanear el teclado conviene que las filas no seleccionadas queden en alta impedancia. En el MCP23017 eso se hace dejando como entrada (IODIR en 1) las filas que no se están leyendo y como salida en bajo solo la fila activa. Si quedan en alto push-pull, dos teclas de la misma columna presionadas a la vez ponen en corto una fila en alto con la fila en bajo.

## Pantalla

DS1 es el módulo "3.5' LCD MODULE" que tiene Roy (foto del 8 de noviembre de 2026): ILI9486, 480x320, touch resistivo con XPT2046, ranura microSD y una flash en la placa. El conector es una tira de 2x17 pines (34), con el pin 1 arriba a la izquierda viendo la serigrafía; los impares van en la fila de arriba y los pares en la de abajo.

| Pin | Señal | Pin | Señal |
| --- | --- | --- | --- |
| 1 | CS, a GND | 2 | RS, GPIO1 |
| 3 | WR, GPIO2 | 4 | RD, a 3.3 V con R1 |
| 5 | RST, a EN de la tarjeta | 6 | DB0, GPIO4 |
| 7 | DB1, GPIO5 | 8 | DB2, GPIO6 |
| 9 | DB3, GPIO7 | 10 | DB4, GPIO15 |
| 11 | DB5, GPIO16 | 12 | DB6, GPIO17 |
| 13 | DB7, GPIO18 | 14 | DB8, GPIO8 |
| 15 | DB9, GPIO9 | 16 | DB10, GPIO11 |
| 17 | DB11, GPIO12 | 18 | DB12, GPIO13 |
| 19 | DB13, GPIO14 | 20 | DB14, GPIO21 |
| 21 | DB15, GPIO47 | 22 | SDCS, a 3.3 V |
| 23 | BL, U6 GPB4 | 24 | VDD, 3.3 V |
| 25 | VDD, 3.3 V | 26 | GND |
| 27 | GND | 28 | 5V (BL_VDD), sin conectar |
| 29 | MISO, GPIO48 | 30 | MOSI, GPIO46 |
| 31 | PEN, U6 GPB3 | 32 | F_CS, a 3.3 V |
| 33 | T_CS, GPIO41 | 34 | CLK, GPIO38 |

La serigrafía coincide con el modelo MRB3503 de LCDWIKI (https://www.lcdwiki.com/3.5inch_16BIT_Module_ILI9486_SKU:MRB3503). Su manual dice "This module hardware only supports 16-bit parallel bus transmission", así que el bus de 8 bits de las versiones anteriores no habría funcionado. El ESP32-S3 maneja el bus 8080 de 16 bits con el periférico LCD_CAM (`esp_lcd_new_i80_bus` con `bus_width = 16`).

CS va fijo a GND porque la pantalla es lo único en el bus (en ESP-IDF, `cs_gpio_num = -1`). RD queda en alto con R1, solo se escribe. RST va al EN de la tarjeta, de modo que la pantalla se reinicia junto con el micro; en caliente el firmware usa el comando de reset por software (0x01).

Alimentación. Según el esquemático del MRB3503, VDD entra a un regulador XC6206 de 3.3 V, y el puente J1 de la placa lo puentea cuando se alimenta con 3.3 V. Alimentar VDD con 3.3 V funciona con J1 abierto o en corto; con 5 V y J1 en corto se quemaría la lógica. Por eso VDD (pines 24 y 25) va al 3V3 del DevKit, que es además lo que recomienda el manual. El pin 5V (28) es BL_VDD, la alimentación externa de la retroiluminación, que solo se usa si se suelda R4 en la placa; viene con R5, que la toma de los 3.3 V internos, así que el pin 28 queda sin conectar. La lógica es de 3.3 V, igual que el ESP32-S3, sin traslador.

El SPI del touch es compartido en el módulo con la microSD y la flash. SDCS (22) y F_CS (32) van a 3.3 V para dejarlas fuera del bus. Si después se quiere usar la microSD, SDCS pasa a GPB5 de U6 o a un GPIO que se libere.

Pendiente de medir en la pantalla de Roy: la corriente de la retroiluminación desde 3.3 V. El regulador del DevKitC-1 da hasta unos 800 mA y el ESP32-S3 con WiFi pide picos de unos 350 mA, así que hay margen, pero conviene medirlo.

## LED de estado

D5 es un LED verde de 5 mm difuso (verde estándar, unos 2.1 V de caída) conectado de GPIO43 a GND a través de R21 de 330 Ω. Es activo en alto y toma (3.3 − 2.1) / 330 = 3.6 mA, poco para el pin y suficiente para un indicador en interior. Al sol puede quedarse corto; si hace falta más brillo, R21 baja a 150 Ω (8 mA). R21 usa el mismo valor que R5 y R8.

GPIO43 es U0TXD, la salida de la UART0. En el diseño no tiene otro uso. En el DevKitC-1 va también a la entrada RX del puente USB-UART de la tarjeta, que es una entrada, así que el LED no choca eléctricamente con nada. Sí hay efectos que debe conocer el firmware.

La ROM imprime los mensajes de arranque por U0TXD antes de que corra el firmware, así que el LED parpadea unos cientos de milisegundos al encender o después de cada reset. Mientras la UART está en reposo la línea queda en alto, de modo que el LED se ve encendido en ese tramo.

ESP-IDF manda la consola (ESP_LOGx y printf) a UART0 por omisión. Al configurar GPIO43 como GPIO la consola deja de salir por el conector UART de la tarjeta. Hay que pasarla al USB nativo (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` en `Sw/sdkconfig.defaults`) y conectar la tarjeta por su conector USB, o desactivarla. Grabar por el conector UART sigue funcionando, con el LED parpadeando durante la carga.

GPIO43 no es pin de arranque. El firmware lo tiene como `C_PIN_LED_ESTADO` en `Sw/AirsoftToolSw/GlobalDefine.h`.

## Alimentación

Opción A, la principal. El módulo LUORNG V8 (M1) aloja dos celdas 18650 en paralelo (BT1 y BT2), las carga por USB-C o micro USB, tiene botón ON/OFF y entrega 5 V a 2.2 A nominales (3 A de emergencia) y 3 V a 1 A. Se usa solo la salida de 5 V, que va al riel +5V que alimenta la pantalla, las tiras LED, el amplificador de audio y el pin 5V del DevKit, cuyo regulador da los 3.3 V. R13 y R14 leen el voltaje de la batería desde el contacto positivo del portapilas. Los datos salen de la publicación en Amazon MX tal como se ve en las capturas de Roy del 2 de noviembre de 2026, no pude abrir la página.

Cosas por confirmar al recibir el módulo: que BAT- y GND sean comunes, que el contacto positivo del portapilas se pueda tomar para el divisor, qué interruptor de modo trae (hay que dejarlo en encendido continuo, porque en el modo automático se apaga con poca carga) y si el DevKit tiene diodo entre su USB y el pin 5V. Si no lo tiene, no se debe conectar USB al DevKit con M1 encendido. El proveedor es extranjero, la publicación avisa que puede diferir de la versión mexicana y solo quedaban 4 piezas.

Opción B, alternativa. Dos celdas 18650 en paralelo, cargador TP4056 con protección y USB-C, interruptor de encendido y un elevador con el circuito integrado MT3608 (SOT-23-6) y sus componentes mínimos: capacitor de entrada C5 de 22 µF, inductor L1 de 22 µH y 3 A de saturación, diodo Schottky D4 (SS34), capacitor de salida C6 de 22 µF y el divisor de realimentación R15 de 100k y R16 de 13k. EN va a VIN. La salida es 0.6 V × (1 + 100k / 13k) = 5.2 V, con la realimentación después de D4 para compensar su caída. D4 también bloquea el retorno desde el USB del DevKit. Es SMD, así que requiere PCB propia o una placa adaptadora SOT-23-6. Cuesta unos 156 MXN menos que la opción A.

El consumo estimado sin las tiras es de unos 370 mA desde la batería con WiFi encendido y la pantalla con retroiluminación completa. Las tiras lo cambian bastante; el cálculo está en la sección siguiente. Con las tiras en un color al 50 % salen unas 6.8 horas nominales con 6000 mAh. Hay que medirlo en el prototipo.

## Tiras LED RGB

Los LEDs rojo y azul de 10 mm (D1, D2, con Q1, Q2, R5, R7, R8 y R10) se cambiaron por dos tiras RGB direccionables WS2812B de 5 V, DS2 y DS3. Desde v0.8 las dos tiras van encadenadas en una sola línea de datos, GPIO3: el dato entra a DS2 y sale por su DOUT hacia DS3 a través de R8. El firmware las sigue manejando por separado: los LEDs 0 a 14 son DS2 y los 15 a 29 son DS3, con un solo canal RMT. GPIO46 pasó al touch. Si DS2 se desconecta, DS3 se queda sin dato. Con tiras direccionables cada LED toma su propio color, lo que permite mostrar el equipo con cualquier color, una barra que se vacía como contador de la bomba, el avance de captura de una zona o parpadeos de alerta, todo por firmware.

Se descartaron las tiras RGB analógicas (las de 4 hilos, 12 V). Pintan toda la tira de un solo color, necesitan un elevador a 12 V y tres MOSFET con PWM por tira, seis en total. Las WS2812B ocupan los mismos dos GPIO que ya usaban los LEDs y van directo al riel de 5 V.

El WS2812B alimentado a 5 V pide un alto de al menos 0.7 × VDD, 3.5 V, y el ESP32 da 3.3 V. U5 es un 74AHCT125 alimentado a 5 V, con entradas TTL (alto desde 2 V), que sube la señal; sus otros tres buffers quedan con la entrada y el habilitador a GND. R5 de 330 Ω va junto a la entrada DIN de DS2 y R8 de 330 Ω entre DOUT de DS2 y DIN de DS3, para amortiguar reflexiones en el cable. C8 de 1000 µF va en la entrada de 5 V de las tiras y C7 de 100 nF junto a U5. R6 de 100k mantiene el dato en bajo durante el arranque. Conviene un conector JST SM de 3 hilos en cada tira para poder sacarlas del gabinete.

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

Lista de la opción A. El Excel `lista_materiales_v0.8.xlsx` trae las dos opciones en hojas separadas, con subtotales y totales calculados. Precios aproximados en MXN y sin verificar en tienda, salvo el de M1 ($278.10 en la captura de Roy). Mercado Libre y Amazon MX no permiten lectura automática.

| Cant. | Referencia | Pieza | Precio aprox. c/u |
| --- | --- | --- | --- |
| 1 | U1 | ESP32-S3-DevKitC-1 N16R8 | 300 |
| 1 | DS1 | Módulo TFT 3.5" 480x320 ILI9486, bus de 16 bits, touch XPT2046, conector 2x17 (Roy ya lo tiene) | 300 |
| 1 | KP1 | Teclado de membrana 4x4 | 40 |
| 1 | U6 | Expansor I2C MCP23017-E/SP DIP-28 | 50 (estimado) |
| 1 | sin ref. | Zócalo DIP-28 angosto para U6 | 8 (estimado) |
| 2 | BT1, BT2 | Celda 18650 3000 mAh de marca (Samsung 30Q, LG HG2 o similar) | 120 |
| 1 | M1 | Módulo LUORNG V8 para 2 celdas 18650, carga USB-C y micro USB, salida 5 V y 3 V | 278.10 (captura de Roy) |
| 1 | SW1 | Interruptor de palanca (selector de equipo) | 25 |
| 1 | SW2 | Interruptor de llave (armado de bomba) | 80 |
| 1 | SW3 | Push button de panel 16 a 22 mm | 40 |
| 1 | DS2, DS3 | Tira WS2812B 5 V, 60 LEDs/m, IP65, rollo de 1 m (dos tramos de 15 LEDs encadenados) | 180 (estimado) |
| 1 | U5 | 74AHCT125 DIP-14 (SN74AHCT125N); el 74HCT125 también sirve | 30 (estimado) |
| 1 | D5 | LED verde 5 mm difuso, Vf ~2.1 V (LED de estado) | 2 (estimado) |
| 2 | sin ref. | Par de conectores JST SM de 3 pines con cable | 10 |
| 1 | U4 | Módulo amplificador I2S MAX98357A | 90 (estimado) |
| 1 | LS1 | Bocina 4 Ω, 3 a 5 W, cono de 40 a 57 mm | 60 (estimado) |
| 9 | R1, R2, R3, R4, R7, R17, R18, R19, R20 | 10k | 1 |
| 2 | R10, R11 | 4.7k | 1 |
| 3 | R5, R8, R21 | 330 Ω | 1 |
| 4 | R6, R9, R13, R14 | 100k | 1 |
| 5 | C1, C2, C4, C7, C9 | 100 nF | 2 |
| 1 | C3 | 470 µF 10 V electrolítico | 8 |
| 1 | C8 | 1000 µF 10 V electrolítico | 12 |

Total aproximado de la opción A: 1,791 MXN por unidad sin gabinete.

La opción B cambia M1 por portapilas (35), TP4056 (35), interruptor de encendido (15), MT3608 (8), L1 (12), C5 y C6 (10), D4 (5), R15 (1) y R16 (1), para un total aproximado de 1,635 MXN. El expansor U6 con su zócalo y pasivos suma 63 MXN en las dos. En las dos opciones el cambio a tiras suma unos 222 MXN.

Precios confirmados para comparar: ESP32 DevKit V1 (WROOM-32) a 199 en Steren y 130 + IVA en Teknomovo; Raspberry Pi Pico 2 W a 208 en 330ohms. El análisis completo de la elección del micro está en el documento del paso 1.

## Pendientes

- Confirmar al recibir M1 los puntos listados en Alimentación.
- Opción B: el MT3608, el inductor y los capacitores son SMD, y el riel debe quedar entre 5.1 y 5.3 V con resistencias de 1%.
- Revisar en la pantalla de Roy si J1 (junto al regulador) está abierto o en corto y si R5 está soldado y R4 no; el diseño funciona en los dos casos de J1.
- Medir la corriente de la retroiluminación desde 3.3 V.
- Confirmar la versión de la tarjeta (v1.0 o v1.1): el LED RGB está en GPIO48 o en GPIO38.
- Firmware: mover teclado, switches y botón al MCP23017 y actualizar los pines en `Sw/AirsoftToolSw/GlobalDefine.h`.
- Medir el consumo real y la corriente de la retroiluminación.
- Decidir gabinete y conectores para las tiras y los switches de panel.
- Confirmar longitud y número de LEDs de cada tira (supuesto: 15 LEDs, 25 cm).
- Medir la corriente real de las tiras compradas al 50 % y al 100 % de un color.
