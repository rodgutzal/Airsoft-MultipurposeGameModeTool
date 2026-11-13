/**
 * Archivo:           DisplayDriver.c
 * Descripcion:       Driver de la pantalla TFT sobre el bus paralelo i80 de
 *                    esp_lcd (16 bits, ver C_LCD_BUS_WIDTH). Crea el bus y la
 *                    interfaz del panel, ejecuta la secuencia de inicio del
 *                    controlador elegido en Kconfig y ofrece relleno de color
 *                    y dibujo de mapas de bits RGB565. El DMA del bus lo maneja
 *                    esp_lcd. Las transferencias son bloqueantes: esperan a que
 *                    termine el DMA, asi que no se llaman desde el ciclo de 5 ms.
 *                    SIN VALIDAR EN HARDWARE.
 * Fecha de creacion: 2026-11-12
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "esp_attr.h"
#include "esp_heap_caps.h"
#include "esp_lcd_io_i80.h"
#include "esp_lcd_panel_io.h"
#include "esp_memory_utils.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include "DisplayDriver.h"
#include "PanelIli9486Driver.h"
#include "PanelSt7796Driver.h"
#include "Ram.h"

static const char *TAG = "DisplayDriver";

/* Estado privado del driver. El fin de transferencia lo da la ISR del DMA por
 * medio del semaforo; el mutex deja pasar una sola tarea a la vez por las
 * funciones publicas de dibujo. El semaforo y el mutex se crean una sola vez y
 * no se borran, asi la ISR nunca ve un handle invalido. */
static esp_lcd_i80_bus_handle_t sI80Bus = NULL;          /* bus i80; NULL si no esta creado */
static esp_lcd_panel_io_handle_t sPanelIo = NULL;        /* interfaz del panel; NULL si no esta creada */
static SemaphoreHandle_t sTransferDoneSemaphore = NULL;  /* la ISR lo da al terminar una transferencia de color */
static SemaphoreHandle_t sDisplayMutex = NULL;           /* exclusion mutua de DisplayFillColor y DisplayDrawBitmap */
static uint16_t *sLineBuffer = NULL;                     /* buffer DMA de C_LCD_BUFFER_LINES lineas */
static const PanelDescriptor_t *sPanel = NULL;           /* controlador elegido en Kconfig */
static bool sIsDisplayReady = false;                     /* true solo si DisplayInit termino bien */
static bool sTransferPending = false;                    /* true si una transferencia expiro y el DMA puede seguir leyendo el buffer */

/**
 * Nombre:      DisplayColorTransferDoneIsr
 * Descripcion: Callback de esp_lcd que se ejecuta cuando el DMA termino de
 *              enviar un bloque de color. Libera el semaforo que espera
 *              DisplayWriteWindow. No bloquea. esp_lcd registra esta
 *              interrupcion sin la bandera IRAM-safe, asi que mientras se
 *              escribe la flash (por ejemplo un commit de NVS) queda diferida
 *              hasta que vuelve la cache; no hay fallo, solo un retraso menor
 *              que C_LCD_TRANSFER_TIMEOUT_MS en condiciones normales.
 * Entradas:    panelIo   - interfaz del panel que termino (no se usa).
 *              eventData - datos del evento (no se usan).
 *              userCtx   - dato del usuario (no se usa).
 * Salidas:     true si hay que ceder el procesador a una tarea de mayor
 *              prioridad al salir de la interrupcion, false en otro caso.
 */
static bool IRAM_ATTR DisplayColorTransferDoneIsr(esp_lcd_panel_io_handle_t panelIo,
                                                  esp_lcd_panel_io_event_data_t *eventData,
                                                  void *userCtx)
{
  BaseType_t higherPriorityTaskWoken = pdFALSE;

  xSemaphoreGiveFromISR(sTransferDoneSemaphore, &higherPriorityTaskWoken);

  return (higherPriorityTaskWoken == pdTRUE);
}

/**
 * Nombre:      DisplaySelectPanel
 * Descripcion: Elige el descriptor del controlador segun la opcion
 *              AIRSOFT_LCD_CONTROLLER de Kconfig.
 * Entradas:    Ninguna.
 * Salidas:     Descriptor del controlador elegido.
 */
static const PanelDescriptor_t *DisplaySelectPanel(void)
{
#if defined(CONFIG_AIRSOFT_LCD_CONTROLLER_ST7796U)
  return PanelSt7796GetDescriptor();
#else
  return PanelIli9486GetDescriptor();
#endif
}

/**
 * Nombre:      DisplaySendCommand
 * Descripcion: Envia un comando con sus parametros al controlador.
 * Entradas:    command    - codigo del comando.
 *              params     - parametros, o NULL si no hay.
 *              paramCount - cuantos parametros se envian.
 * Salidas:     ESP_OK si se envio; el error de esp_lcd en otro caso.
 */
static esp_err_t DisplaySendCommand(uint8_t command, const uint8_t *params, size_t paramCount)
{
  return esp_lcd_panel_io_tx_param(sPanelIo, command, params, paramCount);
}

/**
 * Nombre:      DisplayWaitPendingTransfer
 * Descripcion: Si una transferencia anterior expiro, espera a que el DMA la
 *              termine. Debe llamarse con el mutex tomado y antes de tocar el
 *              bus o el buffer de lineas.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si no hay transferencia pendiente o ya termino;
 *              ESP_ERR_TIMEOUT si el DMA sigue sin terminar.
 */
static esp_err_t DisplayWaitPendingTransfer(void)
{
  if(sTransferPending == true)
  {
    if(xSemaphoreTake(sTransferDoneSemaphore, pdMS_TO_TICKS(C_LCD_TRANSFER_TIMEOUT_MS)) != pdTRUE)
    {
      return ESP_ERR_TIMEOUT;
    }
    sTransferPending = false;
  }

  return ESP_OK;
}

/**
 * Nombre:      DisplayReleaseResources
 * Descripcion: Libera el buffer DMA, la interfaz del panel y el bus i80 que
 *              existan y deja sus variables en NULL, para que DisplayInit se
 *              pueda reintentar despues de un error. No borra el semaforo ni el
 *              mutex (se crean una sola vez).
 * Entradas:    Ninguna.
 * Salidas:     Ninguna.
 */
static void DisplayReleaseResources(void)
{
  sIsDisplayReady = false;
  sTransferPending = false;
  sPanel = NULL;

  if(sLineBuffer != NULL)
  {
    heap_caps_free(sLineBuffer);
    sLineBuffer = NULL;
  }
  if(sPanelIo != NULL)
  {
    esp_lcd_panel_io_del(sPanelIo);
    sPanelIo = NULL;
  }
  if(sI80Bus != NULL)
  {
    esp_lcd_del_i80_bus(sI80Bus);
    sI80Bus = NULL;
  }
}

/**
 * Nombre:      DisplayWriteWindow
 * Descripcion: Fija la ventana de memoria (columnas y filas inclusivas) y envia
 *              los pixeles. Espera a que termine el DMA, asi el buffer se puede
 *              reutilizar al volver. Si expira, deja sTransferPending en true.
 *              Debe llamarse con el mutex tomado y despues de
 *              DisplayWaitPendingTransfer.
 * Entradas:    xStart, yStart - esquina superior izquierda.
 *              xEnd, yEnd     - esquina inferior derecha (inclusive).
 *              pixels         - pixeles RGB565, memoria apta para DMA.
 * Salidas:     ESP_OK si se dibujo; ESP_ERR_TIMEOUT si el DMA no termino a
 *              tiempo; otro error de esp_lcd si falla el envio.
 */
static esp_err_t DisplayWriteWindow(int xStart, int yStart, int xEnd, int yEnd, const uint16_t *pixels)
{
  uint8_t columns[4] = { (uint8_t)(xStart >> 8), (uint8_t)xStart, (uint8_t)(xEnd >> 8), (uint8_t)xEnd };
  uint8_t rows[4]    = { (uint8_t)(yStart >> 8), (uint8_t)yStart, (uint8_t)(yEnd >> 8), (uint8_t)yEnd };
  size_t byteCount = (size_t)(xEnd - xStart + 1) * (size_t)(yEnd - yStart + 1) * C_LCD_BYTES_PER_PIXEL;

  esp_err_t err = DisplaySendCommand(C_LCD_CMD_CASET, columns, sizeof(columns));
  if(err == ESP_OK)
  {
    err = DisplaySendCommand(C_LCD_CMD_RASET, rows, sizeof(rows));
  }
  if(err == ESP_OK)
  {
    err = esp_lcd_panel_io_tx_color(sPanelIo, C_LCD_CMD_RAMWR, pixels, byteCount);
  }
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "Envio de color fallo (%s)", esp_err_to_name(err));
    return err;
  }

  if(xSemaphoreTake(sTransferDoneSemaphore, pdMS_TO_TICKS(C_LCD_TRANSFER_TIMEOUT_MS)) != pdTRUE)
  {
    ESP_LOGE(TAG, "La transferencia de color no termino en %d ms", C_LCD_TRANSFER_TIMEOUT_MS);
    sTransferPending = true;
    return ESP_ERR_TIMEOUT;
  }

  return ESP_OK;
}

/**
 * Nombre:      DisplayStart
 * Descripcion: Crea el bus i80, la interfaz del panel y el buffer DMA, ejecuta
 *              la secuencia de inicio y enciende la pantalla. No libera nada si
 *              falla: lo hace DisplayInit con DisplayReleaseResources.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si la pantalla quedo encendida.
 *              ESP_ERR_NO_MEM si falta memoria DMA para el buffer.
 *              Otro codigo de esp_err_t si esp_lcd falla.
 */
static esp_err_t DisplayStart(void)
{
  esp_lcd_i80_bus_config_t busConfig =
  {
    .dc_gpio_num        = C_PIN_LCD_RS,
    .wr_gpio_num        = C_PIN_LCD_WR,
    .clk_src            = LCD_CLK_SRC_DEFAULT,
    .data_gpio_nums     =
    {
      C_PIN_LCD_D0, C_PIN_LCD_D1, C_PIN_LCD_D2,  C_PIN_LCD_D3,
      C_PIN_LCD_D4, C_PIN_LCD_D5, C_PIN_LCD_D6,  C_PIN_LCD_D7,
      C_PIN_LCD_D8, C_PIN_LCD_D9, C_PIN_LCD_D10, C_PIN_LCD_D11,
      C_PIN_LCD_D12, C_PIN_LCD_D13, C_PIN_LCD_D14, C_PIN_LCD_D15,
    },
    .bus_width          = C_LCD_BUS_WIDTH,
    .max_transfer_bytes = C_LCD_H_RES * C_LCD_BUFFER_LINES * C_LCD_BYTES_PER_PIXEL,
    .dma_burst_size     = 0,
  };
  esp_err_t err = esp_lcd_new_i80_bus(&busConfig, &sI80Bus);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "esp_lcd_new_i80_bus fallo (%s)", esp_err_to_name(err));
    return err;
  }

  uint32_t pclkHz = (C_LCD_PCLK_HZ < sPanel->maxPclkHz) ? C_LCD_PCLK_HZ : sPanel->maxPclkHz;
  esp_lcd_panel_io_i80_config_t ioConfig =
  {
    .cs_gpio_num       = C_LCD_CS_NOT_USED,  /* CS de la pantalla esta a GND */
    .pclk_hz           = pclkHz,
    .trans_queue_depth = 1,
    .on_color_trans_done = DisplayColorTransferDoneIsr,
    .user_ctx          = NULL,
    .lcd_cmd_bits      = C_LCD_CMD_BITS,
    .lcd_param_bits    = C_LCD_PARAM_BITS,
    .dc_levels         =
    {
      .dc_idle_level  = 0,
      .dc_cmd_level   = 0,
      .dc_dummy_level = 0,
      .dc_data_level  = 1,
    },
  };
  err = esp_lcd_new_panel_io_i80(sI80Bus, &ioConfig, &sPanelIo);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "esp_lcd_new_panel_io_i80 fallo (%s)", esp_err_to_name(err));
    return err;
  }

  sLineBuffer = esp_lcd_i80_alloc_draw_buffer(sPanelIo,
                                              C_LCD_H_RES * C_LCD_BUFFER_LINES * C_LCD_BYTES_PER_PIXEL,
                                              MALLOC_CAP_DMA);
  if(sLineBuffer == NULL)
  {
    ESP_LOGE(TAG, "No hay memoria DMA para el buffer de la pantalla");
    return ESP_ERR_NO_MEM;
  }

  for(size_t index = 0; index < sPanel->initCommandCount; index++)
  {
    const PanelInitCommand_t *step = &sPanel->initCommands[index];

    err = DisplaySendCommand(step->command, (step->paramCount > 0) ? step->params : NULL, step->paramCount);
    if(err != ESP_OK)
    {
      ESP_LOGE(TAG, "Comando 0x%02X de inicio fallo (%s)", step->command, esp_err_to_name(err));
      return err;
    }
    if(step->delayMs > 0)
    {
      vTaskDelay(pdMS_TO_TICKS(step->delayMs));
    }
  }

  err = DisplaySendCommand(C_LCD_CMD_MADCTL, &sPanel->madctlLandscape, 1);
  if(err == ESP_OK)
  {
    err = DisplaySendCommand(C_LCD_CMD_DISPON, NULL, 0);
  }
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "No se pudo fijar la orientacion o encender la pantalla (%s)", esp_err_to_name(err));
    return err;
  }
  vTaskDelay(pdMS_TO_TICKS(C_LCD_DISPON_DELAY_MS));

  ESP_LOGI(TAG, "Pantalla %s lista: bus de %d bits, %lu Hz, %dx%d",
           sPanel->name, C_LCD_BUS_WIDTH, (unsigned long)pclkHz, C_LCD_H_RES, C_LCD_V_RES);
  return ESP_OK;
}

/**
 * Nombre:      DisplayInit
 * Descripcion: Crea (una sola vez) el semaforo y el mutex, y luego el bus i80
 *              de C_LCD_BUS_WIDTH bits, la interfaz del panel y el buffer DMA;
 *              ejecuta la secuencia de inicio del controlador elegido, fija la
 *              orientacion horizontal y enciende la pantalla. Si algo falla,
 *              libera lo creado y se puede reintentar. No toca la
 *              retroiluminacion (va por el expansor U6, GPB4). Se llama desde
 *              una sola tarea, antes de dibujar.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si la pantalla quedo lista.
 *              ESP_ERR_INVALID_STATE si ya estaba inicializada.
 *              ESP_ERR_NO_MEM si falta memoria para el semaforo, el mutex o el buffer.
 *              Otro codigo de esp_err_t si esp_lcd falla.
 */
esp_err_t DisplayInit(void)
{
  if(sIsDisplayReady == true)
  {
    return ESP_ERR_INVALID_STATE;
  }

  if(sTransferDoneSemaphore == NULL)
  {
    sTransferDoneSemaphore = xSemaphoreCreateBinary();
  }
  if(sDisplayMutex == NULL)
  {
    sDisplayMutex = xSemaphoreCreateMutex();
  }
  if(sTransferDoneSemaphore == NULL || sDisplayMutex == NULL)
  {
    return ESP_ERR_NO_MEM;
  }

  /* Descartar una senal de fin de transferencia que haya quedado de un intento anterior */
  xSemaphoreTake(sTransferDoneSemaphore, 0);

  sPanel = DisplaySelectPanel();

  esp_err_t err = DisplayStart();
  if(err != ESP_OK)
  {
    DisplayReleaseResources();
    return err;
  }

  sIsDisplayReady = true;
  return ESP_OK;
}

/**
 * Nombre:      DisplayFillColor
 * Descripcion: Llena toda la pantalla con un color, por bloques de
 *              C_LCD_BUFFER_LINES lineas. Bloqueante. Toma el mutex del driver,
 *              asi que varias tareas pueden llamarla sin mezclar transferencias.
 * Entradas:    color565 - color RGB565 (por ejemplo C_LCD_COLOR_RED).
 * Salidas:     ESP_OK si se dibujo.
 *              ESP_ERR_INVALID_STATE si DisplayInit no termino bien.
 *              ESP_ERR_TIMEOUT si el DMA no termina a tiempo.
 *              Otro error de esp_lcd si falla un bloque.
 */
esp_err_t DisplayFillColor(uint16_t color565)
{
  if(sIsDisplayReady == false)
  {
    return ESP_ERR_INVALID_STATE;
  }

  xSemaphoreTake(sDisplayMutex, portMAX_DELAY);

  /* Antes de reescribir el buffer, el DMA anterior debe haber terminado */
  esp_err_t err = DisplayWaitPendingTransfer();
  if(err == ESP_OK)
  {
    for(int index = 0; index < C_LCD_H_RES * C_LCD_BUFFER_LINES; index++)
    {
      sLineBuffer[index] = color565;
    }

    for(int yStart = 0; (yStart < C_LCD_V_RES) && (err == ESP_OK); yStart += C_LCD_BUFFER_LINES)
    {
      int yEnd = yStart + C_LCD_BUFFER_LINES - 1;
      if(yEnd > C_LCD_V_RES - 1)
      {
        yEnd = C_LCD_V_RES - 1;
      }

      err = DisplayWriteWindow(0, yStart, C_LCD_H_RES - 1, yEnd, sLineBuffer);
    }
  }

  xSemaphoreGive(sDisplayMutex);
  return err;
}

/**
 * Nombre:      DisplayDrawBitmap
 * Descripcion: Dibuja un rectangulo de pixeles RGB565. El bloque debe caber en
 *              C_LCD_BUFFER_LINES lineas de la pantalla y estar en memoria
 *              interna apta para DMA (por ejemplo asignada con heap_caps_malloc
 *              y MALLOC_CAP_DMA) y alineada a 2 bytes; no sirve la PSRAM.
 *              Bloqueante. Toma el mutex del driver.
 * Entradas:    xStart, yStart - esquina superior izquierda.
 *              xEnd, yEnd     - esquina inferior derecha (inclusive).
 *              pixels         - pixeles RGB565 por filas, sin NULL.
 * Salidas:     ESP_OK si se dibujo.
 *              ESP_ERR_INVALID_STATE si DisplayInit no termino bien.
 *              ESP_ERR_INVALID_ARG si el rectangulo esta fuera de la pantalla,
 *              es mayor que el bloque maximo, o pixels es NULL, esta desalineado
 *              o no es memoria apta para DMA.
 *              ESP_ERR_TIMEOUT si el DMA no termina a tiempo.
 *              Otro error de esp_lcd si falla el envio.
 */
esp_err_t DisplayDrawBitmap(int xStart, int yStart, int xEnd, int yEnd, const uint16_t *pixels)
{
  if(sIsDisplayReady == false)
  {
    return ESP_ERR_INVALID_STATE;
  }

  if(pixels == NULL || (((uintptr_t)pixels & 1) != 0) || (esp_ptr_dma_capable(pixels) == false) ||
     xStart < 0 || yStart < 0 || xEnd < xStart || yEnd < yStart ||
     xEnd >= C_LCD_H_RES || yEnd >= C_LCD_V_RES ||
     (xEnd - xStart + 1) * (yEnd - yStart + 1) > C_LCD_H_RES * C_LCD_BUFFER_LINES)
  {
    return ESP_ERR_INVALID_ARG;
  }

  xSemaphoreTake(sDisplayMutex, portMAX_DELAY);

  esp_err_t err = DisplayWaitPendingTransfer();
  if(err == ESP_OK)
  {
    err = DisplayWriteWindow(xStart, yStart, xEnd, yEnd, pixels);
  }

  xSemaphoreGive(sDisplayMutex);
  return err;
}

/**
 * Nombre:      DisplayGetControllerName
 * Descripcion: Devuelve el nombre del controlador elegido en Kconfig.
 * Entradas:    Ninguna.
 * Salidas:     Nombre del controlador ("ILI9486" o "ST7796U"), o "sin inicializar"
 *              si DisplayInit no se ha llamado o fallo.
 */
const char *DisplayGetControllerName(void)
{
  return ((sIsDisplayReady == true) && (sPanel != NULL)) ? sPanel->name : "sin inicializar";
}
