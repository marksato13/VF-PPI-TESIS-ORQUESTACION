#!/usr/bin/env bash
# Analisis definitivo con inventario frente a la repeticion offline (solo lectura de evidencias; escribe resultados.json)
set -u
B=$HOME/cf-paso2-20261101T0254Z
echo "replay rc: $(cat $B/replay/rc.txt)  decisiones replay: $(grep -c '"decision"' $B/replay/motor_decision.log)"
python3 $B/herramientas/analizar_p2.py --base $B --copias copias --t-normal 2026-11-01T03:20:00Z --t-fin 2026-11-01T04:18:15Z \
  --replay $B/replay/motor_decision.log --salida $B/copias/resultados.json || exit 1
sha256sum $B/copias/resultados.json $B/herramientas/analizar_p2.py $B/copias/eve-segmento.json
python3 - $B/copias/resultados.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
inv = d.get("inventario") or d.get("inventario_replay")
print("CLAVES:", list(d.keys()))
print("INVENTARIO:", json.dumps(inv, default=str)[:6000])
for c, v in d["condiciones"].items():
    print(c, "http", v["http_kali_servidor"])
    print("   etapas", json.dumps(v.get("etapas_s") or v.get("etapas"), default=str)[:900])
for k, e in d["deteccion"].items():
    print(k, "derivadas", e["derivadas_durante"], "emitidas", e["emitidas"])
print(json.dumps(d["alertas_no_kali_por_condicion"].get("normal"), indent=0))
PY
