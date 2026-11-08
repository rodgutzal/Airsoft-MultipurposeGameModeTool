# Esquemático v0.9, opción C (discreta para PCB)

La opción C quita los tres módulos comprados de v0.8 y los cambia por sus componentes para armar todo en una PCB propia. El ESP32-S3-DevKitC-1 pasa a ser el módulo ESP32-S3-WROOM-1-N16R8 soldado directo en la placa. El módulo LUORNG V8 se reemplaza por cargador, protección de celda, reparto de carga USB/batería, elevador a 5.1 V y regulador de 3.3 V. La tarjeta MAX98357A pasa a ser el circuito integrado suelto con sus pasivos. Se agrega un USB-C al USB nativo del ESP32-S3 para grabar, depurar y cargar, más un header UART0 de respaldo.

Pantalla, expansor MCP23017, teclado, switches, push button, tiras WS2812B y LED de estado quedan igual que en v0.8 (ver `../README.md`). Las opciones A y B siguen en v0.8 sin cambios.

Archivos: `airsoft_tool_opcion_C.kicad_sch` (KiCad 7, hoja A2), vista rápida en `airsoft_tool_opcion_C.pdf`, lista de materiales en `../lista_materiales_v0.9_opcionC.xlsx`. Se genera con `python3 gen_sch_c.py airsoft_tool_opcion_C.kicad_sch bom.csv` (necesita la librería de símbolos de KiCad en `/usr/share/kicad/symbols`). Igual que en v0.8 las conexiones son por etiqueta de red y el script avisa si alguna red tiene una sola etiqueta.

## Asignación de pines del ESP32-S3-WROOM-1-N16R8

Es la misma de v0.8. Cambian tres cosas: GPIO19 y GPIO20 ahora van al USB-C, GPIO44 (U0RXD) pasa al header J2 porque ya no hay puente USB-UART que lo maneje, y GPIO43 sigue con el LED de estado y además sale como TX0 al header.

| GPIO | Pin del módulo | Señal |
| --- | --- | --- |
| 1 | 39 | LCD_RS |
| 2 | 38 | LCD_WR |
| 4, 5, 6, 7, 15, 16, 17, 18 | 4, 5, 6, 7, 8, 9, 10, 11 | LCD_D0 a LCD_D7 |
| 8, 9, 11, 12, 13, 14, 21, 47 | 12, 17, 19, 20, 21, 22, 23, 24 | LCD_D8 a LCD_D15 |
| 38 | 31 | TOUCH_CLK |
| 46 | 16 | TOUCH_MOSI, pull-down R9 |
| 48 | 25 | TOUCH_MISO |
| 41 | 34 | TOUCH_CS |
| 39 | 32 | I2C_SDA, pull-up R10 |
| 42 | 35 | I2C_SCL, pull-up R11 |
| 3 | 15 | LED_TIRA, pull-down R6 |
| 40 | 33 | I2S_BCLK |
| 45 | 26 | I2S_LRC, pull-down R24 |
| 0 | 27 | I2S_DIN, pull-up R23 y botón BOOT (SW6) |
| 10 | 18 | VBAT_ADC |
| 43 | 37 | LED_ESTADO y TX0 de J2 (por R29) |
| 44 | 36 | RX0 de J2, pull-up R37 |
| 19 | 13 | USB D- (por R28) |
| 20 | 14 | USB D+ (por R27) |
| EN | 3 | ESP_EN: R22, C10, botón RESET (SW5), RST de la pantalla y pin 4 de J2 |

GPIO35, 36 y 37 (pines 28 a 30 del módulo) quedan sin conectar. En la N16R8 la PSRAM es octal y esos tres pines van a ella, según la nota b de la tabla 3-1 de la hoja de datos del WROOM-1 (v1.8, en `Hw/docs`). La asignación de v0.8 no los usaba, así que no hubo que mover nada.

No queda ningún GPIO libre. El expansor U6 recibe dos funciones nuevas en GPB5 (SD del amplificador) y GPB6 (USB presente); GPB7 queda libre.

## Microcontrolador

U1 es el ESP32-S3-WROOM-1-N16R8 (flash de 16 MB quad y PSRAM de 8 MB octal, las dos a 3.3 V). Hay que comprar exactamente N16R8. La variante N16R16V trabaja la PSRAM y los GPIO47/48 a 1.8 V, y GPIO47 lleva LCD_D15.

Alimentación: pin 2 (3V3) desde el regulador U9, con C11 de 22 µF y C12 de 100 nF junto al pin, como en el circuito de referencia de la sección 9 de la hoja de datos del módulo. GND en los pines 1, 40 y el pad 41. La antena necesita la zona sin cobre que marca la guía de diseño de Espressif, con el módulo en el borde de la placa.

EN lleva R22 de 10k a 3.3 V y C10 de 1 µF a GND, los valores que recomienda la guía de diseño de hardware del ESP32-S3 en la parte de temporización de encendido de CHIP_PU. SW5 lleva EN a GND (RESET). La pantalla sigue reiniciándose con el micro porque su RST va a ESP_EN.

Pines de arranque, según la tabla 4-1 y la sección 4 de la hoja de datos del WROOM-1:

| Pin | Qué decide | Lo que tiene en la placa |
| --- | --- | --- |
| GPIO0 | Arranque normal (1) o descarga (0) | R23 de 10k a 3.3 V y SW6 (BOOT) a GND. Durante el uso es I2S_DIN, una salida hacia la entrada DIN del MAX98357A. |
| GPIO46 | Con GPIO0 en 0 debe estar en 0 para entrar a descarga | R9 de 100k a GND (TOUCH_MOSI). |
| GPIO45 | Voltaje de VDD_SPI: 0 = 3.3 V | R24 de 10k a GND, además del pull-down interno. Así una entrada externa no puede subirlo y dejar la flash a 1.8 V. Durante el uso es I2S_LRC. |
| GPIO3 | Origen del JTAG, solo si se programa el eFuse STRAP_JTAG_SEL | R6 de 100k a GND (LED_TIRA). No tiene pull interno. |

## USB-C, grabación y depuración

J1 es un USB-C de 16 pines (solo USB 2.0). CC1 y CC2 llevan R25 y R26 de 5.1k a GND para que cualquier cargador o puerto USB-C entregue 5 V. D+ y D- van unidos en las dos caras del conector, pasan por U7 (USBLC6-2SC6, protección ESD junto a J1) y por R27 y R28 de 22 Ω junto al módulo, que es el valor inicial que da la guía de diseño en la sección 1.3.13. C23 de 10 µF va en VBUS.

Se graba y se depura por el USB nativo. El ESP32-S3 trae el controlador USB-Serial-JTAG, así que `idf.py flash`, el monitor serie y OpenOCD con GDB funcionan con un cable USB-C, sin adaptador ni JTAG externo. esptool pone el chip en modo de descarga por el mismo USB; los botones BOOT y RESET quedan para cuando el firmware deja el USB inservible (por ejemplo si reconfigura GPIO19/20): se mantiene BOOT, se pulsa RESET y se suelta BOOT. El firmware ya manda la consola a USB-Serial-JTAG desde el PR #16.

No se puso header JTAG externo. Los pines de JTAG por hardware son GPIO39 a 42 y los cuatro están ocupados (I2C, I2S_BCLK y TOUCH_CS). La depuración JTAG va por USB.

J2 es un header de 1x6 a 2.54 mm de respaldo, para grabar por UART0 con un adaptador USB-serial de 3.3 V. Pines: 1 GND, 2 TX0, 3 RX0, 4 EN, 5 IO0, 6 3V3. TX0 sale de GPIO43 por R29 de 499 Ω (la guía pide esa resistencia en U0TXD). RX0 es GPIO44 con R37 de 10k a 3.3 V. Con EN e IO0 en el header, un adaptador con DTR y RTS puede usar el reinicio automático si se cablea como en el DevKit, o se usan los botones. El pin 6 sirve de referencia; no se debe alimentar la placa desde el adaptador con la batería puesta.

El LED de estado se queda en GPIO43. El LED con R21 toma 3.6 mA, muy poco para el pin, y no impide que TX0 transmita. El efecto es el mismo de v0.7: D5 parpadea con el log de la ROM al arrancar y durante una grabación por UART. Como la consola del firmware va por USB, en uso normal GPIO43 es solo el LED. Si algún día se quiere la consola por UART0, el LED se mueve a GPB7 de U6.

## Alimentación

Bloque completo, de la celda al riel:

Celdas. BT1 y BT2 son dos 18650 en paralelo en un portapilas para PCB. Su negativo es BAT_NEG.

Protección. U10 (DW01A) vigila la celda y corta con dos MOSFET dobles FS8205A (Q1 y Q2) en paralelo, puestos en el negativo. FS8205A tiene drenador común: S1 a BAT_NEG con G1 en OD (corte de descarga), S2 a GND con G2 en OC (corte de carga). R31 de 100 Ω y C14 de 100 nF filtran el VCC del DW01A y R32 de 1k va de CS a GND. Desde aquí GND del sistema es el negativo protegido (P-). El DW01A mide la sobrecorriente como caída en los MOSFET. Con un solo FS8205A (28 mΩ máximo por transistor a 4.5 V según LCSC, 56 mΩ los dos en serie) y el umbral típico de 150 mV del DW01A, cortaría alrededor de 2.7 A, justo en el pico que puede pedir el equipo. Con dos en paralelo sube a unos 5 A.

Carga. U2 (TP4056) carga a 1 A con R33 de 1.2k (tabla de RPROG de la hoja de datos) y termina en 4.2 V. Dos celdas de 3000 mAh tardan unas 6.5 a 7 horas. TEMP va a GND, que según la hoja de datos desactiva el sensado de temperatura. D6 rojo indica carga y D7 verde carga terminada, cada uno con 1k desde VBUS al pin de estado (CHRG pin 7, STDBY pin 6). El TP4056 disipa hasta 1.3 W con 5 V de entrada y la celda en 3.7 V; necesita cobre bajo el pad expuesto. Si se carga casi siempre desde una computadora, conviene R33 de 2k (580 mA), porque un puerto USB 2.0 solo garantiza 500 mA.

Reparto de carga. Con USB conectado el equipo se alimenta de VBUS a través de D8 (SS34) y la batería solo se carga. Q3 (AO3401A, MOSFET P) tiene el gate en VBUS: con USB queda abierto, sin USB R36 de 10k baja el gate y Q3 conecta la batería a VSYS con poca caída. D9 (SS34) va en paralelo con Q3 para que VSYS no caiga a la batería menos el diodo interno de Q3 en el instante en que se desconecta el USB. R38 de 47k y R39 de 100k mandan "USB presente" a GPB6 de U6 (3.4 V con 5 V en VBUS, bajo sin USB).

Encendido. SW4 corta VSYS hacia los reguladores. La carga sigue funcionando con SW4 apagado. Debe soportar 3 A, porque por ahí pasa toda la corriente; un interruptor deslizable pequeño no sirve.

5.1 V. U8 es un elevador síncrono TPS61022 (VIN de 0.5 a 5.5 V, límite de corriente de valle de 6.5 A mínimo, 3 A de salida a 5 V con entrada de 2.7 a 4.35 V según la tabla 8-1 de TI). Vout = 0.6 V × (1 + R15/R16) = 0.6 × (1 + 750k/100k) = 5.1 V. L1 de 1 µH (la hoja de datos admite de 0.33 a 2.9 µH para 5 V y su ejemplo usa 1 µH) con saturación de 8 A o más. C17 de 22 µF a la entrada y C18 a C20 de 22 µF a la salida, como el ejemplo de TI. EN a VSYS_SW. MODE a GND, que según la tabla 5-1 es PFM automático y ahorra batería con poca carga; si el PFM mete ruido audible en la bocina, MODE pasa a VSYS_SW (PWM forzado). De +5V comen las tiras, U5 y el amplificador. Nada de 3.3 V sale de aquí.

3.3 V. U9 (AP7361C-33E, 1 A, SOT-223) toma VSYS_SW, es decir la batería o VBUS, y da +3V3 para el módulo, la pantalla, U6 y el touch. C21 y C22 de 10 µF. Es más eficiente que v0.8, donde el 3.3 V salía del regulador del DevKit alimentado desde el elevador. Con la celda en 3.4 V la salida empieza a bajar de 3.3 V por la caída del regulador; el ESP32-S3 funciona desde 3.0 V. El firmware debe apagar el equipo con la batería en unos 3.3 V.

Medición. R13 y R14 (100k cada una) llevan la celda a GPIO10 a la mitad, igual que en v0.8, tomada directo de la celda y no después del interruptor, para leer la batería también mientras carga por USB.

Consumo estimado, sin medir: unos 250 mA en 3.3 V (WiFi y retroiluminación), que salen casi igual de la batería por ser un regulador lineal, más unos 30 mA de batería para el riel de 5 V en reposo. Con las tiras en un color al 50 % se suman unos 0.5 A. Total cercano a 0.8 A, unas 7.5 horas nominales con 6000 mAh, contra 6.8 h de v0.8. Pico: tiras topadas a 600 mA y amplificador a 0.8 A dan 1.45 A en 5 V, unos 2.5 A de batería con la celda en 3.3 V, más 0.5 A del 3.3 V. Queda dentro de los 3 A de U8 y del corte de unos 5 A de la protección.

## Audio

U4 es el MAX98357AETE+ (TQFN-16 de 3x3 mm) con la bocina de 4 Ω en J4. Pines según la hoja de datos de Analog Devices (rev 16): DIN 1, GAIN_SLOT 2, GND 3, 11 y 15, SD_MODE 4, VDD 7 y 8, OUTP 9, OUTN 10, LRCLK 14, BCLK 16, pad expuesto a GND.

VDD a +5V con C13 de 10 µF y C4 de 100 nF pegados al pin, como pide la hoja de datos, y C3 de 470 µF cerca como reserva para los picos. GAIN_SLOT a GND da 12 dB, la ganancia con la que la hoja de datos especifica 3.2 W en 4 Ω a 5 V con 10 % de THD. En v0.8 el módulo quedaba en 9 dB.

SD_MODE va a GPB5 de U6 a través de R30 de 634k (1 %). Con GPB5 en 3.3 V el amplificador mezcla (izquierdo + derecho)/2, que es el valor RLARGE de la tabla 6 para VDDIO de 3.3 V. Con GPB5 en bajo el amplificador se apaga, así no consume ni sopla cuando no hay sonido. Al arrancar U6 deja GPB5 como entrada y el pull-down interno del MAX98357A lo mantiene apagado hasta que el firmware lo encienda.

La salida es clase D sin filtro, como indica la hoja de datos. El cable a la bocina debe ser corto y trenzado.

## Lo que cambia contra v0.8

Salen: U1 ESP32-S3-DevKitC-1, M1 LUORNG V8 (o el TP4056 en módulo y el MT3608 de la opción B), módulo MAX98357A.

Entran: U1 WROOM-1, U2 TP4056, U4 MAX98357A suelto, U7 USBLC6-2SC6, U8 TPS61022, U9 AP7361C-33E, U10 DW01A, Q1 y Q2 FS8205A, Q3 AO3401A, D6 a D9, L1, J1 USB-C, J2 header UART, J4 conector de bocina, SW4 a SW6, R22 a R39 (sin R12) y C10 a C23. R15 y R16 cambian de valor contra la opción B.

Costo estimado de la opción C: unos 1,547 MXN sin margen, contra 1,791 de la opción A y 1,635 de la opción B. Incluye 80 MXN de PCB por pieza. Todos los precios de C son estimados.

## Sin verificar

Lo siguiente no lo pude confirmar con la hoja de datos del fabricante y hay que revisarlo antes de mandar a fabricar:

- DW01A: la página de Fortune Semiconductor no se dejó leer. El patillaje usado (1 OD, 2 CS, 3 OC, 4 TD, 5 VCC, 6 GND), el umbral de sobrecorriente de 150 mV y los valores de R31, C14 y R32 son los del circuito típico que circula en módulos TP4056, no de la hoja de datos.
- FS8205A: el patillaje TSSOP-8 (1 y 8 drenador, 2 y 3 S1, 4 G1, 5 G2, 6 y 7 S2) no está verificado. LCSC lista también un FS8205 en SOT-23-6 con otro patillaje; hay que comprar el TSSOP-8. La resistencia de 28 mΩ salió de la ficha de LCSC.
- AP7361C-33E: la página de Diodes no se dejó leer. El orden de pines del SOT-223 (1 entrada, 2 GND en la aleta, 3 salida) viene del símbolo de KiCad. En AP7361C la letra final cambia el orden de pines, así que hay que revisar la hoja de datos de la variante exacta. Tampoco verifiqué la caída a 1 A ni los capacitores mínimos.
- USBLC6-2SC6: patillaje tomado del símbolo de KiCad, no de la hoja de ST.
- TP4056: los nombres CHRG y STDBY de los pines 7 y 6 vienen de la versión en inglés del circuito típico; la hoja leída solo dice qué hace cada pin. La regulación térmica no la verifiqué.
- TPS61022: la corriente a exactamente 3.3 V de entrada no está en la hoja de datos (da 3 A para 2.7 a 4.35 V). No puse capacitor de adelanto en R15; TI lo pide solo con más de 40 µF efectivos de salida, y con tres de 22 µF en 0805 a 5 V la capacitancia efectiva queda por debajo.
- MAX98357A: el pull-down interno de SD_MODE y si las entradas DIN y LRCLK tienen resistencias internas que afecten a GPIO0 y GPIO45 al arrancar. Con R23 y R24 de 10k no debería importar.
- Corrientes de retroiluminación, WiFi y tiras: siguen siendo estimaciones.

## Pendientes

- Revisar los puntos de la sección anterior con las hojas de datos.
- Elegir huellas y hacer el ruteo. Para el TPS61022 seguir el ejemplo de layout de TI (lazo de potencia corto entre SW, VOUT y GND). Respetar la zona de la antena del WROOM-1.
- Decidir si el ensamble SMD lo hace JLCPCB o PCBWay: TPS61022 (VQFN de 2x2 mm) y MAX98357A (TQFN de 3x3 mm) no se sueldan con cautín.
- Firmware: control de GPB5 (SD del amplificador) y lectura de GPB6 (USB presente) en U6; corte por batería baja.
- Medir consumo real y autonomía en el prototipo.
