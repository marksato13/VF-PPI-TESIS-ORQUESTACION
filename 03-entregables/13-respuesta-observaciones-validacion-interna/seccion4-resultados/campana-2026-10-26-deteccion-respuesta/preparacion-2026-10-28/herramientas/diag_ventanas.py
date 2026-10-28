#!/usr/bin/env python3
"""Diagnostico de ventanas registradas por el motor con 0 paquetes vivos (solo lectura).

Para cada decision del motor (entidad, window_end) en un rango compara, por la MISMA clave:
  * VIVO     : lo que registro el motor (packet_count_10s, score, detector, logged_at).
  * COMPLETO : la misma ventana recalculada con el CODIGO DEL MOTOR (parse_con_contexto, exclusion de
               protocolos, deduplicar_espejo, attribute_packets, v2.build_rows, mismo pipeline/modelo) sobre
               las fuentes completas: PCAP full-SPAN archivados + eve.json.
  * LOTES    : la fila de multilayer-v3.csv (acumular_v3), con su score calculado por el mismo pipeline.
y reconstruye la DISPONIBILIDAD de la fuente PCAP en el instante de la decision: que ficheros estaban
cerrados (el motor solo lee los cerrados) y hasta que paquete llegaban (marca de agua PCAP), a partir de las
marcas de primer/ultimo paquete de cada fichero archivado. Tambien la marca de agua EVE (evento mas nuevo con
timestamp <= logged_at entre los tipos que usa el motor) para ver si L7 estaba completo.

No modifica nada. Se ejecuta en el sensor con el venv del motor:
  ~/cyberflow/.venv/bin/python diag_ventanas.py --archivo DIR [--archivo DIR2] --desde ISO --hasta ISO
"""
from __future__ import annotations
import argparse, bisect, collections, csv, ipaddress, json, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402
import joblib  # noqa: E402

EXCL = "10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32"
MODELO = RAIZ / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"
TIPOS_L7 = ('"event_type":"http"', '"event_type":"dns"', '"event_type":"tls"')


def ts(iso: str) -> float:
    return v2.parse_eve_timestamp(iso)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", action="append", required=True, type=Path)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--log", type=Path, default=RAIZ / "logs/motor_decision.log")
    ap.add_argument("--csv", type=Path, default=RAIZ / "artifacts/linea-base/multilayer-v3.csv")
    ap.add_argument("--eve", type=Path, action="append", default=None)
    ap.add_argument("--ejemplos", type=int, default=6)
    ap.add_argument("--json", type=Path, default=None, help="vuelca la comparacion por clave")
    a = ap.parse_args()
    eves = a.eve or [Path("/var/log/suricata/eve.json")]
    d0, d1 = ts(a.desde), ts(a.hasta)
    red = ipaddress.ip_network("10.10.0.0/16")
    fuera = [ipaddress.ip_network(t, strict=False) for t in EXCL.split(",")]
    excl = lambda ip: any(ipaddress.ip_address(ip) in r for r in fuera)
    nombres = v2.FEATURE_NAMES
    pipe = joblib.load(MODELO)

    # --- 1) PCAP archivados: indice de disponibilidad + paquetes con el codigo del motor
    ficheros = sorted({p for d in a.archivo for p in d.glob("live-*.pcap")}, key=lambda p: p.name)
    indice = []          # (primer_ts, ultimo_ts, nombre)
    contextos, tramas, vlan_tag, no_ip = [], 0, 0, 0
    for f in ficheros:
        marcas = []
        for t, trama in v2.iter_pcap_frames(f):
            marcas.append(t)
            if not (d0 - 300 <= t <= d1 + 60):
                continue
            tramas += 1
            c = v3.parse_con_contexto(t, trama)
            if c is None:
                no_ip += 1
                continue
            if c.vlan:
                vlan_tag += 1
            if c.packet.protocol not in (112, 240):
                contextos.append(c)
        if marcas:
            indice.append((marcas[0], marcas[-1], f.name))
    indice.sort()
    primeros = [x[0] for x in indice]

    def marca_pcap(T: float):
        """Hasta donde llegaban los PCAP CERRADOS en T: el motor excluye el fichero mas nuevo existente."""
        i = bisect.bisect_right(primeros, T) - 1      # fichero activo (mas nuevo creado <= T)
        if i <= 0:
            return None, None
        return indice[i - 1][1], indice[i][2]

    huecos = [round(b[0] - a_[1], 3) for a_, b in zip(indice, indice[1:])]
    paquetes, dup = v3.deduplicar_espejo(contextos)
    atrib = v2.attribute_packets(paquetes, red)

    # --- 2) EVE (mismo cargador del motor) + marca de agua L7
    tmp = Path("/tmp/diag_eve_slice.jsonl")
    l7 = []
    with tmp.open("w", encoding="utf-8") as out:
        for e in eves:
            if not e.exists():
                continue
            with e.open("r", encoding="utf-8", errors="replace") as fh:
                for linea in fh:
                    i = linea.find('"timestamp":"')
                    if i < 0:
                        continue
                    try:
                        t = ts(linea[i + 13:i + 13 + 31].split('"')[0])
                    except ValueError:
                        continue
                    if d0 - 300 <= t <= d1 + 60:
                        out.write(linea)
                        if any(k in linea for k in TIPOS_L7):
                            l7.append(t)
    l7.sort()
    apps = v2.load_app_observations(tmp, red)
    inicio = min([p.timestamp for p in atrib] + [x.timestamp for x in apps])
    filas = v2.build_rows("diag-completo", atrib, apps, step_seconds=10, capture_start=inicio)
    completo = {(r["entity_ip"], r["window_end_utc"]): r for r in filas}

    # --- 3) VIVO (log del motor) y LOTES (csv)
    vivo = {}
    with a.log.open(encoding="utf-8") as fh:
        for l in fh:
            if '"event": "decision"' not in l:
                continue
            r = json.loads(l)
            we = ts(r["window_end_utc"])
            if d0 <= we <= d1 and not excl(r["entity_ip"]):
                vivo.setdefault((r["entity_ip"], r["window_end_utc"]), []).append(r)
    lotes = {}
    with a.csv.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if d0 <= ts(r["window_end_utc"]) <= d1:
                lotes[(r["entity_ip"], r["window_end_utc"])] = r

    def score(fila):
        return float(pipe.score_samples([[float(fila[n]) for n in nombres]])[0])

    # --- 4) comparacion por clave
    cls = collections.Counter(); ej = collections.defaultdict(list); filas_json = []
    retraso = []; dup_keys = sum(1 for v in vivo.values() if len(v) > 1)
    for k, regs in sorted(vivo.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        r = regs[0]; we = ts(k[1]); la = float(r["logged_at"])
        retraso.append(la - we)
        c = completo.get(k); b = lotes.get(k)
        mp, activo = marca_pcap(la)
        j = bisect.bisect_right(l7, la); me = l7[j - 1] if j else None
        pk_v = int(r["packet_count_10s"]); pk_c = int(c["packet_count_10s"]) if c else None
        pk_b = int(float(b["packet_count_10s"])) if b else None
        s_v = r.get("score"); s_c = score(c) if c and pk_c else None
        s_b = score(b) if b and pk_b else None
        pcap_ok = mp is not None and mp >= we
        eve_ok = me is not None and me >= we
        if c is None:
            clase = "sin_referencia_completa"
        elif pk_v == 0 and pk_c == 0:
            clase = "vacia_real"
        elif pk_v == 0 and pk_c > 0:
            clase = "cero_vivo_con_trafico__pcap_incompleto" if not pcap_ok else "cero_vivo_con_trafico__pcap_completo"
        elif pk_v != pk_c:
            clase = "conteo_distinto__pcap_incompleto" if not pcap_ok else "conteo_distinto__pcap_completo"
        elif s_v is not None and s_c is not None and abs(s_v - s_c) > 1e-9:
            clase = "score_distinto__eve_incompleto" if not eve_ok else "score_distinto__eve_completo"
        else:
            clase = "igual"
        cls[clase] += 1
        fila = {"clave": k, "clase": clase, "logged_at": la, "retraso_s": round(la - we, 3),
                "marca_pcap": mp, "pcap_completo": pcap_ok, "fichero_activo": activo,
                "marca_eve": me, "eve_completo": eve_ok,
                "vivo": {"pk10": pk_v, "score": s_v, "detector": r.get("detector_name"), "decision": r.get("decision")},
                "completo": {"pk10": pk_c, "score": s_c}, "lotes": {"pk10": pk_b, "score": s_b}}
        if c is not None and clase.startswith("score_distinto"):
            fila["features_distintas_vs_completo"] = "no disponibles en el log vivo (solo pk10 y score)"
        if b is not None and c is not None:
            fila["features_distintas_completo_vs_lotes"] = {n: (c[n], b[n]) for n in nombres
                                                           if abs(float(c[n]) - float(b[n])) > 1e-6}
        filas_json.append(fila)
        if len(ej[clase]) < a.ejemplos:
            ej[clase].append(fila)

    print(f"## rango ventanas [{a.desde}, {a.hasta}]  | archivos PCAP {len(ficheros)} ({indice[0][2]} .. {indice[-1][2]})")
    print(f"   tramas en rango {tramas}: 802.1Q {vlan_tag} ({100*vlan_tag/max(tramas,1):.1f} %), no IP {no_ip}; "
          f"duplicados de espejo quitados {dup}; mayor hueco entre ficheros {max(huecos) if huecos else 0} s")
    print(f"   decisiones del motor (claves) {len(vivo)} | claves con >1 decision: {dup_keys} | filas completas {len(completo)} | filas lotes {len(lotes)}")
    q = statistics.quantiles(retraso, n=20) if len(retraso) > 2 else []
    print(f"   logged_at - window_end: min {min(retraso):.2f} p5 {q[0]:.2f} mediana {statistics.median(retraso):.2f} p95 {q[-1]:.2f} max {max(retraso):.2f} s")
    print("## clases")
    for k, n in cls.most_common():
        print(f"   {k:45s} {n}")
    con_trafico = sum(n for k, n in cls.items() if k.startswith(("cero_vivo", "conteo", "score", "igual")))
    print(f"   ventanas-entidad con trafico (completo pk10>0): {con_trafico}; vivo=0 entre ellas: "
          f"{cls['cero_vivo_con_trafico__pcap_incompleto'] + cls['cero_vivo_con_trafico__pcap_completo']}")
    # relacion clase / disponibilidad
    tab = collections.Counter((f["clase"], f["pcap_completo"]) for f in filas_json)
    print("## disponibilidad PCAP en el instante de la decision, por clase (pcap_completo=True/False)")
    for (k, ok), n in sorted(tab.items()):
        print(f"   {k:45s} pcap_completo={ok!s:5s} {n}")
    # coherencia completo vs lotes
    cmp_ = [f for f in filas_json if f["lotes"]["pk10"] is not None and f["completo"]["pk10"] is not None]
    igual_pk = sum(1 for f in cmp_ if f["lotes"]["pk10"] == f["completo"]["pk10"])
    print(f"## completo vs lotes: {len(cmp_)} claves comunes, pk10 igual en {igual_pk}; "
          f"con alguna feature distinta: {sum(1 for f in cmp_ if f.get('features_distintas_completo_vs_lotes'))}")
    print("## ejemplos")
    for k, lst in ej.items():
        for f in lst:
            print("  ", json.dumps(f, default=str)[:900])
    if a.json:
        a.json.write_text("\n".join(json.dumps(f, default=str) for f in filas_json) + "\n", encoding="utf-8")
        print(f"## comparacion por clave -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
