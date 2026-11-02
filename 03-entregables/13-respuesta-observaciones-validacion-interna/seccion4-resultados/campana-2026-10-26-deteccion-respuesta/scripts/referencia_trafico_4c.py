#!/usr/bin/env python3
"""Etapa 4, 4C: tiempos por episodio y referencia al TRÁFICO observado (PROTOCOLO-4C-CAMPANA-A.md §7). Solo lee.

No cambia nada de analizar_3b.py: toma su resultado (analisis-3b.json, categorías con la referencia del generador,
OBJETIVOS v3) y añade, por episodio, lo que el 3B no separaba:

  generador        t_proc_inicio / t_proc_fin (marcas.jsonl, reloj de la Kali)
  tráfico          t_trafico_inicio / t_trafico_fin (trafico_observado.py: primer y último paquete del origen al
                   destino y servicio del escenario en el PCAP archivado, reloj del Sensor1; en escaneos, SYN sin ACK)
  evidencia        window_end de la primera ventana con señal atribuible
  disponibilidad   disponible_utc del registro (registro_escrito_en del ciclo; analizar_3b)
  emisión          emisiones reales del motor (ALERT/heurístico registrados) y, aparte, la vía rápida (emitido_en)
  publicación      primera propuesta del publicador v2 para el origen (traza: publicado_en, regla, acción, tipo)
  entrega          primera entrega del relé v2 a srv-dmz posterior a esa publicación (traza del relé)
  respuesta        SOLO propuesta: en sombra no hay t_apl ni t_efecto (nadie aplica)

Referencia (fijada ANTES de ejecutar, PROTOCOLO-4C §7):
  escaneo_breve      t_ini_ref = primer SYN observado; t_fin_eval = min(último SYN observado, t_proc_fin).
                     Su categoría PRINCIPAL es la de esta referencia ("categoria_trafico").
  resto              la categoría principal sigue siendo la de analizar_3b (referencia del generador, v3);
                     "categoria_trafico" se publica como información.
  oportuna           señal atribuible con disponible <= t_fin_eval + ε (ε = 0,01 s, OBJETIVOS v3).
Sin tráfico observado (paquetes_ataque = 0 o captura que no cubre la ventana) la referencia de tráfico es
"no_determinable" y no se inventa: se conserva la categoría de analizar_3b.

Uso:
  python3 referencia_trafico_4c.py --analisis analisis-4c/analisis-3b.json --trafico trafico-observado.json \
     [--senales-rapidas senales-rapidas.jsonl] [--traza-publicador traza.jsonl] [--traza-rele traza-rele.jsonl] \
     [--origen 10.10.20.30] --salida referencia-trafico.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2026-11-02.1"
EPS = 0.01
CONFIGS = ("IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01")
PRINCIPAL_TRAFICO = {"escaneo_breve"}


def ep(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()


def iso(t):
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def jsonl(p: Path | None) -> list:
    if p is None:
        return []
    out = []
    for ln in open(p, encoding="utf-8", errors="replace"):
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def escenario_de(eid: str) -> str:
    return eid.rsplit("-r", 1)[0]


def referencia(tr: dict, escenario: str) -> dict:
    p_ini, p_fin = ep(tr.get("t_proc_inicio_utc")), ep(tr.get("t_proc_fin_utc"))
    t_ini, t_fin = ep(tr.get("t_trafico_inicio_utc")), ep(tr.get("t_trafico_fin_utc"))
    if not tr.get("captura_cubre_ventana") or not tr.get("paquetes_ataque") or t_ini is None:
        return {"determinable": False, "motivo": tr.get("observacion") or "sin tráfico de ataque observado"}
    fin_eval = min(t_fin, p_fin) if p_fin is not None else t_fin
    return {"determinable": True, "t_ini_ref": t_ini, "t_fin_eval": fin_eval,
            "regla": ("primer SYN observado; fin = min(último SYN, fin del generador)" if escenario.startswith("escaneo")
                      else "primer paquete observado; fin = min(último paquete, fin del generador)"),
            "t_proc_inicio": p_ini, "t_proc_fin": p_fin}


def categoria_trafico(e: dict, conf: str, ref: dict) -> dict:
    base = (e.get(conf) or {}).get("categoria")
    if not ref["determinable"]:
        return {"categoria": base, "fuente": "analizar_3b (referencia de tráfico no determinable)"}
    sen = [w for w in e.get("ventanas", []) if conf in (w.get("senales") or []) and w.get("atribucion") == "atribuible"
           and w.get("disponible_utc")]
    if not sen:
        return {"categoria": base, "fuente": "analizar_3b (sin señal atribuible)"}
    disp = sorted((ep(w["disponible_utc"]), w) for w in sen)
    oport = [(t, w) for t, w in disp if t <= ref["t_fin_eval"] + EPS]
    if oport:
        t, w = oport[0]
        return {"categoria": "oportuna", "fuente": "referencia de tráfico", "primera_window_end_utc": w["window_end_utc"],
                "disponible_utc": w["disponible_utc"], "desde_inicio_trafico_s": round(t - ref["t_ini_ref"], 3),
                "margen_antes_fin_eval_s": round(ref["t_fin_eval"] - t, 3)}
    t, w = disp[0]
    return {"categoria": "solo_posterior", "fuente": "referencia de tráfico", "primera_window_end_utc": w["window_end_utc"],
            "disponible_utc": w["disponible_utc"], "tras_fin_eval_s": round(t - ref["t_fin_eval"], 3)}


def via_rapida(senales: list, origen: str, destino: str, ref: dict, tr: dict) -> dict:
    a = ref["t_ini_ref"] if ref["determinable"] else ep(tr.get("t_proc_inicio_utc"))
    b = ref["t_fin_eval"] if ref["determinable"] else ep(tr.get("t_proc_fin_utc"))
    if a is None or b is None:
        return {"evaluable": False}
    s = sorted((x for x in senales if x.get("event") == "senal_rapida" and x.get("origen") == origen
                and x.get("destino") == destino and a - 1 <= float(x.get("t_evidencia") or 0) <= b + 60),
               key=lambda x: float(x["t_evidencia"]))
    if not s:
        return {"evaluable": True, "senal": False}
    x = s[0]
    em = float(x.get("emitido_en") or x.get("disponible_en") or 0)
    return {"evaluable": True, "senal": True, "t_evidencia_utc": iso(float(x["t_evidencia"])),
            "disponible_utc": iso(x.get("disponible_en")), "emitido_utc": iso(em),
            "oportuna": em <= b + EPS, "desde_inicio_s": round(em - a, 3), "señales": len(s),
            "referencia": "tráfico" if ref["determinable"] else "generador"}


def propuesta_y_entrega(traza_pub: list, traza_rele: list, origen: str, a: float, b: float) -> dict:
    props = []
    for x in traza_pub:
        if x.get("evento") != "publicacion":
            continue
        for n in x.get("nuevos") or []:
            if n.get("ip") == origen and n.get("tipo") != "rechazada" and a - 1 <= float(x["publicado_en"]) <= b + 300:
                props.append((float(x["publicado_en"]), n, x))
    if not props:
        return {"propuesta": False, "nota": "sombra: sin t_apl ni t_efecto"}
    t, n, x = min(props, key=lambda p: p[0])
    out = {"propuesta": True, "publicado_utc": iso(t), "desde_inicio_s": round(t - a, 3), "regla": n.get("regla"),
           "accion": n.get("accion"), "tipo": n.get("tipo"), "destino_aplicacion": n.get("destino"),
           "secuencia_feed": x.get("secuencia"), "nota": "sombra: propuesta publicada, NO aplicada (sin t_apl ni t_efecto)"}
    ent = sorted(float((r.get("destinos") or {}).get("srv-dmz", {}).get("entregado_en"))
                 for r in traza_rele if (r.get("destinos") or {}).get("srv-dmz", {}).get("entregado_en")
                 and float(r.get("traido_en") or 0) >= t)
    out["entrega_srv_dmz_utc"] = iso(ent[0]) if ent else None
    out["entrega_desde_publicacion_s"] = round(ent[0] - t, 3) if ent else None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analisis", required=True, type=Path)
    ap.add_argument("--trafico", required=True, type=Path)
    ap.add_argument("--senales-rapidas", type=Path)
    ap.add_argument("--traza-publicador", type=Path)
    ap.add_argument("--traza-rele", type=Path)
    ap.add_argument("--origen", default="10.10.20.30")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)
    an = json.load(open(a.analisis, encoding="utf-8"))
    tr = {x["episodio"]: x for x in json.load(open(a.trafico, encoding="utf-8"))["episodios"]}
    sr, tp, tl = jsonl(a.senales_rapidas), jsonl(a.traza_publicador), jsonl(a.traza_rele)
    res = {}
    for eid, e in sorted(an["episodios"].items()):
        esc = escenario_de(eid)
        t = tr.get(eid)
        if t is None:
            res[eid] = {"escenario": esc, "trafico": None, "motivo": "episodio sin fila en trafico-observado.json"}
            continue
        ref = referencia(t, esc)
        cats = {c: {"categoria_3b": (e.get(c) or {}).get("categoria"), "categoria_trafico": categoria_trafico(e, c, ref)}
                for c in CONFIGS}
        for c in CONFIGS:
            cats[c]["principal"] = (cats[c]["categoria_trafico"]["categoria"] if esc in PRINCIPAL_TRAFICO
                                    else cats[c]["categoria_3b"])
        a0 = ref["t_ini_ref"] if ref["determinable"] else ep(t.get("t_proc_inicio_utc"))
        b0 = ref["t_fin_eval"] if ref["determinable"] else ep(t.get("t_proc_fin_utc"))
        res[eid] = {
            "escenario": esc, "destino": t.get("destino"), "en_poblacion_principal": e.get("en_poblacion_principal"),
            "referencia_principal": "tráfico" if esc in PRINCIPAL_TRAFICO else "generador (v3)",
            "generador": {"inicio_utc": t.get("t_proc_inicio_utc"), "fin_utc": t.get("t_proc_fin_utc")},
            "trafico": {"inicio_utc": t.get("t_trafico_inicio_utc"), "fin_utc": t.get("t_trafico_fin_utc"),
                        "paquetes": t.get("paquetes_ataque"), "puertos_distintos_syn": t.get("puertos_distintos_syn"),
                        "retraso_primer_paquete_s": t.get("retraso_primer_paquete_s"),
                        "captura_cubre_ventana": t.get("captura_cubre_ventana")},
            "referencia_trafico": {k: (iso(v) if k.startswith("t_") else v) for k, v in ref.items()},
            "configuraciones": cats,
            "emisiones_reales": {k: (e.get("emisiones_reales") or {}).get(k)
                                 for k in ("emisiones", "atribuibles", "oportunas", "latencia_primera_oportuna_s")},
            "via_rapida": via_rapida(sr, a.origen, t.get("destino"), ref, t) if a.senales_rapidas else None,
            "respuesta_propuesta": (propuesta_y_entrega(tp, tl, a.origen, a0, b0)
                                    if a.traza_publicador and a0 is not None and b0 is not None else None)}
    out = {"version": VERSION, "epsilon_s": EPS, "fuentes": {k: str(v) for k, v in vars(a).items() if v is not None},
           "definicion": __doc__.split("Uso:")[0].strip(), "episodios": res}
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    resumen = {}
    for eid, r in res.items():
        if r.get("configuraciones"):
            resumen[eid] = {c: r["configuraciones"][c]["principal"] for c in ("IF_0.05", "HEUR")}
    print(json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
