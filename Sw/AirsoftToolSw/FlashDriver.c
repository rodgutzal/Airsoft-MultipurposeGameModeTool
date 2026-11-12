/**
 * Archivo:           FlashDriver.c
 * Descripcion:       Driver de almacenamiento persistente en flash (NVS):
 *                    guarda y lee valores y bloques de datos por clave dentro de
 *                    un espacio de nombres propio (C_FLASH_NAMESPACE). Las
 *                    escrituras borran y escriben flash: son bloqueantes y
 *                    pueden tardar decenas de milisegundos, por lo que no deben
 *                    llamarse dentro de las subrutinas del ciclo de 5 ms.
 * Fecha de creacion: 2026-11-04
 * Microcontrolador:  ESP32-S3 (modulo ESP32-S3-WROOM-1 N16R8, placa DevKitC-1)
 * Compilador:        xtensa-esp-elf-gcc 15.2.0 (esp-15.2.0_20251204)
 * IDE:               Visual Studio Code con la extension ESP-IDF
 * ADE:               ESP-IDF v6.1
 * Licencia:          Por definir (el proyecto aun no tiene licencia).
 *                    ESP-IDF se distribuye bajo Apache-2.0.
 */

#include <string.h>
#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "FlashDriver.h"
#include "Ram.h"

static const char *TAG = "FlashDriver";

/* C_TRUE cuando FlashInit termino bien. Las demas funciones lo revisan y
 * devuelven ESP_ERR_INVALID_STATE si todavia es C_FALSE. */
static bool sIsFlashReady = C_FALSE;

/**
 * Nombre:      IsFlashKeyValid
 * Descripcion: Revisa que una clave exista y tenga entre 1 y
 *              C_FLASH_KEY_MAX_LENGTH caracteres (limite de NVS).
 * Entradas:    key - clave a revisar.
 * Salidas:     C_TRUE si la clave es valida, C_FALSE si es NULL, esta vacia o
 *              es demasiado larga.
 */
static bool IsFlashKeyValid(const char *key)
{
  if(key == NULL)
  {
    return C_FALSE;
  }

  size_t length = strlen(key);

  return (length >= 1) && (length <= C_FLASH_KEY_MAX_LENGTH);
}

/**
 * Nombre:      OpenFlashNamespace
 * Descripcion: Abre el espacio de nombres C_FLASH_NAMESPACE para leer o
 *              escribir. Requiere haber llamado antes a FlashInit.
 * Entradas:    mode   - NVS_READONLY o NVS_READWRITE.
 *              handle - recibe el handle abierto; debe cerrarse con nvs_close.
 * Salidas:     ESP_OK si abrio bien.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
static esp_err_t OpenFlashNamespace(nvs_open_mode_t mode, nvs_handle_t *handle)
{
  if(sIsFlashReady == C_FALSE)
  {
    ESP_LOGE(TAG, "FlashInit no se ha ejecutado");
    return ESP_ERR_INVALID_STATE;
  }

  return nvs_open(C_FLASH_NAMESPACE, mode, handle);
}

/**
 * Nombre:      FlashInit
 * Descripcion: Inicializa el almacenamiento en flash (NVS). Si la particion no
 *              tiene espacio libre o fue creada por otra version de NVS, la
 *              borra y la inicializa de nuevo (se pierden los datos
 *              guardados).
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si el almacenamiento quedo listo.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashInit(void)
{
  esp_err_t err = nvs_flash_init();
  if((err == ESP_ERR_NVS_NO_FREE_PAGES) || (err == ESP_ERR_NVS_NEW_VERSION_FOUND))
  {
    ESP_LOGW(TAG, "La particion nvs se borra y se vuelve a crear (%s)", esp_err_to_name(err));
    err = nvs_flash_erase();
    if(err != ESP_OK)
    {
      ESP_LOGE(TAG, "nvs_flash_erase fallo (%s)", esp_err_to_name(err));
      return err;
    }
    err = nvs_flash_init();
  }

  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "nvs_flash_init fallo (%s)", esp_err_to_name(err));
    return err;
  }

  sIsFlashReady = C_TRUE;
  ESP_LOGI(TAG, "Almacenamiento en flash listo");
  return ESP_OK;
}

/**
 * Nombre:      FlashReadU32
 * Descripcion: Lee un valor de 32 bits guardado con la clave dada.
 * Entradas:    key   - clave del valor (1 a C_FLASH_KEY_MAX_LENGTH caracteres).
 *              value - recibe el valor leido.
 * Salidas:     ESP_OK si leyo el valor.
 *              ESP_ERR_NVS_NOT_FOUND si la clave no existe todavia (el
 *              llamador puede usar un valor por omision).
 *              ESP_ERR_INVALID_ARG si la clave no es valida o value es NULL.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashReadU32(const char *key, uint32_t *value)
{
  if((IsFlashKeyValid(key) == C_FALSE) || (value == NULL))
  {
    return ESP_ERR_INVALID_ARG;
  }

  nvs_handle_t handle;
  esp_err_t err = OpenFlashNamespace(NVS_READONLY, &handle);
  if(err != ESP_OK)
  {
    return err;
  }

  err = nvs_get_u32(handle, key, value);
  nvs_close(handle);

  if((err != ESP_OK) && (err != ESP_ERR_NVS_NOT_FOUND))
  {
    ESP_LOGE(TAG, "Lectura de '%s' fallo (%s)", key, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      FlashWriteU32
 * Descripcion: Guarda un valor de 32 bits con la clave dada y confirma la
 *              escritura en flash. Es bloqueante.
 * Entradas:    key   - clave del valor (1 a C_FLASH_KEY_MAX_LENGTH caracteres).
 *              value - valor a guardar.
 * Salidas:     ESP_OK si el valor quedo guardado.
 *              ESP_ERR_INVALID_ARG si la clave no es valida.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashWriteU32(const char *key, uint32_t value)
{
  if(IsFlashKeyValid(key) == C_FALSE)
  {
    return ESP_ERR_INVALID_ARG;
  }

  nvs_handle_t handle;
  esp_err_t err = OpenFlashNamespace(NVS_READWRITE, &handle);
  if(err != ESP_OK)
  {
    return err;
  }

  err = nvs_set_u32(handle, key, value);
  if(err == ESP_OK)
  {
    err = nvs_commit(handle);
  }
  nvs_close(handle);

  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "Escritura de '%s' fallo (%s)", key, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      FlashReadBlob
 * Descripcion: Lee un bloque de datos guardado con la clave dada.
 * Entradas:    key    - clave del bloque (1 a C_FLASH_KEY_MAX_LENGTH
 *                       caracteres).
 *              buffer - memoria donde se copia el bloque.
 *              length - al entrar, tamano de buffer en bytes; al salir, tamano
 *                       del bloque guardado (si buffer es chico, ESP-IDF
 *                       devuelve el tamano necesario).
 * Salidas:     ESP_OK si leyo el bloque.
 *              ESP_ERR_NVS_NOT_FOUND si la clave no existe todavia.
 *              ESP_ERR_NVS_INVALID_LENGTH si buffer es mas chico que el
 *              bloque.
 *              ESP_ERR_INVALID_ARG si la clave no es valida o algun puntero es
 *              NULL.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashReadBlob(const char *key, void *buffer, size_t *length)
{
  if((IsFlashKeyValid(key) == C_FALSE) || (buffer == NULL) || (length == NULL))
  {
    return ESP_ERR_INVALID_ARG;
  }

  nvs_handle_t handle;
  esp_err_t err = OpenFlashNamespace(NVS_READONLY, &handle);
  if(err != ESP_OK)
  {
    return err;
  }

  err = nvs_get_blob(handle, key, buffer, length);
  nvs_close(handle);

  if((err != ESP_OK) && (err != ESP_ERR_NVS_NOT_FOUND))
  {
    ESP_LOGE(TAG, "Lectura del bloque '%s' fallo (%s)", key, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      FlashWriteBlob
 * Descripcion: Guarda un bloque de datos con la clave dada y confirma la
 *              escritura en flash. Es bloqueante.
 * Entradas:    key    - clave del bloque (1 a C_FLASH_KEY_MAX_LENGTH
 *                       caracteres).
 *              data   - bloque a guardar.
 *              length - tamano del bloque en bytes (mayor que cero).
 * Salidas:     ESP_OK si el bloque quedo guardado.
 *              ESP_ERR_INVALID_ARG si la clave no es valida, data es NULL o
 *              length es cero.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashWriteBlob(const char *key, const void *data, size_t length)
{
  if((IsFlashKeyValid(key) == C_FALSE) || (data == NULL) || (length == 0))
  {
    return ESP_ERR_INVALID_ARG;
  }

  nvs_handle_t handle;
  esp_err_t err = OpenFlashNamespace(NVS_READWRITE, &handle);
  if(err != ESP_OK)
  {
    return err;
  }

  err = nvs_set_blob(handle, key, data, length);
  if(err == ESP_OK)
  {
    err = nvs_commit(handle);
  }
  nvs_close(handle);

  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "Escritura del bloque '%s' fallo (%s)", key, esp_err_to_name(err));
  }

  return err;
}

/**
 * Nombre:      FlashEraseAll
 * Descripcion: Borra todas las claves del espacio de nombres C_FLASH_NAMESPACE
 *              y confirma el borrado en flash. Es bloqueante.
 * Entradas:    Ninguna.
 * Salidas:     ESP_OK si se borraron las claves.
 *              ESP_ERR_INVALID_STATE si FlashInit no se ha ejecutado.
 *              Otro codigo de esp_err_t si NVS falla.
 */
esp_err_t FlashEraseAll(void)
{
  nvs_handle_t handle;
  esp_err_t err = OpenFlashNamespace(NVS_READWRITE, &handle);
  if(err != ESP_OK)
  {
    return err;
  }

  err = nvs_erase_all(handle);
  if(err == ESP_OK)
  {
    err = nvs_commit(handle);
  }
  nvs_close(handle);

  if(err != ESP_OK)
  {
    ESP_LOGE(TAG, "Borrado fallo (%s)", esp_err_to_name(err));
  }

  return err;
}
