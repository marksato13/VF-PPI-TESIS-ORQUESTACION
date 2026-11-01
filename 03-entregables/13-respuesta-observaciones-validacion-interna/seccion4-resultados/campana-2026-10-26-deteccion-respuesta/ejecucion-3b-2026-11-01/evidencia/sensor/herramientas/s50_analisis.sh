#!/usr/bin/env bash
# PASO3B s50 — sensor: analisis completo con las herramientas verificadas (hashes en herramientas/). Solo lee las
# copias de la ejecucion y escribe en ~/cf-3b-ID/analisis/. Uso: s50_analisis.sh <inv_desde_iso> <inv_hasta_iso>
#  1) evidencia de destino formato 3b   2) calidad de fuentes   3) suricata-stats.json (conversion de stats.log)
#  4) recalculo de las 28 caracteristicas (respaldo)   5) respaldos + descriptor   6) verificar_integridad
#  7) analizar_3b (7 configuraciones, poblacion comun, inventario offline, control)
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; H=$B/herramientas; C=$B/copias; A=$B/analisis; PY=$HOME/cyberflow/.venv/bin/python
[ -e "$A" ] && { echo "PARAR: existe $A"; exit 2; }
mkdir -p "$A"; cd "$H"
echo "## s50 $(date -u +%FT%T.%3NZ) inventario=[$1, $2]"
sha256sum $H/*.py $H/config-campana-3b.json | tee $A/sha256-herramientas.txt | sed 's/^/  /'
M=$C/marcas.jsonl; L=$C/motor_decision.log
echo "## 1) destinos 3b"; python3 extraer_evidencia_destino.py --formato 3b --marcas $M --motor $L --pcap-dir $B/archivo-pcap \
  --salida-csv $A/destinos-3b.csv --salida-json $A/actividad-3b.json > $A/destinos.stdout 2> $A/destinos.stderr; echo "  rc=$?"; tail -2 $A/destinos.stdout
echo "## 2) calidad de fuentes"; python3 calidad_fuentes.py --marcas $M --stats $C/stats-inicio.log $C/stats-fin.log \
  --archivador $C/archivar.log --muestras $C/muestras.jsonl --salida $A/calidad-fuentes.json > $A/calidad.stdout 2> $A/calidad.stderr; echo "  rc=$?"
echo "## 3) suricata-stats.json (conversion de stats.log: Date + capture.kernel_packets/drops)"
python3 - $C/stats-fin.log $A/suricata-stats.json <<'PY'
import sys, json, re
from datetime import datetime, timezone
out, cur = [], None
for l in open(sys.argv[1], errors="replace"):
    m = re.match(r"Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)", l)
    if m:
        mo, d, y, hh, mm, ss = map(int, m.groups()); cur = {"momento": datetime(y, mo, d, hh, mm, ss, tzinfo=timezone.utc).timestamp()}
        cur["timestamp"] = datetime.fromtimestamp(cur["momento"], timezone.utc).isoformat(); continue
    m = re.match(r"capture\.kernel_(packets|drops)\s*\|\s*Total\s*\|\s*(\d+)", l)
    if m and cur is not None:
        cur["kernel_" + m.group(1)] = int(m.group(2))
        if "kernel_packets" in cur and "kernel_drops" in cur and cur["momento"] >= 1793515200:   # desde 2026-11-01 07:00Z
            out.append(cur); cur = None
json.dump(out, open(sys.argv[2], "w"), indent=0); print("  muestras:", len(out), "drops", out[0]["kernel_drops"], "->", out[-1]["kernel_drops"])
PY
echo "## 4) recalculo de caracteristicas"; AR=$(cat $HOME/cf-paso2-20261101T0254Z/reinicio.t)
$PY recalcular_caracteristicas.py --marcas $M --motor $L --pcap-dir $B/archivo-pcap --eve $C/eve-segmento.json \
  --arranque-motor $AR --salida $A/caracteristicas.jsonl > $A/recalculo.stdout 2> $A/recalculo.stderr; echo "  rc=$? $(tail -1 $A/recalculo.stdout)"
echo "## 5) respaldos y descriptor"
python3 generar_respaldos.py --marcas $M --motor $L --eve $C/eve-segmento.json --caracteristicas $A/caracteristicas.jsonl \
  --pcap-dir $B/archivo-pcap --relojes $C/relojes-3b.log --servicios-inicio $B/estado-inicial/servicios.txt \
  --servicios-fin $C/servicios-fin.txt --suricata-stats $A/suricata-stats.json $( [ -f $C/descartes-tcpdump.json ] && echo --descartes-tcpdump $C/descartes-tcpdump.json ) \
  --campana campana-A-repetida-3b-$ID --salida-dir $A/respaldos > $A/respaldos.stdout 2> $A/respaldos.stderr; echo "  rc=$?"; tail -2 $A/respaldos.stdout
echo "## 6) integridad"; python3 verificar_integridad.py --descriptor $A/respaldos/descriptor-integridad.json --salida $A/integridad.json > $A/integridad.stdout 2> $A/integridad.stderr; echo "  rc=$?"; tail -3 $A/integridad.stdout
echo "## 7) analizar_3b"
python3 analizar_3b.py --marcas $M --motor $L --config $H/config-campana-3b.json --ciclos $C/ciclos.jsonl \
  --inventario $B/replay/motor_decision.log --inventario-rango "$1,$2" --destinos $A/destinos-3b.csv \
  --integridad $A/integridad.json --calidad-fuentes $A/calidad-fuentes.json \
  --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "campaña A repetida (3B) 2026-11-01" \
  --salida $A/analisis-3b > $A/analizar.stdout 2> $A/analizar.stderr; echo "  rc=$?"; tail -25 $A/analizar.stdout
( cd $A && find . -type f ! -name SHA256SUMS -exec sha256sum {} + > SHA256SUMS ); echo "## fin $(date -u +%FT%T.%3NZ)"
