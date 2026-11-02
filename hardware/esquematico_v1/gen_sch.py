#!/usr/bin/env python3
"""Genera el esquemático v1 (KiCad 7) de la herramienta de airsoft.

Estilo: cada pin lleva un tramo corto de cable y una etiqueta de red.
La conectividad se da por nombre de etiqueta.
"""
import re
import sys
import uuid as _uuid

LIBDIR = "/usr/share/kicad/symbols"
PROJECT = "airsoft_tool"
G = 2.54


def uid():
    return str(_uuid.uuid4())


ROOT_UUID = uid()


# ---------------------------------------------------------------- librerías
def extract_lib_symbol(lib, name):
    t = open(f"{LIBDIR}/{lib}.kicad_sym").read()
    i = t.find(f'(symbol "{name}"')
    if i < 0:
        sys.exit(f"no existe {lib}:{name}")
    d = 0
    j = i
    while True:
        c = t[j]
        if c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                break
        j += 1
    s = t[i : j + 1]
    pins = {}
    for m in re.finditer(
        r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length [\d.]+\)[\s\S]*?\(name "([^"]*)"[\s\S]*?\(number "([^"]*)"',
        s,
    ):
        x, y, a, _n, num = m.groups()
        pins[num] = (float(x), float(y), int(a))
    s = s.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return s, pins


def box_symbol(name, ref, left, right, width=25.4, desc=""):
    """Símbolo rectangular con pines pasivos. left/right: listas de (num, nombre)."""
    n = max(len(left), len(right))
    top = (n - 1) / 2 * G
    hw = width / 2
    pins = {}
    body = []
    for side, lst in (("L", left), ("R", right)):
        for i, (num, pname) in enumerate(lst):
            y = round(top - i * G, 2)
            if side == "L":
                x, a = -(hw + G), 0
            else:
                x, a = hw + G, 180
            pins[num] = (x, y, a)
            body.append(
                f'(pin passive line (at {x} {y} {a}) (length {G}) '
                f'(name "{pname}" (effects (font (size 1.27 1.27)))) '
                f'(number "{num}" (effects (font (size 1.27 1.27)))))'
            )
    ytop = top + G
    ybot = -top - G
    s = (
        f'(symbol "custom:{name}" (in_bom yes) (on_board yes)\n'
        f'  (property "Reference" "{ref}" (at 0 {ytop + 1.27} 0) (effects (font (size 1.27 1.27))))\n'
        f'  (property "Value" "{name}" (at 0 {ybot - 1.27} 0) (effects (font (size 1.27 1.27))))\n'
        f'  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'  (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'  (symbol "{name}_0_1" (rectangle (start {-hw} {ytop}) (end {hw} {ybot}) '
        f'(stroke (width 0.254) (type default)) (fill (type background))))\n'
        f'  (symbol "{name}_1_1" {" ".join(body)})\n)'
    )
    return s, pins


LIB = {}  # lib_id -> (texto, pines)


def use_std(lib, name):
    lid = f"{lib}:{name}"
    if lid not in LIB:
        LIB[lid] = extract_lib_symbol(lib, name)
    return lid


def use_box(name, ref, left, right, width=25.4, desc=""):
    lid = f"custom:{name}"
    LIB[lid] = box_symbol(name, ref, left, right, width, desc)
    return lid


# ---------------------------------------------------------------- dibujo
ITEMS = []
BOM = []


def snap(v):
    return round(round(v / 1.27) * 1.27, 2)


def place(lid, ref, value, x, y, nets, stub=5.08, rot=0, fields=None, ref_at=None, val_at=None):
    """Coloca un símbolo y pone tramo + etiqueta en cada pin.
    nets: {num_pin: nombre_red | None (= no conectado)}"""
    x, y = snap(x), snap(y)
    _txt, pins = LIB[lid]
    rj = vj = "(justify left)"
    if ref_at is None and lid.startswith("custom:"):
        top = max(p[1] for p in pins.values()) + G
        ref_at = (0, -(top + 2.54)); val_at = (0, top + 2.54)
        rj = vj = ""
    if lid.endswith("Q_NMOS_GSD") and ref_at is None:
        ref_at = (6.35, -1.27); val_at = (6.35, 1.27)
    if ref_at is not None and len(ref_at) == 3:
        rj = vj = ""; ref_at = ref_at[:2]; val_at = val_at[:2]
    fa = (360 - rot) % 360
    ref_at = ref_at or (3.81, -1.27)
    val_at = val_at or (3.81, 1.27)
    pin_uuids = " ".join(f'(pin "{n}" (uuid {uid()}))' for n in pins)
    extra = ""
    for k, v in (fields or {}).items():
        extra += f'  (property "{k}" "{v}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
    ITEMS.append(
        f'(symbol (lib_id "{lid}") (at {x} {y} {rot}) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid()})\n'
        f'  (property "Reference" "{ref}" (at {x + ref_at[0]} {y + ref_at[1]} {fa}) (effects (font (size 1.27 1.27)) {rj}))\n'
        f'  (property "Value" "{value}" (at {x + val_at[0]} {y + val_at[1]} {fa}) (effects (font (size 1.27 1.27)) {vj}))\n'
        f'  (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'  (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f"{extra}"
        f"  {pin_uuids}\n"
        f'  (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n)'
    )
    BOM.append((ref, value, lid, fields or {}))
    for num, (px, py, a) in pins.items():
        # rotación del símbolo (solo 0 y 90 usados)
        if rot == 90:
            px, py, a = -py, px, (a + 90) % 360
        elif rot == 270:
            px, py, a = py, -px, (a + 270) % 360
        sx, sy = x + px, y - py  # el eje Y de la librería apunta hacia arriba
        # dirección del tramo: opuesta a la dirección hacia el cuerpo
        d = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}[a]
        net = nets.get(num, "__NC__")
        if net is None or net == "__NC__":
            if net == "__NC__" and num not in nets:
                print(f"aviso: {ref} pin {num} sin asignar", file=sys.stderr)
            ITEMS.append(f"(no_connect (at {round(sx,2)} {round(sy,2)}) (uuid {uid()}))")
            continue
        ex, ey = round(sx + d[0] * stub, 2), round(sy + d[1] * stub, 2)
        ITEMS.append(
            f"(wire (pts (xy {round(sx,2)} {round(sy,2)}) (xy {ex} {ey})) "
            f"(stroke (width 0) (type default)) (uuid {uid()}))"
        )
        la = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
        just = "right" if la in (180, 270) else "left"
        ITEMS.append(
            f'(label "{net}" (at {ex} {ey} {la}) (fields_autoplaced) '
            f"(effects (font (size 1.27 1.27)) (justify {just})) (uuid {uid()}))"
        )


def text(s, x, y, size=1.27, bold=False):
    s = s.replace('"', "'")
    b = " bold" if bold else ""
    ITEMS.append(
        f'(text "{s}" (at {snap(x)} {snap(y)} 0) '
        f"(effects (font (size {size} {size}){b}) (justify left)) (uuid {uid()}))"
    )


def frame(x1, y1, x2, y2):
    ITEMS.append(
        f"(rectangle (start {x1} {y1}) (end {x2} {y2}) "
        f"(stroke (width 0.2) (type dash)) (fill (type none)) (uuid {uid()}))"
    )


# ---------------------------------------------------------------- símbolos
R = use_std("Device", "R")
C = use_std("Device", "C")
LED = use_std("Device", "LED")
D = use_std("Device", "D")
Q = use_std("Device", "Q_NMOS_GSD")
SPK = use_std("Device", "Speaker")
CP = use_std("Device", "C_Polarized")
BAT = use_std("Device", "Battery_Cell")
SPST = use_std("Switch", "SW_SPST")
PUSH = use_std("Switch", "SW_Push")

J1 = ["3V3", "3V3", "RST", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO15", "GPIO16", "GPIO17",
      "GPIO18", "GPIO8", "GPIO3", "GPIO46", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
      "GPIO14", "5V", "GND"]
J3 = ["GND", "GPIO43_TX", "GPIO44_RX", "GPIO1", "GPIO2", "GPIO42", "GPIO41", "GPIO40", "GPIO39",
      "GPIO38", "GPIO37", "GPIO36", "GPIO35", "GPIO0", "GPIO45", "GPIO48", "GPIO47", "GPIO21",
      "GPIO20", "GPIO19", "GND", "GND"]
MCU = use_box(
    "ESP32-S3-DevKitC-1_N16R8", "U",
    [(str(i + 1), n) for i, n in enumerate(J1)],
    [(str(i + 23), n) for i, n in enumerate(J3)],
    width=30.48, desc="Tarjeta ESP32-S3-DevKitC-1 v1.1, headers J1 (izq) y J3 (der)",
)
TFT_L = ["LCD_RST", "LCD_CS", "LCD_RS", "LCD_WR", "LCD_RD", "LCD_D0", "LCD_D1", "LCD_D2",
         "LCD_D3", "LCD_D4", "LCD_D5", "LCD_D6", "LCD_D7"]
TFT_R = ["5V", "3V3", "GND", "SD_SS", "SD_DI", "SD_DO", "SD_SCK"]
TFT = use_box(
    "TFT_3.5in_ILI9486_ST7796_UNO_Shield", "DS",
    [(str(i + 1), n) for i, n in enumerate(TFT_L)],
    [(str(i + 14), n) for i, n in enumerate(TFT_R)],
    width=30.48, desc="Shield TFT 3.5in 480x320, bus 8 bits, touch resistivo en RS/WR y datos",
)
KEY = use_box("Teclado_4x4", "KP",
              [(str(i + 1), f"F{i+1}") for i in range(4)] + [(str(i + 5), f"C{i+1}") for i in range(4)],
              [], width=12.7, desc="Teclado matricial de membrana 4x4")
CHG = use_box("TP4056_USB-C_con_proteccion", "U",
              [("1", "IN+"), ("2", "IN-")],
              [("3", "B+"), ("4", "B-"), ("5", "OUT+"), ("6", "OUT-")],
              width=20.32, desc="Modulo cargador TP4056 + DW01 + FS8205")
AMP = use_box("MAX98357A_I2S_3W", "U",
              [("1", "VIN"), ("2", "GND"), ("3", "SD"), ("4", "GAIN"), ("5", "DIN"), ("6", "BCLK"), ("7", "LRC")],
              [("8", "OUT+"), ("9", "OUT-")],
              width=20.32, desc="Modulo amplificador I2S clase D MAX98357A, 3.2 W en 4 ohm a 5 V")
BST = use_box("Elevador_MT3608_5V", "U",
              [("1", "VIN+"), ("2", "VIN-")], [("3", "VOUT+"), ("4", "VOUT-")],
              width=20.32, desc="Modulo elevador ajustado a 5.1 V")

# ---------------------------------------------------------------- microcontrolador
mcu_nets = {
    "1": "+3V3", "2": "+3V3", "3": None,
    "4": "LCD_D0", "5": "LCD_D1", "6": "LCD_D2", "7": "LCD_D3", "8": "LCD_D4", "9": "LCD_D5",
    "10": "LCD_D6", "11": "LCD_D7", "12": "KEY_C1", "13": "LED_ROJO", "14": "LED_AZUL",
    "15": "KEY_C2", "16": "VBAT_SENSE", "17": "KEY_F1", "18": "KEY_F2", "19": "KEY_F3",
    "20": "KEY_F4", "21": "+5V", "22": "GND",
    "23": "GND", "24": None, "25": None, "26": "LCD_RS", "27": "LCD_WR", "28": "LCD_CS",
    "29": "LCD_RST", "30": "I2S_BCLK", "31": "KEY_C4", "32": "KEY_C3", "33": None, "34": None,
    "35": None, "36": "I2S_DIN", "37": "I2S_LRC", "38": "BTN_ACCION", "39": "SW_ARMADO",
    "40": "SW_EQUIPO", "41": None, "42": None, "43": "GND", "44": "GND",
}
frame(10, 25, 215, 125)
text("MICROCONTROLADOR", 83, 29, 2, True)
place(MCU, "U1", "ESP32-S3-DevKitC-1 N16R8", 147.32, 76.2, mcu_nets, stub=7.62)
text("GPIO1 y GPIO2 son ADC1: leen el touch resistivo compartido con LCD_RS y LCD_WR.", 83, 112)
text("GPIO35-37 los usa la PSRAM octal. GPIO19/20 son el USB nativo. GPIO43/44 quedan para depuracion.", 83, 115)
text("GPIO0, GPIO45 y GPIO46 son pines de arranque: solo llevan entradas de alta impedancia (DIN, LRC y la compuerta de Q2 con 100k a GND).", 83, 118)
text("GPIO48 maneja el LED RGB de la tarjeta v1.1: el boton solo lo lee como entrada.", 83, 121)

# ---------------------------------------------------------------- pantalla
frame(225, 25, 405, 95)
text("PANTALLA TFT 3.5in PARALELA 8 BITS CON TOUCH", 228, 29, 2, True)
tft_nets = {str(i + 1): n for i, n in enumerate(TFT_L)}
tft_nets.update({"14": "+5V", "15": None, "16": "GND", "17": None, "18": None, "19": None, "20": None})
place(TFT, "DS1", "TFT 3.5in 480x320 ILI9486/ST7796U", 289.56, 60.96, tft_nets, stub=7.62)
place(R, "R1", "10k", 360.68, 50.8, {"1": "+3V3", "2": "LCD_RD"})
text("LCD_RD fijo en alto (solo escritura).", 345, 70)
text("Pasar a un GPIO libre para leer el ID", 345, 73)
text("del driver. 3V3 y microSD sin usar.", 345, 76)
text("Touch: 4 hilos resistivos multiplexados con RS, WR y dos lineas de datos", 228, 88)
text("(cuales depende del lote; confirmar con el diagnostico de MCUFRIEND_kbv).", 228, 91)

# ---------------------------------------------------------------- teclado
frame(225, 100, 405, 150)
text("TECLADO 4x4", 228, 104, 2, True)
place(KEY, "KP1", "Teclado membrana 4x4", 270.0, 127.0,
      {"1": "KEY_F1", "2": "KEY_F2", "3": "KEY_F3", "4": "KEY_F4",
       "5": "KEY_C1", "6": "KEY_C2", "7": "KEY_C3", "8": "KEY_C4"})
text("Filas como salidas, columnas como entradas con pull-up interno.", 300, 122)
text("Escaneo por firmware, sin componentes extra.", 300, 125)

# ---------------------------------------------------------------- entradas de usuario
frame(10, 135, 215, 200)
text("ENTRADAS: SWITCHES Y PUSH BUTTON", 13, 139, 2, True)
H = ((0, -3.81, 1), (0, 3.81, 1))
place(SPST, "SW1", "Selector de equipo", 45.72, 149.86, {"1": "SW_EQUIPO", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R2", "10k", 45.72, 170.18, {"1": "+3V3", "2": "SW_EQUIPO"})
place(SPST, "SW2", "Armado de bomba (llave)", 106.68, 149.86, {"1": "SW_ARMADO", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R3", "10k", 106.68, 170.18, {"1": "+3V3", "2": "SW_ARMADO"})
place(PUSH, "SW3", "Push button de accion", 167.64, 149.86, {"1": "BTN_ACCION", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R4", "10k", 162.56, 170.18, {"1": "+3V3", "2": "BTN_ACCION"})
place(C, "C1", "100nF", 185.42, 170.18, {"1": "BTN_ACCION", "2": "GND"})
text("Pull-ups externos de 10k por los cables largos en campo. C1 filtra el rebote del boton (tau = 1 ms).", 13, 192)
text("Switch cerrado = nivel bajo. SW1 abierto = equipo rojo, cerrado = equipo azul.", 13, 195)

# ---------------------------------------------------------------- salidas
frame(225, 155, 405, 250)
text("SALIDAS: LEDS DE EQUIPO Y AUDIO", 228, 159, 2, True)
def canal_led(x0, y, color, rr, rg, rp, q, d, rl, r_led):
    n = "LED_" + color
    place(R, rg, "100", x0, y, {"1": n, "2": q + "_G"})
    place(R, rp, "100k", x0 + 15.24, y, {"1": q + "_G", "2": "GND"})
    place(Q, q, "AO3400A", x0 + 40.64, y, {"1": q + "_G", "2": "GND", "3": n + "_K"})
    place(LED, d, color.capitalize() + " 10mm", x0 + 55.88, y, {"1": n + "_K", "2": n + "_A"}, rot=270)
    place(R, rl, r_led, x0 + 73.66, y, {"1": "+5V", "2": n + "_A"})
canal_led(238.76, 190.5, "ROJO", None, "R5", "R6", "Q1", "D1", "R7", "150")
canal_led(322.58, 190.5, "AZUL", None, "R8", "R9", "Q2", "D2", "R10", "100")
place(AMP, "U4", "MAX98357A I2S", 270.0, 229.0,
      {"1": "+5V", "2": "GND", "3": "+3V3", "4": None, "5": "I2S_DIN", "6": "I2S_BCLK", "7": "I2S_LRC",
       "8": "SPK_P", "9": "SPK_N"})
place(SPK, "LS1", "Bocina 4 ohm 3-5 W", 322.58, 229.0, {"1": "SPK_P", "2": "SPK_N"},
      ref_at=(2.54, -6.35, 1), val_at=(2.54, 8.89, 1))
place(CP, "C3", "470uF 10V", 356.0, 229.0, {"1": "+5V", "2": "GND"})
place(C, "C4", "100nF", 372.0, 229.0, {"1": "+5V", "2": "GND"})
text("LEDs a 5 V con MOSFET, unos 20 mA cada uno. Indican equipo activo y parpadean como contador en el modo bomba.", 228, 246)
text("Audio: MAX98357A por I2S, 3.2 W en 4 ohm a 5 V. SD a 3V3 mezcla L+R, GAIN abierto = 9 dB. C3 y C4 junto al modulo.", 228, 249)

# ---------------------------------------------------------------- alimentación
frame(10, 205, 215, 285)
text("ALIMENTACION: 1S2P 18650, CARGA USB-C, ELEVADOR A 5 V", 13, 209, 2, True)
place(BAT, "BT1", "18650", 33.02, 223.52, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(BAT, "BT2", "18650", 33.02, 236.22, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(CHG, "U2", "TP4056 USB-C con proteccion", 81.28, 231.14,
      {"1": None, "2": None, "3": "VBAT_CELDA", "4": "BAT_NEG", "5": "VBAT_PROT", "6": "GND"})
place(SPST, "SW4", "Encendido", 132.08, 220.98, {"1": "VBAT_PROT", "2": "VBAT_SW"}, ref_at=H[0], val_at=H[1])
place(BST, "U3", "MT3608 ajustado a 5.1 V", 182.88, 231.14,
      {"1": "VBAT_SW", "2": "GND", "3": "5V_BOOST", "4": "GND"})
place(D, "D4", "SS34", 205.74, 250.19, {"1": "+5V", "2": "5V_BOOST"}, rot=270)
place(R, "R13", "100k", 124.46, 256.54, {"1": "VBAT_SW", "2": "VBAT_SENSE"})
place(R, "R14", "100k", 142.24, 256.54, {"1": "VBAT_SENSE", "2": "GND"})
place(C, "C2", "100nF", 160.02, 256.54, {"1": "VBAT_SENSE", "2": "GND"})
text("Carga por el USB-C del TP4056 (IN+/IN- son su conector).", 13, 252)
text("D4 evita retroalimentar el elevador con el USB del DevKit.", 13, 255)
text("R13/R14: 4.2 V de bateria -> 2.1 V en GPIO10 (ADC1).", 13, 258)
text("Consumo estimado ~400 mA de bateria. 2 x 3000 mAh", 13, 263)
text("nominales dan unas 10 h, el doble de las 5 h pedidas.", 13, 266)

# ---------------------------------------------------------------- notas


# ---------------------------------------------------------------- salida
lib_txt = "\n".join(v[0] for v in LIB.values())
out = f"""(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A3")
  (title_block
    (title "Herramienta multiproposito para airsoft")
    (date "2026-11-02")
    (rev "v0.1")
    (comment 1 "Esquematico v1: ESP32-S3-DevKitC-1 + TFT 3.5in paralela")
    (comment 2 "Modos: bandera, zona, rey de la colina, bomba, extraccion")
    (comment 3 "Conexiones por etiqueta de red: etiquetas iguales = mismo nodo")
  )
  (lib_symbols
{lib_txt}
  )
{chr(10).join(ITEMS)}
  (sheet_instances (path "/" (page "1")))
)
"""
open(sys.argv[1], "w").write(out)

# BOM simple
import csv
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Referencia", "Valor", "Simbolo"])
    for ref, val, lid, _ in sorted(BOM, key=lambda b: (re.sub(r"\d", "", b[0]), int(re.sub(r"\D", "", b[0])))):
        w.writerow([ref, val, lid])
print("ok", len(ITEMS), "elementos")
