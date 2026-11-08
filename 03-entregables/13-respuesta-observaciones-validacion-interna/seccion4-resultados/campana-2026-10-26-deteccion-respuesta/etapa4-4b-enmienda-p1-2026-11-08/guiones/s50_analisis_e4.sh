#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s50 — análisis con herramientas verificadas. Solo lee las copias y escribe en
# ~/cf-e4/<fase>/analisis/. Sin sudo. Uso:
#   s50_analisis_e4.sh <4b|4c> <inv_desde_iso> <inv_hasta_iso> <control_desde_iso> <control_hasta_iso>
#   REANUDAR=1 s50_analisis_e4.sh …   # reanuda un análisis que terminó con pasos fallidos
# Herramientas: ~/cf-e4/herramientas/ (copiadas del repositorio de documentación y verificadas con
# herramientas-e4.sha256); salud_captura.py y trafico_observado.py del candidato (~/cyberflow-e4/ec78ca5).
#  4b y 4c: a1) incrementos de salud  a2/a3) clase del control (anillo / vía rápida)  b) control_4b
#           c) analizar_3b (cobertura contra el inventario, cotas)
#  solo 4c: 1) destinos 3b  2) calidad de fuentes (--duracion-pcap 5)  3) suricata-stats.json  4) recálculo de
#           características  5) respaldos  6) integridad  7) clase de salud por episodio  8) tráfico observado
#           9) referencia_trafico_4c. La traza del relé (bastión) se copia a copias/traza-rele.jsonl antes (b20).
#
# Errores (2026-11-02, corrección del defecto 4): cada paso corre con set -e y pipefail; un fallo de una orden, de
# Python o de una tubería hace FALLO el paso; sus dependientes quedan «omitido_dependencia» y el rc global es 1.
# Se conservan las salidas parciales. ESTADO-PASOS.tsv registra paso, estado, rc, inicio, fin y dependencias; cada
# paso OK deja .pasos/<paso>.sha256 con el hash de sus salidas.
# Manifiesto: SHA256SUMS solo si TODOS los pasos requeridos están OK (y su primera línea lo dice); si no,
# SHA256SUMS.PARCIAL con la lista de pasos fallidos u omitidos en PARCIAL.txt. Nunca se declara completo un parcial.
# Reanudar: los pasos OK cuyas salidas verifican contra .pasos/<paso>.sha256 se reutilizan; si alguna no verifica,
# PARAR (no se sobrescribe un resultado válido ni se reutiliza uno alterado). Las salidas de los pasos fallidos se
# mueven a .fallidos/<paso>-<UTC>/ antes de repetirlos.
# Resultado esperado: «ANÁLISIS COMPLETO» y rc=0. Parada: hash de una herramienta distinto, salida alterada.
#
# ENMIENDA P1 (2026-11-08, etapa4-4b-enmienda-p1-2026-11-08): la clasificación (a2, a3, b y, en la 4C, 7) usa
# salud_captura 2026-11-06.1 de ~/cyberflow-e4/herramientas-20261106 (hash fijado) y mide Suricata por los eventos `stats`
# de EVE del segmento copiado por s30 ($C/eve-segmento.json), tanto para el periodo completo como para cada
# ventana: cero descartes (C0), descartes (C1) o datos faltantes (C3, con su estado). No cambia ningún criterio.
# PENDIENTE 4C: el paso 3 (suricata-stats.json) sigue leyendo stats.log y no es válido con Suricata 7; no se toca aquí.
set -u -o pipefail
FASE=${1:?fase}; ID=${2:?inv_desde}; IH=${3:?inv_hasta}; CD=${4:?control_desde}; CH=${5:?control_hasta}
B=$HOME/cf-e4/$FASE; H=$HOME/cf-e4/herramientas; C=$B/copias; A=$B/analisis; E4=$HOME/cyberflow-e4/ec78ca5
PY=$HOME/cyberflow/.venv/bin/python; HP=$HOME/cyberflow-e4/herramientas-20261106; SC=$HP/salud_captura.py
SC_SHA=274b4d613357be60e362f13ce007f07b6bb8055e0e0029316f7bafaa845344d2; EVE=$C/eve-segmento.json
case "$FASE" in 4b|4c) ;; *) echo "PARAR: fase $FASE"; exit 2;; esac
if [ -e "$A" ] && [ "${REANUDAR:-0}" != 1 ]; then echo "PARAR: existe $A (REANUDAR=1 para reanudar)"; exit 2; fi
if [ "${REANUDAR:-0}" = 1 ] && [ ! -f "$A/ESTADO-PASOS.tsv" ]; then echo "PARAR: no hay ESTADO-PASOS.tsv que reanudar"; exit 2; fi
( cd "$H" && sha256sum -c --quiet herramientas-e4.sha256 ) || { echo "PARAR: herramientas con hash distinto"; exit 2; }
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: el código candidato no verifica"; exit 2; }
( cd "$HP" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: las herramientas P1 no verifican"; exit 2; }
[ "$(sha256sum "$SC" | cut -c1-64)" = "$SC_SHA" ] || { echo "PARAR: salud_captura de P1 con hash distinto"; exit 2; }
[ -s "$EVE" ] || { echo "PARAR: falta el segmento EVE $EVE (lo copia s30): sin él Suricata no se puede medir"; exit 2; }
mkdir -p "$A/.pasos" "$A/.fallidos"; cd "$H" || exit 2
echo "## s50-e4 $FASE $(date -u +%FT%T.%3NZ) inventario=[$ID, $IH] control=[$CD, $CH] reanudar=${REANUDAR:-0}"
sha256sum "$H"/*.py "$H"/*.json "$SC" "$E4/scripts/etapa4/trafico_observado.py" > "$A/sha256-herramientas.$(date -u +%Y%m%dT%H%M%SZ).txt" || exit 2
L=$C/motor_decision.log
if [ "$FASE" = 4b ]; then M=$A/marcas-vacias.jsonl; [ -e "$M" ] || : > "$M"; else M=$C/marcas.jsonl; fi
EST=$A/ESTADO-PASOS.tsv
[ -f "$EST" ] || printf 'paso\testado\trc\tinicio_utc\tfin_utc\tdepende_de\n' > "$EST"
declare -A ESTADO
# en una reanudación, el último estado registrado de cada paso
while IFS=$'\t' read -r p e _; do [ "$p" = paso ] || ESTADO[$p]=$e; done < "$EST"

# paso <id> "<dependencias>" "<salidas relativas a A>" <función>
paso() {
  local id=$1 deps=$2 salidas=$3 fn=$4 d t0 rc
  if [ "${ESTADO[$id]:-}" = ok ] || [ "${ESTADO[$id]:-}" = reutilizado ]; then
    if ( cd "$A" && sha256sum -c --quiet ".pasos/$id.sha256" ) 2>/dev/null; then
      echo "## $id: reutilizado (salidas verificadas)"; ESTADO[$id]=reutilizado
      printf '%s\treutilizado\t0\t%s\t%s\t%s\n' "$id" "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" "$deps" >> "$EST"; return 0
    fi
    echo "PARAR: las salidas del paso $id ya OK no verifican contra .pasos/$id.sha256 (alteradas): no se reutilizan ni se sobrescriben"
    exit 2
  fi
  for d in $deps; do
    case "${ESTADO[$d]:-}" in ok|reutilizado) ;; *)
      echo "## $id: OMITIDO (depende de $d, estado ${ESTADO[$d]:-sin_ejecutar})"; ESTADO[$id]=omitido_dependencia
      printf '%s\tomitido_dependencia\t-\t%s\t%s\t%s\n' "$id" "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" "$deps" >> "$EST"
      return 0;;
    esac
  done
  # salidas de un intento anterior fallido: se apartan, no se sobrescriben
  local hay=0 s
  for s in $salidas; do [ -e "$A/$s" ] && hay=1; done
  if [ "$hay" = 1 ]; then
    local dst="$A/.fallidos/$id-$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$dst"
    for s in $salidas; do [ -e "$A/$s" ] && mv "$A/$s" "$dst/"; done
    echo "## $id: salidas del intento anterior movidas a ${dst#$A/}"
  fi
  t0=$(date -u +%FT%TZ); echo "## $id"
  ( set -e -o pipefail; "$fn" ); rc=$?
  if [ "$rc" = 0 ]; then
    for s in $salidas; do [ -e "$A/$s" ] || { echo "  FALLO $id: falta la salida $s"; rc=97; }; done
  fi
  if [ "$rc" = 0 ]; then
    ( cd "$A" && for s in $salidas; do if [ -d "$s" ]; then find "$s" -type f -print0 | sort -z | xargs -0 -r sha256sum; else sha256sum "$s"; fi; done ) > "$A/.pasos/$id.sha256"
    ESTADO[$id]=ok; echo "  $id OK"
  else
    ESTADO[$id]=fallo; echo "  FALLO $id rc=$rc (salidas parciales conservadas)"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "${ESTADO[$id]}" "$rc" "$t0" "$(date -u +%FT%TZ)" "$deps" >> "$EST"
  return 0
}

# estado de Suricata (EVE) que quedó en un JSON de clasificar: cero_explicito | descartes | ausente | desactualizada | ...
est_sur() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('info',{}).get('suricata',{}).get('estado'))" "$1"; }
p_a1() { python3 -I "$SC" intervalos "$B/salud/muestras.jsonl" "$A/incrementos.jsonl"; }
p_a2() { python3 -I "$SC" clasificar --incrementos "$A/incrementos.jsonl" --tcpdump-log "$B/salud/tcpdump-anillo.log" \
           --desde "$CD" --hasta "$CH" --rotacion 5 --suricata-eve "$EVE" > "$A/salud-control-anillo.json"
         echo "  control (IF/heur): $(grep -m1 '"clase"' "$A/salud-control-anillo.json")  Suricata (EVE): $(est_sur "$A/salud-control-anillo.json")"; }
p_a3() { python3 -I "$SC" clasificar --incrementos "$A/incrementos.jsonl" --tcpdump-log "$B/salud/tcpdump-via.log" \
           --desde "$CD" --hasta "$CH" --rotacion 5 --suricata-eve "$EVE" > "$A/salud-control-via.json"
         echo "  control (vía rápida): $(grep -m1 '"clase"' "$A/salud-control-via.json")  Suricata (EVE): $(est_sur "$A/salud-control-via.json")"; }
p_b() { python3 control_4b.py --motor "$L" --config "$H/config-campana-4c.json" --desde "$CD" --hasta "$CH" \
          --salud-captura "$SC" --incrementos "$A/incrementos.jsonl" --tcpdump-anillo "$B/salud/tcpdump-anillo.log" \
          --tcpdump-via "$B/salud/tcpdump-via.log" --suricata-eve "$EVE" --senales-rapidas "$C/feed-v2/senales-rapidas.jsonl" \
          --traza-publicador "$C/feed-v2/traza.jsonl" --salida "$A/control-4b.json" > "$A/control-4b.stdout" 2> "$A/control-4b.stderr"
        echo "  $(cut -c1-300 "$A/control-4b.stdout")"; }
p_1() { python3 extraer_evidencia_destino.py --formato 3b --marcas "$M" --motor "$L" --pcap-dir "$B/archivo-pcap" \
          --salida-csv "$A/destinos-3b.csv" --salida-json "$A/actividad-3b.json" > "$A/destinos.stdout" 2> "$A/destinos.stderr"; }
p_2() { python3 calidad_fuentes.py --marcas "$M" --stats "$C/stats-inicio.log" "$C/stats-fin.log" --archivador "$C/archivar.log" \
          --muestras "$C/muestras.jsonl" --duracion-pcap 5 --salida "$A/calidad-fuentes.json" > "$A/calidad.stdout" 2> "$A/calidad.stderr"; }
p_3() {
  local desde; desde=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['t']-600)" "$B/eve/inicio.json")
  python3 - "$C/stats-fin.log" "$A/suricata-stats.json" "$desde" <<'PY'
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
if not out:
    sys.exit("sin muestras de stats.log posteriores a inicio - 600 s")
json.dump(out, open(sys.argv[2], "w"), indent=0); print("  muestras:", len(out), "drops", out[0]["kernel_drops"], "->", out[-1]["kernel_drops"])
PY
}
p_4() { $PY recalcular_caracteristicas.py --marcas "$M" --motor "$L" --pcap-dir "$B/archivo-pcap" --eve "$C/eve-segmento.json" \
          --arranque-motor "$(cat "$B/estado-inicial/arranque-motor.t")" --salida "$A/caracteristicas.jsonl" > "$A/recalculo.stdout" 2> "$A/recalculo.stderr"; }
p_5() { python3 generar_respaldos.py --marcas "$M" --motor "$L" --eve "$C/eve-segmento.json" --caracteristicas "$A/caracteristicas.jsonl" \
          --pcap-dir "$B/archivo-pcap" --relojes "$C/relojes-4c.log" --servicios-inicio "$B/estado-inicial/servicios.txt" \
          --servicios-fin "$C/servicios-fin.txt" --suricata-stats "$A/suricata-stats.json" \
          --campana "etapa4-campana-A-4c" --salida-dir "$A/respaldos" > "$A/respaldos.stdout" 2> "$A/respaldos.stderr"; }
p_6() { python3 verificar_integridad.py --descriptor "$A/respaldos/descriptor-integridad.json" --salida "$A/integridad.json" \
          > "$A/integridad.stdout" 2> "$A/integridad.stderr"; }
p_7() { python3 - "$H" "$SC" "$M" "$A/incrementos.jsonl" "$B/salud/tcpdump-anillo.log" "$B/salud/tcpdump-via.log" "$A/salud-episodios.json" "$EVE" <<'PY'
import importlib.util, json, sys, time
from pathlib import Path
h, sc_path, marcas, incs_p, td_a, td_v, salida, eve_p = sys.argv[1:9]
td_a, td_v = Path(td_a), Path(td_v)
sys.path.insert(0, h)
import analizar as an
spec = importlib.util.spec_from_file_location("salud_captura", sc_path); sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
incs = [json.loads(l) for l in open(incs_p) if l.strip()]
ta, tv = sc.leer_tcpdump_log(td_a), sc.leer_tcpdump_log(td_v)
crit = dict(sc.CRITERIOS, rotacion_s=5.0)
eps, _ = an.leer_marcas(marcas)
lect = sc.leer_eve_stats([Path(eve_p)])
ahora = time.time()
res = {}
for eid, ep in eps.items():
    if ep.get("fin_ep") is None:
        res[eid] = {"clase": "C3", "motivos": ["episodio sin fin"]}; continue
    d, f = ep["inicio_ep"] - 60, ep["fin_ep"] + 60
    se = sc.medida_suricata_eve(lect, d, f, ahora)       # Suricata de ESTE periodo, por EVE stats
    res[eid] = {"if_heur": sc.clasificar(incs, ta, d, f, crit, suricata_eve=se),
                "via_rapida": sc.clasificar(incs, tv, d, f, crit, suricata_eve=se), "suricata_estado": se.get("estado")}
json.dump(res, open(salida, "w"), indent=1, sort_keys=True)
from collections import Counter
print("  clases IF/heur:", dict(Counter(v.get("if_heur", v).get("clase") for v in res.values())))
PY
}
p_8() { python3 -I "$E4/scripts/etapa4/trafico_observado.py" --marcas "$M" --config "$H/escenarios-4c.json" \
          --pcap-dir "$B/archivo-pcap" --salida "$A/trafico-observado.json" > "$A/trafico.stdout" 2> "$A/trafico.stderr"; }
EXTRA=()
p_c() { python3 analizar_3b.py --marcas "$M" --motor "$L" --config "$H/config-campana-4c.json" --ciclos "$C/ciclos.jsonl" \
          --inventario "$B/replay/motor_decision.log" --inventario-rango "$ID,$IH" "${EXTRA[@]}" \
          --control "$CD,$CH" --etiqueta "Etapa 4 $FASE $(date -u +%F)" --salida "$A/analisis-$FASE" > "$A/analizar.stdout" 2> "$A/analizar.stderr"
        tail -25 "$A/analizar.stdout"; }
p_9() { local RL=(); [ -s "$C/traza-rele.jsonl" ] && RL=(--traza-rele "$C/traza-rele.jsonl")
        python3 referencia_trafico_4c.py --analisis "$A/analisis-$FASE/analisis-3b.json" --trafico "$A/trafico-observado.json" \
          --senales-rapidas "$C/feed-v2/senales-rapidas.jsonl" --traza-publicador "$C/feed-v2/traza.jsonl" "${RL[@]}" \
          --salida "$A/referencia-trafico.json" > "$A/referencia.stdout" 2> "$A/referencia.stderr"
        echo "  $(cut -c1-300 "$A/referencia.stdout")"; }

REQ=(a1 a2 a3 b c)
paso a1 ""   "incrementos.jsonl" p_a1
paso a2 "a1" "salud-control-anillo.json" p_a2
paso a3 "a1" "salud-control-via.json" p_a3
paso b  "a1" "control-4b.json control-4b.stdout control-4b.stderr" p_b
DEPS_C=""
if [ "$FASE" = 4c ]; then
  REQ+=(1 2 3 4 5 6 7 8 9)
  paso 1 ""    "destinos-3b.csv actividad-3b.json destinos.stdout destinos.stderr" p_1
  paso 2 ""    "calidad-fuentes.json calidad.stdout calidad.stderr" p_2
  paso 3 ""    "suricata-stats.json" p_3
  paso 4 ""    "caracteristicas.jsonl recalculo.stdout recalculo.stderr" p_4
  paso 5 "3 4" "respaldos respaldos.stdout respaldos.stderr" p_5
  paso 6 "5"   "integridad.json integridad.stdout integridad.stderr" p_6
  paso 7 "a1"  "salud-episodios.json" p_7
  paso 8 ""    "trafico-observado.json trafico.stdout trafico.stderr" p_8
  EXTRA=(--destinos "$A/destinos-3b.csv" --integridad "$A/integridad.json" --calidad-fuentes "$A/calidad-fuentes.json")
  DEPS_C="1 2 6"
fi
paso c "$DEPS_C" "analisis-$FASE analizar.stdout analizar.stderr" p_c
[ "$FASE" = 4c ] && paso 9 "c 8" "referencia-trafico.json referencia.stdout referencia.stderr" p_9

MAL=()
for p in "${REQ[@]}"; do case "${ESTADO[$p]:-sin_ejecutar}" in ok|reutilizado) ;; *) MAL+=("$p=${ESTADO[$p]:-sin_ejecutar}");; esac; done
lista() { find . -type f ! -name 'SHA256SUMS*' ! -name PARCIAL.txt ! -path './.fallidos/*' -print0 | sort -z | xargs -0 sha256sum; }
if [ "${#MAL[@]}" = 0 ]; then
  ( cd "$A" && rm -f SHA256SUMS.PARCIAL PARCIAL.txt && { echo "# COMPLETO $(date -u +%FT%TZ) pasos: ${REQ[*]}"; lista; } > SHA256SUMS )
  echo "## ANÁLISIS COMPLETO $(date -u +%FT%T.%3NZ)"; exit 0
fi
( cd "$A" && rm -f SHA256SUMS && { echo "# PARCIAL $(date -u +%FT%TZ): ${MAL[*]}"; lista; } > SHA256SUMS.PARCIAL \
  && printf 'ANÁLISIS PARCIAL — NO es el resultado de la fase %s\npasos no completados: %s\nver ESTADO-PASOS.tsv; reanudar con REANUDAR=1 tras corregir la causa\n' "$FASE" "${MAL[*]}" > PARCIAL.txt )
echo "## ANÁLISIS PARCIAL: ${MAL[*]} $(date -u +%FT%T.%3NZ)"; exit 1
