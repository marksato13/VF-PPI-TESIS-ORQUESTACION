#!/usr/bin/env python3
"""Runner del piloto de comparación (P0-09) — método de replay (nota 19).

Toma UN episodio `episodio.pcap` etiquetado y lo corre por los dos detectores
OFFLINE sobre el MISMO PCAP, anclando el tiempo al propio paquete (sin NTP):

  1) Suricata:   `suricata -r pcap -l out/suricata`  -> eve.json (alertas)
  2) CyberFlow:  extractor (pcap + ese eve.json) -> features.csv (window_end_utc)
                 -> 20-puntuar-por-ventana.py (modelo congelado) -> primera alerta
  3) Compara la PRIMERA alerta de cada uno contra t_inicio del ataque.

Produce `out/<id>/comparacion.json` y añade una fila a `out/resultados.csv`.

Se ejecuta DONDE está el detector desplegado (Sensor1) con su modelo y extractor.
Todos los paths son configurables; por defecto apuntan al extractor v3 (31 vars).

Ejemplo:
  python3 22-correr-piloto.py --id E3-dns-01 \
    --pcap /ruta/episodio.pcap --t-inicio 2026-10-02T12:00:00+00:00 \
    --familia dns_entropy \
    --extractor ~/cyberflow/scripts/features/extract_multilayer_v2.py \
    --schema ~/cyberflow/configs/features/multilayer-v2.json \
    --modelo ~/cyberflow/artifacts/preliminar/if_recalibrado_desplegable.joblib \
    --manifest ~/cyberflow/artifacts/preliminar/manifest-if-recalibrado.json \
    --detector-name if_recalibrado_2026_09 \
    --scorer ./20-puntuar-por-ventana.py \
    --entity-network 10.10.0.0/16 --outdir ./resultados-piloto

NO usa contraseñas. No aplica bloqueos. Solo lee el PCAP y escribe resultados.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _ts(valor: str) -> float | None:
    """epoch (float) o ISO-8601 (incl. '+0000' de Suricata) -> epoch."""
    if not valor:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        pass
    v = valor.strip().replace("Z", "+00:00")
    # Suricata emite '+0000' (sin dos puntos); fromisoformat quiere '+00:00'.
    v = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", v)
    try:
        return datetime.fromisoformat(v).timestamp()
    except ValueError:
        return None


def correr(cmd: list[str], registro: Path) -> tuple[int, str]:
    """Ejecuta un subproceso, guarda stdout+stderr, devuelve (rc, stdout)."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    registro.write_text(
        "$ " + " ".join(cmd) + "\n\n--- stdout ---\n" + (r.stdout or "")
        + "\n--- stderr ---\n" + (r.stderr or ""), encoding="utf-8")
    return r.returncode, (r.stdout or "")


def suricata_primera_alerta(eve: Path, t_inicio: float | None) -> dict:
    """Recorre eve.json: primera alerta (por ts del PCAP) y conteo."""
    primera = None
    n = 0
    firmas: dict[str, int] = {}
    if not eve.exists():
        return {"error": "no hay eve.json", "n_alertas": 0, "primera_alerta": None}
    with eve.open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or '"alert"' not in linea:
                continue
            try:
                ev = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if ev.get("event_type") != "alert":
                continue
            n += 1
            sig = (ev.get("alert") or {}).get("signature", "?")
            firmas[sig] = firmas.get(sig, 0) + 1
            te = _ts(ev.get("timestamp", ""))
            if te is not None and (primera is None or te < primera["epoch"]):
                primera = {"epoch": te, "timestamp": ev.get("timestamp"),
                           "firma": sig}
    if primera and t_inicio is not None:
        primera["tiempo_deteccion_s"] = round(primera["epoch"] - t_inicio, 3)
    return {"n_alertas": n, "firmas": firmas, "primera_alerta": primera}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True, help="id del episodio")
    ap.add_argument("--pcap", required=True, type=Path, help="PCAP del episodio")
    ap.add_argument("--t-inicio", required=True, help="inicio del ataque (epoch o ISO)")
    ap.add_argument("--familia", default="", help="metadato (E1-scan, E3-dns, ...)")
    ap.add_argument("--outdir", type=Path, default=Path("resultados-piloto"))
    # CyberFlow (valores por defecto = detector DESPLEGADO en Sensor1, que usa v2)
    ap.add_argument("--extractor", type=Path, required=True,
                    help="extract_multilayer_v2.py (el desplegado usa v2, no v3)")
    ap.add_argument("--schema", type=Path, required=True, help="multilayer-v2.json")
    ap.add_argument("--modelo", type=Path, required=True, help="Pipeline .joblib")
    ap.add_argument("--manifest", type=Path, required=True,
                    help="manifest-if-recalibrado.json (umbral + feature_names)")
    ap.add_argument("--detector-name", default="if_recalibrado_2026_09")
    ap.add_argument("--scorer", type=Path, required=True,
                    help="ruta a 20-puntuar-por-ventana.py")
    ap.add_argument("--entity-network", default="10.10.0.0/16")
    ap.add_argument("--excluir-protocolos", default="",
                    help="solo para el extractor v3; el v2 no lo acepta -> dejar vacío")
    # Suricata
    ap.add_argument("--suricata", default="suricata")
    ap.add_argument("--suricata-config", default="", help="yaml opcional (-c)")
    ap.add_argument("--python", default=sys.executable,
                    help="intérprete para extractor y scorer (venv del sensor)")
    a = ap.parse_args()

    t_inicio = _ts(a.t_inicio)
    if t_inicio is None:
        print(json.dumps({"error": "t-inicio no parseable", "valor": a.t_inicio}))
        return 2
    if not a.pcap.exists():
        print(json.dumps({"error": "no existe el PCAP", "pcap": str(a.pcap)}))
        return 2

    base = a.outdir / a.id
    (base / "suricata").mkdir(parents=True, exist_ok=True)

    # --- 1) Suricata offline ------------------------------------------------
    scmd = [a.suricata]
    if a.suricata_config:
        scmd += ["-c", a.suricata_config]
    scmd += ["-r", str(a.pcap), "-l", str(base / "suricata")]
    rc_s, _ = correr(scmd, base / "suricata.log")
    eve = base / "suricata" / "eve.json"
    suri = suricata_primera_alerta(eve, t_inicio)
    suri["rc"] = rc_s

    # --- 2) CyberFlow: extractor + scorer ----------------------------------
    features = base / "features.csv"
    ecmd = [a.python, str(a.extractor),
            "--pcap", str(a.pcap), "--eve", str(eve),
            "--campaign-id", a.id, "--output", str(features),
            "--schema", str(a.schema),
            "--entity-network", a.entity_network,
            "--capture-start", a.t_inicio]
    if a.excluir_protocolos:
        ecmd += ["--excluir-protocolos", a.excluir_protocolos]
    rc_e, _ = correr(ecmd, base / "extractor.log")

    cf: dict = {"rc_extractor": rc_e}
    if rc_e == 0 and features.exists():
        pcmd = [a.python, str(a.scorer),
                "--modelo", str(a.modelo),
                "--manifest", str(a.manifest),
                "--detector-name", a.detector_name,
                "--csv", str(features),
                "--t-inicio", a.t_inicio,
                "--salida-csv", str(base / "cyberflow-por-ventana.csv")]
        rc_p, out_p = correr(pcmd, base / "scorer.log")
        cf["rc_scorer"] = rc_p
        try:
            cf["resultado"] = json.loads(out_p)
        except json.JSONDecodeError:
            cf["resultado"] = {"error": "salida del scorer no es JSON",
                               "ver": str(base / "scorer.log")}
    else:
        cf["resultado"] = {"error": "el extractor falló o no generó CSV",
                           "ver": str(base / "extractor.log")}

    # --- 3) Comparación -----------------------------------------------------
    suri_td = (suri.get("primera_alerta") or {}).get("tiempo_deteccion_s")
    cf_prim = (cf.get("resultado") or {}).get("primera_alerta") or {}
    cf_td = cf_prim.get("tiempo_deteccion_s")

    def _quien() -> str:
        if suri_td is None and cf_td is None:
            return "ninguno detectó"
        if suri_td is None:
            return "solo CyberFlow"
        if cf_td is None:
            return "solo Suricata"
        if cf_td < suri_td:
            return "CyberFlow primero"
        if suri_td < cf_td:
            return "Suricata primero"
        return "empate"

    comp = {
        "id": a.id, "familia": a.familia, "pcap": str(a.pcap),
        "t_inicio": a.t_inicio,
        "suricata": suri,
        "cyberflow": cf,
        "quien_primero": _quien(),
    }
    (base / "comparacion.json").write_text(
        json.dumps(comp, indent=2, ensure_ascii=False), encoding="utf-8")

    # fila acumulada
    res = a.outdir / "resultados.csv"
    nuevo = not res.exists()
    with res.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["id", "familia", "t_inicio",
                        "suri_td_s", "suri_alertas",
                        "cf_td_s", "cf_detectadas", "quien_primero"])
        w.writerow([a.id, a.familia, a.t_inicio,
                    suri_td if suri_td is not None else "",
                    suri.get("n_alertas", 0),
                    cf_td if cf_td is not None else "",
                    (cf.get("resultado") or {}).get("detectadas", ""),
                    comp["quien_primero"]])

    print(json.dumps(comp, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
