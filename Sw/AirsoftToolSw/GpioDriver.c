/**
 * Archivo:           GpioDriver.c
 * Descripcion:       Driver de GPIO: configuracion de pines como salida y
 *                    como entrada sin resistencias internas, con validacion
 *                    del pin.
 * Fecha de creacion: 2026-11-02
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "driver/gpio.h"
#include "esp_log.h"
#include "GpioDriver.h"
#include "Ram.h"

static const char *TAG = "GpioDriver";

/**
 * Nombre:      IsGpioPinUsable
 * Descripcion: Revisa que el numero de pin exista en el ESP32-S3 y que no
 *              este reservado (USB nativo, flash o PSRAM octal).
 * Entradas:    pin - numero de GPIO.
 * Salidas:     true si el pin se puede usar, false si no existe o esta
 *              reservado.
 */
static bool IsGpioPinUsable(int pin)
{
  if(pin < 0 || pin >= C_GPIO_PIN_COUNT_MAX)
  {
    return C_FALSE;
  }

  if(GPIO_IS_VALID_GPIO(pin) == C_FALSE)
  {
    return C_FALSE;
  }

  return (C_GPIO_RESERVED_MASK & (1ULL << pin)) == 0;
}

/**
 * Nombre:      ConfigGpioAsOutput
 * Descripcion: Configura un GPIO como salida, sin resistencias internas ni
 *              interrupciones, y le asigna un nivel inicial.
 * Entradas:    pin   - numero de GPIO.
 *              level - nivel inicial (0 = bajo, distinto de 0 = alto).
 * Salidas:     ESP_OK si se configuro bien.
 *              ESP_ERR_INVALID_ARG si el pin no existe o esta reservado.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t ConfigGpioAsOutput(int pin, int level)
{
  if(IsGpioPinUsable(pin) == C_FALSE)
  {
    ESP_LOGE(TAG, "GPIO%d no existe o esta reservado", pin);
    return ESP_ERR_INVALID_ARG;
  }

  gpio_config_t cfg =
  {
    .pin_bit_mask = 1ULL << pin,
    .mode         = GPIO_MODE_OUTPUT,
    .pull_up_en   = GPIO_PULLUP_DISABLE,
    .pull_down_en = GPIO_PULLDOWN_DISABLE,
    .intr_type    = GPIO_INTR_DISABLE,
  };

  esp_err_t err = gpio_config(&cfg);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "GPIO%d: fallo al configurar como salida (%s)", pin, esp_err_to_name(err));
    return err;
  }

  err = gpio_set_level((gpio_num_t)pin, (level != C_FALSE) ? C_TRUE : C_FALSE);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "GPIO%d: fallo al fijar el nivel inicial (%s)", pin, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      ConfigGpioAsInput
 * Descripcion: Configura un GPIO como entrada sin resistencias internas
 *              (ni pull-up ni pull-down) y sin interrupciones. El nivel en
 *              reposo lo debe fijar el hardware con una resistencia externa.
 * Entradas:    pin - numero de GPIO.
 * Salidas:     ESP_OK si se configuro bien.
 *              ESP_ERR_INVALID_ARG si el pin no existe o esta reservado.
 *              Otro codigo de esp_err_t si el driver de ESP-IDF falla.
 */
esp_err_t ConfigGpioAsInput(int pin)
{
  if(IsGpioPinUsable(pin) == C_FALSE)
  {
    ESP_LOGE(TAG, "GPIO%d no existe o esta reservado", pin);
    return ESP_ERR_INVALID_ARG;
  }

  gpio_config_t cfg =
  {
    .pin_bit_mask = 1ULL << pin,
    .mode         = GPIO_MODE_INPUT,
    .pull_up_en   = GPIO_PULLUP_DISABLE,
    .pull_down_en = GPIO_PULLDOWN_DISABLE,
    .intr_type    = GPIO_INTR_DISABLE,
  };

  esp_err_t err = gpio_config(&cfg);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "GPIO%d: fallo al configurar como entrada (%s)", pin, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      SetGpioLevel
 * Descripcion: Fija el nivel de un GPIO ya configurado como salida. No escribe
 *              en el log, por lo que se puede llamar dentro del ciclo de 5 ms.
 * Entradas:    pin   - numero de GPIO.
 *              level - nivel (0 = bajo, distinto de 0 = alto).
 * Salidas:     ESP_OK si se fijo el nivel.
 *              ESP_ERR_INVALID_ARG si el pin no existe o esta reservado.
 */
esp_err_t SetGpioLevel(int pin, int level)
{
  if(IsGpioPinUsable(pin) == C_FALSE)
  {
    return ESP_ERR_INVALID_ARG;
  }

  return gpio_set_level((gpio_num_t)pin, (level != C_FALSE) ? C_TRUE : C_FALSE);
}