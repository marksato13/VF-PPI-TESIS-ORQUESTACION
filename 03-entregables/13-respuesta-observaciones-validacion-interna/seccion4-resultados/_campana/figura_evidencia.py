#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.4 - Figura de evidencia de respuesta: 3 paneles del MISMO ensayo.
(a) Decision del motor  (b) Entrada del feed firmado  (c) Regla nftables del host.
Relaciona por id de ensayo + IP + marcas temporales. Oculta secretos (no imprime claves).

Entrada: un JSON de evidencia recogida (--evidencia) con la forma:
  {"ensayo":"E-scan-1","ip":"10.10.20.30",
   "decision":{"window_end_utc":...,"score":...,"threshold":...,"heuristico":{...},"decision":"ALERT"},
   "feed":{"ts":...,"ip":...,"accion":"BLOCK","hasta":...,"detector":...,"nivel":...},
   "nft":{"ts":...,"set":"cyberflow_bloqueados","timeout_s":...,"expires_s":...}}
Salida: PNG (>=300 DPI) y SVG. Una captura del panel NO prueba aplicacion: el panel (c)
viene del nft real del host.
"""
from __future__ import annotations
import argparse, json, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidencia", required=True)
    ap.add_argument("--out", required=True, help="ruta PNG de salida (se genera tambien .svg)")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ev = json.loads(pathlib.Path(a.evidencia).read_text(encoding="utf-8"))
    ensayo = ev.get("ensayo", "?"); ip = ev.get("ip", "?")
    d = ev.get("decision", {}) or {}; fd = ev.get("feed", {}) or {}; nf = ev.get("nft", {}) or {}

    def bloque(txt_lines):
        return "\n".join(txt_lines)

    heur = d.get("heuristico") or {}
    panel_a = bloque([
        "(a) DECISION DEL MOTOR  (sensor)",
        "ventana: %s" % d.get("window_end_utc", "?"),
        "decision: %s   score: %s   umbral: %s" % (d.get("decision", "?"), d.get("score", "?"), d.get("threshold", "?")),
        "heuristico: %s -> %s" % (heur.get("heuristico", "-"), heur.get("accion", "-")),
        "motivo: %s" % (heur.get("motivo", "-")),
    ])
    panel_b = bloque([
        "(b) ENTRADA DEL FEED FIRMADO  (sensor -> host, ed25519)",
        "ts emision: %s" % fd.get("ts", "?"),
        "ip: %s   accion: %s   hasta: %s" % (fd.get("ip", "?"), fd.get("accion", "?"), fd.get("hasta", "?")),
        "detector: %s   nivel: %s" % (fd.get("detector", "-"), fd.get("nivel", "-")),
    ])
    panel_c = bloque([
        "(c) REGLA NFTABLES APLICADA  (host protegido)",
        "ts: %s" % nf.get("ts", "?"),
        "set: %s   ip: %s" % (nf.get("set", "?"), ip),
        "timeout: %ss   expira en: %ss" % (nf.get("timeout_s", "?"), nf.get("expires_s", "?")),
    ])

    fig, axes = plt.subplots(3, 1, figsize=(9, 7.2))
    fig.suptitle("Evidencia de respuesta  ·  ensayo %s  ·  %s" % (ensayo, ip), fontsize=13, fontweight="bold")
    for ax, (txt, color) in zip(axes, [(panel_a, "#1b4965"), (panel_b, "#5fa8d3"), (panel_c, "#bee9e8")]):
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor=color, alpha=0.18, edgecolor=color, lw=1.5))
        ax.text(0.02, 0.5, txt, transform=ax.transAxes, va="center", ha="left",
                family="monospace", fontsize=9.5)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    png = pathlib.Path(a.out)
    fig.savefig(png, dpi=300)
    fig.savefig(png.with_suffix(".svg"))
    print("Figura:", png, "y", png.with_suffix(".svg"))

if __name__ == "__main__":
    raise SystemExit(main())
