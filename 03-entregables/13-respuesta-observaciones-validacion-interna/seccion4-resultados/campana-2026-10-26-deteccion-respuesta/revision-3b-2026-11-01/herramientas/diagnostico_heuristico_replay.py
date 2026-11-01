#!/usr/bin/env python3
"""Replay completo frente a vivo, clave a clave, en el rango del inventario (solo lee).

Compara presencia, score, decisión, packet_count_10s y heurístico (tipo, acción, motivo). Para cada diferencia del
heurístico informa paquetes, score, fase del ciclo (inicio_ciclo mod 10) e inicio_ciclo - marca_eve en vivo y en
replay. Explica por qué el replay coincide (mismo main() del motor, mismo conjunto de PCAP cerrados) mientras el
recálculo individual v1 difería (otra regla de selección de PCAP).
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

LO, HI = "2026-11-01T07:28:30", "2026-11-01T10:03:30"


def load(p: Path) -> dict:
    d, dup = {}, 0
    for l in open(p, encoding="utf-8"):
        if '"event": "decision"' not in l:
            continue
        r = json.loads(l)
        k = (r["entity_ip"], r["window_end_utc"])
        if LO <= k[1][:19] <= HI:
            dup += k in d
            d.setdefault(k, r)
    return d, dup


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vivo", required=True, type=Path)
    ap.add_argument("--replay", required=True, type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()
    (V, dv), (R, dr) = load(a.vivo), load(a.replay)
    comunes = set(V) & set(R)
    h = lambda r, c: (r.get("heuristico") or {}).get(c)  # noqa: E731
    cmp = {c: sum(1 for k in comunes if V[k].get(c) != R[k].get(c)) for c in ("score", "decision", "packet_count_10s")}
    difs = []
    for k in sorted(comunes, key=lambda k: k[1]):
        if h(V[k], "motivo") != h(R[k], "motivo"):
            v, r = V[k], R[k]
            difs.append({"entity_ip": k[0], "window_end_utc": k[1], "pk10": [v["packet_count_10s"], r["packet_count_10s"]],
                         "score": [v["score"], r["score"]],
                         "heuristico_tipo": [h(v, "heuristico"), h(r, "heuristico")],
                         "accion": [h(v, "accion"), h(r, "accion")], "motivo": [h(v, "motivo"), h(r, "motivo")],
                         "fase_ciclo_s": [round(v["inicio_ciclo"] % 10, 2), round(r["inicio_ciclo"] % 10, 2)],
                         "inicio_ciclo_menos_marca_eve_s": [round(v["inicio_ciclo"] - v["marca_eve"], 2),
                                                            round(r["inicio_ciclo"] - r["marca_eve"], 2)]})
    out = {"rango_window_end": [LO, HI], "claves_vivo": len(V), "claves_replay": len(R), "comunes": len(comunes),
           "solo_vivo": len(set(V) - set(R)), "solo_replay": len(set(R) - set(V)), "duplicados": [dv, dr],
           "diferencias": cmp,
           "heuristico": {"diferencias_motivo": len(difs),
                          "diferencias_tipo": sum(1 for d in difs if d["heuristico_tipo"][0] != d["heuristico_tipo"][1]),
                          "diferencias_accion": sum(1 for d in difs if d["accion"][0] != d["accion"][1]),
                          "todas_con_0_paquetes_y_score_null": all(d["pk10"] == [0, 0] and d["score"] == [None, None]
                                                                   for d in difs),
                          "detalle": difs},
           "explicacion": (
               "Las diferencias son ventanas SIN paquetes del origen (pk10=0, score null en ambos): su fila solo tiene "
               "datos L7 del EVE (consultas DNS / peticiones HTTP en 60 s) y se construye cuando la entidad reaparece. "
               "El contenido L7 depende de qué líneas del EVE estaban en el búfer en ese ciclo: en vivo el ciclo "
               "empieza a x3,5/x4,5 s y ve el EVE tal como Suricata lo había volcado; el replay usa una rejilla x0,0 s y "
               "da por escrita una línea en cuanto el reloj alcanza su timestamp. Tipo y acción coinciden; cambia el "
               "conteo explicativo. No afecta al IF (no puntúa sin paquetes)."),
           "por_que_el_replay_coincide_y_el_recalculo_v1_no": (
               "El replay ejecuta el main() real del motor con su lectura de PCAP (todos los cerrados, files[:-1]) y su "
               "marca_pcap (máximo de paquetes decodificados). El recálculo v1 reconstruía la entrada con otra regla "
               "(ficheros con última TRAMA <= marca_pcap): excluía ficheros que terminan en tramas no decodificables. "
               "La v2 usa la regla del motor.")}
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("comunes", "solo_vivo", "solo_replay", "duplicados", "diferencias")}),
          json.dumps({k: v for k, v in out["heuristico"].items() if k != "detalle"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
