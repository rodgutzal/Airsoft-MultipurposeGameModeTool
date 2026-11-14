#!/usr/bin/env python3
"""Genera el esquematico v0.9 opcion C (KiCad 7) de la herramienta de airsoft.

Opcion C: sin modulos comprados. Modulo ESP32-S3-WROOM-1 N16R8 sin tarjeta de
desarrollo, cargador TP4056, proteccion DW01A + FS8205A, reparto de carga USB/bateria,
elevador sincrono TPS61022 a 5.1 V, LDO AP7361C a 3.3 V, MAX98357A suelto (TQFN-16),
USB-C al USB nativo y header UART0.

Uso: gen_sch_c.py salida.kicad_sch bom.csv
v0.9.1: dentro de cada bloque las conexiones se dibujan con cable (wire()), con cada
capacitor unido a los pines que desacopla. Las etiquetas de red quedan solo para las
señales que pasan de un bloque a otro y para los rieles (+3V3, +5V, GND).
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
        for i, e in enumerate(lst):
            if e is None:
                continue
            num, pname = e
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


P = {}  # "REF.PIN" -> (x, y) de la punta del pin
LOCAL = {}  # "REF.PIN" -> red, pines que se cablean a mano dentro del bloque


def place(lid, ref, value, x, y, nets, stub=5.08, rot=0, fields=None, ref_at=None, val_at=None, local=(), mirror=False):
    """Coloca un símbolo y pone tramo + etiqueta en cada pin.
    nets: {num_pin: nombre_red | None (= no conectado)}
    local: pines sin tramo ni etiqueta; se unen con wire() a otros pines del mismo bloque.
    local="*" deja todos los pines conectados sin etiqueta."""
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
    fa = 0 if rot == 180 else (360 - rot) % 360
    if rot == 180 and rj == "(justify left)":
        rj = vj = "(justify right)"  # KiCad invierte la justificación con el símbolo girado 180°
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
        f'(symbol (lib_id "{lid}") (at {x} {y} {rot}){" (mirror x)" if mirror else ""} (unit 1) (in_bom yes) (on_board {onb}) (dnp no) (uuid {uid()})\n'
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
        elif rot == 180:
            px, py, a = -px, -py, (a + 180) % 360
        if mirror:  # espejo sobre el eje X (de arriba abajo)
            py, a = -py, (360 - a) % 360
        sx, sy = round(x + px, 2), round(y - py, 2)  # el eje Y de la librería apunta hacia arriba
        P[f"{ref}.{num}"] = (sx, sy)
        # dirección del tramo: opuesta a la dirección hacia el cuerpo
        d = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}[a]
        net = nets.get(num, "__NC__")
        if net is None or net == "__NC__":
            if net == "__NC__" and num not in nets:
                print(f"aviso: {ref} pin {num} sin asignar", file=sys.stderr)
            ITEMS.append(f"(no_connect (at {round(sx,2)} {round(sy,2)}) (uuid {uid()}))")
            continue
        if local == "*" or num in local:
            LOCAL[f"{ref}.{num}"] = net
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


SEGS = []  # tramos de cable dibujados con wire()/stub()


def _seg(a, b):
    if a == b:
        return
    SEGS.append((a, b))


def pt(p):
    if isinstance(p, str):
        return P[p]
    return (snap(p[0]), snap(p[1]))


def wire(*pts, v=False):
    """Cable entre pines ("U5.14") o puntos (x, y). Si dos puntos seguidos no están
    alineados se hace un codo: primero horizontal, o primero vertical con v=True."""
    q = [pt(p) for p in pts]
    for a, b in zip(q, q[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            m = (a[0], b[1]) if v else (b[0], a[1])
            _seg(a, m)
            _seg(m, b)
        else:
            _seg(a, b)


def X(p):
    return pt(p)[0]


def Y(p):
    return pt(p)[1]


def label(net, p, d):
    """Etiqueta de red en el punto p; d = hacia dónde se escribe: L, R, U, D."""
    x, y = pt(p)
    la = {"L": 180, "R": 0, "U": 90, "D": 270}[d]
    just = "right" if la in (180, 270) else "left"
    ITEMS.append(
        f'(label "{net}" (at {x} {y} {la}) (fields_autoplaced) '
        f"(effects (font (size 1.27 1.27)) (justify {just})) (uuid {uid()}))"
    )


def stub(p, d, net, n=5.08):
    """Tramo corto desde p hacia d con etiqueta al final (red que sale del bloque)."""
    x, y = pt(p)
    dx, dy = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}[d]
    e = (round(x + dx * n, 2), round(y + dy * n, 2))
    _seg((x, y), e)
    label(net, e, d)


def _on(p, a, b):
    """p está en el interior del tramo a-b."""
    return (p not in (a, b) and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
            and (a[0] == b[0] == p[0] or a[1] == b[1] == p[1]))


def junctions():
    """Parte los tramos en cada derivación (KiCad solo une cables por sus extremos),
    escribe los cables y pone punto de unión donde se juntan tres o más."""
    ends = {q for s in SEGS for q in s}
    pins = set(P.values())
    cuts = ends | pins
    segs = []
    for a, b in SEGS:
        mid = sorted((q for q in cuts if _on(q, a, b)), key=lambda q: abs(q[0] - a[0]) + abs(q[1] - a[1]))
        pts = [a] + mid + [b]
        segs += list(zip(pts, pts[1:]))
    cnt = Counter()
    for a, b in segs:
        cnt[a] += 1
        cnt[b] += 1
        ITEMS.append(
            f"(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) "
            f"(stroke (width 0) (type default)) (uuid {uid()}))"
        )
    for p in pins:
        if p in cnt:
            cnt[p] += 1
    for (x, y), k in cnt.items():
        if k >= 3:
            ITEMS.append(f"(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))")


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
    [(str(n), f"GPB{n - 1}") for n in range(1, 9)] + [("12", "SCL"), ("13", "SDA"), ("11", "NC"),
     ("14", "NC"), ("9", "VDD"), ("10", "VSS")],
    [(str(n), f"GPA{n - 21}") for n in range(21, 29)] + [("20", "INTA"), ("19", "INTB"), ("18", "RESET"),
     ("17", "A2"), ("16", "A1"), ("15", "A0")],
    width=25.4, desc="Expansor de 16 E/S por I2C, DIP-28, 3.3 V",
)
KEY = use_box("Teclado_4x4", "KP",
              [(str(i + 1), f"F{i+1}") for i in range(4)] + [(str(i + 5), f"C{i+1}") for i in range(4)],
              [], width=12.7, desc="Teclado matricial de membrana 4x4")
BUF = use_box("74AHCT125", "U",
              [("2", "1A"), ("1", "~1OE"), ("5", "2A"), ("4", "~2OE"), ("9", "3A"), ("10", "~3OE"), ("12", "4A"), ("13", "~4OE")],
              [("14", "VCC"), ("7", "GND"), None, None, ("3", "1Y"), ("6", "2Y"), ("8", "3Y"), ("11", "4Y")],
              width=15.24, desc="Cuatro buffers con entrada TTL (VIH 2 V) alimentados a 5 V, DIP-14 (SN74AHCT125N)")
TIRA = use_box("Tira_WS2812B", "DS",
               [("2", "DIN"), None, ("4", "DOUT")], [("1", "+5V"), ("3", "GND")],
               width=15.24, desc="Tira LED RGB direccionable WS2812B 5 V")
CHG = use_box("TP4056", "U",
              [("4", "VCC"), ("8", "CE"), ("2", "PROG"), ("1", "TEMP"), ("3", "GND"), ("9", "EP")],
              [("7", "~CHRG"), ("6", "~STDBY"), None, None, ("5", "BAT")],
              width=17.78, desc="Cargador lineal Li-ion 1 A, ESOP-8 con pad expuesto")
PROT = use_box("DW01A", "U",
               [("5", "VCC"), ("6", "GND")],
               [("1", "OD"), ("2", "CS"), ("3", "OC"), ("4", "TD")],
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
LOCAL_U1 = ("1", "40", "41", "2", "3", "15", "26", "27", "32", "35", "37", "16")
place(WROOM, "U1", "ESP32-S3-WROOM-1-N16R8", 110.0, 85.0, mcu_nets, stub=7.62,
      ref_at=(-12.7, -30.48, 1), val_at=(0, 50.8, 1), local=LOCAL_U1)
# 3V3 del módulo: C11 y C12 entre el pin 2 y el GND del módulo (pin 1/40/41)
Y3 = 40.64
place(C, "C11", "22uF", 137.16, Y3 + 3.81, {"1": "+3V3", "2": "GND"}, local="*")
place(C, "C12", "100nF", 149.86, Y3 + 3.81, {"1": "+3V3", "2": "GND"}, local="*")
wire("U1.2", (110.49, Y3), (149.86, Y3))
wire("C11.1", (137.16, Y3)); wire("C12.1", (149.86, Y3))
label("+3V3", (115.57, Y3), "R")
XG, YG = 195.58, 129.54          # tierra del bloque, vuelve al pin GND del módulo
wire("C11.2", (137.16, 50.8), (XG, 50.8), (XG, YG), (110.49, YG), "U1.1")
wire("C12.2", (149.86, 50.8))
label("GND", (182.88, YG), "R")
# EN: R22 a 3V3, C10 a GND, SW5 (RESET) a GND
YE = 50.8
wire("U1.3", (88.9, 62.23), (88.9, YE), (33.02, YE))
place(R, "R22", "10k", 78.74, YE - 3.81, {"1": "+3V3", "2": "ESP_EN"}, local=("2",))
place(C, "C10", "1uF", 68.58, YE + 3.81, {"1": "ESP_EN", "2": "GND"}, local=("1",))
place(PUSH, "SW5", "RESET", 27.94, YE, {"1": "ESP_EN", "2": "GND"}, rot=180, ref_at=H[0], val_at=H[1], local=("1",))
label("ESP_EN", (38.1, YE), "R")
# GPIO0 (I2S_DIN): R23 a 3V3 y SW6 (BOOT) a GND
YB = 67.31
wire("U1.27", (33.02, YB))
place(R, "R23", "10k", 55.88, YB - 3.81, {"1": "+3V3", "2": "I2S_DIN"}, local=("2",))
wire("R23.2", (55.88, YB))
place(PUSH, "SW6", "BOOT", 27.94, YB, {"1": "I2S_DIN", "2": "GND"}, rot=180, ref_at=H[0], val_at=H[1], local=("1",))
label("I2S_DIN", (38.1, YB), "R")
# GPIO3 (LED_TIRA): R6 a GND
YT = 74.93
place(R, "R6", "100k", 50.8, YT, {"1": "LED_TIRA", "2": "GND"}, local=("1",), rot=270, ref_at=HR["ref_at"], val_at=HR["val_at"])
wire("U1.15", "R6.1")
label("LED_TIRA", (66.04, YT), "R")
# GPIO43: R21 y D5 (LED de estado) al GND del bloque
place(R, "R21", "330", 165.1, 62.23, {"1": "LED_ESTADO", "2": "LED_ESTADO_A"}, local="*", **HR)
place(LED, "D5", "Verde 5 mm", 177.8, 62.23, {"1": "GND", "2": "LED_ESTADO_A"}, rot=180,
      ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1), local="*")
wire("U1.37", "R21.1"); wire("R21.2", "D5.2"); wire("D5.1", (XG, 62.23))
label("LED_ESTADO", (133.35, 62.23), "R")
# I2C: pull-ups R10 y R11 a 3V3
place(R, "R10", "4.7k", 162.56, 82.55, {"1": "+3V3", "2": "I2C_SDA"}, local=("2",))
place(R, "R11", "4.7k", 175.26, 82.55, {"1": "+3V3", "2": "I2C_SCL"}, local=("2",))
wire("U1.32", (162.56, 90.17), "R10.2")
wire("U1.35", (175.26, 97.79), "R11.2")
label("I2C_SDA", (133.35, 90.17), "R"); label("I2C_SCL", (133.35, 97.79), "R")
# GPIO45 (I2S_LRC) y GPIO46 (TOUCH_MOSI): pull-downs R24 y R9 al GND del bloque
place(R, "R24", "10k", 175.26, 115.57, {"1": "I2S_LRC", "2": "GND"}, local="*")
place(R, "R9", "100k", 162.56, 115.57, {"1": "TOUCH_MOSI", "2": "GND"}, local="*")
wire("U1.26", (175.26, 100.33), "R24.1"); wire("R24.2", (175.26, YG))
wire("U1.16", (162.56, 102.87), "R9.1"); wire("R9.2", (162.56, YG))
label("I2S_LRC", (133.35, 100.33), "R"); label("TOUCH_MOSI", (133.35, 102.87), "R")
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
      ref_at=(-2.54, -21.59, 1), val_at=(12.7, -21.59, 1),
      local=("A4", "A9", "B4", "B9", "A5", "B5", "A6", "B6", "A7", "B7"))
# VBUS: sube y pasa por C23 hacia U7 (pin 5); CC1/CC2 con R25/R26 a GND
YV, YGU = 33.02, 40.64
wire("J1.A4", (242.57, Y("J1.A4")), (242.57, YV), (289.56, YV))
label("VBUS_USB", (247.65, YV), "R")
place(R, "R25", "5.1k", 250.19, YGU + 3.81, {"1": "USB_CC1", "2": "GND"}, rot=180, local="*")
place(R, "R26", "5.1k", 262.89, YGU + 3.81, {"1": "USB_CC2", "2": "GND"}, rot=180, local="*")
wire("J1.A5", (250.19, Y("J1.A5")), "R25.1")
wire("J1.B5", (262.89, Y("J1.B5")), "R26.1")
place(C, "C23", "10uF", 275.59, YV + 3.81, {"1": "VBUS_USB", "2": "GND"}, local="*")
wire("R25.2", "R26.2", "C23.2", (280.67, YGU))
label("GND", (280.67, YGU), "R")
# D-/D+: se unen las dos caras del conector, pasan por U7 y por R28/R27 al módulo
wire("J1.A7", (242.57, Y("J1.A7")), (242.57, Y("J1.B7")), "J1.B7")
wire("J1.A6", (245.11, Y("J1.A6")), (245.11, Y("J1.B6")), "J1.B6")
place(ESD, "U7", "USBLC6-2SC6", 289.56, Y("J1.A7"),
      {"1": "USB_DN", "6": "USB_DN", "3": "USB_DP", "4": "USB_DP", "2": "GND", "5": "VBUS_USB"},
      ref_at=(-8.89, 8.89, 1), val_at=(-8.89, 11.43, 1), local=("1", "2", "3", "4", "5", "6"))
wire((242.57, Y("J1.A7")), "U7.1")
wire((245.11, Y("J1.A6")), (279.4, Y("J1.A6")), (279.4, Y("U7.3")), "U7.3")
wire((289.56, YV), "U7.5")
place(R, "R28", "22", 304.8, Y("U7.6"), {"1": "USB_DN", "2": "USB_DN_MCU"}, local=("1",), **HR)
place(R, "R27", "22", 304.8, 69.85, {"1": "USB_DP", "2": "USB_DP_MCU"}, local=("1",), **HR)
wire("U7.6", "R28.1")
wire("U7.4", (299.72, Y("U7.4")), (299.72, 69.85), "R27.1")
# los pines 1-6 y 3-4 del USBLC6 son la misma línea (paso directo): se unen por fuera
wire((281.94, Y("U7.1")), (281.94, 49.53), (297.18, 49.53), (297.18, Y("U7.6")))
wire((281.94, Y("U7.3")), (281.94, 66.04), (299.72, 66.04))
wire("U7.2", (289.56, 71.12))
label("GND", (289.56, 71.12), "D")
# J2: R29 desde el LED de estado a TX0, R37 pull-up de RX0 al 3V3 del pin 6
place(CONN6, "J2", "UART0 / BOOT 1x6", 365.76, 80.01,
      {"1": "GND", "2": "UART_TX0", "3": "UART_RX0", "4": "ESP_EN", "5": "I2S_DIN", "6": "+3V3"},
      ref_at=(0, -11.43, 1), val_at=(0, 11.43, 1), local=("2", "3", "6"))
place(R, "R29", "499", 330.2, Y("J2.2"), {"1": "LED_ESTADO", "2": "UART_TX0"}, local=("2",), rot=90,
      ref_at=(0, -5.08, 1), val_at=(0, -2.54, 1))
wire("R29.2", "J2.2")
place(R, "R37", "10k", 340.36, 83.82, {"1": "+3V3", "2": "UART_RX0"}, rot=180, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire("J2.3", (340.36, Y("J2.3")), "R37.2")
wire("J2.6", (340.36, Y("J2.6")), "R37.1")
wire((340.36, Y("J2.3")), (337.82, Y("J2.3")))
label("UART_RX0", (337.82, Y("J2.3")), "L")
wire((340.36, Y("J2.6")), (337.82, Y("J2.6")))
label("+3V3", (337.82, Y("J2.6")), "L")
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
place(TFT, "DS1", "LCD 3.5in 480x320 ILI9486 2x17", 445.0, 63.5, tft_nets, stub=7.62, local=("4",))
# RD (pin 4) alto con R1
place(R, "R1", "10k", 505.0, Y("DS1.4") - 3.81, {"1": "+3V3", "2": "LCD_RD"}, local=("2",))
wire("DS1.4", (X("R1.2"), Y("DS1.4")), "R1.2")
text("CS a GND, RD alto con R1, RST al EN del modulo.", 515, 38)
text("VDD (24, 25) a +3V3 del LDO U9.", 515, 42)
text("5V (28) sin conectar.", 515, 46)
text("SDCS y F_CS a 3V3.", 515, 50)
text("BL en U6 GPB4, PEN en U6 GPB3.", 515, 54)

# ================================================================ EXPANSOR Y TECLADO
frame(395, 105, 584, 180)
text("EXPANSOR I2C Y TECLADO 4x4", 398, 109, 2, True)
exp_nets = {"1": "SW_EQUIPO", "2": "SW_ARMADO", "3": "BTN_ACCION", "4": "TOUCH_PEN", "5": "LCD_BL",
            "6": "AMP_SD_CTRL", "7": "USB_PRESENTE", "8": None, "9": "+3V3", "10": "GND", "11": None,
            "12": "I2C_SCL", "13": "I2C_SDA", "14": None, "15": "GND", "16": "GND", "17": "GND",
            "18": "EXP_RESET", "19": None, "20": None}
exp_nets.update({str(21 + i): f"KEY_F{i + 1}" for i in range(4)})
exp_nets.update({str(25 + i): f"KEY_C{i + 1}" for i in range(4)})
place(EXP, "U6", "MCP23017-E/SP", 491.49, 143.51, exp_nets, stub=5.08,
      local=[str(n) for n in range(21, 29)] + ["9", "10", "15", "16", "17", "18"])
# Teclado: GPA0-GPA7 directo a KP1, pull-ups R17-R20 en las columnas
place(KEY, "KP1", "Teclado membrana 4x4", 566.42, Y("U6.21") + 8.89,
      {"1": "KEY_F1", "2": "KEY_F2", "3": "KEY_F3", "4": "KEY_F4",
       "5": "KEY_C1", "6": "KEY_C2", "7": "KEY_C3", "8": "KEY_C4"}, local="*")
for i in range(8):
    wire(f"U6.{21 + i}", f"KP1.{i + 1}")
YP = 114.3
for i, rr in enumerate(("R17", "R18", "R19", "R20")):
    xr = 515.62 + i * 10.16
    place(R, rr, "10k", xr, YP + 3.81, {"1": "+3V3", "2": f"KEY_C{i + 1}"}, local="*")
    wire(f"{rr}.2", (xr, Y(f"KP1.{i + 5}")))
wire("R17.1", "R20.1")
label("+3V3", "R17.1", "L")
# RESET con R7 a 3V3; A0-A2 a GND (dirección 0x20)
place(R, "R7", "10k", 525.78, Y("U6.18"), {"1": "+3V3", "2": "EXP_RESET"}, rot=270, local="*",
      ref_at=HR["ref_at"], val_at=HR["val_at"])
wire("U6.18", "R7.2")
stub("R7.1", "R", "+3V3", 2.54)
wire("U6.17", (509.27, Y("U6.17")), (509.27, Y("U6.15")), "U6.15")
wire("U6.16", (509.27, Y("U6.16")))
stub((509.27, Y("U6.15")), "D", "GND", 2.54)
# C9 entre VDD (9) y VSS (10) de U6
place(C, "C9", "100nF", 463.55, Y("U6.9") + 3.81, {"1": "+3V3", "2": "GND"}, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire("U6.9", (458.47, Y("U6.9")))
wire("U6.10", (468.63, Y("U6.10")), (468.63, Y("C9.2")), "C9.2")
label("+3V3", (458.47, Y("U6.9")), "L")
stub("C9.2", "L", "GND", 5.08)
text("U6 en 0x20. GPB5 = SD del amplificador (por R30), GPB6 = USB presente (R38/R39), GPB7 libre.", 398, 176)

# ================================================================ ENTRADAS
frame(205, 125, 390, 175)
text("ENTRADAS: SWITCHES Y PUSH BUTTON (igual que v0.8)", 208, 129, 2, True)
YI = 152.4
for x0, sw, sym, swv, rr, net in ((210.82, "SW1", SPST, "Selector de equipo", "R2", "SW_EQUIPO"),
                                  (269.24, "SW2", SPST, "Armado de bomba (llave)", "R3", "SW_ARMADO"),
                                  (327.66, "SW3", PUSH, "Push button de accion", "R4", "BTN_ACCION")):
    place(sym, sw, swv, x0 + 43.18, YI, {"1": net, "2": "GND"}, ref_at=H[0], val_at=H[1], local="*")
    place(R, rr, "10k", x0 + 27.94, YI - 3.81, {"1": "+3V3", "2": net}, local=("2",))
    wire((x0 + 15.24, YI), f"{sw}.1")
    label(net, (x0 + 15.24, YI), "L")
    wire(f"{sw}.2", (X(f"{sw}.2") + 2.54, YI), (X(f"{sw}.2") + 2.54, YI + 7.62))
    label("GND", (X(f"{sw}.2") + 2.54, YI + 7.62), "D")
place(C, "C1", "100nF", 327.66 + 20.32, YI + 3.81, {"1": "BTN_ACCION", "2": "GND"}, local=("1",),
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
text("Pull-ups externos de 10k. Switch cerrado = nivel bajo. Se leen en U6 (GPB0 a GPB2). C1 filtra rebotes de SW3.", 208, 168)

# ================================================================ TIRAS
frame(395, 185, 584, 255)
text("TIRAS LED RGB WS2812B (igual que v0.8)", 398, 189, 2, True)
place(BUF, "U5", "74AHCT125", 425.45, 213.36,
      {"1": "GND", "2": "LED_TIRA", "3": "TIRA1_5V", "4": "GND", "5": "GND", "6": None,
       "7": "GND", "8": None, "9": "GND", "10": "GND", "11": None, "12": "GND", "13": "GND", "14": "+5V"},
      local=("1", "3", "4", "5", "7", "9", "10", "12", "13", "14"))
# compuertas 2 a 4 sin uso y ~1OE: todos a GND por un mismo cable
XB = X("U5.1") - 2.54
for n in ("1", "5", "4", "9", "10", "12", "13"):
    wire(f"U5.{n}", (XB, Y(f"U5.{n}")))
wire((XB, Y("U5.1")), (XB, Y("U5.13")))
stub((XB, Y("U5.13")), "D", "GND", 2.54)
# C7 entre VCC (14) y GND (7) de U5
place(C, "C7", "100nF", X("U5.14") + 7.62, Y("U5.14") + 3.81, {"1": "+5V", "2": "GND"}, local="*")
wire("U5.14", "C7.1")
wire("U5.7", (X("U5.7") + 2.54, Y("U5.7")), (X("U5.7") + 2.54, Y("C7.2")), "C7.2")
wire("C7.1", (X("C7.1") + 5.08, Y("C7.1")))
label("+5V", (X("C7.1") + 5.08, Y("C7.1")), "R")
stub("C7.2", "R", "GND", 5.08)
# 1Y -> R5 -> DIN de DS2; DOUT de DS2 -> R8 -> DIN de DS3
place(TIRA, "DS2", "Tira WS2812B 15 LEDs", 500.38, Y("U5.3"),
      {"1": "+5V", "2": "TIRA1_DIN", "3": "GND", "4": "TIRA1_DOUT"}, local="*")
place(R, "R5", "330", 474.98, Y("U5.3"), {"1": "TIRA1_5V", "2": "TIRA1_DIN"}, local="*", **HR)
wire("U5.3", "R5.1"); wire("R5.2", "DS2.2")
place(TIRA, "DS3", "Tira WS2812B 15 LEDs", 500.38, Y("DS2.2") + 25.4,
      {"1": "+5V", "2": "TIRA2_DIN", "3": "GND", "4": None}, local=("1", "2", "3"))
place(R, "R8", "330", 482.6, Y("DS3.2") - 6.35, {"1": "TIRA1_DOUT", "2": "TIRA2_DIN"}, local="*",
      ref_at=(-3.81, -1.27, 1), val_at=(-3.81, 1.27, 1))
wire("DS2.4", (482.6, Y("DS2.4")), "R8.1")
wire("R8.2", (482.6, Y("DS3.2")), "DS3.2")
# C8 en el conector de DS2, entre +5V (1) y GND (3)
place(CP, "C8", "1000uF", X("DS2.1") + 10.16, Y("DS2.1") + 3.81, {"1": "+5V", "2": "GND"}, local="*")
wire("DS2.1", "C8.1")
wire("DS2.3", (X("DS2.3") + 5.08, Y("DS2.3")), (X("DS2.3") + 5.08, Y("C8.2")), "C8.2")
wire("C8.1", (X("C8.1") + 7.62, Y("C8.1")))
label("+5V", (X("C8.1") + 7.62, Y("C8.1")), "R")
stub("C8.2", "R", "GND", 7.62)
wire("DS3.1", (X("DS3.1") + 5.08, Y("DS3.1")))
label("+5V", (X("DS3.1") + 5.08, Y("DS3.1")), "R")
wire("DS3.3", (X("DS3.3") + 5.08, Y("DS3.3")))
label("GND", (X("DS3.3") + 5.08, Y("DS3.3")), "R")
text("Dato en GPIO3 (RMT), U5 lo sube a 5 V. LEDs 0-14 en DS2, 15-29 en DS3. Firmware limita las tiras a 600 mA.", 398, 250)

# ================================================================ AUDIO
frame(395, 260, 584, 345)
text("AUDIO: MAX98357A SUELTO (TQFN-16) Y BOCINA 4 OHM", 398, 264, 2, True)
place(AMPIC, "U4", "MAX98357AETE+", 452.12, 298.45,
      {"1": "I2S_DIN", "16": "I2S_BCLK", "14": "I2S_LRC", "4": "AMP_SD", "2": "GND",
       "7": "+5V", "8": "+5V", "3": "GND", "11": "GND", "15": "GND", "17": "GND",
       "9": "SPK_P", "10": "SPK_N", "5": None, "6": None, "12": None, "13": None},
      ref_at=(-7.62, -16.51, 1), val_at=(-27.94, 12.7, 1),
      local=("4", "2", "7", "8", "3", "11", "15", "17", "9", "10"))
YVA, YGA = Y("U4.7") - 5.08, Y("U4.3") + 7.62
# SD_MODE por R30; GAIN a GND
place(R, "R30", "634k 1%", X("U4.4") - 12.7, Y("U4.4"), {"1": "AMP_SD_CTRL", "2": "AMP_SD"}, local=("2",), **HR)
wire("R30.2", "U4.4")
wire("U4.2", (X("U4.2") - 2.54, Y("U4.2")), (X("U4.2") - 2.54, YGA), (X("U4.17"), YGA))
wire("U4.3", (X("U4.3"), YGA)); wire("U4.17", (X("U4.17"), YGA))
# VDD (7, 8): C3, C13 y C4 entre VDD y los GND de U4
XC = 548.64
wire("U4.7", (X("U4.7"), YVA), (XC + 20.32, YVA))
label("+5V", (X("U4.7") + 2.54, YVA), "R")
for i, (rr, val, sym) in enumerate((("C3", "470uF 10V", CP), ("C13", "10uF", C), ("C4", "100nF", C))):
    xc = XC + i * 10.16
    dy = YGA - (YVA + 3.81)
    place(sym, rr, val, xc, YVA + 3.81, {"1": "+5V", "2": "GND"}, local="*",
          ref_at=(0, dy + 2.54, 1), val_at=(0, dy + 5.08, 1))
    wire(f"{rr}.1", (xc, YVA)); wire(f"{rr}.2", (xc, YGA))
wire((X("U4.17"), YGA), (XC + 20.32, YGA))
label("GND", (X("U4.17") + 5.08, YGA), "R")
# Salida: J4 (conector de la bocina) y LS1
place(CONN2, "J4", "Bocina", 525.78, Y("U4.9"), {"1": "SPK_P", "2": "SPK_N"}, local="*",
      ref_at=(0, -7.62, 1), val_at=(0, -5.08, 1))
wire("U4.9", "J4.1"); wire("U4.10", "J4.2")
place(SPK, "LS1", "Bocina 4 ohm 3-5 W", 525.78, Y("J4.1") + 12.7, {"1": "SPK_P", "2": "SPK_N"}, local="*",
      ref_at=(5.08, -6.35, 1), val_at=(5.08, 8.89, 1))
wire((508.0, Y("U4.9")), (508.0, Y("LS1.1")), "LS1.1")
wire((502.92, Y("U4.10")), (502.92, Y("LS1.2")), "LS1.2")
text("GAIN_SLOT a GND = 12 dB (3.2 W en 4 ohm a 5 V, 10% THD). SD_MODE por R30 634k desde U6 GPB5 (3.3 V):", 398, 331)
text("GPB5 alto = (L+R)/2, GPB5 bajo = apagado. C13 10uF y C4 100nF pegados a VDD (7, 8). Pad expuesto a GND.", 398, 335)
text("Salida sin filtro (clase D filterless). Cable corto y trenzado a la bocina. J4 es el conector en la placa; LS1 va en el gabinete.", 398, 339)

# ================================================================ ALIMENTACION
frame(10, 180, 390, 355)
text("ALIMENTACION (OPCION C): 1S2P 18650, PROTECCION, CARGA USB-C CON REPARTO DE CARGA, 5.1 V Y 3.3 V", 13, 184, 2, True)
# ---- Celdas, protección y medición
frame(12, 189, 122, 330)
text("Celdas, proteccion y medicion", 14, 193, 1.5, True)
YVB = 205.74
place(BAT, "BT1", "18650", 25.4, YVB, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1), local="*")
place(BAT, "BT2", "18650", 25.4, YVB + 12.7, {"1": "VBAT_CELDA", "2": "BAT_NEG"}, rot=270, ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1), local="*")
wire("BT1.1", (33.02, YVB), (33.02, Y("BT2.1")), "BT2.1")
wire("BT1.2", (17.78, YVB), (17.78, Y("BT2.2")), "BT2.2")
wire((33.02, YVB), (99.06, YVB))                       # VBAT_CELDA
label("VBAT_CELDA", (50.8, YVB), "R")
place(PROT, "U10", "DW01A", 60.96, 222.25, {"5": "DW_VCC", "6": "BAT_NEG", "2": "DW_CS", "1": "PROT_OD", "3": "PROT_OC", "4": None},
      local="*")
# R31 de VBAT al VCC de U10; C14 entre VCC (5) y GND (6) de U10
place(R, "R31", "100", 44.45, Y("U10.5") - 3.81, {"1": "VBAT_CELDA", "2": "DW_VCC"}, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire("R31.1", (44.45, YVB)); wire("R31.2", "U10.5")
place(C, "C14", "100nF", 44.45, Y("U10.5") + 3.81, {"1": "DW_VCC", "2": "BAT_NEG"}, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
YBN = Y("C14.2")
wire("U10.6", (49.53, Y("U10.6")), (49.53, YBN), (17.78, YBN), (17.78, Y("BT2.2")))   # BAT_NEG
# CS por R32 a GND (P-)
place(R, "R32", "1k", 77.47, Y("U10.2") + 3.81, {"1": "DW_CS", "2": "GND"}, local=("1",))
wire("U10.2", "R32.1")
# FETs de protección en paralelo
place(DFET, "Q1", "FS8205A", 60.96, 241.3,
      {"1": "PROT_D", "8": "PROT_D", "2": "BAT_NEG", "3": "BAT_NEG", "4": "PROT_OD", "7": "GND", "6": "GND", "5": "PROT_OC"},
      local="*", ref_at=(-27.94, -1.27, 1), val_at=(-27.94, 1.27, 1))
place(DFET, "Q2", "FS8205A", 60.96, 261.62,
      {"1": "PROT_D", "8": "PROT_D", "2": "BAT_NEG", "3": "BAT_NEG", "4": "PROT_OD", "7": "GND", "6": "GND", "5": "PROT_OC"},
      local="*", ref_at=(-27.94, -1.27, 1), val_at=(-27.94, 1.27, 1))
XS1, XG1, XS2, XG2 = 46.99, 41.91, 72.39, 74.93
for q in ("Q1", "Q2"):
    wire(f"{q}.2", (XS1, Y(f"{q}.2"))); wire(f"{q}.3", (XS1, Y(f"{q}.3")))
    wire(f"{q}.4", (XG1, Y(f"{q}.4")))
    wire(f"{q}.7", (XS2, Y(f"{q}.7"))); wire(f"{q}.6", (XS2, Y(f"{q}.6")))
    wire(f"{q}.5", (XG2, Y(f"{q}.5")))
wire((XS1, YBN), (XS1, Y("Q2.3")))                       # S1 = BAT_NEG
wire((XS2, 231.14), (XS2, Y("Q2.6")))                    # S2 = GND (P-)
label("GND", (XS2, 231.14), "U")
wire((XG2, Y("Q1.5")), (XG2, Y("Q2.5")))
wire((XG1, Y("Q1.4")), (XG1, Y("Q2.4")))
# drenadores comunes (PROT_D): arriba de Q1, entre Q1 y Q2, y unión por la izquierda
wire("Q1.1", (50.8, Y("Q1.1")), (50.8, 233.68), (71.12, 233.68), (71.12, Y("Q1.8")), "Q1.8")
wire("Q2.1", (50.8, Y("Q2.1")), (50.8, 252.73), (71.12, 252.73), (71.12, Y("Q2.8")), "Q2.8")
wire((50.8, Y("Q1.1")), (50.8, 252.73))
# OD y OC de U10 a las compuertas
wire("U10.3", (XG2, Y("U10.3")), (XG2, Y("Q1.5")))
wire("U10.1", (87.63, Y("U10.1")), (87.63, 273.05), (XG1, 273.05), (XG1, Y("Q2.4")))
# Medición de batería: R13/R14 y C2
place(R, "R13", "100k", 99.06, YVB + 3.81, {"1": "VBAT_CELDA", "2": "VBAT_ADC"}, local="*")
place(R, "R14", "100k", 99.06, YVB + 11.43, {"1": "VBAT_ADC", "2": "GND"}, local="*")
place(C, "C2", "100nF", 111.76, YVB + 11.43, {"1": "VBAT_ADC", "2": "GND"}, local="*")
wire("R13.2", "C2.1", (116.84, Y("C2.1")))
label("VBAT_ADC", (116.84, Y("C2.1")), "U")
wire("R14.2", "C2.2")
stub((105.41, Y("C2.2")), "D", "GND", 2.54)

# ---- Cargador TP4056
frame(127, 189, 205, 330)
text("Cargador USB (TP4056)", 129, 193, 1.5, True)
YU = 200.66
place(CHG, "U2", "TP4056", 163.83, 228.6,
      {"4": "VBUS_USB", "8": "VBUS_USB", "1": "GND", "2": "CHG_PROG", "3": "GND", "9": "GND",
       "5": "VBAT_CELDA", "7": "CHG_LED_R", "6": "CHG_LED_G"}, local="*",
      ref_at=(0, -13.97, 1), val_at=(0, -11.43, 1))
XL, XR = X("U2.4"), X("U2.5")
YB2 = Y("U2.9") + 5.08                                   # tierra del cargador
wire((132.08, YU), (193.04, YU))                         # VBUS_USB
label("VBUS_USB", (132.08, YU), "R")
wire((XL - 5.08, YU), (XL - 5.08, Y("U2.4")), "U2.4")
wire("U2.8", (XL - 2.54, Y("U2.8")), (XL - 2.54, Y("U2.4")))
for n in ("1", "3", "9"):
    wire(f"U2.{n}", (XL - 2.54, Y(f"U2.{n}")))
wire((XL - 2.54, Y("U2.1")), (XL - 2.54, YB2))
# C15 entre VCC (4) y GND (3); R33 de PROG a GND
place(C, "C15", "10uF", 133.35, Y("U2.4") + 3.81, {"1": "VBUS_USB", "2": "GND"}, local="*")
wire((XL - 5.08, Y("U2.4")), "C15.1")
wire("C15.2", (133.35, YB2), (XR + 5.08, YB2))
place(R, "R33", "1.2k", XL - 7.62, Y("U2.2") + 3.81, {"1": "CHG_PROG", "2": "GND"}, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire("U2.2", "R33.1"); wire("R33.2", (XL - 2.54, Y("R33.2")))
stub((163.83, YB2), "D", "GND", 2.54)
# C16 entre BAT (5) y GND; BAT a VBAT_CELDA
place(C, "C16", "10uF", XR + 5.08, Y("U2.5") + 3.81, {"1": "VBAT_CELDA", "2": "GND"}, local="*")
wire("U2.5", (199.39, Y("U2.5")))
label("VBAT_CELDA", (199.39, Y("U2.5")), "D")
wire("C16.2", (XR + 5.08, YB2))
# LEDs de estado: VBUS -> R34/R35 -> LED -> ~CHRG / ~STDBY
for i, (rr, dd, col, pin) in enumerate((("R34", "D6", "Rojo", "7"), ("R35", "D7", "Verde", "6"))):
    xd = XR + 7.62 + i * 10.16
    place(R, rr, "1k", xd, YU + 3.81, {"1": "VBUS_USB", "2": f"CHG_LED_{col[0]}A"}, local="*")
    place(LED, dd, col, xd, YU + 11.43, {"1": f"CHG_LED_{col[0]}", "2": f"CHG_LED_{col[0]}A"}, rot=90,
          ref_at=(3.81, -1.27), val_at=(3.81, 1.27), local="*")
    wire(f"{rr}.2", f"{dd}.2")
    wire(f"U2.{pin}", (xd, Y(f"U2.{pin}")), f"{dd}.1")
wire((193.04, YU), "R35.1")

# ---- Reparto de carga USB/batería y encendido
frame(210, 189, 300, 330)
text("Reparto de carga y encendido", 212, 193, 1.5, True)
YBT, XVS = 241.3, 271.78
wire((213.36, YU), (260.35, YU))                         # VBUS_USB
label("VBUS_USB", (213.36, YU), "R")
place(SCHOT, "D8", "SS34", 264.16, YU, {"2": "VBUS_USB", "1": "VSYS"}, rot=180,
      ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1), local="*")
wire("D8.1", (XVS, YU), (XVS, YBT))                      # VSYS
place(PFET, "Q3", "AO3401A", 256.54, 223.52, {"1": "VBUS_USB", "3": "VBAT_CELDA", "2": "VSYS"}, mirror=True,
      local="*", ref_at=(5.08, -1.27), val_at=(5.08, 1.27))
wire("Q3.2", (XVS, Y("Q3.2")))
wire("Q3.1", (248.92, Y("Q3.1")), (248.92, YU))
place(R, "R36", "10k", 248.92, Y("Q3.1") + 3.81, {"1": "VBUS_USB", "2": "GND"}, local=("1",),
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire((213.36, YBT), (260.35, YBT))                       # VBAT_CELDA
label("VBAT_CELDA", (213.36, YBT), "R")
wire("Q3.3", (X("Q3.3"), YBT))
place(SCHOT, "D9", "SS34", 264.16, YBT, {"2": "VBAT_CELDA", "1": "VSYS"}, rot=180,
      ref_at=(0, -3.81, 1), val_at=(0, 3.81, 1), local="*")
wire("D9.1", (XVS, YBT))
place(SPST, "SW4", "Encendido (3 A)", 281.94, 220.98, {"1": "VSYS", "2": "VSYS_SW"}, ref_at=H[0], val_at=H[1], local="*")
wire((XVS, 220.98), "SW4.1")
wire("SW4.2", (294.64, 220.98), (294.64, 226.06))
label("VSYS_SW", (294.64, 226.06), "D")
# USB presente: R38/R39 desde VBUS hacia U6 GPB6
place(R, "R38", "47k", 223.52, YU + 3.81, {"1": "VBUS_USB", "2": "USB_PRESENTE"}, local="*",
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
place(R, "R39", "100k", 223.52, YU + 11.43, {"1": "USB_PRESENTE", "2": "GND"}, local=("1",),
      ref_at=(-5.08, -1.27, 1), val_at=(-5.08, 1.27, 1))
wire("R38.2", (226.06, Y("R38.2")))
label("USB_PRESENTE", (226.06, Y("R38.2")), "R")

# ---- 5.1 V (TPS61022) y 3.3 V (AP7361C)
frame(305, 189, 390, 330)
text("Elevador 5.1 V y regulador 3.3 V", 307, 193, 1.5, True)
YS, YG5 = 205.74, 241.3
place(BOOST, "U8", "TPS61022", 340.36, 223.52,
      {"7": "VSYS_SW", "5": "VSYS_SW", "6": "GND", "1": "GND", "2": "BOOST_SW", "3": "+5V", "4": "FB_5V"},
      ref_at=(-10.16, -10.16, 1), val_at=(0, 12.7, 1), local="*")
place(IND, "L1", "1uH Isat 8A", 341.63, YS, {"1": "VSYS_SW", "2": "BOOST_SW"}, rot=90,
      ref_at=(0, -6.35, 1), val_at=(0, -3.81, 1), local="*")
wire((309.88, YS), "L1.1")                               # VSYS_SW
label("VSYS_SW", (309.88, YS), "U")
wire("U8.7", (X("U8.7"), YS))
wire("U8.2", (X("U8.2"), YS), "L1.2")
wire("U8.5", (325.12, Y("U8.5")), (325.12, YS))
wire("U8.6", (327.66, Y("U8.6")), (327.66, YG5))
# C17 entre VIN y GND de U8
place(C, "C17", "22uF", 317.5, YS + 3.81, {"1": "VSYS_SW", "2": "GND"}, local="*")
wire("C17.2", (317.5, YG5), (386.08, YG5))
wire("U8.1", (X("U8.1"), YG5))
label("GND", (330.2, YG5), "R")
# VOUT: R15/R16 al FB, C18-C20 entre VOUT y GND de U8
wire("U8.3", (386.08, Y("U8.3")))
label("+5V", (364.49, Y("U8.3")), "R")
place(R, "R15", "750k 1%", 355.6, Y("U8.3") + 3.81, {"1": "+5V", "2": "FB_5V"}, local="*")
place(R, "R16", "100k 1%", 355.6, Y("U8.3") + 11.43, {"1": "FB_5V", "2": "GND"}, local="*")
wire("U8.4", (353.06, Y("U8.4")), (353.06, Y("R15.2")), "R15.2")
wire("R16.2", (355.6, YG5))
for i, rr in enumerate(("C18", "C19", "C20")):
    xc = 373.38 + i * 6.35
    place(C, rr, "22uF", xc, Y("U8.3") + 3.81, {"1": "+5V", "2": "GND"}, local="*",
          ref_at=(0, 16.51, 1), val_at=(0, 19.05, 1))
    wire(f"{rr}.2", (xc, YG5))
# LDO: C21 en VI, C22 en VO, ambos al GND de U9
YL, YGL = 271.78, 284.48
place(LDO, "U9", "AP7361C-33E", 345.44, YL, {"1": "VSYS_SW", "2": "GND", "3": "+3V3"},
      ref_at=(-6.35, -5.08, 1), val_at=(6.35, -5.08, 1), local="*")
wire((309.88, YS), (309.88, YL), "U9.1")
place(C, "C21", "10uF", 325.12, YL + 3.81, {"1": "VSYS_SW", "2": "GND"}, local="*")
place(C, "C22", "10uF", 365.76, YL + 3.81, {"1": "+3V3", "2": "GND"}, local="*")
wire("U9.3", (375.92, YL))
label("+3V3", (375.92, YL), "R")
wire("C21.2", (325.12, YGL), (365.76, YGL), "C22.2")
wire("U9.2", (X("U9.2"), YGL))
stub((345.44, YGL), "D", "GND", 2.54)

text("BAT_NEG es el negativo de las celdas; GND es P-, despues de los MOSFET de proteccion. Q1 y Q2 en paralelo: disparo por sobrecorriente ~5 A.", 13, 336)
text("U2: R33 1.2k = 1 A de carga. D6 rojo = cargando, D7 verde = carga terminada. TEMP a GND (sin termistor).", 13, 339)
text("Con USB: VSYS sale de VBUS por D8 y Q3 se abre (gate en VBUS). Sin USB: R36 baja el gate y Q3 conecta la bateria a VSYS.", 13, 342)
text("SW4 corta VSYS (la carga sigue con SW4 apagado). U8: Vout = 0.6 V x (1 + R15/R16) = 5.1 V, MODE a GND (PFM a baja carga).", 13, 345)
text("U9 da 3.3 V a 1 A desde VSYS_SW. R13/R14: 4.2 V -> 2.1 V en GPIO10. R38/R39: USB presente a U6 GPB6 (3.4 V con 5 V).", 13, 348)

# ================================================================ NOTAS
text("Opcion C (v0.9): todo discreto para PCB propia. Sin modulos comprados: ni DevKit, ni LUORNG V8, ni tarjeta MAX98357A.", 13, 362, 1.5, True)
text("Sin verificar en hoja de datos: pines de FS8205A y DW01A y su umbral de sobrecorriente, patillaje SOT-223 de AP7361C-33E. Ver README de opcion_c.", 13, 366, 1.5)

# ---------------------------------------------------------------- salida
junctions()
used = {b[2] for b in BOM}
lib_txt = "\n".join(v[0] for k, v in LIB.items() if k in used)
out = f"""(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A2")
  (title_block
    (title "Herramienta multiproposito para airsoft")
    (date "2026-11-14")
    (rev "v0.9.1-C")
    (comment 1 "Opcion C: ESP32-S3-WROOM-1 N16R8 en PCB propia, sin modulos comprados")
    (comment 2 "Modos: bandera, zona, rey de la colina, bomba, extraccion")
    (comment 3 "Dentro de cada bloque las conexiones van con cable; entre bloques, por etiqueta de red")
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
