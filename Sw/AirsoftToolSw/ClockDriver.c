/**
 * Archivo:           ClockDriver.c
 * Descripcion:       Driver del reloj del CPU: lo fija a la frecuencia objetivo
 *                    (C_CPU_CLOCK_TARGET_MHZ) y verifica que se logro.
 * Fecha de creacion: 2026-11-03
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include "esp_log.h"
#include "esp_clk_tree.h"
#include "esp_pm.h"
#include "soc/rtc.h"
#include "soc/clk_tree_defs.h"
#include "ClockDriver.h"
#include "GlobalDefine.h"

static const char *TAG = "ClockDriver";

/**
 * Nombre:      ConfigCpuClock
 * Descripcion: Configura el reloj del CPU a la frecuencia objetivo
 *              (C_CPU_CLOCK_TARGET_MHZ = 240 MHz, el maximo del ESP32-S3) y lo
 *              deja fijo, sin escalado de frecuencia ni light sleep. El CPU
 *              corre desde el PLL, que multiplica el cristal de 40 MHz del
 *              modulo. Usa esp_pm_configure, la via soportada por ESP-IDF
 *              para cambiar la frecuencia con FreeRTOS en marcha (ajusta los
 *              timers). El oscilador interno RC_FAST (unos 17.5 MHz) no se
 *              usa. Al terminar informa la fuente del reloj y verifica la
 *              frecuencia con VerifyCpuClockFrequency.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si el CPU quedo a la frecuencia objetivo.
 *              Otro codigo de esp_err_t si esp_pm_configure falla o la
 *              frecuencia final no coincide con la objetivo.
 */
esp_err_t ConfigCpuClock(void)
{
  esp_pm_config_t pmConfig =
  {
    .max_freq_mhz       = C_CPU_CLOCK_TARGET_MHZ,
    .min_freq_mhz       = C_CPU_CLOCK_TARGET_MHZ,
    .light_sleep_enable = false,
  };

  esp_err_t err = esp_pm_configure(&pmConfig);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "esp_pm_configure fallo (%s)", esp_err_to_name(err));
    return err;
  }

  rtc_cpu_freq_config_t clockConfig;
  rtc_clk_cpu_freq_get_config(&clockConfig);
  ESP_LOGI(TAG, "Fuente del CPU: %s, %lu MHz de fuente, divisor %lu",
           (clockConfig.source == SOC_CPU_CLK_SRC_PLL) ? "PLL" :
           (clockConfig.source == SOC_CPU_CLK_SRC_XTAL) ? "XTAL" : "RC_FAST",
           (unsigned long)clockConfig.source_freq_mhz,
           (unsigned long)clockConfig.div);

  return VerifyCpuClockFrequency();
}

/**
 * Nombre:      VerifyCpuClockFrequency
 * Descripcion: Lee la frecuencia real del CPU y comprueba que sea la objetivo
 *              (C_CPU_CLOCK_TARGET_MHZ). El reloj arranca a esa frecuencia por
 *              sdkconfig.defaults: el CPU corre desde el PLL, que multiplica
 *              el cristal de 40 MHz del modulo, para llegar a 240 MHz (el
 *              maximo del ESP32-S3). El oscilador interno RC_FAST solo da
 *              unos 17.5 MHz y no se usa como fuente del CPU.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si la frecuencia coincide con la objetivo.
 *              ESP_FAIL si es distinta (tambien se escribe un aviso en el log).
 *              Otro codigo de esp_err_t si no se pudo leer la frecuencia.
 */
esp_err_t VerifyCpuClockFrequency(void)
{
  uint32_t cpuHz = 0;
  esp_err_t err = esp_clk_tree_src_get_freq_hz(SOC_MOD_CLK_CPU, ESP_CLK_TREE_SRC_FREQ_PRECISION_CACHED, &cpuHz);
  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "No se pudo leer la frecuencia del CPU (%s)", esp_err_to_name(err));
    return err;
  }

  uint32_t cpuMHz = cpuHz / C_HZ_PER_MHZ;
  ESP_LOGI(TAG, "CPU: %lu MHz (objetivo %d MHz)", (unsigned long)cpuMHz, C_CPU_CLOCK_TARGET_MHZ);

  if(cpuMHz != C_CPU_CLOCK_TARGET_MHZ)
  {
    ESP_LOGW(TAG, "El CPU no corre a la frecuencia objetivo; revisar sdkconfig.defaults");
    return ESP_FAIL;
  }

  return ESP_OK;
}
