#!/usr/bin/env bash
# PASO2 k01 — Kali: simulacion SIN trafico del episodio tecnico (comprueba hashes, validacion y comando).
set -u
cd ~/cf-paso2-20261101T0254Z
python3 kali_episodio_tecnico.py --rep SIM --salida-dir ~/cf-paso2-20261101T0254Z/simulacion-sin-trafico; echo "rc=$?"
cut -c1-900 simulacion-sin-trafico/marcas.jsonl
python3 -c 'import json;c=json.load(open("simulacion-sin-trafico/config-tecnica.json"));print(c["_campana"]);print(c["_comando_constructor_aprobado"])'
echo "procesos curl: $(pgrep -c curl)"
