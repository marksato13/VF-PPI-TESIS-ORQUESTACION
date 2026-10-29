#!/usr/bin/env python3
"""Evidencia de destino y actividad observada por episodio, desde el PCAP full-SPAN archivado (corre en el sensor).

No toca el detector ni la red: lee marcas.jsonl, motor_decision.log y los PCAP cerrados que copió archivar_captura.sh.

Salidas:
  --salida-csv   episodio_id,window_end_utc,destino   (formato de analizar.py --destinos)
                 Una fila por destino observado en el intervalo de la ventana (window_end-60, window_end], que es el
                 mismo intervalo que analizar.py usa para relacionar una ventana con el ataque. window_end_utc se copia
                 literal del registro del motor. Una ventana sin paquetes del origen en ese intervalo NO recibe fila
                 (el analizador la trata como atribución incompleta; no se inventa un destino).
  --salida-json  actividad observada por episodio: paquetes del origen por destino, primer y último paquete hacia el
                 destino del episodio, SYN TCP hacia ese destino y PCAP leídos. Es actividad que CRUZÓ EL ESPEJO; no
                 son intentos del generador ni respuestas confirmadas.

Uso (sensor):
  python3 extraer_evidencia_destino.py --marcas marcas.jsonl --motor motor_decision.log \
      --pcap-dir archivo-pcap --salida-csv destinos.csv --salida-json actividad.json
"""
from __future__ import annotations
import argparse, csv, json, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402  (mismas lecturas de marcas y motor que el analizador)

HORIZONTE_S = an.HORIZONTE_S
DURACION_PCAP_S = 15
LINEA = re.compile(r"^(\d+\.\d+) IP (\d+\.\d+\.\d+\.\d+)(?:\.\d+)? > (\d+\.\d+\.\d+\.\d+)(?:\.\d+)?: (.*)$")


def inicio_pcap(p: Path) -> float | None:
    m = re.match(r"live-(\d{14})\.pcap$", p.name)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()


def paquetes(ficheros, origen, vlan):
    """(ts, destino, es_syn) de los paquetes IPv4 con origen dado, leídos con tcpdump.

    El espejo entrega las tramas con etiqueta 802.1Q y cada paquete enrutado aparece dos veces (VLAN de origen y VLAN
    de destino). Se leen solo las de la VLAN del origen, así cada paquete emitido cuenta una vez."""
    for f in ficheros:
        out = subprocess.run(["tcpdump", "-tt", "-nn", "-r", str(f), "vlan", str(vlan), "and", "src", "host", origen],
                             capture_output=True, text=True)
        for ln in out.stdout.splitlines():
            m = LINEA.match(ln)
            if m:
                resto = m.group(4)
                syn = resto.startswith("Flags [S]")
                yield float(m.group(1)), m.group(3), syn


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True)
    ap.add_argument("--motor", required=True)
    ap.add_argument("--pcap-dir", required=True)
    ap.add_argument("--origen", default="10.10.20.30")
    ap.add_argument("--vlan-origen", type=int, default=20, help="VLAN 802.1Q del origen en el espejo")
    ap.add_argument("--salida-csv", required=True)
    ap.add_argument("--salida-json", required=True)
    a = ap.parse_args()

    eps, inc_m = an.leer_marcas(Path(a.marcas))
    regs, _, _ = an.leer_motor(Path(a.motor))
    kali = [r for r in regs if r["entity_ip"] == a.origen]
    pcaps = sorted((inicio_pcap(p), p) for p in Path(a.pcap_dir).glob("live-*.pcap") if inicio_pcap(p) is not None)

    filas, actividad = [], {}
    for eid, ep in sorted(eps.items(), key=lambda kv: kv[1]["inicio_ep"]):
        ini, fin = ep["inicio_ep"], ep["fin_ep"]
        if fin is None:
            actividad[eid] = {"estado": ep["estado"], "nota": "sin fin: no se extrae evidencia"}
            continue
        desde, hasta = ini - HORIZONTE_S, fin + HORIZONTE_S
        fich = [p for t, p in pcaps if t + DURACION_PCAP_S >= desde and t <= hasta]
        pk = sorted(paquetes(fich, a.origen, a.vlan_origen))
        # ventanas de la Kali durante el ataque, igual que analizar.cobertura/_evidencia_destino_cubre
        ventanas = [r for r in kali if ini < r["_wend"] <= fin]
        sin_paquetes = 0
        for r in ventanas:
            w = r["_wend"]
            dst = sorted({d for t, d, _ in pk if w - HORIZONTE_S < t <= w})
            if not dst:
                sin_paquetes += 1
            for d in dst:
                filas.append({"episodio_id": eid, "window_end_utc": r["window_end_utc"], "destino": d})
        en_ataque = [(t, d, s) for t, d, s in pk if ini <= t <= fin]
        hacia = [(t, s) for t, d, s in en_ataque if d == ep["destino"]]
        posterior = [t for t, d, _ in pk if d == ep["destino"] and fin < t <= fin + HORIZONTE_S]
        actividad[eid] = {
            "escenario": ep["escenario"], "repeticion": ep["repeticion"], "destino": ep["destino"],
            "inicio_utc": an.iso(ini), "fin_utc": an.iso(fin), "estado_generador": ep["estado"],
            "duracion_comando_s": round(fin - ini, 3),
            "pcap_leidos": [p.name for p in fich],
            "paquetes_origen_durante_por_destino": dict(Counter(d for _, d, _ in en_ataque).most_common()),
            "paquetes_hacia_destino_durante": len(hacia),
            "syn_tcp_hacia_destino_durante": sum(1 for _, s in hacia if s),
            "primer_paquete_hacia_destino_utc": an.iso(hacia[0][0]) if hacia else None,
            "ultimo_paquete_hacia_destino_utc": an.iso(hacia[-1][0]) if hacia else None,
            "actividad_observada_s": round(hacia[-1][0] - hacia[0][0], 3) if hacia else 0.0,
            "paquetes_hacia_destino_hasta_fin_mas_60": len(posterior),
            "ventanas_kali_durante": len(ventanas), "ventanas_sin_paquetes_del_origen": sin_paquetes,
        }
    with open(a.salida_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["episodio_id", "window_end_utc", "destino"])
        w.writeheader()
        w.writerows(filas)
    Path(a.salida_json).write_text(json.dumps({
        "fuente": "PCAP full-SPAN archivado (archivar_captura.sh); tcpdump -tt -nn 'vlan <vlan_origen> and src host "
                  "<origen>' (una copia por paquete: la de la VLAN del origen)",
        "vlan_origen": a.vlan_origen,
        "intervalo_ventana": f"(window_end-{HORIZONTE_S}, window_end]", "origen": a.origen,
        "nota": "actividad que cruzó el espejo; no equivale a intentos del generador ni a respuestas del servidor",
        "incidencias_marcas": inc_m, "episodios": actividad}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(filas)} filas de destino; {len(actividad)} episodios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
