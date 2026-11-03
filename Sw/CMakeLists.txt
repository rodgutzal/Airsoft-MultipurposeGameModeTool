cmake_minimum_required(VERSION 3.16)

# El componente principal vive en AirsoftToolSw (en lugar de la carpeta "main" por defecto)
set(EXTRA_COMPONENT_DIRS AirsoftToolSw)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(airsoft_tool)
