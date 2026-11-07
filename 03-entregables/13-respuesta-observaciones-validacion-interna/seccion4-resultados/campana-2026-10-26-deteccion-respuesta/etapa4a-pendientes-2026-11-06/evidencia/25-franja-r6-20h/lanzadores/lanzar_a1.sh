#!/usr/bin/env bash
# [LAPTOP Git Bash] Fase A, pasos A0–A5, de la franja indicada. SOLO LECTURA en los hosts. VERSION 2026-11-07.1
#   lanzar_a1.sh r6|r5
# Se detiene en el primer paso que no da rc 0. rc: 0 conforme · 10 A0b no cumple · 1 otro paso · 2 uso o antes de hora
set -u -o pipefail
F=${1:-}
E24=evidencia/24-c1-registro-franja-domingo; E25=evidencia/25-franja-r6-20h
case "$F" in
  r6) INI=1794096300; P0=1794097800; P8="$E25/herramientas/comprobar_p8_r6.sh";;
  r5) INI=1794103500; P0=1794105000; P8="$E24/herramientas/comprobar_p8_r5.sh";;
  *) echo "uso: lanzar_a1.sh r6|r5"; exit 2;;
esac
R="${CF_R:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06}"
EJ="$R/evidencia/14-ecarga-ejecucion"; W="${CF_W:-/c/Users/markp/cf-ecarga-v2-1}"
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
[ -d "$EJ" ] || para 1 "no existe la carpeta de evidencia"
[ ! -e "$EJ/A0.txt" ] || para 1 "ya existe A0.txt: hay un intento anterior sin apartar"
[ ! -e "$W" ] || para 1 "ya existe la copia $W"
cd "$HOME" || exit 2
{ date -u +%FT%TZ; date +%s; echo "lanzar_a1 $F; ANTES DE P0: viable"; } | tee "$EJ/A0.txt"
if [ "$F" = r6 ]; then
  bash "$R/$E25/herramientas/comprobar_rotacion.sh" rotacion "$EJ/A0b-rotacion"; r=$?
  echo "A0b rc=$r"; [ "$r" = 0 ] || para 10 "A0b rc=$r: rotación o sensor sin confirmar"
fi
paso_t A1 "$EJ/A1-referencias.txt" bash "$R/$E25/herramientas/00_referencias.sh" "$W"
C=$(sed -n 's/^COPIA //p' "$EJ/A1-referencias.txt"); [ -n "$C" ] || para 1 "A1 sin COPIA"
paso cmp cmp "$R/$E25/herramientas/00_referencias.sh" "$C/$E25/herramientas/00_referencias.sh"
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
