#!/usr/bin/env bash
# [LAPTOP Git Bash] Fase A, pasos A0–A5, de la variante r8 (T_g 11:00Z del 08-nov). SOLO LECTURA en los hosts. VERSION 2026-11-08.3
#   lanzar_a1.sh r8
# Derivado de evidencia/25-franja-r6-20h/lanzadores/lanzar_a1.sh: sin A0b (la r8 no cruza la rotación de las 00:00Z),
# con la evidencia en evidencia/29-ecarga-r8-ejecucion y la copia en cf-ecarga-v2-r8.
# Se detiene en el primer paso que no da rc 0. rc: 0 conforme · 1 algún paso · 2 uso o antes de hora
set -u -o pipefail
F=${1:-}
E24=evidencia/24-c1-registro-franja-domingo; E26=evidencia/28-franja-r8-1100z
case "$F" in
  r8) INI=1794132300; P0=1794133800; P8="$E26/herramientas/comprobar_p8_r8.sh";;
  *) echo "uso: lanzar_a1.sh r8"; exit 2;;
esac
R="${CF_R:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06}"
EJ="$R/evidencia/29-ecarga-r8-ejecucion"; W="${CF_W:-/c/Users/markp/cf-ecarga-v2-r8}"
para() { echo "DETENIDO_A1 $F: $2"; echo "RESULTADO_A1 $F rc=$1"; exit "$1"; }
paso() {  # nombre comando...
  local n=$1 r; shift; "$@" 2>&1 | tail -3 | cut -c1-170; r=${PIPESTATUS[0]}; echo "$n rc=$r"
  [ "$r" = 0 ] || para 1 "$n rc=$r"
}
paso_t() {  # nombre fichero comando...
  local n=$1 s=$2 r; shift 2; "$@" 2>&1 | tee "$s" | tail -2 | cut -c1-170; r=${PIPESTATUS[0]}; echo "$n rc=$r"
  [ "$r" = 0 ] || para 1 "$n rc=$r"
}
ahora=$(date +%s)
[ "$ahora" -ge "$INI" ] || { echo "todavía no: la fase A de la $F empieza en $INI"; exit 2; }
[ "$ahora" -lt "$P0" ] || para 1 "ya pasó la hora del P0"
[ -d "$EJ" ] || para 1 "no existe la carpeta de evidencia (la crea F0)"
grep -q '^RESULTADO_FORZAR rc=0 .*REQ FORZAR\.con CUMPLE' "$EJ/F3-forzar-con/resumen.txt" 2>/dev/null || para 1 "F3 no está conforme: sin F2 comprobado no hay fase A"
[ ! -e "$EJ/A0.txt" ] || para 1 "ya existe A0.txt: hay un intento anterior sin apartar"
[ ! -e "$W" ] || para 1 "ya existe la copia $W"
cd "$HOME" || exit 2
{ date -u +%FT%TZ; date +%s; echo "lanzar_a1 $F; ANTES DE P0: viable"; } | tee "$EJ/A0.txt"
paso_t A1 "$EJ/A1-referencias.txt" bash "$R/$E26/herramientas/00_referencias.sh" "$W"
C=$(sed -n 's/^COPIA //p' "$EJ/A1-referencias.txt"); [ -n "$C" ] || para 1 "A1 sin COPIA"
paso cmp cmp "$R/$E26/herramientas/00_referencias.sh" "$C/$E26/herramientas/00_referencias.sh"
paso A2 bash "$C/evidencia/19-correccion-p11/laboratorio/previa.sh" "$EJ/A2-previa"
paso A3 bash "$C/evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh" "$EJ/A3-postcopia-r3"
paso_t A3b "$EJ/A3b-verificar.txt" bash "$C/$E24/traslado/trasladar_bastion.sh" verificar
grep -q 'ESTADO_FINAL=VERIFICADO' "$EJ/A3b-verificar.txt" || para 1 "A3b sin VERIFICADO"
paso A3c bash "$C/$E24/variante/comprobar_forzar.sh" con "$EJ/A3c-forzar-con"
paso A4 bash "$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh" antes-p0-inmediato
paso A5 bash "$C/$P8" "$EJ/A5-p8"
echo "$F" > "$EJ/A1-lanzador.ok"
date -u +%FT%TZ
echo "RESULTADO_A1 $F rc=0"
