#!/usr/bin/env bash
# PASO3A s06 — sensor (solo lectura de la evidencia del paso 2): destinos formato 3b y calidad de fuentes por episodio.
# Escribe solo en ~/cf-paso3a-20261101T0523Z/reanalisis-paso2/. No toca motor, captura ni Suricata.
set -u
B=$HOME/cf-paso3a-20261101T0523Z; H=$B/herramientas3b; P2=$HOME/cf-paso2-20261101T0254Z; O=$B/reanalisis-paso2
mkdir -p $O
echo "## s06 $(date -u +%FT%T.%3NZ)"
ls $P2/copias | tr '\n' ' '; echo
ls $P2/archivo-pcap | head -2; echo "pcap: $(ls $P2/archivo-pcap/*.pcap | wc -l)"
cd $H
python3 extraer_evidencia_destino.py --formato 3b --marcas $P2/copias/marcas-episodios.jsonl \
  --motor $P2/copias/motor_decision.log --pcap-dir $P2/archivo-pcap \
  --salida-csv $O/destinos-3b.csv --salida-json $O/actividad-3b.json 2>&1 | tail -3
python3 calidad_fuentes.py --marcas $P2/copias/marcas-episodios.jsonl \
  --stats $P2/copias/stats-inicio.log $P2/copias/stats-fin.log --archivador $P2/archivo-pcap/archivar.log \
  --muestras $P2/copias/muestras.jsonl --salida $O/calidad-fuentes.json 2>&1 | tail -20
sha256sum $O/* $H/*.py
echo "## fin"
