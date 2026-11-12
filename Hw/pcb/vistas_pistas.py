#!/usr/bin/env python3
"""Dibuja las vistas del ruteo (PNG): una por capa de cobre y una combinada.

Uso: python3.12 vistas_pistas.py airsoft_tool_opcion_C.kicad_pcb carpeta_salida
Genera pistas_combinada.png, pistas_L1_F.Cu.png, pistas_L2_In1.Cu.png,
pistas_L3_In2.Cu.png y pistas_L4_B.Cu.png. Vista superior en mm (la capa
inferior se ve a traves de la placa, sin espejar).
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PatchCollection
import pcbnew

CAPAS = [
    ("L1_F.Cu", pcbnew.F_Cu, "#C83737", "L1 superior (piezas y señales)"),
    ("L2_In1.Cu", pcbnew.In1_Cu, "#2E8B57", "L2 interna, plano de GND"),
    ("L3_In2.Cu", pcbnew.In2_Cu, "#C08A00", "L3 interna (alimentación y señales lentas)"),
    ("L4_B.Cu", pcbnew.B_Cu, "#2F5FB3", "L4 inferior (batería y desborde)"),
]
W, H = 145.0, 80.0
FIG_W = 14.0  # pulgadas
X0, X1, Y0, Y1 = -4, W + 4, -10, H + 4


def mm(v):
    return pcbnew.ToMM(v)


def poly_patches(shape_poly_set, **kw):
    out = []
    for i in range(shape_poly_set.OutlineCount()):
        o = shape_poly_set.Outline(i)
        pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
        if len(pts) > 2:
            out.append(mp.Polygon(pts, closed=True, **kw))
        for h in range(shape_poly_set.HoleCount(i)):
            ho = shape_poly_set.Hole(i, h)
            hp = [(mm(ho.CPoint(j).x), mm(ho.CPoint(j).y)) for j in range(ho.PointCount())]
            if len(hp) > 2:
                out.append(mp.Polygon(hp, closed=True, fc="white", ec="none"))
    return out


def dibujar(board, capas, titulo, out, zonas=True, alfa_zona=0.35):
    fig = plt.figure(figsize=(FIG_W, FIG_W * (Y1 - Y0) / (X1 - X0) + 0.6), dpi=150)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.92])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y1, Y0)
    ax.set_aspect("equal")
    ax.axis("off")
    pt_por_mm = FIG_W * 0.96 * 72 / (X1 - X0)
    ax.add_patch(mp.Rectangle((0, 0), W, H, fc="#FBFAF5", ec="black", lw=1.2, zorder=0))

    for nombre, lid, color, _ in capas:
        if zonas:
            for z in board.Zones():
                if z.GetIsRuleArea() or not z.IsOnLayer(lid):
                    continue
                fp = z.GetFilledPolysList(lid)
                for p in poly_patches(fp, fc=color, ec="none", alpha=alfa_zona, zorder=1):
                    ax.add_patch(p)
        segs, anchos = [], []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetLayer() == lid:
                segs.append([(mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))])
                anchos.append(mm(t.GetWidth()) * pt_por_mm)
        if segs:
            ax.add_collection(LineCollection(segs, linewidths=anchos, colors=color, capstyle="round",
                                             alpha=0.9 if len(capas) == 1 else 0.75, zorder=3))
        pads = []
        for f in board.GetFootprints():
            for p in f.Pads():
                if not p.IsOnLayer(lid):
                    continue
                bb = p.GetBoundingBox()
                pads.append(mp.Rectangle((mm(bb.GetX()), mm(bb.GetY())), mm(bb.GetWidth()), mm(bb.GetHeight())))
        ax.add_collection(PatchCollection(pads, fc="#B0A060" if len(capas) > 1 else color, ec="none",
                                          alpha=0.55, zorder=2))
    vias = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            vias.append(mp.Circle((mm(c.x), mm(c.y)), mm(t.GetWidth()) / 2))
    ax.add_collection(PatchCollection(vias, fc="#555555", ec="black", lw=0.2, zorder=4))
    # contorno del LCD y textos de referencia
    ax.add_patch(mp.Rectangle((7, 5), 98.25, 56.34, fc="none", ec="#1F77B4", lw=0.8, ls=(0, (6, 3)), zorder=5))
    for f in board.GetFootprints():
        r = f.GetReference()
        if r[0] in "UJ" or r in ("DS1", "KP1", "L1", "Q1", "Q2", "BT1", "BT2"):
            c = f.GetPosition()
            ax.text(mm(c.x), mm(c.y), r, fontsize=6, ha="center", va="center", color="black", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.3))
    ax.set_title(titulo, fontsize=11)
    fig.savefig(out)
    plt.close(fig)
    print("ok", out)


def main(pcb, outdir):
    board = pcbnew.LoadBoard(pcb)
    os.makedirs(outdir, exist_ok=True)
    dibujar(board, CAPAS, "PCB opción C v0.2, ruteo preliminar: las cuatro capas (L1 rojo, L2 verde, L3 ocre, L4 azul)",
            os.path.join(outdir, "pistas_combinada.png"), zonas=False)
    for c in CAPAS:
        dibujar(board, [c], f"PCB opción C v0.2, ruteo preliminar: {c[3]}",
                os.path.join(outdir, f"pistas_{c[0]}.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
