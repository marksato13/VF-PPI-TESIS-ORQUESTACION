#!/usr/bin/env python3
"""Reproduce, ciclo a ciclo, lo que el motor tenia disponible al decidir (solo lectura).

Para cada ciclo del motor (decisiones escritas seguidas; entre ciclos hay >= 0,5 s de espera) se acota su
inicio entre [ultimo registro del ciclo anterior + 0,5 s, primer registro del ciclo] y, para cada cota, se
reconstruye la entrada del motor desplegado:
  * PCAP: solo ficheros CERRADOS en ese instante (el motor excluye el mas nuevo, que tcpdump escribe), buffer
    podado a history_seconds (230 s) desde el paquete mas nuevo; protocolos 112/240 fuera; deduplicar_espejo;
    attribute_packets.
  * EVE: eventos con timestamp en [inicio-230, inicio].
  * capture_start = arranque del motor (24-oct) -> cobertura 60 s, como en vivo.
Despues v2.build_rows por entidad (cada fila solo usa observaciones de su entidad) y el mismo pipeline.
Compara packet_count_10s y score con lo registrado por el motor.
"""
from __future__ import annotations
import argparse, bisect, collections, ipaddress, json, sys
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402
import joblib  # noqa: E402

HIST = 230.0
ARRANQUE_MOTOR = 1792838970.0      # 2026-10-24 10:49:30 UTC (ActiveEnterTimestamp de ppi-motor)
EXCL = "10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32"
MODELO = RAIZ / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", action="append", required=True, type=Path)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--log", type=Path, default=RAIZ / "logs/motor_decision.log")
    ap.add_argument("--eve", type=Path, default=Path("/var/log/suricata/eve.json"))
    ap.add_argument("--solo-ciclos-con-cero", action="store_true")
    ap.add_argument("--max-ciclos", type=int, default=60)
    ap.add_argument("--ejemplos", type=int, default=12)
    ap.add_argument("--comparacion", type=Path, default=None,
                    help="JSONL de diag_ventanas.py: aporta el pk10 COMPLETO para clasificar los ceros con trafico")
    a = ap.parse_args()
    completo = {}
    if a.comparacion:
        for l in a.comparacion.open(encoding="utf-8"):
            f = json.loads(l); completo[tuple(f["clave"])] = f["completo"]["pk10"]
    cero_trafico = collections.Counter(); cero_ej = []
    d0, d1 = v2.parse_eve_timestamp(a.desde), v2.parse_eve_timestamp(a.hasta)
    red = ipaddress.ip_network("10.10.0.0/16")
    fuera = [ipaddress.ip_network(t, strict=False) for t in EXCL.split(",")]
    pipe = joblib.load(MODELO); nombres = v2.FEATURE_NAMES

    regs = []
    with a.log.open(encoding="utf-8") as fh:
        for l in fh:
            if '"event": "decision"' in l:
                r = json.loads(l)
                if d0 - 400 <= float(r["logged_at"]) <= d1 + 300:
                    regs.append(r)
    regs.sort(key=lambda r: float(r["logged_at"]))
    ciclos, act = [], [regs[0]]
    for r in regs[1:]:
        if float(r["logged_at"]) - float(act[-1]["logged_at"]) > 0.3:
            ciclos.append(act); act = [r]
        else:
            act.append(r)
    ciclos.append(act)

    ficheros = sorted({p for d in a.archivo for p in d.glob("live-*.pcap")}, key=lambda p: p.name)
    idx, ctx_por = [], []
    for f in ficheros:
        marcas, cs = [], []
        for t, tr in v2.iter_pcap_frames(f):
            marcas.append(t)
            c = v3.parse_con_contexto(t, tr)
            if c is not None and c.packet.protocol not in (112, 240):
                cs.append(c)
        if marcas:
            idx.append((marcas[0], marcas[-1])); ctx_por.append(cs)
    primeros = [x[0] for x in idx]

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
            if d0 - 700 <= t <= d1 + 300:
                eve.append((t, linea))
    eve.sort(key=lambda x: x[0]); eve_t = [x[0] for x in eve]
    tmp = Path("/tmp/emular_eve.jsonl")

    def reconstruir(inicio: float, entidades: set[str]):
        """-> ({(ip, window_end): fila}, marca de agua PCAP) con lo disponible en 'inicio'."""
        i = bisect.bisect_right(primeros, inicio) - 1          # fichero activo (mas nuevo creado <= inicio)
        if i < 1:
            return None, None
        nuevo = idx[i - 1][1]                                    # ultimo paquete de los cerrados
        buf = [c for j in range(i) if idx[j][1] >= nuevo - HIST
               for c in ctx_por[j] if c.packet.timestamp >= nuevo - HIST]
        paq, _ = v3.deduplicar_espejo(buf)
        at = v2.attribute_packets(paq, red)
        lo, hi = bisect.bisect_left(eve_t, inicio - HIST), bisect.bisect_right(eve_t, inicio)
        with tmp.open("w", encoding="utf-8") as out:
            for _, l in eve[lo:hi]:
                out.write(l)
        apps = v2.load_app_observations(tmp, red)
        filas = {}
        for e in entidades:
            pe = [p for p in at if p.entity_ip == e]; ae = [x for x in apps if x.entity_ip == e]
            if pe or ae:
                for r in v2.build_rows("emul", pe, ae, step_seconds=10, capture_start=ARRANQUE_MOTOR):
                    filas[(e, r["window_end_utc"])] = r
        return filas, nuevo

    def sc(f):
        return float(pipe.score_samples([[float(f[n]) for n in nombres]])[0]) if f and f["packet_count_10s"] else None

    tot = collections.Counter(); ejemplos = []; n = 0
    for k in range(1, len(ciclos)):
        c = ciclos[k]
        dentro = [r for r in c if d0 <= v2.parse_eve_timestamp(r["window_end_utc"]) <= d1
                  and not any(ipaddress.ip_address(r["entity_ip"]) in x for x in fuera)]
        if not dentro:
            continue
        if a.solo_ciclos_con_cero and not any(int(r["packet_count_10s"]) == 0 for r in dentro):
            continue
        n += 1
        if n > a.max_ciclos:
            break
        L = float(ciclos[k - 1][-1]["logged_at"]) + 0.5; U = float(c[0]["logged_at"])
        ents = {r["entity_ip"] for r in dentro}
        cot = {"inf": reconstruir(L, ents), "sup": reconstruir(U, ents)}
        # la cota que reproduce mas registros exactamente (pk10 y score)
        def exactos(nom):
            filas, _ = cot[nom]
            if filas is None:
                return -1
            m = 0
            for r in dentro:
                f = filas.get((r["entity_ip"], r["window_end_utc"]))
                s = sc(f)
                if f is not None and int(f["packet_count_10s"]) == int(r["packet_count_10s"]) and \
                   ((s is None and r.get("score") is None) or (s is not None and r.get("score") is not None and abs(s - r["score"]) < 1e-9)):
                    m += 1
            return m
        ex = {nom: exactos(nom) for nom in cot}
        nom = max(ex, key=ex.get)
        filas, marca = cot[nom]
        tot["ciclos"] += 1; tot[f"cota_elegida_{nom}"] += 1
        tot["cotas_misma_marca"] += int(cot["inf"][1] == cot["sup"][1])
        for r in dentro:
            f = filas.get((r["entity_ip"], r["window_end_utc"])) if filas else None
            s = sc(f); we = v2.parse_eve_timestamp(r["window_end_utc"])
            tot["decisiones"] += 1
            pk_ok = f is not None and int(f["packet_count_10s"]) == int(r["packet_count_10s"])
            s_ok = f is not None and ((s is None and r.get("score") is None) or
                                      (s is not None and r.get("score") is not None and abs(s - r["score"]) < 1e-9))
            tot["reproducidas_exactas"] += int(pk_ok and s_ok)
            tot["reproducidas_pk10"] += int(pk_ok)
            pc = completo.get((r["entity_ip"], r["window_end_utc"]))
            if int(r["packet_count_10s"]) == 0 and pc:
                # cero en vivo con trafico real: ¿lo reproduce la emulacion y la ventana terminaba despues de la
                # marca de agua de los PCAP cerrados en la cota que lo reproduce?
                rep = {nm: (cot[nm][0] or {}).get((r["entity_ip"], r["window_end_utc"])) for nm in cot}
                rep_ok = [nm for nm in cot if rep[nm] is not None and int(rep[nm]["packet_count_10s"]) == 0]
                posterior = [nm for nm in rep_ok if cot[nm][1] is not None and we > cot[nm][1]]
                clave = ("reproducido" if rep_ok else "NO_reproducido") + \
                        ("__ventana_posterior_a_marca_pcap" if posterior else ("__ventana_dentro_de_marca" if rep_ok else ""))
                cero_trafico[clave] += 1
                if len(cero_ej) < 8 or not posterior:
                    cero_ej.append({"clave": [r["entity_ip"], r["window_end_utc"]], "completo_pk10": pc,
                                    "logged_at": r["logged_at"], "inicio_ciclo_entre": [round(L, 3), round(U, 3)],
                                    "marca_pcap": {nm: cot[nm][1] for nm in cot}, "reproduce": rep_ok, "clase": clave})
            if int(r["packet_count_10s"]) == 0:
                tot["vivo_cero"] += 1
                tot["vivo_cero_reproducido"] += int(pk_ok)
                tot["vivo_cero_con_ventana_posterior_a_marca"] += int(marca is not None and we > marca)
            if not (pk_ok and s_ok) and len(ejemplos) < a.ejemplos:
                ejemplos.append({"ciclo": k, "cota": nom, "clave": [r["entity_ip"], r["window_end_utc"]],
                                 "logged_at": r["logged_at"], "marca_pcap": marca,
                                 "vivo": [r["packet_count_10s"], r.get("score")],
                                 "emulado": [f["packet_count_10s"] if f else None, s]})
            if int(r["packet_count_10s"]) == 0 and len([e for e in ejemplos if e.get("tipo") == "cero"]) < 6:
                ejemplos.append({"tipo": "cero", "ciclo": k, "cota": nom, "clave": [r["entity_ip"], r["window_end_utc"]],
                                 "logged_at": r["logged_at"], "marca_pcap": marca,
                                 "ventana_posterior_a_marca": marca is not None and we > marca,
                                 "vivo": [r["packet_count_10s"], r.get("score")],
                                 "emulado": [f["packet_count_10s"] if f else None, s]})
    print(f"## emulacion de ciclos [{a.desde}, {a.hasta}] solo_con_cero={a.solo_ciclos_con_cero}")
    for k, v in tot.items():
        print(f"   {k:45s} {v}")
    if a.comparacion:
        print("## ceros en vivo con trafico real (pk10 completo > 0)")
        for k, v in cero_trafico.most_common():
            print(f"   {k:60s} {v}")
        for e in cero_ej[:20]:
            print("  ", json.dumps(e))
    print("## ejemplos (no reproducidos y ceros)")
    for e in ejemplos:
        print("  ", json.dumps(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
