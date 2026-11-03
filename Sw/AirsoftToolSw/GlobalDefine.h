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

#include <stdint.h>

/* No usar: GPIO19/20 (USB nativo), GPIO26-32 (flash), GPIO35-37 (PSRAM octal). */
#define C_GPIO_RESERVED_MASK  ((1ULL << 19) | (1ULL << 20) | (0x7FULL << 26) | (0x7ULL << 35))

/* ---- Reloj ---- */
#define C_CPU_CLOCK_TARGET_MHZ  240  /* maximo del ESP32-S3, desde el PLL (cristal de 40 MHz) */

/* ---- Pantalla TFT, bus paralelo de 8 bits ---- */
#define C_PIN_LCD_RS      1
#define C_PIN_LCD_WR      2
#define C_PIN_LCD_D0      4
#define C_PIN_LCD_D1      5
#define C_PIN_LCD_D2      6
#define C_PIN_LCD_D3      7
#define C_PIN_LCD_D4      15
#define C_PIN_LCD_D5      16
#define C_PIN_LCD_D6      17
#define C_PIN_LCD_D7      18
#define C_PIN_LCD_RST     41
#define C_PIN_LCD_CS      42

/* ---- Teclado 4x4: filas salidas, columnas entradas con pull-up externo ---- */
#define C_PIN_KEY_F1      11
#define C_PIN_KEY_F2      12
#define C_PIN_KEY_F3      13
#define C_PIN_KEY_F4      14
#define C_PIN_KEY_C1      8
#define C_PIN_KEY_C2      9
#define C_PIN_KEY_C3      38
#define C_PIN_KEY_C4      39

/* ---- Entradas ---- */
#define C_PIN_SW_EQUIPO   21  /* abierto = rojo */
#define C_PIN_SW_ARMADO   47  /* interruptor de llave */
#define C_PIN_BTN_ACCION  48  /* comparte linea con el LED RGB de la tarjeta */

/* ---- LEDs ---- */
#define C_PIN_LED_ROJO    3   /* pin de arranque */
#define C_PIN_LED_AZUL    46  /* pin de arranque, pull-down de 100k */

/* ---- Audio I2S (MAX98357A) ---- */
#define C_PIN_I2S_BCLK    40
#define C_PIN_I2S_LRC     45  /* pin de arranque */
#define C_PIN_I2S_DIN     0   /* pin de arranque (boton BOOT) */

/* ---- Bateria ---- */
#define C_PIN_VBAT_ADC    10  /* divisor 1:2 */

/* ---- Cuentas y tamanos ---- */
#define C_KEY_ROWS        4
#define C_KEY_COLS        4

/* ---- Equipos ---- */
#define C_TEAM_RED        0
#define C_TEAM_BLUE       1

/* ---- Booleanos ---- */
#define C_TRUE            1
#define C_FALSE           0

/* ---- Teclado ---- */
#define C_KEY_NONE        0xFF  /* ninguna tecla presionada */

/* ---- Timer periodico del ciclo principal (GPTimer) ---- */
#define C_TIMER_PERIOD_MS       5        /* periodo de la interrupcion */
#define C_TIMER_RESOLUTION_HZ   1000000  /* 1 MHz: cada cuenta del timer es 1 us */
#define C_TIMER_ALARM_COUNT     ((C_TIMER_RESOLUTION_HZ / 1000) * C_TIMER_PERIOD_MS)

/* ---- Conversiones y limites ---- */
#define C_HZ_PER_MHZ      1000000UL
#define C_BYTES_PER_KB    1024
#define C_BYTES_PER_MB    (1024 * 1024)
#define C_GPIO_PIN_COUNT_MAX  64  /* tamano de la mascara de pines (uint64_t) */

/* ---- Uniones para acceder como byte/palabra o bit a bit ----
 * Bits.Bit0 es el bit menos significativo (el ESP32-S3 es little-endian).
 * Ejemplos: flags.Byte = 0; flags.Bits.Bit3 = 1; value.Word = 0x1234;
 */
typedef union
{
  uint8_t Byte;
  struct
  {
    uint8_t Bit0 : 1;
    uint8_t Bit1 : 1;
    uint8_t Bit2 : 1;
    uint8_t Bit3 : 1;
    uint8_t Bit4 : 1;
    uint8_t Bit5 : 1;
    uint8_t Bit6 : 1;
    uint8_t Bit7 : 1;
  } Bits;
} Union8_t;

typedef union
{
  uint16_t Word;
  uint8_t  Bytes[2];  /* Bytes[0] = parte baja, Bytes[1] = parte alta */
  struct
  {
    uint16_t Bit0 : 1;
    uint16_t Bit1 : 1;
    uint16_t Bit2 : 1;
    uint16_t Bit3 : 1;
    uint16_t Bit4 : 1;
    uint16_t Bit5 : 1;
    uint16_t Bit6 : 1;
    uint16_t Bit7 : 1;
    uint16_t Bit8 : 1;
    uint16_t Bit9 : 1;
    uint16_t Bit10 : 1;
    uint16_t Bit11 : 1;
    uint16_t Bit12 : 1;
    uint16_t Bit13 : 1;
    uint16_t Bit14 : 1;
    uint16_t Bit15 : 1;
  } Bits;
} Union16_t;

typedef union
{
  uint32_t Dword;
  uint16_t Words[2];  /* Words[0] = parte baja, Words[1] = parte alta */
  uint8_t  Bytes[4];  /* Bytes[0] = byte menos significativo */
  struct
  {
    uint32_t Bit0 : 1;
    uint32_t Bit1 : 1;
    uint32_t Bit2 : 1;
    uint32_t Bit3 : 1;
    uint32_t Bit4 : 1;
    uint32_t Bit5 : 1;
    uint32_t Bit6 : 1;
    uint32_t Bit7 : 1;
    uint32_t Bit8 : 1;
    uint32_t Bit9 : 1;
    uint32_t Bit10 : 1;
    uint32_t Bit11 : 1;
    uint32_t Bit12 : 1;
    uint32_t Bit13 : 1;
    uint32_t Bit14 : 1;
    uint32_t Bit15 : 1;
    uint32_t Bit16 : 1;
    uint32_t Bit17 : 1;
    uint32_t Bit18 : 1;
    uint32_t Bit19 : 1;
    uint32_t Bit20 : 1;
    uint32_t Bit21 : 1;
    uint32_t Bit22 : 1;
    uint32_t Bit23 : 1;
    uint32_t Bit24 : 1;
    uint32_t Bit25 : 1;
    uint32_t Bit26 : 1;
    uint32_t Bit27 : 1;
    uint32_t Bit28 : 1;
    uint32_t Bit29 : 1;
    uint32_t Bit30 : 1;
    uint32_t Bit31 : 1;
  } Bits;
} Union32_t;

_Static_assert(sizeof(Union8_t)  == 1, "Union8_t debe medir 1 byte");
_Static_assert(sizeof(Union16_t) == 2, "Union16_t debe medir 2 bytes");
_Static_assert(sizeof(Union32_t) == 4, "Union32_t debe medir 4 bytes");

#endif /* GLOBAL_DEFINE_H */
