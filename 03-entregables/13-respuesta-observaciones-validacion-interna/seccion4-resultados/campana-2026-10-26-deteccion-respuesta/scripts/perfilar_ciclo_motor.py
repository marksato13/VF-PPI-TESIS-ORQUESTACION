#!/usr/bin/env python3
"""Reproduce, sin conexión, el trabajo de ciclos concretos del motor y cronometra cada etapa (corre en el sensor,
solo lectura sobre PCAP archivado y EVE congelado).

Para cada ciclo pedido (instante UTC aproximado) toma del registro del motor su inicio_ciclo, marca_pcap y marca_eve y
rehace lo que el motor 7b275b8 hace en ese ciclo, con TODAS las entidades (no solo la Kali):
  parseo   decodificar los PCAP nuevos del ciclo (el motor parsea incrementalmente: solo los ficheros no vistos)
  filtro   quitar protocolos 112/240 del búfer de 230 s
  dedup    v3.deduplicar_espejo sobre el búfer completo
  atrib    v2.attribute_packets sobre el búfer completo
  eve_w    reescribir el trozo de EVE de 230 s a un fichero
  eve_r    v2.load_app_observations de ese fichero
  rows     v2.build_rows de todas las entidades y ventanas de la historia
  score    pipeline.score_samples de las ventanas nuevas del ciclo (las que el registro muestra decididas en él)
y lo compara con la duración real del ciclo en el registro (max logged_at - inicio_ciclo). Además mide build_rows
llamado por entidad (misma función, solo con las observaciones de esa entidad) y comprueba que las filas son idénticas.
Uso: perfilar_ciclo_motor.py --motor M --pcap-dir D --eve E --arranque-motor EPOCH --ciclo HH:MM:SS [...] --fecha AAAA-MM-DD
"""
from __future__ import annotations
import argparse, bisect, collections, datetime, ipaddress, json, sys, time
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402
import joblib  # noqa: E402

HIST = 230.0
MODELO = RAIZ / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"


def t_fich(f: Path) -> float:
    n = f.name
    return v2.parse_eve_timestamp(f"{n[5:9]}-{n[9:11]}-{n[11:13]}T{n[13:15]}:{n[15:17]}:{n[17:19]}Z")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--pcap-dir", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--arranque-motor", required=True, type=float)
    ap.add_argument("--fecha", required=True)
    ap.add_argument("--ciclo", action="append", required=True)
    a = ap.parse_args()

    ciclos = collections.OrderedDict()
    for l in a.motor.open(encoding="utf-8"):
        if '"event": "decision"' not in l:
            continue
        d = json.loads(l)
        c = ciclos.setdefault(d["inicio_ciclo"], {"mp": d["marca_pcap"], "me": d["marca_eve"], "fin": 0, "n": 0})
        c["fin"] = max(c["fin"], d["logged_at"]); c["n"] += 1
    ks = sorted(ciclos)
    pedidos = []
    for h in a.ciclo:
        t = v2.parse_eve_timestamp(f"{a.fecha}T{h}Z")
        k = min(ks, key=lambda x: abs(x - t))
        pedidos.append(k)
    t0, t1 = min(pedidos) - HIST - 60, max(pedidos) + 60

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
    ficheros = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    pipe = joblib.load(MODELO); nombres = v2.FEATURE_NAMES
    red = ipaddress.ip_network("10.10.0.0/16")
    tmp = Path("/tmp/perfilar_eve.jsonl")

    print("ciclo,real_s,decisiones,ficheros_buffer,frames_buffer,tras_filtro,tras_dedup,paq_atribuidos,eventos_eve,"
          "apps,filas,parseo_nuevos_s,filtro_s,dedup_s,atrib_s,eve_w_s,eve_r_s,rows_s,score_s,total_sin_parseo_s,"
          "rows_por_entidad_s,filas_identicas")
    for k in pedidos:
        c = ciclos[k]
        mp, me = float(c["mp"]), float(c["me"])
        # ficheros del búfer: los que empiezan en (mp-HIST-16, mp]; parseados (el motor ya los tenía en memoria)
        fb = [f for f in ficheros if mp - HIST - 16 < t_fich(f) <= mp]
        frames = []
        for f in fb:
            for t, tr in v2.iter_pcap_frames(f):
                cx = v3.parse_con_contexto(t, tr)
                if cx is not None:
                    frames.append(cx)
        nuevo = max(cx.packet.timestamp for cx in frames)
        frames = [cx for cx in frames if cx.packet.timestamp >= nuevo - HIST]
        # parseo de lo nuevo en este ciclo: ficheros que empiezan en el último paso (aprox. 1 fichero de 15 s)
        nuevos = [f for f in fb if t_fich(f) > mp - 16]
        s = time.perf_counter()
        for f in nuevos:
            for t, tr in v2.iter_pcap_frames(f):
                v3.parse_con_contexto(t, tr)
        t_parse = time.perf_counter() - s
        T = {}
        s = time.perf_counter(); util = [cx for cx in frames if cx.packet.protocol not in (112, 240)]; T["filtro"] = time.perf_counter() - s
        s = time.perf_counter(); paq, _ = v3.deduplicar_espejo(util); T["dedup"] = time.perf_counter() - s
        s = time.perf_counter(); at = v2.attribute_packets(paq, red); T["atrib"] = time.perf_counter() - s
        i0, i1 = bisect.bisect_left(eve_t, k - HIST), bisect.bisect_right(eve_t, me)
        s = time.perf_counter()
        with tmp.open("w", encoding="utf-8") as fo:
            for _, l in eve[i0:i1]:
                fo.write(l)
        T["eve_w"] = time.perf_counter() - s
        s = time.perf_counter(); apps = v2.load_app_observations(tmp, red); T["eve_r"] = time.perf_counter() - s
        obs = [p.timestamp for p in at] + [x.timestamp for x in apps]
        cs = min(a.arranque_motor, min(obs))
        s = time.perf_counter(); rows = v2.build_rows("perfil", at, apps, step_seconds=10, capture_start=cs); T["rows"] = time.perf_counter() - s
        # alternativa sin tocar el extractor: misma función, llamada por entidad con solo sus observaciones
        s = time.perf_counter()
        por_p, por_a = collections.defaultdict(list), collections.defaultdict(list)
        for p in at:
            por_p[p.entity_ip].append(p)
        for x in apps:
            por_a[x.entity_ip].append(x)
        rows_part = []
        for ent in sorted(set(por_p) | set(por_a)):
            rows_part += v2.build_rows("perfil", por_p[ent], por_a[ent], step_seconds=10, capture_start=cs)
        t_part = time.perf_counter() - s
        iguales = rows_part == rows
        nuevas = rows[-c["n"]:] if c["n"] else []
        s = time.perf_counter()
        for r in nuevas:
            if r["packet_count_10s"]:
                pipe.score_samples([[float(r[x]) for x in nombres]])
        T["score"] = time.perf_counter() - s
        hora = datetime.datetime.fromtimestamp(k, datetime.timezone.utc).strftime("%H:%M:%S")
        print(",".join(str(v) for v in [hora, round(c["fin"] - k, 1), c["n"], len(fb), len(frames), len(util), len(paq),
                                         len(at), i1 - i0, len(apps), len(rows), round(t_parse, 2),
                                         *[round(T[x], 2) for x in ("filtro", "dedup", "atrib", "eve_w", "eve_r", "rows", "score")],
                                         round(sum(T.values()), 1), round(t_part, 2), iguales]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
