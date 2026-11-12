#!/usr/bin/env python3
"""Ruteo preliminar de la PCB de la opcion C con Freerouting.

Pasos:
  1. python3.12 rutear.py dsn airsoft_tool_opcion_C.kicad_pcb ruteo.dsn
  2. java -jar freerouting-1.9.0.jar -de ruteo.dsn -do ruteo.ses -mp 20
  3. python3.12 rutear.py ses airsoft_tool_opcion_C.kicad_pcb ruteo.ses

El paso 3 borra las pistas y vias que hubiera, carga las del .ses, agrega rellenos
de GND en las dos caras, rellena todas las zonas y guarda la PCB. KiCad 7 solo importa
.ses desde la interfaz grafica, por eso el .ses se lee aqui.
"""
import re
import sys

import pcbnew

W, H = 145.0, 80.0


def tokens(text):
    return re.findall(r'"[^"]*"|\(|\)|[^\s()]+', text)


def parse(tok, i=0):
    """Convierte tokens a listas anidadas."""
    out = []
    while i < len(tok):
        t = tok[i]
        if t == "(":
            sub, i = parse(tok, i + 1)
            out.append(sub)
        elif t == ")":
            return out, i + 1
        else:
            out.append(t.strip('"'))
            i += 1
    return out, i


def find(node, key):
    for n in node:
        if isinstance(n, list) and n and n[0] == key:
            yield n


def zona_gnd(board, layer, nombre, net):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(nombre)
    ol = z.Outline()
    ol.NewOutline()
    for px, py in ((0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)):
        ol.Append(pcbnew.FromMM(px), pcbnew.FromMM(py))
    z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetLocalClearance(pcbnew.FromMM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.3))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    z.SetAssignedPriority(0)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)


ANCHOS = {"POTENCIA": (2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4), "5V": (1.5, 1.0, 0.8, 0.6, 0.5, 0.4)}


def ensanchar(board, separacion=0.25):
    """Ensancha las pistas de potencia al mayor ancho que no choque con cobre de otra red."""
    from collections import defaultdict
    por_capa = defaultdict(list)  # capa -> [(netcode, shape)]
    for f in board.GetFootprints():
        for p in f.Pads():
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(l) and p.FlashLayer(l):
                    por_capa[l].append((p.GetNetCode(), p.GetEffectiveShape(l)))
    tracks = [t for t in board.GetTracks()]
    for t in tracks:
        if t.GetClass() == "PCB_VIA":
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                por_capa[l].append((t.GetNetCode(), t.GetEffectiveShape(l)))
    sep = pcbnew.FromMM(separacion)
    cambios = 0
    # se procesan de mayor a menor importancia; las pistas ya ensanchadas cuentan con su ancho nuevo
    for t in tracks:
        if t.GetClass() != "PCB_TRACK":
            continue
        clase = t.GetNetClassName()
        if clase not in ANCHOS:
            continue
        l = t.GetLayer()
        otros = [s for n, s in por_capa[l] if n != t.GetNetCode()]
        otras_pistas = [o for o in tracks if o.GetClass() == "PCB_TRACK" and o.GetLayer() == l
                        and o.GetNetCode() != t.GetNetCode()]
        original = t.GetWidth()
        for w in ANCHOS[clase]:
            if pcbnew.FromMM(w) <= original:
                break
            t.SetWidth(pcbnew.FromMM(w))
            sh = t.GetEffectiveShape(l)
            choca = any(sh.Collide(o, sep) for o in otros) or \
                any(sh.Collide(o.GetEffectiveShape(l), sep) for o in otras_pistas)
            if not choca:
                cambios += 1
                break
            t.SetWidth(original)
    print("ensanchadas", cambios)


def costura(board, gnd, paso=4.0, d=0.6, broca=0.3, sep=0.3):
    """Vias de costura de GND en una reticula, solo donde caben dentro del relleno de GND
    de las dos caras."""
    zf = [z for z in board.Zones() if z.GetZoneName() == "GND_SUP"][0].GetFilledPolysList(pcbnew.F_Cu)
    zb = [z for z in board.Zones() if z.GetZoneName() == "GND_INF"][0].GetFilledPolysList(pcbnew.B_Cu)
    r = pcbnew.FromMM(d / 2 + 0.05)
    agujeros = [(t.GetPosition(), t.GetDrillValue()) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    agujeros += [(p.GetPosition(), p.GetDrillSize().x) for f in board.GetFootprints() for p in f.Pads()
                 if p.GetDrillSize().x > 0]
    # nada de costura bajo las piezas (salvo las celdas, que van en la otra cara)
    cajas = [f.GetBoundingBox(False, False) for f in board.GetFootprints()
             if f.GetReference() not in ("BT1", "BT2") and not f.GetReference().startswith("H")]
    ajenos = {l: [o.GetEffectiveShape(l) for o in board.GetTracks()
                  if o.GetClass() == "PCB_TRACK" and o.GetLayer() == l and o.GetNetCode() != gnd.GetNetCode()]
              + [p.GetEffectiveShape(l) for f in board.GetFootprints() for p in f.Pads()
                 if p.IsOnLayer(l) and p.GetNetCode() != gnd.GetNetCode()]
              for l in (pcbnew.F_Cu, pcbnew.B_Cu)}
    n = 0
    y = 2.0
    while y < H - 1.5:
        x = 2.0
        while x < W - 1.5:
            c = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
            pts = [c] + [pcbnew.VECTOR2I(c.x + dx, c.y + dy) for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))]
            if all(zf.Contains(q) and zb.Contains(q) for q in pts) and not any(b.Contains(c) for b in cajas):
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(c)
                via.SetWidth(pcbnew.FromMM(d))
                via.SetDrill(pcbnew.FromMM(broca))
                via.SetNet(gnd)
                # el relleno solo se revisa en cinco puntos; aqui se revisa la via completa contra
                # pistas y pads de otras redes en las dos caras
                choca = any(via.GetEffectiveShape(l).Collide(o, pcbnew.FromMM(sep))
                            for l in (pcbnew.F_Cu, pcbnew.B_Cu) for o in ajenos[l])
                lejos = not choca and all((c - pos).EuclideanNorm() > (dr + pcbnew.FromMM(broca)) / 2 + pcbnew.FromMM(0.5)
                            for pos, dr in agujeros)
                if lejos:
                    board.Add(via)
                    agujeros.append((c, pcbnew.FromMM(broca)))
                    n += 1
            x += paso
        y += paso
    print("vias de costura", n)


def exportar_dsn(pcb, dsn):
    board = pcbnew.LoadBoard(pcb)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    t = open(dsn).read()
    # potencia en las dos caras (1 oz). Se rutea a 0.3 mm para poder entrar a los
    # pads de TSSOP, SOT-23 y VQFN; al importar el .ses cada tramo se ensancha hasta donde
    # dejan las separaciones (ensanchar())
    t = re.sub(r"(\(class POTENCIA[^(]*\(circuit\n\s*)(\(use_via [^)]*\))",
               r"\1\2 (use_layer F.Cu B.Cu)", t)
    t = re.sub(r"(\(class POTENCIA[\s\S]*?\(width )1500", r"\g<1>300", t)
    open(dsn, "w").write(t)
    print("dsn", ok)


def importar_ses(pcb, ses):
    board = pcbnew.LoadBoard(pcb)
    for t in list(board.GetTracks()):
        board.Remove(t)
    tree, _ = parse(tokens(open(ses).read()))
    tree = tree[0]
    routes = next(find(tree, "routes"))
    res = next(find(routes, "resolution"))
    escala = {"um": 1e3, "mil": 25400.0, "mm": 1e6}[res[1]] / float(res[2])  # nm por unidad

    def nm(v):
        return int(round(float(v) * escala))

    vias_tam = {}
    for lib in find(routes, "library_out"):
        for ps in find(lib, "padstack"):
            m = re.search(r"_(\d+):(\d+)_um", ps[1])
            if m:
                vias_tam[ps[1]] = (int(m.group(1)) * 1000, int(m.group(2)) * 1000)
    capas = {board.GetLayerName(l): l for l in (pcbnew.F_Cu, pcbnew.B_Cu)}
    nets = board.GetNetsByName()
    n_pistas = n_vias = 0
    for netout in find(routes, "network_out"):
        for net in find(netout, "net"):
            ni = nets[net[1]] if nets.has_key(net[1]) else None
            for w in find(net, "wire"):
                for p in find(w, "path"):
                    layer, ancho, coords = p[1], nm(p[2]), p[3:]
                    pts = [(nm(coords[k]), -nm(coords[k + 1])) for k in range(0, len(coords) - 1, 2)]
                    for a, b in zip(pts, pts[1:]):
                        t = pcbnew.PCB_TRACK(board)
                        t.SetStart(pcbnew.VECTOR2I(*a))
                        t.SetEnd(pcbnew.VECTOR2I(*b))
                        t.SetWidth(ancho)
                        t.SetLayer(capas[layer])
                        if ni:
                            t.SetNet(ni)
                        board.Add(t)
                        n_pistas += 1
            for v in find(net, "via"):
                d, dr = vias_tam.get(v[1], (600000, 300000))
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(nm(v[2]), -nm(v[3])))
                via.SetWidth(d)
                via.SetDrill(dr)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                if ni:
                    via.SetNet(ni)
                board.Add(via)
                n_vias += 1
    ensanchar(board)
    gnd = nets["/GND"]
    nombres = [z.GetZoneName() for z in board.Zones()]
    if "GND_SUP" not in nombres:
        zona_gnd(board, pcbnew.F_Cu, "GND_SUP", gnd)
    if "GND_INF" not in nombres:
        zona_gnd(board, pcbnew.B_Cu, "GND_INF", gnd)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    costura(board, gnd)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)
    print("ok", n_pistas, "segmentos,", n_vias, "vias")


if __name__ == "__main__":
    {"dsn": exportar_dsn, "ses": importar_ses}[sys.argv[1]](sys.argv[2], sys.argv[3])
