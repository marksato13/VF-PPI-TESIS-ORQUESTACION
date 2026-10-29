#!/usr/bin/env python3
"""Valida, ciclo a ciclo, que llamar a extract_multilayer_v2.build_rows entidad por entidad (con solo las
observaciones de cada entidad) produce exactamente las mismas filas que la llamada global del motor 7b275b8.

Corre en el sensor, solo lectura sobre PCAP archivado y EVE congelado. Para cada ciclo registrado con historia de PCAP
completa en el archivo reconstruye la entrada como perfilar_ciclo_motor.py (búfer de 230 s desde el paquete más nuevo
cerrado en marca_pcap; protocolos 112/240 fuera; deduplicar_espejo; attribute_packets; EVE en
[inicio_ciclo-230, marca_eve]; capture_start = min(arranque, primera observación)) y compara:
  * igualdad exacta de la lista de filas (orden, claves y valores, floats incluidos);
  * si difieren, la primera diferencia (índice, entidad, ventana, claves distintas).
Salida JSONL, una línea por ciclo, con tiempos de ambas versiones. Admite reparto en trabajadores (--trabajador i
--trabajadores n, por tramos contiguos para aprovechar la caché de PCAP).
"""
from __future__ import annotations
import argparse, bisect, collections, datetime, ipaddress, json, os, sys, time
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402

HIST = 230.0
PCAP_S = 15.0


def t_fich(f: Path) -> float:
    n = f.name
    return v2.parse_eve_timestamp(f"{n[5:9]}-{n[9:11]}-{n[11:13]}T{n[13:15]}:{n[15:17]}:{n[17:19]}Z")


def por_entidad(at, apps, cs):
    pp, pa = collections.defaultdict(list), collections.defaultdict(list)
    for p in at:
        pp[p.entity_ip].append(p)
    for x in apps:
        pa[x.entity_ip].append(x)
    out = []
    for ent in sorted(set(pp) | set(pa)):
        out += v2.build_rows("validar", pp[ent], pa[ent], step_seconds=10, capture_start=cs)
    return out


def primera_diferencia(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"indice": i, "entidad": x.get("entity_ip"), "ventana": x.get("window_end_utc"),
                    "claves": sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))[:10]}
    return {"indice": min(len(a), len(b)), "longitudes": [len(a), len(b)]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--pcap-dir", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--arranque-motor", required=True, type=float)
    ap.add_argument("--trabajador", type=int, default=0)
    ap.add_argument("--trabajadores", type=int, default=1)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()

    ficheros = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    tf = [t_fich(f) for f in ficheros]
    ciclos = collections.OrderedDict()
    for l in a.motor.open(encoding="utf-8"):
        if '"event": "decision"' not in l:
            continue
        d = json.loads(l)
        ciclos.setdefault(d["inicio_ciclo"], (float(d["marca_pcap"]), float(d["marca_eve"])))
    # solo ciclos cuyo búfer de 230 s está entero dentro del archivo
    ks = [k for k, (mp, _) in ciclos.items() if mp - HIST - PCAP_S >= tf[0] and mp <= tf[-1] + PCAP_S]
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
    tmp = Path(f"/tmp/validar_eve_{os.getpid()}.jsonl")
    cache: dict[str, list] = {}
    out = a.salida.open("w", encoding="utf-8")

    for k in ks:
        mp, me = ciclos[k]
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
            # solo ficheros cerrados en marca_pcap: su último paquete <= marca_pcap
            if cache[f.name] and cache[f.name][-1].packet.timestamp <= mp + 1e-6:
                frames.extend(cache[f.name])
        reg = {"inicio_ciclo": k, "hora": datetime.datetime.fromtimestamp(k, datetime.timezone.utc).strftime("%H:%M:%S")}
        if frames:
            nuevo = max(cx.packet.timestamp for cx in frames)
            util = [cx for cx in frames if cx.packet.timestamp >= nuevo - HIST and cx.packet.protocol not in (112, 240)]
            paq, _ = v3.deduplicar_espejo(util)
            at = v2.attribute_packets(paq, red) if paq else []
        else:
            at = []
        j0, j1 = bisect.bisect_left(eve_t, k - HIST), bisect.bisect_right(eve_t, me)
        with tmp.open("w", encoding="utf-8") as fo:
            for _, l in eve[j0:j1]:
                fo.write(l)
        apps = v2.load_app_observations(tmp, red) if j1 > j0 else []
        obs = [p.timestamp for p in at] + [x.timestamp for x in apps]
        if not obs:
            reg.update({"filas": 0, "identicas": True, "nota": "sin observaciones"})
        else:
            cs = min(a.arranque_motor, min(obs))
            s = time.perf_counter(); g = v2.build_rows("validar", at, apps, step_seconds=10, capture_start=cs); tg = time.perf_counter() - s
            s = time.perf_counter(); e = por_entidad(at, apps, cs); te = time.perf_counter() - s
            reg.update({"paquetes": len(at), "apps": len(apps), "entidades": len({r["entity_ip"] for r in g}),
                        "filas": len(g), "identicas": g == e, "t_global_s": round(tg, 3), "t_entidad_s": round(te, 3)})
            if g != e:
                reg["diferencia"] = primera_diferencia(g, e)
        out.write(json.dumps(reg) + "\n"); out.flush()
    out.close()
    tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
