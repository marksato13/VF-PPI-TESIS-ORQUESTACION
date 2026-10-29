#!/usr/bin/env python3
"""Valida, ciclo a ciclo, la variante «solo ventanas pendientes» de build_rows frente a la llamada global del motor
7b275b8 (corre en el sensor, solo lectura sobre PCAP archivado y EVE congelado).

Variante (sin tocar extract_multilayer_v2): por cada entidad e,
  A_min(e) = primera ancla del rango de e en este ciclo (de su primera a su última observación, igual que
             build_rows) que NO está en scored_windows. El motor tiene ese conjunto; aquí se emula con las ventanas
             que el registro muestra decididas antes de este ciclo (desde su inicio). Cubre ventanas pendientes que
             quedan atrás y ventanas que nacen por detrás de la última decidida (observaciones tardías).
             Si todas las anclas del rango están puntuadas, la entidad no necesita filas este ciclo.
  (Regla descartada, --regla ultima: A_min = última ventana registrada + 10 s; se conserva para documentar que no
  cubre esos dos casos.)
  entrada  = observaciones de e con ts > A_min-30 (paquetes) o ts > A_min-60 (L7), más la primera y la última
             observación de e (fijan el mismo rango de anclas; quedan fuera de toda ventana >= A_min).
             El filtrado conserva el orden original de las listas.
  salida   = filas de build_rows con ventana >= A_min.
Comprueba, por ciclo:
  * idénticas: filas de la variante == filas globales con ventana >= A_min(e), entidad a entidad (orden y floats);
  * cubiertas: toda ventana decidida en este ciclo tiene ventana >= A_min(e) (las ventana_no_evaluada no salen de
    build_rows sino de la lista de pendientes del motor, que no cambia);
y mide t_global (build_rows original), t_entidad (partición por entidad) y t_pendientes (esta variante).
Salida JSONL por ciclo. Reparto en trabajadores por tramos contiguos (--trabajador/--trabajadores).
"""
from __future__ import annotations
import argparse, bisect, collections, datetime, ipaddress, json, math, os, sys, time
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402

HIST = 230.0
PCAP_S = 15.0
PASO = 10


def t_fich(f: Path) -> float:
    n = f.name
    return v2.parse_eve_timestamp(f"{n[5:9]}-{n[9:11]}-{n[11:13]}T{n[13:15]}:{n[15:17]}:{n[17:19]}Z")


def agrupar(at, apps):
    pp, pa = collections.defaultdict(list), collections.defaultdict(list)
    for p in at:
        pp[p.entity_ip].append(p)
    for x in apps:
        pa[x.entity_ip].append(x)
    return pp, pa


def recortar(lp, la, a_min):
    """Observaciones necesarias para las ventanas >= a_min, conservando primera y última de la entidad."""
    ts = [p.timestamp for p in lp] + [x.timestamp for x in la]
    t_lo, t_hi = min(ts), max(ts)
    rp = [p for p in lp if p.timestamp > a_min - 30 or p.timestamp in (t_lo, t_hi)]
    ra = [x for x in la if x.timestamp > a_min - 60 or x.timestamp in (t_lo, t_hi)]
    return rp, ra


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--pcap-dir", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--arranque-motor", required=True, type=float)
    ap.add_argument("--trabajador", type=int, default=0)
    ap.add_argument("--trabajadores", type=int, default=1)
    ap.add_argument("--salida", required=True, type=Path)
    ap.add_argument("--regla", choices=("no_puntuada", "ultima"), default="no_puntuada")
    a = ap.parse_args()

    ficheros = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    tf = [t_fich(f) for f in ficheros]
    # Registro: por ciclo, marcas y ventanas registradas por entidad; estado previo emulado de scored_windows.
    ciclos = collections.OrderedDict()
    for l in a.motor.open(encoding="utf-8"):
        if '"event": "decision"' not in l and '"event": "ventana_no_evaluada"' not in l:
            continue
        d = json.loads(l)
        c = ciclos.setdefault(d["inicio_ciclo"], {"mp": d.get("marca_pcap"), "me": d.get("marca_eve"),
                                                 "reg": collections.defaultdict(list), "dec": False})
        c["reg"][d["entity_ip"]].append(v2.parse_eve_timestamp(d["window_end_utc"]))
        if d["event"] == "decision":
            c.setdefault("decididas", []).append((d["entity_ip"], v2.parse_eve_timestamp(d["window_end_utc"])))
            c["dec"] = True
            c["mp"], c["me"] = d["marca_pcap"], d["marca_eve"]
    # estado emulado antes de cada ciclo: última ventana registrada y conjunto de ventanas decididas por entidad
    ultimo: dict[str, float] = {}
    previo = {}
    puntuadas_desde: dict[tuple[str, float], float] = {}
    for k, c in ciclos.items():
        previo[k] = dict(ultimo)
        for e, ws in c["reg"].items():
            ultimo[e] = max(ultimo.get(e, 0.0), max(ws))
        for e, w in c.get("decididas", []):  # solo decisiones: es lo que entra en scored_windows
            puntuadas_desde.setdefault((e, w), k)

    def a_min_de(e, lp, la, k):
        if a.regla == "ultima":
            return previo[k][e] + PASO if e in previo[k] else None
        ts = [p.timestamp for p in lp] + [x.timestamp for x in la]
        anc = (math.floor(min(ts) / PASO) + 1) * PASO
        ult = math.ceil(max(ts) / PASO) * PASO
        while anc <= ult:
            if puntuadas_desde.get((e, float(anc)), float("inf")) >= k:  # no decidida antes de este ciclo
                return float(anc)
            anc += PASO
        return float("inf")
    ks = [k for k, c in ciclos.items() if c["dec"] and c["mp"] is not None
          and float(c["mp"]) - HIST - PCAP_S >= tf[0] and float(c["mp"]) <= tf[-1] + PCAP_S]
    n = len(ks); lo = n * a.trabajador // a.trabajadores; hi = n * (a.trabajador + 1) // a.trabajadores
    ks = ks[lo:hi]
    if not ks:
        return 0
    t0, t1 = ks[0] - HIST - 60, ks[-1] + 60

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
    red = ipaddress.ip_network("10.10.0.0/16")
    tmp = Path(f"/tmp/validar_pend_{os.getpid()}.jsonl")
    cache: dict[str, list] = {}
    out = a.salida.open("w", encoding="utf-8")

    for k in ks:
        c = ciclos[k]; mp, me = float(c["mp"]), float(c["me"])
        i0 = bisect.bisect_right(tf, mp - HIST - PCAP_S - 1); i1 = bisect.bisect_right(tf, mp)
        sel = ficheros[i0:i1]
        for nom in [x for x in cache if x not in {f.name for f in sel}]:
            del cache[nom]
        frames = []
        for f in sel:
            if f.name not in cache:
                cs_ = []
                for t, tr in v2.iter_pcap_frames(f):
                    cx = v3.parse_con_contexto(t, tr)
                    if cx is not None:
                        cs_.append(cx)
                cache[f.name] = cs_
            if cache[f.name] and cache[f.name][-1].packet.timestamp <= mp + 1e-6:
                frames.extend(cache[f.name])
        at = []
        if frames:
            nuevo = max(cx.packet.timestamp for cx in frames)
            util = [cx for cx in frames if cx.packet.timestamp >= nuevo - HIST and cx.packet.protocol not in (112, 240)]
            paq, _ = v3.deduplicar_espejo(util)
            at = v2.attribute_packets(paq, red) if paq else []
        j0, j1 = bisect.bisect_left(eve_t, k - HIST), bisect.bisect_right(eve_t, me)
        with tmp.open("w", encoding="utf-8") as fo:
            for _, l in eve[j0:j1]:
                fo.write(l)
        apps = v2.load_app_observations(tmp, red) if j1 > j0 else []
        reg = {"inicio_ciclo": k, "hora": datetime.datetime.fromtimestamp(k, datetime.timezone.utc).strftime("%H:%M:%S")}
        obs = [p.timestamp for p in at] + [x.timestamp for x in apps]
        if not obs:
            reg.update({"identicas": True, "cubiertas": True, "nota": "sin observaciones"})
            out.write(json.dumps(reg) + "\n"); continue
        cs = min(a.arranque_motor, min(obs))

        s = time.perf_counter(); g = v2.build_rows("v", at, apps, step_seconds=PASO, capture_start=cs); tg = time.perf_counter() - s
        s = time.perf_counter()
        pp, pa = agrupar(at, apps)
        for ent in sorted(set(pp) | set(pa)):
            v2.build_rows("v", pp[ent], pa[ent], step_seconds=PASO, capture_start=cs)
        te = time.perf_counter() - s

        s = time.perf_counter()
        pp, pa = agrupar(at, apps)
        var = {}
        for ent in sorted(set(pp) | set(pa)):
            a_min = a_min_de(ent, pp[ent], pa[ent], k)
            if a_min == float("inf"):
                var[ent] = (a_min, [])
                continue
            lp, la = (recortar(pp[ent], pa[ent], a_min) if a_min is not None else (pp[ent], pa[ent]))
            filas = v2.build_rows("v", lp, la, step_seconds=PASO, capture_start=cs)
            var[ent] = (a_min, [r for r in filas if a_min is None or v2.parse_eve_timestamp(r["window_end_utc"]) >= a_min])
        tp = time.perf_counter() - s
        amin = {e: am for e, (am, _) in var.items()}

        glob = collections.defaultdict(list)
        for r in g:
            glob[r["entity_ip"]].append(r)
        distintas, no_cubiertas = [], []
        for ent, (a_min, filas) in var.items():
            ref = [r for r in glob[ent] if a_min is None or v2.parse_eve_timestamp(r["window_end_utc"]) >= a_min]
            if ref != filas:
                distintas.append({"entidad": ent, "a_min": a_min, "n_ref": len(ref), "n_var": len(filas)})
        # cobertura: solo decisiones (las ventana_no_evaluada no salen de build_rows, sino de la lista de pendientes)
        for ent, w in c.get("decididas", []):
            a_min = amin.get(ent)
            if a_min is not None and w < a_min:
                no_cubiertas.append({"entidad": ent, "a_min": a_min, "ventana": w})
        reg.update({"paquetes": len(at), "apps": len(apps), "filas_global": len(g),
                    "filas_variante": sum(len(f) for _, f in var.values()),
                    "identicas": not distintas, "cubiertas": not no_cubiertas,
                    "t_global_s": round(tg, 3), "t_entidad_s": round(te, 3), "t_pendientes_s": round(tp, 3)})
        if distintas:
            reg["distintas"] = distintas[:5]
        if no_cubiertas:
            reg["no_cubiertas"] = no_cubiertas[:5]
        out.write(json.dumps(reg) + "\n"); out.flush()
    out.close()
    tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
