#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s50 — análisis con herramientas verificadas. Solo lee las copias y escribe en
# ~/cf-e4/<fase>/analisis/. Sin sudo. Uso:
#   s50_analisis_e4.sh <4b|4c> <inv_desde_iso> <inv_hasta_iso> <control_desde_iso> <control_hasta_iso>
# Herramientas: ~/cf-e4/herramientas/ (copiadas del repositorio de documentación y verificadas con
# herramientas-e4.sha256); salud_captura.py y trafico_observado.py del candidato (~/cyberflow-e4/ec78ca5).
#  4b y 4c: a) salud: incrementos y clase del control (anillo y vía rápida)  b) control_4b (por clase, α, regla,
#           vía rápida, propuestas)  c) analizar_3b (cobertura contra el inventario, cotas)
#  solo 4c: 1) destinos 3b  2) calidad de fuentes (--duracion-pcap 5)  3) suricata-stats.json  4) recálculo de
#           características  5) respaldos  6) integridad  7) clase de salud por episodio  8) tráfico observado
#           9) referencia_trafico_4c (todas las marcas; escaneo breve contra la ráfaga real). La traza del relé
#           (bastión) se copia a mano a copias/traza-rele.jsonl antes de s50 (PROTOCOLO-4C §6); si falta, sin entrega.
# Resultado esperado: rc=0 en cada paso y SHA256SUMS. Parada: hash de una herramienta distinto ("PARAR").
set -u
FASE=${1:?fase}; ID=${2:?inv_desde}; IH=${3:?inv_hasta}; CD=${4:?control_desde}; CH=${5:?control_hasta}
B=$HOME/cf-e4/$FASE; H=$HOME/cf-e4/herramientas; C=$B/copias; A=$B/analisis; E4=$HOME/cyberflow-e4/ec78ca5
PY=$HOME/cyberflow/.venv/bin/python; SC=$E4/scripts/etapa4/salud_captura.py
[ -e "$A" ] && { echo "PARAR: existe $A"; exit 2; }
( cd "$H" && sha256sum -c --quiet herramientas-e4.sha256 ) || { echo "PARAR: herramientas con hash distinto"; exit 2; }
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: el código candidato no verifica"; exit 2; }
mkdir -p "$A"; cd "$H" || exit 2
echo "## s50-e4 $FASE $(date -u +%FT%T.%3NZ) inventario=[$ID, $IH] control=[$CD, $CH]"
sha256sum "$H"/*.py "$H"/*.json "$SC" "$E4/scripts/etapa4/trafico_observado.py" > "$A/sha256-herramientas.txt"
L=$C/motor_decision.log
if [ "$FASE" = 4b ]; then M=$A/marcas-vacias.jsonl; : > "$M"; else M=$C/marcas.jsonl; fi
echo "## a) salud"
python3 -I "$SC" intervalos "$B/salud/muestras.jsonl" "$B/salud/incrementos.jsonl"
python3 -I "$SC" clasificar --incrementos "$B/salud/incrementos.jsonl" --tcpdump-log "$B/salud/tcpdump-anillo.log" \
  --desde "$CD" --hasta "$CH" --rotacion 5 > "$A/salud-control-anillo.json"; echo "  control (IF/heur): $(grep -m1 '"clase"' "$A/salud-control-anillo.json")"
python3 -I "$SC" clasificar --incrementos "$B/salud/incrementos.jsonl" --tcpdump-log "$B/salud/tcpdump-via.log" \
  --desde "$CD" --hasta "$CH" --rotacion 5 > "$A/salud-control-via.json"; echo "  control (vía rápida): $(grep -m1 '"clase"' "$A/salud-control-via.json")"
echo "## b) control_4b"
python3 control_4b.py --motor "$L" --config "$H/config-campana-4c.json" --desde "$CD" --hasta "$CH" \
  --salud-captura "$SC" --incrementos "$B/salud/incrementos.jsonl" --tcpdump-anillo "$B/salud/tcpdump-anillo.log" \
  --tcpdump-via "$B/salud/tcpdump-via.log" --senales-rapidas "$C/feed-v2/senales-rapidas.jsonl" \
  --traza-publicador "$C/feed-v2/traza.jsonl" --salida "$A/control-4b.json" > "$A/control-4b.stdout" 2> "$A/control-4b.stderr"
echo "  rc=$? $(cut -c1-300 "$A/control-4b.stdout")"
EXTRA=()
if [ "$FASE" = 4c ]; then
  echo "## 1) destinos 3b"; python3 extraer_evidencia_destino.py --formato 3b --marcas "$M" --motor "$L" --pcap-dir "$B/archivo-pcap" \
    --salida-csv "$A/destinos-3b.csv" --salida-json "$A/actividad-3b.json" > "$A/destinos.stdout" 2> "$A/destinos.stderr"; echo "  rc=$?"
  echo "## 2) calidad de fuentes (ficheros de 5 s)"; python3 calidad_fuentes.py --marcas "$M" --stats "$C/stats-inicio.log" "$C/stats-fin.log" \
    --archivador "$C/archivar.log" --muestras "$C/muestras.jsonl" --duracion-pcap 5 --salida "$A/calidad-fuentes.json" > "$A/calidad.stdout" 2> "$A/calidad.stderr"; echo "  rc=$?"
  echo "## 3) suricata-stats.json"
  python3 - "$C/stats-fin.log" "$A/suricata-stats.json" "$(python3 -c "import json;print(json.load(open('$B/eve/inicio.json'))['t']-600)")" <<'PY'
import sys, json, re
from datetime import datetime, timezone
desde = float(sys.argv[3]); out, cur = [], None
for l in open(sys.argv[1], errors="replace"):
    m = re.match(r"Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)", l)
    if m:
        mo, d, y, hh, mm, ss = map(int, m.groups()); cur = {"momento": datetime(y, mo, d, hh, mm, ss, tzinfo=timezone.utc).timestamp()}
        cur["timestamp"] = datetime.fromtimestamp(cur["momento"], timezone.utc).isoformat(); continue
    m = re.match(r"capture\.kernel_(packets|drops)\s*\|\s*Total\s*\|\s*(\d+)", l)
    if m and cur is not None:
        cur["kernel_" + m.group(1)] = int(m.group(2))
        if "kernel_packets" in cur and "kernel_drops" in cur and cur["momento"] >= desde:
            out.append(cur); cur = None
json.dump(out, open(sys.argv[2], "w"), indent=0); print("  muestras:", len(out), "drops", out[0]["kernel_drops"], "->", out[-1]["kernel_drops"])
PY
  echo "## 4) recálculo de características"
  $PY recalcular_caracteristicas.py --marcas "$M" --motor "$L" --pcap-dir "$B/archivo-pcap" --eve "$C/eve-segmento.json" \
    --arranque-motor "$(cat "$B/estado-inicial/arranque-motor.t")" --salida "$A/caracteristicas.jsonl" > "$A/recalculo.stdout" 2> "$A/recalculo.stderr"; echo "  rc=$?"
  echo "## 5) respaldos y descriptor"
  python3 generar_respaldos.py --marcas "$M" --motor "$L" --eve "$C/eve-segmento.json" --caracteristicas "$A/caracteristicas.jsonl" \
    --pcap-dir "$B/archivo-pcap" --relojes "$C/relojes-4c.log" --servicios-inicio "$B/estado-inicial/servicios.txt" \
    --servicios-fin "$C/servicios-fin.txt" --suricata-stats "$A/suricata-stats.json" \
    --campana "etapa4-campana-A-4c" --salida-dir "$A/respaldos" > "$A/respaldos.stdout" 2> "$A/respaldos.stderr"; echo "  rc=$?"
  echo "## 6) integridad"; python3 verificar_integridad.py --descriptor "$A/respaldos/descriptor-integridad.json" --salida "$A/integridad.json" \
    > "$A/integridad.stdout" 2> "$A/integridad.stderr"; echo "  rc=$?"
  echo "## 7) clase de salud por episodio [inicio − 60, fin + 60]"
  python3 - "$H" "$SC" "$M" "$B/salud/incrementos.jsonl" "$B/salud/tcpdump-anillo.log" "$B/salud/tcpdump-via.log" "$A/salud-episodios.json" <<'PY'
import importlib.util, json, sys
from pathlib import Path
h, sc_path, marcas, incs_p, td_a, td_v, salida = sys.argv[1:8]
td_a, td_v = Path(td_a), Path(td_v)
sys.path.insert(0, h)
import analizar as an
spec = importlib.util.spec_from_file_location("salud_captura", sc_path); sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
incs = [json.loads(l) for l in open(incs_p) if l.strip()]
ta, tv = sc.leer_tcpdump_log(td_a), sc.leer_tcpdump_log(td_v)
crit = dict(sc.CRITERIOS, rotacion_s=5.0)
eps, _ = an.leer_marcas(marcas)
res = {}
for eid, ep in eps.items():
    if ep.get("fin_ep") is None:
        res[eid] = {"clase": "C3", "motivos": ["episodio sin fin"]}; continue
    d, f = ep["inicio_ep"] - 60, ep["fin_ep"] + 60
    res[eid] = {"if_heur": sc.clasificar(incs, ta, d, f, crit), "via_rapida": sc.clasificar(incs, tv, d, f, crit)}
json.dump(res, open(salida, "w"), indent=1, sort_keys=True)
from collections import Counter
print("  clases IF/heur:", dict(Counter(v.get("if_heur", v).get("clase") for v in res.values())))
PY
  echo "## 8) tráfico observado"; python3 -I "$E4/scripts/etapa4/trafico_observado.py" --marcas "$M" --config "$H/escenarios-4c.json" \
    --pcap-dir "$B/archivo-pcap" --salida "$A/trafico-observado.json" > "$A/trafico.stdout" 2> "$A/trafico.stderr"; echo "  rc=$?"
  EXTRA=(--destinos "$A/destinos-3b.csv" --integridad "$A/integridad.json" --calidad-fuentes "$A/calidad-fuentes.json")
fi
echo "## c) analizar_3b"
python3 analizar_3b.py --marcas "$M" --motor "$L" --config "$H/config-campana-4c.json" --ciclos "$C/ciclos.jsonl" \
  --inventario "$B/replay/motor_decision.log" --inventario-rango "$ID,$IH" "${EXTRA[@]}" \
  --control "$CD,$CH" --etiqueta "Etapa 4 $FASE $(date -u +%F)" --salida "$A/analisis-$FASE" > "$A/analizar.stdout" 2> "$A/analizar.stderr"
echo "  rc=$?"; tail -25 "$A/analizar.stdout"
if [ "$FASE" = 4c ]; then
  echo "## 9) tiempos por episodio y referencia al tráfico observado (escaneo breve = ráfaga real)"
  RL=(); [ -s "$C/traza-rele.jsonl" ] && RL=(--traza-rele "$C/traza-rele.jsonl")
  python3 referencia_trafico_4c.py --analisis "$A/analisis-$FASE/analisis-3b.json" --trafico "$A/trafico-observado.json" \
    --senales-rapidas "$C/feed-v2/senales-rapidas.jsonl" --traza-publicador "$C/feed-v2/traza.jsonl" "${RL[@]}" \
    --salida "$A/referencia-trafico.json" > "$A/referencia.stdout" 2> "$A/referencia.stderr"; echo "  rc=$? $(cut -c1-300 "$A/referencia.stdout")"
fi
( cd "$A" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ); echo "## fin $(date -u +%FT%T.%3NZ)"
