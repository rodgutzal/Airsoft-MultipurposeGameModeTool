#!/usr/bin/env python3
"""Genera la PCB de partida (KiCad 7) de la opcion C a partir del netlist del esquematico.

Uso (desde Hw/pcb):
  kicad-cli sch export netlist --format kicadsexpr -o airsoft_tool_opcion_C.net \
      ../esquematico_v1/opcion_c/airsoft_tool_opcion_C.kicad_sch
  python3 gen_pcb.py airsoft_tool_opcion_C.net airsoft_tool_opcion_C.kicad_pcb

Hace: contorno de 145 x 80 mm, 4 capas, huellas colocadas por bloque segun la
propuesta pcb_propuesta_v0.1.md, redes asignadas a cada pad, contorno del modulo
LCD en Dwgs.User, plano de GND en In1.Cu y agujeros de montaje M3.
No hace: ruteo, relleno de zonas de potencia, verificacion de pines de la pantalla.
"""
import re
import sys

import pcbnew

FPDIR = "/usr/share/kicad/footprints"
W, H = 145.0, 80.0          # placa
LCD = (7.0, 5.0, 98.25, 56.34)  # x, y, ancho, alto del modulo DS1 (LCDWIKI MRB3503)

# ref: (x, y, rotacion, cara)  cara F = arriba (lado de la pantalla), B = abajo
PLACE = {
    # ---------------- microcontrolador (arriba a la derecha, antena fuera del borde superior)
    "U1": (129.0, 6.75, 0, "F"),
    "C12": (117.0, 2.6, 0, "F"), "C11": (117.0, 5.0, 0, "F"),
    "R27": (115.5, 16.5, 0, "F"), "R28": (115.5, 18.3, 0, "F"),
    "R22": (112.0, 9.0, 90, "F"), "C10": (114.0, 9.0, 90, "F"),
    "R23": (112.0, 13.0, 90, "F"), "R24": (114.0, 13.0, 90, "F"),
    "R6": (122.0, 21.6, 0, "F"), "R9": (125.0, 21.6, 0, "F"),
    "R10": (128.0, 21.6, 0, "F"), "R11": (131.0, 21.6, 0, "F"),
    "R29": (134.0, 21.6, 0, "F"), "R37": (137.0, 21.6, 0, "F"),
    "R21": (111.0, 21.6, 0, "F"),
    "J2": (112.0, 26.0, 90, "F"),
    "SW5": (139.5, 25.8, 0, "F"), "SW6": (139.5, 31.8, 0, "F"),
    "D5": (129.0, 26.5, 0, "F"),
    "R13": (110.5, 31.0, 0, "F"), "R14": (110.5, 32.8, 0, "F"), "C2": (110.5, 34.6, 0, "F"),
    # ---------------- USB-C (borde derecho)
    "J1": (141.0, 41.0, 90, "F"),
    "U7": (132.5, 41.0, 0, "F"), "C23": (133.0, 47.0, 0, "F"),
    "R25": (133.0, 37.3, 0, "F"), "R26": (133.0, 44.8, 0, "F"),
    # ---------------- reparto de carga y LDO
    "D8": (127.0, 33.0, 0, "F"), "Q3": (121.0, 37.5, 0, "F"), "D9": (127.0, 37.5, 0, "F"),
    "R36": (117.0, 34.0, 0, "F"), "R38": (117.0, 36.0, 0, "F"), "R39": (117.0, 38.0, 0, "F"),
    "U9": (114.0, 44.5, 0, "F"), "C21": (109.5, 49.5, 0, "F"), "C22": (118.5, 49.5, 0, "F"),
    # ---------------- cargador
    "U2": (130.0, 52.0, 0, "F"), "R33": (124.5, 52.0, 90, "F"),
    "C15": (136.5, 49.5, 0, "F"), "C16": (136.5, 54.5, 0, "F"),
    "R34": (141.0, 49.0, 0, "F"), "R35": (141.0, 55.0, 0, "F"),
    "D6": (141.5, 51.0, 0, "F"), "D7": (141.5, 57.0, 0, "F"),
    # ---------------- proteccion de celda (junto a la llegada de la bateria)
    "U10": (112.0, 60.0, 0, "F"), "R31": (108.5, 56.0, 90, "F"), "C14": (110.5, 56.0, 90, "F"),
    "R32": (115.5, 56.0, 90, "F"),
    "Q1": (110.5, 66.5, 0, "F"), "Q2": (110.5, 72.5, 0, "F"),
    # ---------------- elevador 5.1 V
    "U8": (129.0, 67.0, 0, "F"), "L1": (122.5, 67.0, 0, "F"), "C17": (118.0, 67.0, 90, "F"),
    "C18": (133.0, 64.5, 90, "F"), "C19": (135.5, 64.5, 90, "F"), "C20": (138.0, 64.5, 90, "F"),
    "R15": (130.0, 71.5, 0, "F"), "R16": (133.5, 71.5, 0, "F"),
    "SW4": (120.0, 76.0, 0, "F"),
    # ---------------- pantalla, expansor y logica bajo el LCD (solo SMD bajo)
    "DS1": (101.5, 11.0, 0, "F"),
    "R1": (95.0, 8.0, 0, "F"),
    "U6": (60.0, 35.0, 90, "F"), "C9": (60.0, 43.0, 0, "F"), "R7": (66.0, 43.0, 0, "F"),
    "R17": (52.0, 45.0, 0, "F"), "R18": (55.0, 45.0, 0, "F"),
    "R19": (58.0, 45.0, 0, "F"), "R20": (61.0, 45.0, 0, "F"),
    "R2": (64.0, 47.0, 0, "F"), "R3": (67.0, 47.0, 0, "F"), "R4": (70.0, 47.0, 0, "F"),
    "C1": (73.0, 47.0, 0, "F"),
    # ---------------- franja inferior: conectores, tiras y audio
    "DS2": (10.5, 75.0, 0, "F"), "DS3": (24.0, 75.0, 0, "F"),
    "C8": (40.0, 70.0, 0, "F"), "C7": (46.0, 63.5, 0, "F"),
    "U5": (50.0, 70.0, 0, "F"), "R5": (55.5, 66.0, 0, "F"), "R8": (55.5, 68.0, 0, "F"),
    "KP1": (3.5, 20.0, 0, "F"),
    "SW1": (61.0, 75.0, 0, "F"), "SW2": (70.0, 75.0, 0, "F"), "SW3": (79.0, 75.0, 0, "F"),
    "C3": (87.0, 66.5, 0, "F"), "C13": (94.0, 63.5, 0, "F"), "C4": (94.0, 65.5, 0, "F"),
    "U4": (98.5, 66.5, 0, "F"), "R30": (101.5, 63.5, 90, "F"),
    "J4": (88.0, 75.0, 0, "F"),
    # ---------------- celdas, cara inferior (abajo del LCD)
    "BT1": (86.0, 24.0, 180, "B"), "BT2": (86.0, 47.0, 180, "B"),
}
HOLES = [(3.5, 3.5), (3.5, 76.5), (141.5, 76.5), (104.0, 76.5)]


def parse_netlist(path):
    t = open(path).read()
    comps = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', t):
        comps[m.group(1)] = (m.group(2), m.group(3))
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)[\s\S]*?\(tstamps "([^"]+)"\)', t):
        if m.group(1) in comps:
            comps[m.group(1)] += (m.group(2),)
    nets = {}
    for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)([\s\S]*?)\)\s*(?=\(net |\)\s*\)\s*$)', t):
        name = m.group(1)
        for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            nets.setdefault(name, []).append((n.group(1), n.group(2)))
    return comps, nets


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def seg(board, layer, x1, y1, x2, y2, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(x1, y1))
    s.SetEnd(pt(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def rect(board, layer, x, y, w, h, lw=0.1):
    for a, b in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
        seg(board, layer, a[0], a[1], b[0], b[1], lw)


def text(board, layer, s, x, y, size=1.5):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    board.Add(t)


def main(netfile, out):
    comps, nets = parse_netlist(netfile)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)

    netitems = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netitems[name] = ni
    padnet = {}
    for name, nodes in nets.items():
        for ref, pin in nodes:
            padnet[(ref, pin)] = name

    missing = []
    for ref, info in sorted(comps.items()):
        value, fpid = info[0], info[1]
        if not fpid:
            continue
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        if fp is None:
            sys.exit(f"no se encontro {fpid}")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        if len(info) > 2:
            fp.SetPath(pcbnew.KIID_PATH("/" + info[2]))
        if ref not in PLACE:
            missing.append(ref)
            x, y, rot, side = 150, 10 + len(missing) * 5, 0, "F"
        else:
            x, y, rot, side = PLACE[ref]
        board.Add(fp)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        if side == "B":
            fp.Flip(fp.GetPosition(), False)
        for pad in fp.Pads():
            n = padnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netitems[n])
    if missing:
        print("aviso: sin posicion:", missing, file=sys.stderr)

    # contorno
    rect(board, pcbnew.Edge_Cuts, 0, 0, W, H, 0.15)
    # agujeros M3 (huella de la libreria)
    for i, (hx, hy) in enumerate(HOLES):
        h = pcbnew.FootprintLoad(f"{FPDIR}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        h.SetReference(f"H{i + 1}")
        h.SetValue("M3")
        board.Add(h)
        h.SetPosition(pt(hx, hy))
    # contorno del modulo LCD y notas
    x, y, w, hh = LCD
    rect(board, pcbnew.Dwgs_User, x, y, w, hh, 0.2)
    text(board, pcbnew.Dwgs_User, "DS1: contorno del modulo LCD 98.25 x 56.34 (montado encima)", x + w / 2, y + hh / 2, 2.0)
    text(board, pcbnew.Dwgs_User, "Bajo el LCD: solo SMD de menos de 5 mm de alto", x + w / 2, y + hh / 2 + 4, 1.5)
    text(board, pcbnew.Dwgs_User, "Antena del WROOM-1 fuera del borde: nada metalico a menos de 15 mm", 129, -9, 1.2)
    text(board, pcbnew.Dwgs_User, "BT1/BT2 en la cara inferior", 47, 30, 1.5)

    # plano de GND en In1.Cu (la capa 2 queda solo para GND)
    gnd = netitems["/GND"]
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(gnd)
    z.SetZoneName("GND_L2")
    ol = z.Outline()
    ol.NewOutline()
    for px, py in ((0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)):
        ol.Append(mm(px), mm(py))
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    board.Add(z)

    # reglas basicas (JLCPCB 4 capas, ver la propuesta)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_ViasMinAnnularWidth = mm(0.125)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_HoleToHoleMin = mm(0.5)

    # el relleno de la zona se hace en KiCad (tecla B); ZONE_FILLER falla sin proyecto cargado
    pcbnew.SaveBoard(out, board)
    proyecto(out.replace(".kicad_pcb", ".kicad_pro"))
    print("ok", len(board.GetFootprints()), "huellas,", len(netitems), "redes")


NETCLASSES = [
    # nombre, ancho de pista, separacion, via (diametro, broca), patrones de red
    ("POTENCIA", 1.5, 0.25, 0.8, 0.4, ["/VBAT_CELDA", "/BAT_NEG", "/PROT_D", "/VSYS", "/VSYS_SW", "/VBUS_USB",
                                      "/BOOST_SW"]),
    ("5V", 1.0, 0.2, 0.8, 0.4, ["/+5V"]),
    ("BOCINA", 0.6, 0.2, 0.6, 0.3, ["/SPK_P", "/SPK_N"]),
    ("3V3_GND", 0.5, 0.2, 0.6, 0.3, ["/+3V3", "/GND"]),
    ("BUS_LCD", 0.15, 0.15, 0.6, 0.3, ["/LCD_*", "/TOUCH_*"]),
    ("USB", 0.29, 0.15, 0.6, 0.3, ["/USB_DP*", "/USB_DN*"]),
]


def proyecto(path):
    """Clases de red y reglas en el .kicad_pro que crea SaveBoard."""
    import json
    d = json.load(open(path))
    base = d["net_settings"]["classes"][0]
    clases = [base]
    pats = []
    for nombre, tw, cl, vd, vdr, redes in NETCLASSES:
        c = dict(base)
        c.update(name=nombre, track_width=tw, clearance=cl, via_diameter=vd, via_drill=vdr)
        if nombre == "USB":
            c.update(diff_pair_width=0.29, diff_pair_gap=0.2)
        clases.append(c)
        pats += [{"netclass": nombre, "pattern": r} for r in redes]
    d["net_settings"]["classes"] = clases
    d["net_settings"]["netclass_patterns"] = pats
    json.dump(d, open(path, "w"), indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
