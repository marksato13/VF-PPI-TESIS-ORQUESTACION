#!/usr/bin/env bash
# Copia las salidas del cierre tecnico de la Etapa 3 a la carpeta de documentacion.
# Uso: N=<hash>-e5-eventos bash ensamblar_cierre.sh
set -eu
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
DOC="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa3-cierre-tecnico-2026-11-02"
REPO="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa3"
n="${N:?falta N}"; c="cierre-$n"
O="$S/cierre/out"; X="$S/cierreres"; R="$DOC/resultados"; L="$S/replay/$c"
mkdir -p "$R/pruebas" "$R/vlan" "$R/bateria-c" "$R/bateria-c-vlan" "$R/comparaciones" "$R/replay-$n" "$R/dns" "$DOC/guiones"
cp "$O/regresiones.txt" "$R/pruebas/regresiones-y-suite-docker.txt"
cp "$O/ensayos_cierre.txt" "$R/pruebas/ensayos-cierre-stdout.txt"
cp "$O/vlan/ensayo-vlan.json" "$O/vlan/stdout.txt" "$R/vlan/"
for b in bateria-c bateria-c-vlan; do
  cp "$O/$b/ensayo-via-rapida.jsonl" "$O/$b/stdout.txt" "$O/$b/stderr.txt" "$R/$b/"
  ( cd "$REPO" && PYTHONIOENCODING=utf-8 python deploy/pruebas-aisladas/resumir_ensayo_via_rapida.py \
      "$R/$b/ensayo-via-rapida.jsonl" "$R/$b/resumen.json" "$R/$b/TABLA.md" > /dev/null )
done
cp "$S/cierre/res/resumen-bateria-e3.json" "$R/comparaciones/resumen-bateria-e3-tramos.json"
rm -rf "$R/analisis-3b-cierre"; cp -r "$X/analisis-3b-$c" "$R/analisis-3b-cierre"
cp "$X/analisis-3b-$c.stdout" "$R/analisis-3b-cierre.stdout"; cp "$X/analisis-3b-$c.stderr" "$R/analisis-3b-cierre.stderr"
cp "$X"/comparaciones/*.json "$R/comparaciones/"
cp "$X/cambios-auth-failure-e3-vs-$c.json" "$R/comparaciones/cambios-auth-failure-e3-vs-cierre.json"
cp "$X/via-rapida-episodios-$c.json" "$R/comparaciones/via-rapida-episodios-cierre.json"
cp "$X/matriz-reglas-$c.json" "$R/comparaciones/matriz-reglas-cierre.json"
cp "$X/observacion-3b-ensayo.json" "$R/dns/observacion-3b-ensayo.json"
[ -f "$X/rendimiento-$c.json" ] && cp "$X/rendimiento-$c.json" "$R/comparaciones/rendimiento-cierre.json"
for f in motor_decision.log caracteristicas.jsonl stderr.txt; do gzip -n -9 -c "$L/$f" > "$R/replay-$n/$f.gz"; done
gzip -n -9 -c "$L/_state/ciclos.jsonl" > "$R/replay-$n/ciclos.jsonl.gz"
cp "$S/cierre/regresiones.sh" "$S/cierre/ensayos_cierre.sh" "$S/cierre/correr_completo_cierre.sh" \
   "$S/cierre/analizar_cierre.sh" "$S/cierre/ensamblar_cierre.sh" "$S/cierre/comparar_clasificacion.py" \
   "$S/cierre/comparar_analisis.py" "$S/e3/manifiesto_lf.py" "$DOC/guiones/"
sed "s#etapa3-deteccion-temprana-2026-11-02#etapa3-cierre-tecnico-2026-11-02#" "$S/e3/verificar_github.sh" > "$DOC/guiones/verificar_github.sh"
du -sh "$R"
