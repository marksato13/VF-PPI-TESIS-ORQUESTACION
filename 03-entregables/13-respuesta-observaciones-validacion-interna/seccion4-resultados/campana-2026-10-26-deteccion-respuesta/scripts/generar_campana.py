#!/usr/bin/env python3
"""Generador de la campaña (corre en la Kali del laboratorio autorizado).

Lee escenarios.json, ordena los episodios de forma aleatoria con la semilla fija, espera >=120 s entre
episodios y escribe marcas.jsonl con reloj de pared y monotónico, comando, código de salida y actividad.

SEGURO POR DEFECTO:
  - Sin --autorizado hace una simulación (imprime el plan, NO lanza tráfico).
  - Aborta si algún destino no está en la lista blanca de escenarios.json.
  - No se ejecuta en la fase de preparación.

Uso (cuando se autorice la campaña A):
    ZONA_LAB=lab-ppi BRUTE_PUERTO=8081 BRUTE_RUTA=/auth \\
      python3 generar_campana.py --escenarios ../escenarios/escenarios.json --salida marcas.jsonl --autorizado
"""
from __future__ import annotations
import argparse, json, os, random, subprocess, sys, time
from datetime import datetime, timezone

HERRAMIENTAS = {"dig", "curl", "nmap", "openssl"}


def ahora():
    return {"pared_utc": datetime.now(timezone.utc).isoformat(), "monotonico": time.monotonic()}


def comando_de(e: dict) -> list[str]:
    """Construye el comando real del escenario. Un episodio = un proceso de generación."""
    dst, sid = e["destino"], e["id"]
    if sid == "dns_inusual":
        zona = os.environ.get("ZONA_LAB", "<ZONA_LAB>")
        return ["bash", "-c", f'fin=$((SECONDS+{e["duracion_s"]})); '
                f'while [ $SECONDS -lt $fin ]; do dig +time=1 +tries=1 @{dst} "$(openssl rand -hex 8).{zona}" +short >/dev/null 2>&1; sleep 0.4; done']
    if sid == "inundacion_http":
        return ["bash", "-c", f'fin=$((SECONDS+{e["duracion_s"]})); '
                f'while [ $SECONDS -lt $fin ]; do curl -s -o /dev/null --max-time 2 http://{dst}/ ; done']
    if sid == "escaneo_breve":
        return ["nmap", "-sT", "-T4", "--max-retries", "1", "-p", "1-1000", dst]
    if sid == "escaneo_sostenido":
        r = os.environ.get("SCAN_RATE", "1500")
        return ["nmap", "-sT", "-T4", "--max-retries", "0", "--max-rate", r, "-p-", dst]
    if sid == "fuerza_bruta_http":
        pt, ruta = os.environ.get("BRUTE_PUERTO", "<PUERTO>"), os.environ.get("BRUTE_RUTA", "/<auth>")
        return ["bash", "-c", f'fin=$((SECONDS+{e["duracion_s"]})); '
                f'while [ $SECONDS -lt $fin ]; do curl -s -o /dev/null -w "%{{http_code}}\\n" --max-time 2 '
                f'-u fake:fake$RANDOM http://{dst}:{pt}{ruta} ; done']
    raise ValueError(f"escenario desconocido: {sid}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escenarios", required=True)
    ap.add_argument("--salida", default="marcas.jsonl")
    ap.add_argument("--autorizado", action="store_true", help="lanza el tráfico real; sin esto, solo simula")
    a = ap.parse_args()
    cfg = json.load(open(a.escenarios, encoding="utf-8"))
    blanca = set(cfg["lista_blanca_destinos"])
    for e in cfg["escenarios"]:
        if e["destino"] not in blanca:
            print(f"ABORTA: destino {e['destino']} ({e['id']}) fuera de la lista blanca {sorted(blanca)}", file=sys.stderr)
            return 2

    plan = []
    for rep in range(1, cfg["repeticiones"] + 1):
        for e in cfg["escenarios"]:
            plan.append((e, rep))
    random.Random(cfg["semilla"]).shuffle(plan)

    print(f"{'MODO SIMULACIÓN (no lanza tráfico)' if not a.autorizado else 'MODO AUTORIZADO'} · "
          f"{len(plan)} episodios · espera {cfg['espera_entre_episodios_s']} s entre ellos")
    out = open(a.salida, "a", encoding="utf-8") if a.autorizado else None
    for n, (e, rep) in enumerate(plan, 1):
        ep_id = f"{e['id']}-r{rep}"
        cmd = comando_de(e)
        print(f"[{n}/{len(plan)}] {ep_id}: {' '.join(cmd[:3])}…")
        if not a.autorizado:
            continue
        marca = {"episodio_id": ep_id, "escenario": e["id"], "repeticion": rep,
                 "comando": cmd, "inicio": ahora()}
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=e.get("duracion_s", 300) + 120)
            marca["codigo_salida"] = cp.returncode
            marca["stdout_cola"] = cp.stdout[-2000:]
        except subprocess.TimeoutExpired:
            marca["codigo_salida"] = "timeout"
        marca["fin"] = ahora()
        out.write(json.dumps(marca, ensure_ascii=False) + "\n")
        out.flush()
        if n < len(plan):
            time.sleep(cfg["espera_entre_episodios_s"])
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
