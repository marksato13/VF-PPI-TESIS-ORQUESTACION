#!/usr/bin/env python3
"""Recalcula, desde el PCAP archivado y EVE, las 28 características y el score de las ventanas de un origen
alrededor de cada episodio, con lo que el motor tenía disponible al decidir (corre en el sensor, solo lectura).

El motor corregido (producto 7b275b8) registra en cada decisión inicio_ciclo, marca_pcap y marca_eve. Con ellas se
reconstruye su entrada exacta, igual que preparacion-2026-10-28/herramientas/emular_ciclos.py:
  * PCAP: ficheros cuyo último paquete es <= marca_pcap (cerrados en ese instante), búfer podado a 230 s desde el
    paquete más nuevo; protocolos 112/240 fuera; deduplicar_espejo; attribute_packets.
  * EVE: eventos con timestamp en [inicio_ciclo-230, marca_eve].
  * capture_start = arranque del motor (--arranque-motor), como en vivo.
Después extract_multilayer_v2.build_rows por entidad y el pipeline desplegado (score_samples).

Salida JSONL: una línea por decisión registrada del origen con window_end en (inicio-120, fin+90] de algún episodio:
clave, episodio, logged_at, las 28 características recalculadas, score recalculado, score y pk10 registrados y si
coinciden. No modifica nada ni sustituye al registro del motor: lo respalda y lo verifica.
"""
from __future__ import annotations
import argparse, bisect, ipaddress, json, sys
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402
import joblib  # noqa: E402
import analizar as an  # noqa: E402

HIST = 230.0
MODELO = RAIZ / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"
ANTES, DESPUES = 120.0, 90.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--pcap-dir", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--arranque-motor", required=True, type=float, help="epoch de ActiveEnterTimestamp de ppi-motor")
    ap.add_argument("--origen", default="10.10.20.30")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()

    pipe = joblib.load(MODELO); nombres = v2.FEATURE_NAMES
    red = ipaddress.ip_network("10.10.0.0/16")
    eps, _ = an.leer_marcas(a.marcas)
    eps = {k: v for k, v in eps.items() if v["fin_ep"] is not None}
    regs = []
    for l in a.motor.open(encoding="utf-8"):
        if '"event": "decision"' in l and a.origen in l:
            r = json.loads(l)
            if r.get("entity_ip") != a.origen:
                continue
            w = an.ep_iso(r["window_end_utc"])
            ep = next((k for k, e in eps.items() if e["inicio_ep"] - ANTES < w <= e["fin_ep"] + DESPUES), None)
            if ep:
                r["_ep"], r["_w"] = ep, w
                regs.append(r)
    t0 = min(e["inicio_ep"] for e in eps.values()) - ANTES - HIST - 60
    t1 = max(e["fin_ep"] for e in eps.values()) + DESPUES + 300

    eve = []
    with a.eve.open("r", encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            i = linea.find('"timestamp":"')
            if i < 0:
                continue
            try:
                t = v2.parse_eve_timestamp(linea[i + 13:i + 44].split('"')[0])
            except ValueError:
                continue
            if t0 <= t <= t1:
                eve.append((t, linea))
    eve.sort(key=lambda x: x[0]); eve_t = [x[0] for x in eve]
    tmp = Path("/tmp/recalcular_eve.jsonl")

    ficheros = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    cache: dict[Path, tuple] = {}

    def leer(f):
        if f not in cache:
            marcas, cs = [], []
            for t, tr in v2.iter_pcap_frames(f):
                marcas.append(t)
                c = v3.parse_con_contexto(t, tr)
                if c is not None and c.packet.protocol not in (112, 240):
                    cs.append(c)
            cache[f] = (marcas[0], marcas[-1], cs) if marcas else None
        return cache[f]

    out = a.salida.open("w", encoding="utf-8")
    n = exactos = 0
    for ep_id in sorted({r["_ep"] for r in regs}, key=lambda k: eps[k]["inicio_ep"]):
        e = eps[ep_id]
        lo, hi = e["inicio_ep"] - ANTES - HIST - 60, e["fin_ep"] + DESPUES + 300
        fich = [f for f in ficheros if lo - 30 <= v2.parse_eve_timestamp(
            f"{f.name[5:9]}-{f.name[9:11]}-{f.name[11:13]}T{f.name[13:15]}:{f.name[15:17]}:{f.name[17:19]}Z") <= hi]
        info = [(f, leer(f)) for f in fich]
        info = [(f, x) for f, x in info if x]
        for r in [r for r in regs if r["_ep"] == ep_id]:
            mp, me, ic = float(r["marca_pcap"]), float(r["marca_eve"]), float(r["inicio_ciclo"])
            cerr = [x for f, x in info if x[1] <= mp + 1e-6]
            nuevo = max((x[1] for x in cerr), default=None)
            fila = None
            if nuevo is not None:
                buf = [c for x in cerr if x[1] >= nuevo - HIST for c in x[2] if c.packet.timestamp >= nuevo - HIST]
                paq, _ = v3.deduplicar_espejo(buf)
                at = [p for p in v2.attribute_packets(paq, red) if p.entity_ip == a.origen]
                i0, i1 = bisect.bisect_left(eve_t, ic - HIST), bisect.bisect_right(eve_t, me)
                with tmp.open("w", encoding="utf-8") as fo:
                    for _, l in eve[i0:i1]:
                        fo.write(l)
                apps = [x for x in v2.load_app_observations(tmp, red) if x.entity_ip == a.origen]
                for row in v2.build_rows("recalc", at, apps, step_seconds=10, capture_start=a.arranque_motor):
                    if row["window_end_utc"] == r["window_end_utc"]:
                        fila = row
                        break
            s = (float(pipe.score_samples([[float(fila[k]) for k in nombres]])[0])
                 if fila and fila["packet_count_10s"] else None)
            pk_ok = fila is not None and int(fila["packet_count_10s"]) == int(r["packet_count_10s"])
            s_ok = fila is not None and ((s is None and r.get("score") is None) or
                                         (s is not None and r.get("score") is not None and abs(s - r["score"]) < 1e-9))
            n += 1; exactos += int(pk_ok and s_ok)
            out.write(json.dumps({
                "episodio_id": ep_id, "entity_ip": r["entity_ip"], "window_end_utc": r["window_end_utc"],
                "logged_at": r["logged_at"], "inicio_ciclo": ic, "marca_pcap": mp, "marca_eve": me,
                "caracteristicas": {k: (float(fila[k]) if fila else None) for k in nombres},
                "score_recalculado": s, "score_registrado": r.get("score"),
                "pk10_recalculado": int(fila["packet_count_10s"]) if fila else None,
                "pk10_registrado": r["packet_count_10s"], "coincide_pk10": pk_ok, "coincide_score": s_ok},
                ensure_ascii=False) + "\n")
        cache.clear()
    out.close()
    print(json.dumps({"decisiones": n, "reproducidas_exactas": exactos, "salida": str(a.salida)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
