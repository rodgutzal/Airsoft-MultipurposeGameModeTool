# Mapa de pines: hardware contra firmware

Este documento cruza la asignación de pines del hardware con las constantes `C_PIN_*` de [`AirsoftToolSw/GlobalDefine.h`](AirsoftToolSw/GlobalDefine.h). Sirve para saber qué pin hace qué, y para ver dónde el firmware todavía no sigue al hardware.

Fuentes del hardware (si difieren de este documento, mandan ellas):
- [`../Hw/esquematico_v1/README.md`](../Hw/esquematico_v1/README.md), esquemático v0.8 (opciones A y B, con DevKit).
- [`../Hw/esquematico_v1/opcion_c/README.md`](../Hw/esquematico_v1/opcion_c/README.md), v0.9 opción C (PCB propia, mismo pinout que v0.8).

Última comparación: 2026-11-12, contra `GlobalDefine.h` de la branch `b#13_DocumentacionProyecto`.

## Estado

**El firmware sigue el pinout de v0.7 y la placa es v0.8 o posterior.** En v0.8 la pantalla pasó a 16 bits con touch por SPI, y el teclado, los switches y el botón se movieron a un expansor I2C MCP23017. El firmware todavía no tiene ese cambio: está pendiente y figura en los pendientes de `Hw/esquematico_v1/README.md`.

Consecuencia práctica: los nombres `C_PIN_KEY_*`, `C_PIN_SW_*`, `C_PIN_BTN_ACCION` y `C_PIN_TIRA_LED_2` no corresponden a ningún GPIO real de la placa v0.8 u opción C (hoy son bus de pantalla y SPI del touch), así que `InitSimpleGpioPorts` ya no los configura (solo deja `C_PIN_TIRA_LED_1` en bajo). Las constantes siguen en `GlobalDefine.h` hasta migrar al MCP23017. No hay que escribir drivers nuevos sobre esos nombres.

## Pines que coinciden

| Función | GPIO | Constante | Notas |
| --- | --- | --- | --- |
| `LCD_RS` | 1 | `C_PIN_LCD_RS` | Además lee el touch en v0.7; en v0.8 el touch va por SPI. |
| `LCD_WR` | 2 | `C_PIN_LCD_WR` | |
| `LCD_D0` a `LCD_D7` | 4, 5, 6, 7, 15, 16, 17, 18 | `C_PIN_LCD_D0` a `C_PIN_LCD_D7` | |
| `LED_TIRA` (tira 1) | 3 | `C_PIN_TIRA_LED_1` | Pin de arranque (`STRAP_JTAG_SEL`), pull-down R6. En v0.8 las dos tiras van encadenadas en esta sola línea. |
| `I2S_BCLK` | 40 | `C_PIN_I2S_BCLK` | |
| `I2S_LRC` | 45 | `C_PIN_I2S_LRC` | Pin de arranque (voltaje de la flash). No poner pull-up. |
| `I2S_DIN` | 0 | `C_PIN_I2S_DIN` | Pin de arranque (botón BOOT). |
| `VBAT_ADC` | 10 | `C_PIN_VBAT_ADC` | ADC1, divisor 1:2. |
| `LED_ESTADO` | 43 | `C_PIN_LED_ESTADO` | U0TXD. Lo maneja `HeartbeatDriver`; por eso la consola va por USB. |

## Pines que no coinciden

| Constante del firmware | GPIO en firmware | Qué es ese GPIO en el hardware v0.8 | Dónde vive ahora la función |
| --- | --- | --- | --- |
| `C_PIN_LCD_RST` | 41 | `TOUCH_CS` | El RST de la pantalla va a `EN` del micro. No hay GPIO. |
| `C_PIN_LCD_CS` | 42 | `I2C_SCL` | El CS de la pantalla está a GND. No hay GPIO. |
| `C_PIN_KEY_F1` a `C_PIN_KEY_F4` | 11, 12, 13, 14 | `LCD_D10` a `LCD_D13` | Expansor U6, `GPA0` a `GPA3`. |
| `C_PIN_KEY_C1` | 8 | `LCD_D8` | U6, `GPA4`. |
| `C_PIN_KEY_C2` | 9 | `LCD_D9` | U6, `GPA5`. |
| `C_PIN_KEY_C3` | 38 | `TOUCH_CLK` | U6, `GPA6`. |
| `C_PIN_KEY_C4` | 39 | `I2C_SDA` | U6, `GPA7`. |
| `C_PIN_SW_EQUIPO` | 21 | `LCD_D14` | U6, `GPB0`. |
| `C_PIN_SW_ARMADO` | 47 | `LCD_D15` | U6, `GPB1`. |
| `C_PIN_BTN_ACCION` | 48 | `TOUCH_MISO` | U6, `GPB2`. |
| `C_PIN_TIRA_LED_2` | 46 | `TOUCH_MOSI` | Ya no hay segunda línea: las dos tiras van encadenadas en `LED_TIRA` (GPIO3). |

## Funciones del hardware que el firmware aún no nombra

| Función | Dónde está | Notas |
| --- | --- | --- |
| `LCD_D8` a `LCD_D15` | GPIO 8, 9, 11, 12, 13, 14, 21, 47 | Bus de 16 bits de la pantalla. Ya tienen constante `C_PIN_LCD_D8` a `C_PIN_LCD_D15` (las usa `DisplayDriver`), pero los GPIO siguen repetidos en `C_PIN_KEY_*` y `C_PIN_SW_*` de la tabla anterior hasta migrar el teclado al MCP23017. |
| `TOUCH_CLK`, `TOUCH_MOSI`, `TOUCH_MISO`, `TOUCH_CS` | GPIO 38, 46, 48, 41 | SPI del touch resistivo XPT2046. `TOUCH_MOSI` (GPIO46) es pin de arranque con pull-down R9. |
| `I2C_SDA`, `I2C_SCL` | GPIO 39, 42 | Bus del expansor U6 (MCP23017, dirección 0x20), pull-ups R10 y R11. |
| `TOUCH_PEN` | U6 `GPB3` | Bajo cuando se toca la pantalla. |
| `LCD_BL` | U6 `GPB4` | Alto enciende la retroiluminación. Arranca apagada porque U6 deja sus líneas como entradas. |
| SD del amplificador, USB presente | U6 `GPB5`, `GPB6` | Solo en la opción C. `GPB7` queda libre. |
| USB nativo | GPIO 19 (D-), 20 (D+) | Opción C: van al USB-C. El firmware no debe configurarlos (`C_GPIO_RESERVED_MASK`). |
| `RX0` de J2 | GPIO 44 | Opción C: header UART de respaldo. |

## Pines que el firmware nunca debe configurar

`C_GPIO_RESERVED_MASK` (en `GlobalDefine.h`) lo hace cumplir en `GpioDriver`:
- GPIO19 y 20: USB nativo.
- GPIO26 a 32: flash.
- GPIO35 a 37: PSRAM octal de la N16R8.

## Pines de arranque

Estos pines se leen al encender y deciden el modo de arranque. Cambiar lo que tienen conectado puede dejar la placa sin poder grabarse:

| GPIO | Qué decide | Estado en el hardware |
| --- | --- | --- |
| 0 | Arranque normal (1) o modo de descarga (0). | Es `I2S_DIN` (salida del micro) y el botón BOOT. |
| 3 | Fuente del JTAG, solo si se programa el eFuse `STRAP_JTAG_SEL`. | `LED_TIRA`, pull-down R6. |
| 45 | Voltaje de la flash (alto = 1.8 V). La N16R8 trabaja a 3.3 V. | `I2S_LRC`. Sin pull-up. |
| 46 | Con GPIO0 en 0 debe estar en 0 para entrar a modo de descarga. | `TOUCH_MOSI`, pull-down R9. |

## Cómo mantener este documento

Cuando cambie el pinout del hardware o se agregue un `C_PIN_*`:
1. Actualizar `GlobalDefine.h` y el comentario de aviso de su inicio.
2. Actualizar las tres tablas de este documento.
3. Si cambia la sección de pines del README de `Hw`, copiar el cambio aquí en el mismo PR.
