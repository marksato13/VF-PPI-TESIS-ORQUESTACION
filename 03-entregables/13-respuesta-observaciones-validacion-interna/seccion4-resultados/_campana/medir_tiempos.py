#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.4 - Tabla 10 y cronologia t0..t5 por ensayo, a partir de evidencia recogida.

NO inventa tiempos: cada sello que no tenga evidencia queda como "no medido".
Entradas (todas menos marcas/motor son opcionales):
  --marcas   marcas.jsonl (Kali): t0=inicio, t_fin por episodio (wall epoch + mono)
  --motor    recorte JSONL de motor_decision.log (sensor): t1 (1a senal) por entidad
  --feeds    JSONL opcional {"ts":epoch,"entradas":[{"ip","accion","hasta"}...]}: t2
  --nft      JSONL opcional {"ts":epoch,"block":[ip...],"limit":[ip...]}: t3 y t5
  --cortes   JSONL opcional {"ts":epoch,"episodio":id,"estado":"filtered|open"}: t4
  --offsets  JSON opcional {"sensor":seg,"host":seg,...} desfase vs reloj de la Kali
  --entity   IP del atacante (def 10.10.20.30)
  --margen   s tras t_fin donde aun se atribuye senal (def 150)
  --out      carpeta de salida

Relojes: si las marcas estan en maquinas distintas, se corrige con --offsets antes de
restar; se declara la incertidumbre. La duracion de INFERENCIA (reloj monotonico) el
motor no la registra hoy -> "no medido" (requiere instrumentar el motor, experimento aparte).
"""
from __future__ import annotations
import argparse, json, csv, pathlib
from datetime import datetime, timezone

def ts(v):
    try: return float(v)
    except (TypeError, ValueError): pass
    s = str(v).strip().replace("Z", "+00:00")
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

def jsonl(path):
    if not path: return []
    out = []
    for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln: continue
        try: out.append(json.loads(ln))
        except json.JSONDecodeError: continue
    return out

def episodios(marcas_path):
    ini, fin, fam = {}, {}, {}
    for m in jsonl(marcas_path):
        if m.get("familia") == "clock": continue
        eid = m.get("id");  fam[eid] = m.get("familia")
        if m.get("fase") == "inicio": ini[eid] = float(m["wall"])
        elif m.get("fase") == "fin": fin[eid] = float(m["wall"])
    eps = [{"id": e, "familia": fam.get(e, ""), "t0": ini[e], "t_fin": fin.get(e, ini[e])} for e in ini]
    eps.sort(key=lambda x: x["t0"]); return eps

def fmt(x):
    return "no medido" if x is None else ("%.1f s" % x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marcas", required=True); ap.add_argument("--motor", required=True)
    ap.add_argument("--feeds", default=""); ap.add_argument("--nft", default="")
    ap.add_argument("--cortes", default=""); ap.add_argument("--offsets", default="")
    ap.add_argument("--entity", default="10.10.20.30"); ap.add_argument("--margen", type=float, default=150.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    off = json.loads(pathlib.Path(a.offsets).read_text(encoding="utf-8")) if a.offsets else {}
    o_sensor = float(off.get("sensor", 0)); o_host = float(off.get("host", 0))

    motor = []
    for d in jsonl(a.motor):
        if d.get("entity_ip") != a.entity: continue
        la = ts(d.get("logged_at")) or ts(d.get("window_end_utc"))
        if la is None: continue
        motor.append({"la": la, "alert": d.get("decision") == "ALERT",
                      "model": float(d.get("score", 0)) < float(d.get("threshold", -1e9)),
                      "heur": d.get("heuristico") not in (None, "null")})
    feeds = jsonl(a.feeds); nft = jsonl(a.nft); cortes = jsonl(a.cortes)
    eps = episodios(a.marcas)

    filas = []
    for e in eps:
        t0 = e["t0"]; hi = e["t_fin"] + a.margen
        sig = sorted((m["la"] for m in motor if e["t0"] <= m["la"] <= hi and (m["alert"] or m["model"] or m["heur"])))
        t1 = (sig[0] - t0) if sig else None
        # origen de la 1a senal
        origen = ""
        for m in sorted(motor, key=lambda x: x["la"]):
            if t0 <= m["la"] <= hi and (m["model"] or m["heur"]):
                origen = "modelo" if m["model"] and not m["heur"] else ("heuristico" if m["heur"] and not m["model"] else "modelo+heuristico")
                break
        # t2 feed (reloj sensor -> corregir)
        t2 = None
        for fd in sorted(feeds, key=lambda x: x.get("ts", 0)):
            tt = ts(fd.get("ts"));  ips = {en.get("ip") for en in fd.get("entradas", [])}
            if tt is not None and a.entity in ips and (tt + o_sensor) >= t0:
                t2 = (tt + o_sensor) - t0; break
        # t3 aplicacion nft (reloj host -> corregir); t5 retirada
        t3 = t5 = None; visto = False
        for sn in sorted(nft, key=lambda x: x.get("ts", 0)):
            tt = ts(sn.get("ts"))
            if tt is None: continue
            tcorr = (tt + o_host) - t0
            en_set = a.entity in set(sn.get("block", [])) | set(sn.get("limit", []))
            if en_set and t3 is None and tcorr >= 0: t3 = tcorr; visto = True
            if visto and not en_set and t5 is None and tcorr > (t3 or 0): t5 = tcorr
        # t4 efecto (corte)
        t4 = None
        for c in sorted(cortes, key=lambda x: x.get("ts", 0)):
            if c.get("episodio") == e["id"] and c.get("estado") == "filtered":
                tt = ts(c.get("ts"))
                if tt is not None: t4 = (tt + o_host) - t0; break
        det = t1
        dec_apl = (t3 - (t2 if t2 is not None else t1)) if (t3 is not None and (t2 is not None or t1 is not None)) else None
        total = t3 if t3 is not None else None
        filas.append({"ensayo": e["id"], "familia": e["familia"], "origen": origen,
                      "t_deteccion_s": det, "t_decision_aplicacion_s": dec_apl, "t_total_s": total,
                      "t2_feed_s": t2, "t3_nft_s": t3, "t4_corte_s": t4, "t5_reversion_s": t5})

    # salidas
    with open(out / "tabla10.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else
                           ["ensayo","familia","origen","t_deteccion_s","t_decision_aplicacion_s","t_total_s","t2_feed_s","t3_nft_s","t4_corte_s","t5_reversion_s"])
        w.writeheader(); [w.writerow(x) for x in filas]
    L = ["# Tabla 10 - Respuestas y tiempos (modelo limpio)", "",
         "Relojes corregidos con --offsets; incertidumbre declarada. Inferencia monotonica: no medido.", "",
         "| Ensayo | Origen | Accion | t deteccion | t decision->aplicacion | t total | Reversion | Corte |",
         "|---|---|---|---|---|---|---|---|"]
    for x in filas:
        rev = fmt(x["t5_reversion_s"]); corte = fmt(x["t4_corte_s"])
        L.append("| %s | %s | (del feed) | %s | %s | %s | %s | %s |" % (
            x["ensayo"], x["origen"] or "no medido", fmt(x["t_deteccion_s"]),
            fmt(x["t_decision_aplicacion_s"]), fmt(x["t_total_s"]), rev, corte))
    (out / "TABLA10.md").write_text("\n".join(L), encoding="utf-8")
    print("Ensayos:", len(filas), "-> escrito en", out)
    for x in filas:
        print(" %-12s det=%s t3=%s total=%s" % (x["ensayo"], fmt(x["t_deteccion_s"]), fmt(x["t3_nft_s"]), fmt(x["t_total_s"])))

if __name__ == "__main__":
    raise SystemExit(main())
