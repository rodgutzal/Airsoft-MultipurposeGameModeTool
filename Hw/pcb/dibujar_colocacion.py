#!/usr/bin/env python3
"""Dibuja el diagrama de colocacion (PNG) a partir de la PCB generada por gen_pcb.py.

Uso: python3 dibujar_colocacion.py airsoft_tool_opcion_C.kicad_pcb colocacion_v0.1.png
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import pcbnew

sys.path.insert(0, ".")
from gen_pcb import LCD, H, W  # noqa: E402

BLOQUES = [
    ("Microcontrolador WROOM-1", "#4C78A8", ["U1", "C10", "C11", "C12", "R22", "R23", "R24", "R6", "R9", "R10", "R11",
                                             "SW5", "SW6", "J2", "R29", "R37", "R21", "D5", "R13", "R14", "C2"]),
    ("USB-C, ESD y D+/D-", "#9D755D", ["J1", "U7", "C23", "R25", "R26", "R27", "R28"]),
    ("Carga, reparto y LDO 3.3 V", "#E45756", ["U2", "R33", "C15", "C16", "R34", "R35", "D6", "D7", "D8", "D9", "Q3",
                                               "R36", "R38", "R39", "U9", "C21", "C22"]),
    ("Protección de celda", "#B279A2", ["U10", "R31", "C14", "R32", "Q1", "Q2"]),
    ("Elevador 5.1 V", "#F58518", ["U8", "L1", "C17", "C18", "C19", "C20", "R15", "R16", "SW4"]),
    ("Pantalla, expansor y entradas", "#54A24B", ["DS1", "R1", "U6", "C9", "R7", "R17", "R18", "R19", "R20", "R2", "R3",
                                                   "R4", "C1", "KP1", "SW1", "SW2", "SW3"]),
    ("Tiras WS2812B", "#72B7B2", ["DS2", "DS3", "C8", "C7", "U5", "R5", "R8"]),
    ("Audio MAX98357A", "#EECA3B", ["U4", "C3", "C13", "C4", "R30", "J4"]),
    ("Celdas 18650 (cara inferior)", "#BAB0AC", ["BT1", "BT2"]),
]
ETIQUETAS = {"U1": "U1 ESP32-S3-WROOM-1", "DS1": "DS1\n2x17", "U6": "U6 MCP23017", "U2": "U2\nTP4056",
             "U8": "U8", "L1": "L1", "J1": "J1\nUSB-C", "U9": "U9 LDO", "U4": "U4", "U5": "U5", "C8": "C8",
             "C3": "C3", "J4": "J4\nbocina", "KP1": "KP1\nteclado", "SW1": "SW1", "SW2": "SW2", "SW3": "SW3",
             "SW4": "SW4\nencendido", "DS2": "DS2 tira 1", "DS3": "DS3 tira 2", "J2": "J2 UART", "Q1": "Q1",
             "Q2": "Q2", "U10": "U10", "SW5": "RESET", "SW6": "BOOT", "U7": "U7", "BT1": "BT1 18650 (abajo)",
             "BT2": "BT2 18650 (abajo)", "D8": "D8", "D9": "D9", "Q3": "Q3", "D5": "D5"}


def bbox(fp):
    b = fp.GetBoundingBox(False, False)
    return (pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()), pcbnew.ToMM(b.GetWidth()), pcbnew.ToMM(b.GetHeight()))


def main(pcb, out):
    board = pcbnew.LoadBoard(pcb)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    color = {}
    for nombre, c, refs in BLOQUES:
        for r in refs:
            color[r] = c

    fig, ax = plt.subplots(figsize=(14, 9.2), dpi=130)
    ax.set_aspect("equal")
    ax.add_patch(mp.Rectangle((0, 0), W, H, fc="#F4F1E8", ec="black", lw=1.6, zorder=0))
    # zona de antena: parte del modulo fuera del borde y despeje recomendado de 15 mm
    u1 = fps["U1"].GetPosition()
    ux, uy = pcbnew.ToMM(u1.x), pcbnew.ToMM(u1.y)
    ax.add_patch(mp.Rectangle((ux - 24, uy - 27.75), 48, 21, fc="none", ec="#D62728", ls="--", lw=1.2, zorder=1))
    ax.text(ux, uy - 25.5, "Despeje de la antena (huella KiCad): sin cobre, metal ni baterías", ha="center", fontsize=8,
            color="#D62728")
    ax.add_patch(mp.Rectangle((ux - 9, uy - 12.75), 18, 6, fc="#FADBD8", ec="#D62728", lw=1, zorder=7))
    ax.text(ux, uy - 9.7, "antena fuera de la placa", ha="center", va="center", fontsize=7, color="#D62728", zorder=8)

    for ref, fp in fps.items():
        if ref.startswith("H"):
            p = fp.GetPosition()
            ax.add_patch(mp.Circle((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)), 1.6, fc="white", ec="black", lw=1, zorder=5))
            continue
        x, y, w, h = bbox(fp)
        if ref == "U1":  # el bbox incluye la zona de despeje; se dibuja solo el cuerpo de 18 x 25.5
            p = fp.GetPosition()
            x, y, w, h = pcbnew.ToMM(p.x) - 9, pcbnew.ToMM(p.y) - 12.75, 18, 25.5
        bottom = fp.IsFlipped()
        c = color.get(ref, "#999999")
        ax.add_patch(mp.Rectangle((x, y), w, h, fc=c, ec="black" if not bottom else "#555555",
                                  alpha=0.25 if bottom else 0.85, lw=0.5, ls="--" if bottom else "-",
                                  zorder=1 if bottom else 3))
        if ref in ETIQUETAS:
            ax.text(x + w / 2, y + h / 2, ETIQUETAS[ref], ha="center", va="center", fontsize=6.5 if not bottom else 8,
                    zorder=6, color="black")
    x, y, w, h = LCD
    ax.add_patch(mp.Rectangle((x, y), w, h, fc="none", ec="#1F77B4", lw=1.8, ls=(0, (6, 3)), zorder=4))
    ax.text(x + 2, y + 2.5, "DS1: módulo LCD 3.5\" 98.25 x 56.34 mm, montado encima (bajo él solo SMD bajo)",
            fontsize=8, color="#1F77B4", zorder=6)
    ax.annotate("", xy=(0, H + 4), xytext=(W, H + 4), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(W / 2, H + 6.5, f"{W:g} mm", ha="center", fontsize=9)
    ax.annotate("", xy=(-4, 0), xytext=(-4, H), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(-6.5, H / 2, f"{H:g} mm", va="center", rotation=90, fontsize=9)

    handles = [mp.Patch(fc=c, ec="black", label=n) for n, c, _ in BLOQUES]
    handles.append(mp.Patch(fc="none", ec="#1F77B4", ls="--", label="Contorno del LCD (encima)"))
    handles.append(mp.Patch(fc="none", ec="#D62728", ls="--", label="Despeje de antena"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=4, fontsize=8, frameon=False)
    ax.set_xlim(-9, W + 4)
    ax.set_ylim(H + 9, -30)
    ax.set_xticks(range(0, int(W) + 1, 10))
    ax.set_yticks(range(0, int(H) + 1, 10))
    ax.tick_params(labelsize=7)
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_title("PCB opción C v0.1: colocación propuesta, vista superior (mm)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
