# Graph Report - Airsoft-MultipurposeGameModeTool  (2026-11-17)

## Corpus Check
- Corpus is ~44,285 words - fits in a single context window. You may not need a graph.

## Summary
- 176 nodes · 348 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Generador esquematico KiCad
- DisplayDriver i80 y paneles
- Reloj y sistema ESP-IDF
- Generador PCB
- Heartbeat, timer y main
- Vistas y colocacion PCB
- FlashDriver NVS
- GpioDriver

## God Nodes (most connected - your core abstractions)
1. `importar_ses()` - 10 edges
2. `InitMainProcess()` - 10 edges
3. `main()` - 9 edges
4. `OpenFlashNamespace()` - 9 edges
5. `extract_lib_symbol()` - 6 edges
6. `mm()` - 6 edges
7. `pt()` - 6 edges
8. `dibujar()` - 6 edges
9. `DisplayInit()` - 6 edges
10. `app_main()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `InitMainProcess()` --calls--> `ConfigCpuClock()`  [INFERRED]
  Sw/AirsoftToolSw/MainProcess.c → Sw/AirsoftToolSw/ClockDriver.c
- `InitMainProcess()` --calls--> `DisplayInit()`  [INFERRED]
  Sw/AirsoftToolSw/MainProcess.c → Sw/AirsoftToolSw/DisplayDriver.c
- `InitMainProcess()` --calls--> `DisplayFillColor()`  [INFERRED]
  Sw/AirsoftToolSw/MainProcess.c → Sw/AirsoftToolSw/DisplayDriver.c
- `InitMainProcess()` --calls--> `FlashInit()`  [INFERRED]
  Sw/AirsoftToolSw/MainProcess.c → Sw/AirsoftToolSw/FlashDriver.c
- `InitSimpleGpioPorts()` --calls--> `ConfigGpioAsOutput()`  [INFERRED]
  Sw/AirsoftToolSw/MainProcess.c → Sw/AirsoftToolSw/GpioDriver.c

## Import Cycles
- None detected.

## Communities (8 total, 1 thin omitted)

### Community 0 - "Generador esquematico KiCad"
Cohesion: 0.11
Nodes (18): box_symbol(), extract_lib_symbol(), frame(), place(), snap(), text(), uid(), use_box() (+10 more)

### Community 1 - "DisplayDriver i80 y paneles"
Cohesion: 0.11
Nodes (12): DisplayColorTransferDoneIsr(), DisplayDrawBitmap(), DisplayFillColor(), DisplayInit(), DisplayReleaseResources(), DisplaySelectPanel(), DisplaySendCommand(), DisplayStart() (+4 more)

### Community 3 - "Generador PCB"
Cohesion: 0.17
Nodes (16): main(), mm(), parse_netlist(), proyecto(), pt(), rect(), seg(), text() (+8 more)

### Community 4 - "Heartbeat, timer y main"
Cohesion: 0.11
Nodes (10): HeartbeatTick(), app_main(), InitMainProcess(), InitSimpleGpioPorts(), InitRam(), PeriodicTimerAlarmIsr(), TimerEndMainTick(), TimerInit() (+2 more)

### Community 5 - "Vistas y colocacion PCB"
Cohesion: 0.26
Nodes (6): bbox(), main(), dibujar(), main(), mm(), poly_patches()

### Community 6 - "FlashDriver NVS"
Cohesion: 0.28
Nodes (8): FlashEraseAll(), FlashInit(), FlashReadBlob(), FlashReadU32(), FlashWriteBlob(), FlashWriteU32(), IsFlashKeyValid(), OpenFlashNamespace()

### Community 7 - "GpioDriver"
Cohesion: 0.36
Nodes (5): ConfigGpioAsInput(), ConfigGpioAsOutput(), IsGpioPinUsable(), SetGpioLevel(), HeartbeatInit()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `InitMainProcess()` connect `Heartbeat, timer y main` to `DisplayDriver i80 y paneles`, `Reloj y sistema ESP-IDF`, `FlashDriver NVS`, `GpioDriver`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `InitMainProcess()` (e.g. with `app_main()` and `ConfigCpuClock()`) actually correct?**
  _`InitMainProcess()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Generador esquematico KiCad` be split into smaller, more focused modules?**
  _Cohesion score 0.11264367816091954 - nodes in this community are weakly interconnected._
- **Should `DisplayDriver i80 y paneles` be split into smaller, more focused modules?**
  _Cohesion score 0.10804597701149425 - nodes in this community are weakly interconnected._
- **Should `Reloj y sistema ESP-IDF` be split into smaller, more focused modules?**
  _Cohesion score 0.12561576354679804 - nodes in this community are weakly interconnected._
- **Should `Heartbeat, timer y main` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._