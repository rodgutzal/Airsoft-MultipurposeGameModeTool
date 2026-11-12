# Warnings de compilación

Registro de los warnings que salen al compilar, para corregirlos y llevar su trazabilidad. Se actualiza en cada compilación previa a un commit.

Compilador: ESP-IDF v6.1, target esp32s3. Última revisión: 2026-11-12, branch `b#13_DocumentacionProyecto`. Siguen solo los 5 warnings externos de ESP-IDF.

## Abiertos

| ID | Etapa | Origen | Detalle | Causa | Corrección propuesta | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| W-001 | CMake (configuración) | ESP-IDF: `esp_wifi` / `wpa_supplicant` | Directorio privado `esp_wifi/wifi_apps/roaming_app/include` de `esp_wifi` usado por `wpa_supplicant`. | Dependencia circular entre los componentes `esp_wifi` y `wpa_supplicant` dentro de ESP-IDF. | Ninguna en nuestro código; es del framework. Revisar si desaparece en una versión posterior de ESP-IDF, o silenciarlo si molesta. | Abierto, externo |
| W-002 | CMake (configuración) | ESP-IDF: `esp_wifi` / `wpa_supplicant` | Directorio privado `esp_wifi/wifi_apps/roaming_app/src` de `esp_wifi` usado por `wpa_supplicant`. | La misma de W-001. | La misma de W-001. | Abierto, externo |
| W-003 | CMake (configuración) | ESP-IDF: `esp_wifi` / `wpa_supplicant` | Directorio privado `esp_wifi/wifi_apps/include/apps_private` de `esp_wifi` usado por `wpa_supplicant`. | La misma de W-001. | La misma de W-001. | Abierto, externo |
| W-004 | CMake (configuración) | ESP-IDF: `esp_wifi` / `wpa_supplicant` | Directorio privado `wpa_supplicant/src` de `wpa_supplicant` usado por `esp_wifi`. | La misma de W-001, en sentido contrario. | La misma de W-001. | Abierto, externo |
| W-005 | CMake (configuración) | ESP-IDF: `esp_wifi` / `wpa_supplicant` | Directorio privado `wpa_supplicant/esp_supplicant/src` de `wpa_supplicant` usado por `esp_wifi`. | La misma de W-001, en sentido contrario. | La misma de W-001. | Abierto, externo |

Todos salen del archivo `tools/cmake/component_validation.cmake:106` de ESP-IDF. Ninguno viene de `Sw/AirsoftToolSw` y ninguno afecta el binario.

## Cerrados

Ninguno todavía.
