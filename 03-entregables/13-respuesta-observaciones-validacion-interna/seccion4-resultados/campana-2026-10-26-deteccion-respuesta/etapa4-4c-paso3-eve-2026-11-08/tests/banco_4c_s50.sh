#!/usr/bin/env bash
# Banco del paso 3 de s50 (4C): suricata-stats.json medido por EVE en vez de stats.log. Contenedor sin red.
# Recorrido completo de s50 (4c) con las herramientas de ANÁLISIS sustituidas por dobles que escriben su salida (como
# ensayo_errores_s50_r4.sh), y REALES: salud_captura (congelada o P1), los pasos 3 y 7 y la verificación de hashes.
#   R1  guion 4C enmendado, EVE con ráfaga y hueco   -> rc 0, paso 3 OK, paso 7 con C0 / C1 / C3 y estado de Suricata
#   R2  guion ORIGINAL + stats.log como el real (sin kernel_drops) -> rc 1: el paso 3 falla y quedan omitidos 5, 6 y c (defecto)
#   R3  guion 4C enmendado, EVE con una línea stats corrupta -> rc 1, paso 3 en fallo, 5/6/c/9 omitidos (nunca un OK falso)
#   R4  guion 4C enmendado, EVE sano                   -> rc 0 y los tres episodios C0 / cero_explicito
# Montajes: /e (enmienda 4B publicada), /c4 (esta carpeta), /herr (herramientas planas), /orig_g (guiones originales), /congelada, /out.
set -u
OUT=${OUT:-/out}; mkdir -p "$OUT"; LOG=$OUT/banco-4c-s50.txt; : > "$LOG"
export HERR=/herr D3B=/nada AQUI=/e/tests
T=$(mktemp -d); fallo=0
say() { echo "$*" | tee -a "$LOG"; }
ok() { if eval "$2"; then say "OK    $1"; else say "FALLO $1"; fallo=1; fi; }

preparar() {   # preparar nombre variante_salud(p1|congelada) estado_eve(eventos|limpio|corrupta) stats_log(sin_drops|con_drops)
  export HOME=$T/h-$1; local H=$HOME/cf-e4/herramientas B=$HOME/cf-e4/4c
  mkdir -p "$H" "$HOME/cyberflow/.venv/bin" "$B"/{salud,eve,copias/feed-v2,estado-inicial,replay,archivo-pcap} \
           "$HOME/cyberflow-e4/ec78ca5/scripts/etapa4" "$HOME/cyberflow-e4/herramientas-20261106"
  ln -sf "$(command -v python3)" "$HOME/cyberflow/.venv/bin/python"
  cat > "$H/falsa.py" <<'PY'
import os, sys
n = os.path.basename(sys.argv[0]); a = sys.argv[1:]
v = lambda k: a[a.index(k) + 1] if k in a else None
if n == "analizar_3b.py":
    os.makedirs(v("--salida"), exist_ok=True); open(os.path.join(v("--salida"), "analisis-3b.json"), "w").write("{}\n")
else:
    for k in ("--salida", "--salida-csv", "--salida-json"):
        if v(k): open(v(k), "w").write("{}\n")
    if v("--salida-dir"):
        os.makedirs(v("--salida-dir"), exist_ok=True); open(os.path.join(v("--salida-dir"), "descriptor-integridad.json"), "w").write("{}\n")
print(n, "ok")
PY
  for f in control_4b.py extraer_evidencia_destino.py calidad_fuentes.py recalcular_caracteristicas.py generar_respaldos.py \
           verificar_integridad.py analizar_3b.py referencia_trafico_4c.py; do cp "$H/falsa.py" "$H/$f"; done
  rm "$H/falsa.py"
  cat > "$H/analizar.py" <<'PY'
import datetime as dt
def _t(h, m, s=0): return dt.datetime(2026, 11, 1, h, m, s, tzinfo=dt.timezone.utc).timestamp()
def leer_marcas(p):   # tres episodios: limpio, con una ráfaga de descartes (07:45:00) y con un hueco de EVE (07:52:10–07:53:50)
    return {"e1-r1": {"inicio_ep": _t(7, 30), "fin_ep": _t(7, 33)}, "e2-r1": {"inicio_ep": _t(7, 44, 10), "fin_ep": _t(7, 46, 30)},
            "e3-r1": {"inicio_ep": _t(7, 52, 30), "fin_ep": _t(7, 53, 20)}}, None
PY
  echo '{}' > "$H/config-campana-4c.json"; echo '{}' > "$H/escenarios-4c.json"
  ( cd "$H" && sha256sum *.py *.json > herramientas-e4.sha256 )
  local E4s=$HOME/cyberflow-e4/ec78ca5/scripts/etapa4
  if [ "$2" = congelada ]; then cp /congelada/salud_captura.py "$E4s/salud_captura.py"; else echo "# marcador" > "$E4s/salud_captura.py"; fi
  printf 'import sys\na = sys.argv[1:]\nopen(a[a.index("--salida") + 1], "w").write("{}\\n")\n' > "$E4s/trafico_observado.py"
  ( cd "$HOME/cyberflow-e4/ec78ca5" && find scripts -type f | sort | xargs sha256sum > SHA256SUMS )
  cp /herr/salud_captura.py "$HOME/cyberflow-e4/herramientas-20261106/"
  ( cd "$HOME/cyberflow-e4/herramientas-20261106" && sha256sum salud_captura.py > SHA256SUMS )
  python3 - "$B" "$3" "$4" <<'PY'
import json, os, sys
from pathlib import Path
sys.path.insert(0, "/e/tests")
import datos_sinteticos as ds, generar_entorno_4b as g
b, est, stats = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
(b / "salud/muestras.jsonl").write_text(g.muestras(g.INI, g.FIN))
(b / "salud/tcpdump-anillo.log").write_text(ds.tcpdump_log(g.INI - 60, g.FIN + 60, pid=777))
(b / "salud/tcpdump-via.log").write_text(ds.tcpdump_log(g.INI - 60, g.FIN + 60, pid=888))
kw = dict(g.EVENTOS) if est == "eventos" else ({"basura_en": g.utc(7, 40, 0)} if est == "corrupta" else {})
if est == "corrupta":      # la línea corrupta debe caer EN una muestra de la rejilla de 8 s
    kw = {"basura_en": g.INI - 60 + 8 * round((g.utc(7, 40) - (g.INI - 60)) / 8)}
if est == "eventos":
    kw.pop("sin_drops", None)
(b / "copias/eve-segmento.json").write_bytes(ds.eve_stats(g.INI - 60, g.FIN + 60, arranque=g.INI - 86400, **kw))
c = b / "copias"
(c / "marcas.jsonl").write_text('{"evento":"inicio"}\n'); (c / "motor_decision.log").write_text("")
(c / "stats-inicio.log").write_text("")
bloque = "Date: 11/1/2026 -- 08:16:00 (uptime: 1d, 08h 16m 00s)\n" + "-" * 84 + "\nCounter | TM Name | Value\n" + "-" * 84 + "\ncapture.kernel_packets | Total | 41020424\n"
if stats == "con_drops":
    bloque += "capture.kernel_drops | Total | 0\n"
(c / "stats-fin.log").write_text(bloque)
(b / "eve/inicio.json").write_text(json.dumps({"t": g.INI, "inode": 1, "size": 0}))
(b / "estado-inicial/arranque-motor.t").write_text("1\n")
PY
}

estado() { awk -F'\t' -v p="$2" '$1==p{e=$2} END{print e}' "$HOME/cf-e4/$1/analisis/ESTADO-PASOS.tsv"; }
s50() { bash "$1/s50_analisis_e4.sh" 4c 2026-11-01T07:24:40Z 2026-11-01T10:05:30Z 2026-11-01T07:29:00Z 2026-11-01T08:05:00Z; }

say "## R1 guion 4C enmendado, EVE con ráfaga y hueco"
preparar r1 p1 eventos sin_drops; s50 /c4/guiones > "$T/o1" 2>&1; rc=$?; cp "$T/o1" "$OUT/s50-4c-R1.txt"
A=$HOME/cf-e4/4c/analisis
ok "R1a rc 0 y análisis COMPLETO" "[ $rc = 0 ] && head -1 $A/SHA256SUMS | grep -q '^# COMPLETO'"
ok "R1b paso 3 OK y suricata-stats.json con muestras de EVE (formato momento/kernel_*)" "[ \$(estado 4c 3) = ok ] && python3 -c \"import json;d=json.load(open('$A/suricata-stats.json'));assert len(d)>300 and all(k in d[0] for k in ('momento','timestamp','kernel_packets','kernel_drops')) and d[-1]['kernel_drops']==23 and d[0]['kernel_drops']==0\""
ok "R1c los pasos 5, 6, c y 7 ya no quedan omitidos" "[ \$(estado 4c 5) = ok ] && [ \$(estado 4c 6) = ok ] && [ \$(estado 4c c) = ok ] && [ \$(estado 4c 7) = ok ]"
ok "R1d paso 7: episodio limpio C0, con ráfaga C1 (descartes), con hueco C3 (datos faltantes)" "python3 -c \"
import json;d=json.load(open('$A/salud-episodios.json'))
assert (d['e1-r1']['if_heur']['clase'], d['e1-r1']['suricata_estado'])==('C0','cero_explicito'), d['e1-r1']['suricata_estado']
assert (d['e2-r1']['if_heur']['clase'], d['e2-r1']['suricata_estado'])==('C1','descartes')
assert d['e3-r1']['if_heur']['clase']=='C3' and d['e3-r1']['suricata_estado'] in ('cobertura_insuficiente','ausente')\""
ok "R1e el consumidor (generar_respaldos) ve +23 descartes solo en el periodo del episodio con ráfaga" "python3 -c \"
import json;s=json.load(open('$A/suricata-stats.json'))
def delta(ini,fin):
    x=[m for m in s if ini<=m['momento']<=fin]; return (x[-1]['kernel_drops']-x[0]['kernel_drops']) if len(x)>=2 else None
import datetime as dt
t=lambda h,m,sec=0: dt.datetime(2026,11,1,h,m,sec,tzinfo=dt.timezone.utc).timestamp()
assert delta(t(7,29,10),t(7,34,0))==0 and delta(t(7,43,10),t(7,47,30))==23\""
cp "$A/salud-episodios.json" "$OUT/R1-salud-episodios.json"; cp "$A/suricata-stats.json" "$OUT/R1-suricata-stats.json"

say "## R2 guion ORIGINAL con stats.log como el real (sin kernel_drops): el defecto"
preparar r2 congelada eventos sin_drops; s50 /orig_g > "$T/o2" 2>&1; rc=$?; cp "$T/o2" "$OUT/s50-4c-R2.txt"
ok "R2a rc 1 (análisis PARCIAL)" "[ $rc = 1 ] && head -1 $HOME/cf-e4/4c/analisis/SHA256SUMS.PARCIAL | grep -q '^# PARCIAL'"
ok "R2b DEFECTO REPRODUCIDO: el paso 3 falla («sin muestras de stats.log…») y quedan omitidos 5, 6 y c" "[ \$(estado 4c 3) = fallo ] && [ \$(estado 4c 5) = omitido_dependencia ] && [ \$(estado 4c 6) = omitido_dependencia ] && [ \$(estado 4c c) = omitido_dependencia ] && grep -q 'sin muestras de stats.log' $T/o2"
ok "R2c y, además, el paso 7 original da C3 («Suricata sin medida») en los tres episodios" "python3 -c \"
import json;d=json.load(open('$HOME/cf-e4/4c/analisis/salud-episodios.json'))
assert all(v['if_heur']['clase']=='C3' for v in d.values())\""

say "## R3 EVE con una línea stats corrupta"
preparar r3 p1 corrupta sin_drops; s50 /c4/guiones > "$T/o3" 2>&1; rc=$?; cp "$T/o3" "$OUT/s50-4c-R3.txt"
ok "R3a rc 1; paso 3 en fallo con el motivo; 5, 6, c y 9 omitidos; sin SHA256SUMS completo" "[ $rc = 1 ] && [ \$(estado 4c 3) = fallo ] && grep -q 'inválidas' $T/o3 && [ \$(estado 4c 5) = omitido_dependencia ] && [ \$(estado 4c 9) = omitido_dependencia ] && [ ! -e $HOME/cf-e4/4c/analisis/SHA256SUMS ]"

say "## R4 EVE sano"
preparar r4 p1 limpio sin_drops; s50 /c4/guiones > "$T/o4" 2>&1; rc=$?; cp "$T/o4" "$OUT/s50-4c-R4.txt"
ok "R4a rc 0 y los tres episodios C0 / cero_explicito" "[ $rc = 0 ] && python3 -c \"
import json;d=json.load(open('$HOME/cf-e4/4c/analisis/salud-episodios.json'))
assert all(v['if_heur']['clase']=='C0' and v['suricata_estado']=='cero_explicito' for v in d.values()), d\""

say "## Guion de la 4B y guion de la 4C: solo difieren en el paso 3"
ok "D1 el guion de la 4C difiere del de la 4B solo en comentarios de cabecera y en la función p_3 (todo lo demás es idéntico)" "python3 - <<'PY'
a = open('/e/guiones/s50_analisis_e4.sh', encoding='utf-8').read(); b = open('/c4/guiones/s50_analisis_e4.sh', encoding='utf-8').read()
i3a, i4a = a.index('p_3() {'), a.index('p_4() {'); i3b, i4b = b.index('p_3() {'), b.index('p_4() {')
assert a[i4a:] == b[i4b:], 'cola distinta'
ca = [l for l in a[:i3a].splitlines() if not l.startswith('#')]; cb = [l for l in b[:i3b].splitlines() if not l.startswith('#')]
assert ca == cb, 'código previo a p_3 distinto'
PY"
say "RESULTADO: $([ $fallo = 0 ] && echo 'todas las comprobaciones OK' || echo 'HAY FALLOS')"
exit $fallo
