/**
 * Archivo:           GlobalDefine.h
 * Descripcion:       Definiciones globales: pines, cuentas, constantes y
 *                    tiempos. Pines segun Hw/esquematico_v1/README.md.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#ifndef GLOBAL_DEFINE_H
#define GLOBAL_DEFINE_H

/* No usar: GPIO19/20 (USB nativo), GPIO26-32 (flash), GPIO35-37 (PSRAM octal). */
#define GPIO_RESERVED_MASK  ((1ULL << 19) | (1ULL << 20) | (0x7FULL << 26) | (0x7ULL << 35))

/* ---- Pantalla TFT, bus paralelo de 8 bits ---- */
#define PIN_LCD_RS      1
#define PIN_LCD_WR      2
#define PIN_LCD_D0      4
#define PIN_LCD_D1      5
#define PIN_LCD_D2      6
#define PIN_LCD_D3      7
#define PIN_LCD_D4      15
#define PIN_LCD_D5      16
#define PIN_LCD_D6      17
#define PIN_LCD_D7      18
#define PIN_LCD_RST     41
#define PIN_LCD_CS      42

/* ---- Teclado 4x4: filas salidas, columnas entradas con pull-up ---- */
#define PIN_KEY_F1      11
#define PIN_KEY_F2      12
#define PIN_KEY_F3      13
#define PIN_KEY_F4      14
#define PIN_KEY_C1      8
#define PIN_KEY_C2      9
#define PIN_KEY_C3      38
#define PIN_KEY_C4      39

/* ---- Entradas ---- */
#define PIN_SW_EQUIPO   21  /* abierto = rojo */
#define PIN_SW_ARMADO   47  /* interruptor de llave */
#define PIN_BTN_ACCION  48  /* comparte linea con el LED RGB de la tarjeta */

/* ---- LEDs ---- */
#define PIN_LED_ROJO    3   /* pin de arranque */
#define PIN_LED_AZUL    46  /* pin de arranque, pull-down de 100k */

/* ---- Audio I2S (MAX98357A) ---- */
#define PIN_I2S_BCLK    40
#define PIN_I2S_LRC     45  /* pin de arranque */
#define PIN_I2S_DIN     0   /* pin de arranque (boton BOOT) */

/* ---- Bateria ---- */
#define PIN_VBAT_ADC    10  /* divisor 1:2 */

/* ---- Cuentas y tamanos ---- */
#define KEY_ROWS        4
#define KEY_COLS        4

/* ---- Equipos ---- */
#define TEAM_RED        0
#define TEAM_BLUE       1

#endif /* GLOBAL_DEFINE_H */
