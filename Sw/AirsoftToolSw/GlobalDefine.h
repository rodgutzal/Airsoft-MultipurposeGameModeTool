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

/* ATENCION - asignacion de pines desactualizada.
 * Los pines de este archivo siguen el esquematico v0.7 (pantalla de 8 bits,
 * teclado y switches en GPIO directos, dos lineas de tira LED). El hardware
 * v0.8 en adelante usa pantalla de 16 bits, touch por SPI, un expansor I2C
 * MCP23017 para teclado/switches/boton y una sola linea de tira LED. La
 * correspondencia punto por punto esta en Sw/MapaPines.md. Hasta que se
 * migre, estos pines NO coinciden con la placa v0.8 ni con la opcion C. */

/* Pines que el firmware nunca debe configurar (la mascara la valida GpioDriver):
 * GPIO19/20 (USB nativo), GPIO26-32 (flash) y GPIO35-37 (PSRAM octal). */
#define C_GPIO_RESERVED_MASK  ((1ULL << 19) | (1ULL << 20) | (0x7FULL << 26) | (0x7ULL << 35))

/* ---- Reloj ---- */
#define C_CPU_CLOCK_TARGET_MHZ  240  /* MHz. Maximo del ESP32-S3, desde el PLL (cristal de 40 MHz) */

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

/* ---- Pantalla TFT, bus de 16 bits (hardware v0.8 y opcion C) ----
 * D8 a D15 son los GPIO que en las constantes v0.7 de arriba aparecen como
 * teclado, switches y boton (ver Sw/MapaPines.md). DisplayDriver usa solo
 * estas constantes; C_PIN_LCD_RST y C_PIN_LCD_CS no se usan (RST va a EN y CS a GND). */
#define C_PIN_LCD_D8      8
#define C_PIN_LCD_D9      9
#define C_PIN_LCD_D10     11
#define C_PIN_LCD_D11     12
#define C_PIN_LCD_D12     13
#define C_PIN_LCD_D13     14
#define C_PIN_LCD_D14     21
#define C_PIN_LCD_D15     47

/* ---- DisplayDriver: parametros de la pantalla ---- */
#define C_LCD_BUS_WIDTH         16        /* bits del bus i80: 8 o 16 */
#define C_LCD_H_RES             480       /* pixeles por linea (horizontal) */
#define C_LCD_V_RES             320       /* lineas (vertical) */
#define C_LCD_BYTES_PER_PIXEL   2         /* RGB565 */
#define C_LCD_BUFFER_LINES      20        /* lineas por transferencia: 480 x 20 x 2 = 19200 bytes */
#define C_LCD_PCLK_HZ           10000000  /* Hz. Reloj de escritura (WR) pedido; el panel lo limita a su maximo */
#define C_LCD_TRANSFER_TIMEOUT_MS  100    /* ms. Espera maxima a que termine una transferencia de color */
#define C_LCD_INIT_PARAMS_MAX   16        /* parametros maximos de un comando de inicio */
#define C_LCD_COLOR_BLACK       0x0000    /* RGB565 */
#define C_LCD_COLOR_RED         0xF800
#define C_LCD_COLOR_GREEN       0x07E0
#define C_LCD_COLOR_BLUE        0x001F
#define C_LCD_COLOR_WHITE       0xFFFF
#define C_LCD_CMD_CASET         0x2A      /* fijar columnas */
#define C_LCD_CMD_RASET         0x2B      /* fijar filas */
#define C_LCD_CMD_RAMWR         0x2C      /* escribir memoria de imagen */
#define C_LCD_CMD_MADCTL        0x36      /* orientacion y orden de color */
#define C_LCD_CMD_DISPON        0x29      /* encender pantalla */

/* OBSOLETO (v0.7): los GPIO de las constantes C_PIN_KEY_*, C_PIN_SW_*,
 * C_PIN_BTN_ACCION y C_PIN_TIRA_LED_2 de abajo son ahora el bus de la pantalla
 * (C_PIN_LCD_D8..D15) o el SPI del touch. NO usarlas en drivers nuevos: en v0.8
 * esas funciones estan en el MCP23017. Se borraran al migrar el pinout. */

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

/* ---- Tiras LED RGB WS2812B (datos via 74AHCT125) ---- */
#define C_PIN_TIRA_LED_1  3   /* pin de arranque, pull-down de 100k (R6) */
#define C_PIN_TIRA_LED_2  46  /* pin de arranque, pull-down de 100k (R9) */

/* ---- LED de estado (D5 verde, R21 de 330 ohm, activo en alto) ----
 * Lo maneja HeartbeatDriver. GPIO43 es U0TXD, por eso la consola va por el
 * USB-Serial-JTAG (sdkconfig.defaults) y no por UART0. */
#define C_PIN_LED_ESTADO  43

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
#define C_TIMER_PERIOD_MS       5        /* ms. Periodo de la interrupcion y del ciclo principal */
#define C_TIMER_RESOLUTION_HZ   1000000  /* 1 MHz: cada cuenta del timer es 1 us */
#define C_TIMER_ALARM_COUNT     ((C_TIMER_RESOLUTION_HZ / 1000) * C_TIMER_PERIOD_MS)  /* cuentas por periodo: 1000 cuentas/ms x 5 ms = 5000 */

/* ---- Heartbeat: ciclo completo de 1 s (0.5 s encendido, 0.5 s apagado) ---- */
#define C_HEARTBEAT_PERIOD_MS   1000  /* ms. Encendido + apagado del LED */
#define C_HEARTBEAT_HALF_TICKS  (C_HEARTBEAT_PERIOD_MS / 2 / C_TIMER_PERIOD_MS)  /* periodos de 5 ms entre cambios del LED: 1000 / 2 / 5 = 100 */

/* ---- Almacenamiento en flash (NVS) ---- */
#define C_FLASH_NAMESPACE        "airsoft"  /* espacio de nombres de NVS */
#define C_FLASH_KEY_MAX_LENGTH   15         /* largo maximo de una clave de NVS */

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
