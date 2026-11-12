#!/usr/bin/env python3
"""Genera el esquematico v0.9 opcion C (KiCad 7) de la herramienta de airsoft.

Opcion C: sin modulos comprados. Modulo ESP32-S3-WROOM-1 N16R8 sin tarjeta de
desarrollo, cargador TP4056, proteccion DW01A + FS8205A, reparto de carga USB/bateria,
elevador sincrono TPS61022 a 5.1 V, LDO AP7361C a 3.3 V, MAX98357A suelto (TQFN-16),
USB-C al USB nativo y header UART0.

Uso: gen_sch_c.py salida.kicad_sch bom.csv
Mismo estilo que ../gen_sch.py: cada pin lleva un tramo corto y una etiqueta de red.
"""
import re
import sys
import uuid as _uuid
from collections import Counter

LIBDIR = "/usr/share/kicad/symbols"
PROJECT = "airsoft_tool_opcion_C"
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
    ext = re.search(r'\(extends "([^"]+)"\)', s)
    if ext:
        # símbolo derivado: se toma el dibujo y los pines del padre con el nombre del hijo
        ps, pins = extract_lib_symbol(lib, ext.group(1))
        ps = ps.replace(f'(symbol "{lib}:{ext.group(1)}"', f'(symbol "{lib}:{name}"', 1)
        ps = ps.replace(f'(symbol "{ext.group(1)}_', f'(symbol "{name}_')
        return ps, pins
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



# ---------------------------------------------------------------- huellas (v0.1 de la PCB, ver ../../pcb)
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
FOOTPRINT = {
    "U1": "RF_Module:ESP32-S3-WROOM-1",
    "U2": "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm_ThermalVias",
    "U4": "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
    "U5": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "U6": "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
    "U7": "Package_TO_SOT_SMD:SOT-23-6",
    "U8": "Package_DFN_QFN:Texas_RWU0007A_VQFN-7_2x2mm_P0.5mm",
    "U9": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "U10": "Package_TO_SOT_SMD:SOT-23-6",
    "Q1": "Package_SO:TSSOP-8_4.4x3mm_P0.65mm",
    "Q2": "Package_SO:TSSOP-8_4.4x3mm_P0.65mm",
    "Q3": "Package_TO_SOT_SMD:SOT-23",
    "D5": "LED_THT:LED_D5.0mm",
    "D6": "LED_SMD:LED_0805_2012Metric",
    "D7": "LED_SMD:LED_0805_2012Metric",
    "D8": "Diode_SMD:D_SMA",
    "D9": "Diode_SMD:D_SMA",
    "L1": "Inductor_SMD:L_Coilcraft_XAL5030-XXX",
    "J1": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "J2": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "J4": XH2,
    "DS1": "Connector_PinSocket_2.54mm:PinSocket_2x17_P2.54mm_Vertical",
    "DS2": XH4, "DS3": XH4,
    "KP1": "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "SW1": XH2, "SW2": XH2, "SW3": XH2, "SW4": XH2,
    "SW5": "Button_Switch_SMD:SW_SPST_TL3342", "SW6": "Button_Switch_SMD:SW_SPST_TL3342",
    "BT1": "Battery:BatteryHolder_MPD_BH-18650-PC2", "BT2": "Battery:BatteryHolder_MPD_BH-18650-PC2",
    "C3": "Capacitor_SMD:CP_Elec_8x10", "C8": "Capacitor_SMD:CP_Elec_10x10",
}
for _r in ("C11", "C13", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23"):
    FOOTPRINT[_r] = C0805
OFF_BOARD = {"LS1"}  # la bocina va en el gabinete, se conecta en J4

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
    if ref in FOOTPRINT:
        fp = FOOTPRINT[ref]
    elif ref.startswith("R"):
        fp = R0603
    elif ref.startswith("C"):
        fp = C0603
    else:
        fp = ""
    if not fp and ref not in OFF_BOARD:
        print(f"aviso: {ref} sin huella", file=sys.stderr)
    onb = "no" if ref in OFF_BOARD else "yes"
    ITEMS.append(
        f'(symbol (lib_id "{lid}") (at {x} {y} {rot}) (unit 1) (in_bom yes) (on_board {onb}) (dnp no) (uuid {uid()})\n'
        f'  (property "Reference" "{ref}" (at {x + ref_at[0]} {y + ref_at[1]} {fa}) (effects (font (size 1.27 1.27)) {rj}))\n'
        f'  (property "Value" "{value}" (at {x + val_at[0]} {y + val_at[1]} {fa}) (effects (font (size 1.27 1.27)) {vj}))\n'
        f'  (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
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
SPK = use_std("Device", "Speaker")
CP = use_std("Device", "C_Polarized")
IND = use_std("Device", "L")
BAT = use_std("Device", "Battery_Cell")
SPST = use_std("Switch", "SW_SPST")
PUSH = use_std("Switch", "SW_Push")
WROOM = use_std("RF_Module", "ESP32-S3-WROOM-1")
USBC = use_std("Connector", "USB_C_Receptacle_USB2.0_16P")
ESD = use_std("Power_Protection", "USBLC6-2SC6")
LDO = use_std("Regulator_Linear", "AP7361C-33E")
PFET = use_std("Transistor_FET", "AO3401A")
SCHOT = use_std("Diode", "SS34")
BOOST = use_std("Converter_DCDC", "TPS61022")
AMPIC = use_std("Audio", "MAX98357A")
CONN6 = use_std("Connector_Generic", "Conn_01x06")
CONN2 = use_std("Connector_Generic", "Conn_01x02")

TFT_PINS = ["CS", "RS", "WR", "RD", "RST"] + [f"DB{i}" for i in range(16)] + [
    "SDCS", "BL", "VDD", "VDD", "GND", "GND", "5V", "MISO", "MOSI", "PEN", "F_CS", "T_CS", "CLK"]
TFT = use_box(
    "LCD_3.5in_ILI9486_16bit_34p", "DS",
    [(str(n), TFT_PINS[n - 1]) for n in range(1, 35, 2)],
    [(str(n), TFT_PINS[n - 1]) for n in range(2, 35, 2)],
    width=30.48, desc="Modulo TFT 3.5in 480x320 ILI9486, bus 8080 de 16 bits, touch XPT2046 por SPI, conector 2x17",
)
EXP = use_box(
    "MCP23017_SP", "U",
    [(str(n), f"GPB{n - 1}") for n in range(1, 9)] + [("9", "VDD"), ("10", "VSS"), ("11", "NC"),
     ("12", "SCL"), ("13", "SDA"), ("14", "NC")],
    [(str(n), f"GPA{n - 21}") for n in range(21, 29)] + [("20", "INTA"), ("19", "INTB"), ("18", "RESET"),
     ("17", "A2"), ("16", "A1"), ("15", "A0")],
    width=25.4, desc="Expansor de 16 E/S por I2C, DIP-28, 3.3 V",
)
KEY = use_box("Teclado_4x4", "KP",
              [(str(i + 1), f"F{i+1}") for i in range(4)] + [(str(i + 5), f"C{i+1}") for i in range(4)],
              [], width=12.7, desc="Teclado matricial de membrana 4x4")
BUF = use_box("74AHCT125", "U",
              [("1", "1OE"), ("2", "1A"), ("3", "1Y"), ("4", "2OE"), ("5", "2A"), ("6", "2Y"), ("7", "GND")],
              [("14", "VCC"), ("13", "4OE"), ("12", "4A"), ("11", "4Y"), ("10", "3OE"), ("9", "3A"), ("8", "3Y")],
              width=15.24, desc="Cuatro buffers con entrada TTL (VIH 2 V) alimentados a 5 V, DIP-14 (SN74AHCT125N)")
TIRA = use_box("Tira_WS2812B", "DS",
               [("1", "+5V"), ("2", "DIN"), ("3", "GND")], [("4", "DOUT")],
               width=15.24, desc="Tira LED RGB direccionable WS2812B 5 V")
CHG = use_box("TP4056", "U",
              [("4", "VCC"), ("8", "CE"), ("1", "TEMP"), ("2", "PROG"), ("3", "GND"), ("9", "EP")],
              [("5", "BAT"), ("7", "~CHRG"), ("6", "~STDBY")],
              width=17.78, desc="Cargador lineal Li-ion 1 A, ESOP-8 con pad expuesto")
PROT = use_box("DW01A", "U",
               [("5", "VCC"), ("6", "GND"), ("2", "CS")],
               [("1", "OD"), ("3", "OC"), ("4", "TD")],
               width=12.7, desc="Proteccion de una celda Li-ion, SOT-23-6")
DFET = use_box("FS8205A", "Q",
               [("1", "D"), ("2", "S1"), ("3", "S1"), ("4", "G1")],
               [("8", "D"), ("7", "S2"), ("6", "S2"), ("5", "G2")],
               width=12.7, desc="Doble MOSFET N de drenador comun, TSSOP-8")

H = ((0, -3.81, 1), (0, 3.81, 1))
HR = dict(rot=90, ref_at=(0, -2.54, 1), val_at=(0, 2.54, 1))   # resistencia horizontal

# ================================================================ MICROCONTROLADOR
frame(10, 25, 200, 175)
text("MICROCONTROLADOR: MODULO ESP32-S3-WROOM-1 N16R8", 13, 29, 2, True)
mcu_nets = {
    "1": "GND", "2": "+3V3", "3": "ESP_EN",
    "4": "LCD_D0", "5": "LCD_D1", "6": "LCD_D2", "7": "LCD_D3",
    "8": "LCD_D4", "9": "LCD_D5", "10": "LCD_D6", "11": "LCD_D7", "12": "LCD_D8",
    "13": "USB_DN_MCU", "14": "USB_DP_MCU", "15": "LED_TIRA", "16": "TOUCH_MOSI",
    "17": "LCD_D9", "18": "VBAT_ADC", "19": "LCD_D10", "20": "LCD_D11", "21": "LCD_D12",
    "22": "LCD_D13", "23": "LCD_D14", "24": "LCD_D15", "25": "TOUCH_MISO", "26": "I2S_LRC",
    "27": "I2S_DIN", "28": None, "29": None, "30": None, "31": "TOUCH_CLK", "32": "I2C_SDA",
    "33": "I2S_BCLK", "34": "TOUCH_CS", "35": "I2C_SCL", "36": "UART_RX0", "37": "LED_ESTADO",
    "38": "LCD_WR", "39": "LCD_RS", "40": "GND", "41": "GND",
}
place(WROOM, "U1", "ESP32-S3-WROOM-1-N16R8", 110.0, 85.0, mcu_nets, stub=7.62,
      ref_at=(-12.7, -30.48, 1), val_at=(0, 45.72, 1))
# EN, BOOT, RESET
place(R, "R22", "10k", 17.78, 55.88, {"1": "+3V3", "2": "ESP_EN"})
place(C, "C10", "1uF", 27.94, 55.88, {"1": "ESP_EN", "2": "GND"})
place(R, "R23", "10k", 38.1, 55.88, {"1": "+3V3", "2": "I2S_DIN"})
place(R, "R24", "10k", 48.26, 55.88, {"1": "I2S_LRC", "2": "GND"})
place(R, "R6", "100k", 58.42, 55.88, {"1": "LED_TIRA", "2": "GND"})
place(R, "R9", "100k", 17.78, 109.22, {"1": "TOUCH_MOSI", "2": "GND"})
place(C, "C11", "22uF", 27.94, 109.22, {"1": "+3V3", "2": "GND"})
place(C, "C12", "100nF", 38.1, 109.22, {"1": "+3V3", "2": "GND"})
place(R, "R10", "4.7k", 48.26, 109.22, {"1": "+3V3", "2": "I2C_SDA"})
place(R, "R11", "4.7k", 58.42, 109.22, {"1": "+3V3", "2": "I2C_SCL"})
place(PUSH, "SW5", "RESET", 177.8, 45.72, {"1": "ESP_EN", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(PUSH, "SW6", "BOOT", 177.8, 66.04, {"1": "I2S_DIN", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R21", "330", 170.18, 109.22, {"1": "LED_ESTADO", "2": "LED_ESTADO_A"})
place(LED, "D5", "Verde 5 mm", 187.96, 109.22, {"1": "GND", "2": "LED_ESTADO_A"}, rot=90, ref_at=(3.81, -1.27), val_at=(3.81, 1.27))
text("EN: R22 10k + C10 1uF (guia de diseno de Espressif). SW5 = RESET, SW6 = BOOT (GPIO0 a GND).", 13, 150)
text("GPIO0 (I2S_DIN): pull-up R23. GPIO45 (I2S_LRC): pull-down R24, flash a 3.3 V. GPIO46 (TOUCH_MOSI): R9 a GND.", 13, 153)
text("GPIO3 (LED_TIRA): R6 a GND. GPIO35, 36 y 37 son de la PSRAM octal de la N16R8: sin conectar.", 13, 156)
text("GPIO19/20 al USB-C (bloque USB). GPIO43 (U0TXD) maneja D5 y sale al header J2; GPIO44 (U0RXD) es RX de J2.", 13, 159)
text("C11 22uF y C12 100nF junto al pin 2 (3V3). EPAD (41) a GND. Zona libre de cobre bajo la antena.", 13, 162)
text("Pantalla en bus 8080 de 16 bits (LCD_CAM). Teclado, switches, boton, PEN, BL, SD del amplificador y deteccion de USB en U6.", 13, 165)
text("D5 activo en alto, ~3.6 mA. R10/R11 pull-ups del I2C.", 13, 168)

# ================================================================ USB-C Y DEPURACION
frame(205, 25, 390, 120)
text("USB-C (USB NATIVO) Y HEADER DE DEPURACION", 208, 29, 2, True)
place(USBC, "J1", "USB-C 16P (USB 2.0)", 225.0, 62.0,
      {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
       "A4": "VBUS_USB", "A9": "VBUS_USB", "B4": "VBUS_USB", "B9": "VBUS_USB",
       "A5": "USB_CC1", "B5": "USB_CC2", "A6": "USB_DP", "B6": "USB_DP",
       "A7": "USB_DN", "B7": "USB_DN", "A8": None, "B8": None},
      ref_at=(-2.54, -21.59, 1), val_at=(12.7, -21.59, 1))
place(R, "R25", "5.1k", 262.0, 85.0, {"1": "USB_CC1", "2": "GND"})
place(R, "R26", "5.1k", 272.0, 85.0, {"1": "USB_CC2", "2": "GND"})
place(ESD, "U7", "USBLC6-2SC6", 290.0, 55.0,
      {"1": "USB_DN", "6": "USB_DN", "3": "USB_DP", "4": "USB_DP", "2": "GND", "5": "VBUS_USB"},
      ref_at=(7.62, -7.62, 1), val_at=(7.62, 10.16, 1))
place(R, "R27", "22", 322.0, 50.8, {"1": "USB_DP", "2": "USB_DP_MCU"}, **HR)
place(R, "R28", "22", 322.0, 63.5, {"1": "USB_DN", "2": "USB_DN_MCU"}, **HR)
place(C, "C23", "10uF", 296.0, 85.0, {"1": "VBUS_USB", "2": "GND"})
place(CONN6, "J2", "UART0 / BOOT 1x6", 360.0, 55.0,
      {"1": "GND", "2": "UART_TX0", "3": "UART_RX0", "4": "ESP_EN", "5": "I2S_DIN", "6": "+3V3"},
      ref_at=(0, -11.43, 1), val_at=(0, 11.43, 1))
place(R, "R29", "499", 340.0, 85.0, {"1": "LED_ESTADO", "2": "UART_TX0"}, **HR)
place(R, "R37", "10k", 370.0, 85.0, {"1": "+3V3", "2": "UART_RX0"})
text("CC1/CC2 con 5.1k (R25, R26): el cargador entrega 5 V. VBUS_USB carga la bateria y alimenta el equipo.", 208, 100)
text("U7 protege D+/D- contra ESD, junto a J1. R27/R28 22 ohm junto al modulo (guia de Espressif).", 208, 103)
text("Grabar y depurar por USB: USB-Serial-JTAG del ESP32-S3 (esptool y OpenOCD, sin adaptador ni JTAG externo).", 208, 106)
text("J2: 1 GND, 2 TX0 (GPIO43 por R29 499 ohm), 3 RX0 (GPIO44, R37), 4 EN, 5 IO0, 6 3V3 de referencia.", 208, 109)
text("D5 queda en TX0: parpadea con el log de la ROM; la consola del firmware va por USB.", 208, 112)
text("No alimentar la placa por el pin 6 de J2 con la bateria conectada.", 208, 115)

# ================================================================ PANTALLA
frame(395, 25, 584, 100)
text("PANTALLA TFT 3.5in, BUS DE 16 BITS, TOUCH SPI (igual que v0.8)", 398, 29, 2, True)
tft_nets = {"1": "GND", "2": "LCD_RS", "3": "LCD_WR", "4": "LCD_RD", "5": "ESP_EN"}
tft_nets.update({str(6 + i): f"LCD_D{i}" for i in range(16)})
tft_nets.update({"22": "+3V3", "23": "LCD_BL", "24": "+3V3", "25": "+3V3", "26": "GND", "27": "GND",
                 "28": None, "29": "TOUCH_MISO", "30": "TOUCH_MOSI", "31": "TOUCH_PEN", "32": "+3V3",
                 "33": "TOUCH_CS", "34": "TOUCH_CLK"})
place(TFT, "DS1", "LCD 3.5in 480x320 ILI9486 2x17", 445.0, 63.5, tft_nets, stub=7.62)
place(R, "R1", "10k", 500.0, 50.8, {"1": "+3V3", "2": "LCD_RD"})
text("CS a GND, RD alto con R1, RST al EN del modulo.", 510, 38)
text("VDD (24, 25) a +3V3 del LDO U9.", 510, 42)
text("5V (28) sin conectar.", 510, 46)
text("SDCS y F_CS a 3V3.", 510, 50)
text("BL en U6 GPB4, PEN en U6 GPB3.", 510, 54)

# ================================================================ EXPANSOR Y TECLADO
frame(395, 105, 584, 160)
text("EXPANSOR I2C Y TECLADO 4x4", 398, 109, 2, True)
place(KEY, "KP1", "Teclado membrana 4x4", 434.0, 132.0,
      {"1": "KEY_F1", "2": "KEY_F2", "3": "KEY_F3", "4": "KEY_F4",
       "5": "KEY_C1", "6": "KEY_C2", "7": "KEY_C3", "8": "KEY_C4"})
exp_nets = {"1": "SW_EQUIPO", "2": "SW_ARMADO", "3": "BTN_ACCION", "4": "TOUCH_PEN", "5": "LCD_BL",
            "6": "AMP_SD_CTRL", "7": "USB_PRESENTE", "8": None, "9": "+3V3", "10": "GND", "11": None,
            "12": "I2C_SCL", "13": "I2C_SDA", "14": None, "15": "GND", "16": "GND", "17": "GND",
            "18": "EXP_RESET", "19": None, "20": None}
exp_nets.update({str(21 + i): f"KEY_F{i + 1}" for i in range(4)})
exp_nets.update({str(25 + i): f"KEY_C{i + 1}" for i in range(4)})
place(EXP, "U6", "MCP23017-E/SP", 492.0, 130.81, exp_nets, stub=5.08)
for i, (rr, col) in enumerate((("R17", "KEY_C1"), ("R18", "KEY_C2"), ("R19", "KEY_C3"), ("R20", "KEY_C4"), ("R7", "EXP_RESET"))):
    place(R, rr, "10k", 535.0 + i * 7.62, 123.19, {"1": "+3V3", "2": col}, ref_at=(2.54, -1.27, 1), val_at=(2.54, 1.27, 1))
place(C, "C9", "100nF", 552.0, 147.32, {"1": "+3V3", "2": "GND"}, **HR)
text("U6 en 0x20. GPB5 = SD del amplificador (por R30), GPB6 = USB presente (R38/R39), GPB7 libre.", 398, 157)

# ================================================================ ENTRADAS
frame(205, 125, 390, 175)
text("ENTRADAS: SWITCHES Y PUSH BUTTON (igual que v0.8)", 208, 129, 2, True)
place(SPST, "SW1", "Selector de equipo", 233.68, 139.7, {"1": "SW_EQUIPO", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R2", "10k", 233.68, 154.94, {"1": "+3V3", "2": "SW_EQUIPO"}, **HR)
place(SPST, "SW2", "Armado de bomba (llave)", 292.1, 139.7, {"1": "SW_ARMADO", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R3", "10k", 292.1, 154.94, {"1": "+3V3", "2": "SW_ARMADO"}, **HR)
place(PUSH, "SW3", "Push button de accion", 350.52, 139.7, {"1": "BTN_ACCION", "2": "GND"}, ref_at=H[0], val_at=H[1])
place(R, "R4", "10k", 350.52, 154.94, {"1": "+3V3", "2": "BTN_ACCION"}, **HR)
place(C, "C1", "100nF", 350.52, 165.1, {"1": "BTN_ACCION", "2": "GND"}, **HR)
text("Pull-ups externos de 10k. Switch cerrado = nivel bajo. Se leen en U6 (GPB0 a GPB2).", 208, 172)

# ================================================================ TIRAS
frame(395, 165, 584, 230)
text("TIRAS LED RGB WS2812B (igual que v0.8)", 398, 169, 2, True)
place(BUF, "U5", "74AHCT125", 425.0, 190.5,
      {"1": "GND", "2": "LED_TIRA", "3": "TIRA1_5V", "4": "GND", "5": "GND", "6": None,
       "7": "GND", "8": None, "9": "GND", "10": "GND", "11": None, "12": "GND", "13": "GND", "14": "+5V"})
place(R, "R5", "330", 470.0, 182.88, {"1": "TIRA1_5V", "2": "TIRA1_DIN"}, **HR)
place(R, "R8", "330", 470.0, 203.2, {"1": "TIRA1_DOUT", "2": "TIRA2_DIN"}, **HR)
place(TIRA, "DS2", "Tira WS2812B 15 LEDs", 515.0, 182.88, {"1": "+5V", "2": "TIRA1_DIN", "3": "GND", "4": "TIRA1_DOUT"})
place(TIRA, "DS3", "Tira WS2812B 15 LEDs", 515.0, 203.2, {"1": "+5V", "2": "TIRA2_DIN", "3": "GND", "4": None})
place(CP, "C8", "1000uF", 555.0, 193.04, {"1": "+5V", "2": "GND"})
place(C, "C7", "100nF", 570.0, 193.04, {"1": "+5V", "2": "GND"})
text("Dato en GPIO3 (RMT), U5 lo sube a 5 V. LEDs 0-14 en DS2, 15-29 en DS3. Firmware limita las tiras a 600 mA.", 398, 224)

# ================================================================ AUDIO
frame(395, 235, 584, 320)
text("AUDIO: MAX98357A SUELTO (TQFN-16) Y BOCINA 4 OHM", 398, 239, 2, True)
place(AMPIC, "U4", "MAX98357AETE+", 430.0, 268.0,
      {"1": "I2S_DIN", "16": "I2S_BCLK", "14": "I2S_LRC", "4": "AMP_SD", "2": "GND",
       "7": "+5V", "8": "+5V", "3": "GND", "11": "GND", "15": "GND", "17": "GND",
       "9": "SPK_P", "10": "SPK_N", "5": None, "6": None, "12": None, "13": None},
      ref_at=(-7.62, -16.51, 1), val_at=(15.24, 15.24, 1))
place(R, "R30", "634k 1%", 470.0, 280.0, {"1": "AMP_SD_CTRL", "2": "AMP_SD"}, **HR)
place(CONN2, "J4", "Bocina", 478.0, 260.0, {"1": "SPK_P", "2": "SPK_N"}, ref_at=(0, -5.08, 1), val_at=(0, 7.62, 1))
place(SPK, "LS1", "Bocina 4 ohm 3-5 W", 500.0, 260.0, {"1": "SPK_P", "2": "SPK_N"},
      ref_at=(5.08, -6.35, 1), val_at=(5.08, 8.89, 1))
place(CP, "C3", "470uF 10V", 530.0, 262.0, {"1": "+5V", "2": "GND"})
place(C, "C13", "10uF", 545.0, 262.0, {"1": "+5V", "2": "GND"})
place(C, "C4", "100nF", 558.0, 262.0, {"1": "+5V", "2": "GND"})
text("GAIN_SLOT a GND = 12 dB (3.2 W en 4 ohm a 5 V, 10% THD). SD_MODE por R30 634k desde U6 GPB5 (3.3 V):", 398, 306)
text("GPB5 alto = (L+R)/2, GPB5 bajo = apagado. C13 10uF y C4 100nF pegados a VDD (7, 8). Pad expuesto a GND.", 398, 309)
text("Salida sin filtro (clase D filterless). Cable corto y trenzado a la bocina.", 398, 312)

# ================================================================ ALIMENTACION
frame(10, 180, 390, 355)
text("ALIMENTACION (OPCION C): 1S2P 18650, PROTECCION, CARGA USB-C CON REPARTO DE CARGA, 5.1 V Y 3.3 V", 13, 184, 2, True)
# Celdas y protección
place(BAT, "BT1", "18650", 40.64, 203.2, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(BAT, "BT2", "18650", 40.64, 220.98, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(PROT, "U10", "DW01A", 96.52, 205.74, {"5": "DW_VCC", "6": "BAT_NEG", "2": "DW_CS", "1": "PROT_OD", "3": "PROT_OC", "4": None})
place(DFET, "Q1", "FS8205A", 96.52, 248.92,
      {"1": "PROT_D", "8": "PROT_D", "2": "BAT_NEG", "3": "BAT_NEG", "4": "PROT_OD", "7": "GND", "6": "GND", "5": "PROT_OC"})
place(DFET, "Q2", "FS8205A", 96.52, 279.4,
      {"1": "PROT_D", "8": "PROT_D", "2": "BAT_NEG", "3": "BAT_NEG", "4": "PROT_OD", "7": "GND", "6": "GND", "5": "PROT_OC"})
place(R, "R31", "100", 25.4, 264.16, {"1": "VBAT_CELDA", "2": "DW_VCC"})
place(C, "C14", "100nF", 38.1, 264.16, {"1": "DW_VCC", "2": "BAT_NEG"})
place(R, "R32", "1k", 50.8, 264.16, {"1": "DW_CS", "2": "GND"})
# Medicion de bateria
place(R, "R13", "100k", 25.4, 312.42, {"1": "VBAT_CELDA", "2": "VBAT_ADC"})
place(R, "R14", "100k", 38.1, 312.42, {"1": "VBAT_ADC", "2": "GND"})
place(C, "C2", "100nF", 50.8, 312.42, {"1": "VBAT_ADC", "2": "GND"})
# Cargador
place(CHG, "U2", "TP4056", 162.56, 208.28,
      {"4": "VBUS_USB", "8": "VBUS_USB", "1": "GND", "2": "CHG_PROG", "3": "GND", "9": "GND",
       "5": "VBAT_CELDA", "7": "CHG_LED_R", "6": "CHG_LED_G"})
place(R, "R33", "1.2k", 139.7, 264.16, {"1": "CHG_PROG", "2": "GND"})
place(C, "C15", "10uF", 149.86, 264.16, {"1": "VBUS_USB", "2": "GND"})
place(C, "C16", "10uF", 160.02, 264.16, {"1": "VBAT_CELDA", "2": "GND"})
place(R, "R34", "1k", 172.72, 264.16, {"1": "VBUS_USB", "2": "CHG_LED_RA"})
place(LED, "D6", "Rojo", 180.34, 307.34, {"1": "CHG_LED_R", "2": "CHG_LED_RA"}, rot=90, ref_at=(3.81, -1.27), val_at=(3.81, 1.27))
place(R, "R35", "1k", 195.58, 264.16, {"1": "VBUS_USB", "2": "CHG_LED_GA"})
place(LED, "D7", "Verde", 203.2, 307.34, {"1": "CHG_LED_G", "2": "CHG_LED_GA"}, rot=90, ref_at=(3.81, -1.27), val_at=(3.81, 1.27))
# Reparto de carga
place(SCHOT, "D8", "SS34", 243.84, 200.66, {"2": "VBUS_USB", "1": "VSYS"}, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(PFET, "Q3", "AO3401A", 243.84, 238.76, {"1": "VBUS_USB", "3": "VBAT_CELDA", "2": "VSYS"})
place(R, "R36", "10k", 226.06, 289.56, {"1": "VBUS_USB", "2": "GND"})
place(R, "R38", "47k", 238.76, 289.56, {"1": "VBUS_USB", "2": "USB_PRESENTE"})
place(R, "R39", "100k", 251.46, 289.56, {"1": "USB_PRESENTE", "2": "GND"})
place(SCHOT, "D9", "SS34", 266.7, 320.04, {"2": "VBAT_CELDA", "1": "VSYS"}, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(SPST, "SW4", "Encendido (3 A)", 284.48, 205.74, {"1": "VSYS", "2": "VSYS_SW"}, ref_at=H[0], val_at=H[1])
# Elevador 5.1 V
place(BOOST, "U8", "TPS61022", 345.44, 215.9,
      {"7": "VSYS_SW", "5": "VSYS_SW", "6": "GND", "1": "GND", "2": "BOOST_SW", "3": "+5V", "4": "FB_5V"},
      ref_at=(-12.7, -12.7, 1), val_at=(0, 17.78, 1))
place(IND, "L1", "1uH Isat 8A", 299.72, 236.22, {"1": "VSYS_SW", "2": "BOOST_SW"}, rot=90, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1))
place(C, "C17", "22uF", 284.48, 269.24, {"1": "VSYS_SW", "2": "GND"})
place(C, "C18", "22uF", 317.5, 269.24, {"1": "+5V", "2": "GND"})
place(C, "C19", "22uF", 330.2, 269.24, {"1": "+5V", "2": "GND"})
place(C, "C20", "22uF", 342.9, 269.24, {"1": "+5V", "2": "GND"})
place(R, "R15", "750k 1%", 360.68, 254.0, {"1": "+5V", "2": "FB_5V"})
place(R, "R16", "100k 1%", 373.38, 254.0, {"1": "FB_5V", "2": "GND"})
# LDO 3.3 V
place(LDO, "U9", "AP7361C-33E", 330.2, 309.88, {"1": "VSYS_SW", "2": "GND", "3": "+3V3"},
      ref_at=(0, -5.08, 1), val_at=(12.7, 10.16, 1))
place(C, "C21", "10uF", 299.72, 312.42, {"1": "VSYS_SW", "2": "GND"})
place(C, "C22", "10uF", 360.68, 312.42, {"1": "+3V3", "2": "GND"})
text("BAT_NEG es el negativo de las celdas; GND es P-, despues de los MOSFET de proteccion. Q1 y Q2 en paralelo: disparo por sobrecorriente ~5 A.", 13, 336)
text("U2: R33 1.2k = 1 A de carga. D6 rojo = cargando, D7 verde = carga terminada. TEMP a GND (sin termistor).", 13, 339)
text("Con USB: VSYS sale de VBUS por D8 y Q3 se abre (gate en VBUS). Sin USB: R36 baja el gate y Q3 conecta la bateria a VSYS.", 13, 342)
text("SW4 corta VSYS (la carga sigue con SW4 apagado). U8: Vout = 0.6 V x (1 + R15/R16) = 5.1 V, MODE a GND (PFM a baja carga).", 13, 345)
text("U9 da 3.3 V a 1 A desde VSYS_SW. R13/R14: 4.2 V -> 2.1 V en GPIO10. R38/R39: USB presente a U6 GPB6 (3.4 V con 5 V).", 13, 348)

# ================================================================ NOTAS
text("Opcion C (v0.9): todo discreto para PCB propia. Sin modulos comprados: ni DevKit, ni LUORNG V8, ni tarjeta MAX98357A.", 13, 362, 1.5, True)
text("Sin verificar en hoja de datos: pines de FS8205A y DW01A y su umbral de sobrecorriente, patillaje SOT-223 de AP7361C-33E. Ver README de opcion_c.", 13, 366, 1.5)

# ---------------------------------------------------------------- salida
used = {b[2] for b in BOM}
lib_txt = "\n".join(v[0] for k, v in LIB.items() if k in used)
out = f"""(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A2")
  (title_block
    (title "Herramienta multiproposito para airsoft")
    (date "2026-11-08")
    (rev "v0.9-C")
    (comment 1 "Opcion C: ESP32-S3-WROOM-1 N16R8 en PCB propia, sin modulos comprados")
    (comment 2 "Modos: bandera, zona, rey de la colina, bomba, extraccion")
    (comment 3 "Conexiones por etiqueta de red: etiquetas iguales = mismo nodo")
    (comment 4 "Alimentacion: TP4056 + DW01A/FS8205A + TPS61022 + AP7361C, USB-C nativo")
  )
  (lib_symbols
{lib_txt}
  )
{chr(10).join(ITEMS)}
  (sheet_instances (path "/" (page "1")))
)
"""
open(sys.argv[1], "w").write(out)

# comprobación: toda red debe aparecer al menos dos veces
cnt = Counter(re.findall(r'\(label "([^"]+)"', out))
solas = sorted(n for n, k in cnt.items() if k < 2)
if solas:
    print("aviso: redes con una sola etiqueta:", solas, file=sys.stderr)

import csv
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Referencia", "Valor", "Simbolo"])
    for ref, val, lid, _ in sorted(BOM, key=lambda b: (re.sub(r"\d", "", b[0]), int(re.sub(r"\D", "", b[0])))):
        w.writerow([ref, val, lid])
print("ok", len(ITEMS), "elementos,", len(cnt), "redes")
