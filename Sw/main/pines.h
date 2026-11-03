#pragma once

/* Asignación de pines. Fuente: Hw/esquematico_v1/README.md
 * No usar: GPIO19/20 (USB nativo), GPIO26-32 (flash), GPIO35-37 (PSRAM octal). */

/* Pantalla TFT, bus paralelo de 8 bits */
#define PIN_LCD_RS   1
#define PIN_LCD_WR   2
#define PIN_LCD_D0   4
#define PIN_LCD_D1   5
#define PIN_LCD_D2   6
#define PIN_LCD_D3   7
#define PIN_LCD_D4   15
#define PIN_LCD_D5   16
#define PIN_LCD_D6   17
#define PIN_LCD_D7   18
#define PIN_LCD_RST  41
#define PIN_LCD_CS   42

/* Teclado 4x4: filas salidas, columnas entradas con pull-up */
#define PIN_KEY_F1   11
#define PIN_KEY_F2   12
#define PIN_KEY_F3   13
#define PIN_KEY_F4   14
#define PIN_KEY_C1   8
#define PIN_KEY_C2   9
#define PIN_KEY_C3   38
#define PIN_KEY_C4   39

/* Entradas */
#define PIN_SW_EQUIPO   21  /* abierto = rojo */
#define PIN_SW_ARMADO   47  /* interruptor de llave */
#define PIN_BTN_ACCION  48  /* comparte línea con el LED RGB de la tarjeta */

/* LEDs */
#define PIN_LED_ROJO   3    /* pin de arranque */
#define PIN_LED_AZUL   46   /* pin de arranque, pull-down de 100k */

/* Audio I2S (MAX98357A) */
#define PIN_I2S_BCLK   40
#define PIN_I2S_LRC    45   /* pin de arranque */
#define PIN_I2S_DIN    0    /* pin de arranque (botón BOOT) */

/* Batería */
#define PIN_VBAT_ADC   10   /* divisor 1:2 */
