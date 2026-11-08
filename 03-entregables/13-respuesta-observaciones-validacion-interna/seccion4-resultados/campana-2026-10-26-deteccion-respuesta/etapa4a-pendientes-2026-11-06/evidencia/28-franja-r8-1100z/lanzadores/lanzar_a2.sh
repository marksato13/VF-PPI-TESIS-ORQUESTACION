#!/usr/bin/env bash
# [LAPTOP Git Bash] Fase A, pasos A6–A8, de la variante r8 (T_g 11:00Z del 08-nov). SOLO LECTURA en los hosts. VERSION 2026-11-08.2
#   lanzar_a2.sh r8
# Derivado de evidencia/25-franja-r6-20h/lanzadores/lanzar_a2.sh, rama r5 (sin A7b), con la franja r8 y su evidencia.
# No arranca antes de la hora del P0. Se detiene en el primer paso que no da rc 0.
# rc: 0 lecturas de la puerta G conformes · 1 algún paso · 2 uso o antes de hora
set -u -o pipefail
F=${1:-}
E26=evidencia/28-franja-r8-1100z
case "$F" in
  r8) P0=1794133800; B=1794135000; DR="$E26/p0-r3y"; X=ecarga-v2-ejecucion-20261108T1100Z;;
  *) echo "uso: lanzar_a2.sh r8"; exit 2;;
esac
R="${CF_R:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06}"
EJ="$R/evidencia/27-ecarga-r8-ejecucion"
para() { echo "DETENIDO_A2 $F: $1"; echo "RESULTADO_A2 $F rc=1"; exit 1; }
ahora=$(date +%s)
[ "$ahora" -ge "$P0" ] || { echo "todavía no: P5b exige la franja"; exit 2; }
[ "$ahora" -lt "$B" ] || para "ya pasó la hora de los muestreadores: la puerta G no se puede cumplir"
[ "$(cat "$EJ/A1-lanzador.ok" 2>/dev/null)" = "$F" ] || para "A0–A5 de la $F no están conformes"
C=$(sed -n 's/^COPIA //p' "$EJ/A1-referencias.txt"); [ -n "$C" ] || para "sin COPIA"
cd "$HOME" || exit 2
date -u +%FT%TZ
bash "$C/$DR/p0_r3.sh" inmediato "$EJ/A6-p0-r3-inmediato" 2>&1 | tail -6 | cut -c1-170; rc=${PIPESTATUS[0]}
echo "$rc" > "$EJ/A6-p0-r3-inmediato.rc-driver"; echo "A6 rc=$rc"; [ "$rc" = 0 ] || para "A6 rc=$rc"
T="$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh"
bash "$T" despues-p0-inmediato 2>&1 | tail -1 | cut -c1-150; r=${PIPESTATUS[0]}; [ "$r" = 0 ] || para "instantánea posterior rc=$r"
bash "$T" comparar antes-p0-inmediato despues-p0-inmediato 2>&1 | tee "$EJ/A7-comparacion-paquete.txt" | tail -4 | cut -c1-150; r=${PIPESTATUS[0]}
echo "A7 rc=$r"; [ "$r" = 0 ] || para "A7 rc=$r"
S="[ ! -e ~/cf-e4/$X ] && echo LIBRE || echo OCUPADA"
O="-n -o BatchMode=yes -o ConnectTimeout=10 -i"
a=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$S" 2>&1); ra=$?
b=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh $O ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '$S'" 2>&1); rb=$?
{ date -u +%FT%TZ; echo "bastion ssh_rc=$ra salida=$a"; echo "sensor1 ssh_rc=$rb salida=$b"; } | tee "$EJ/A8.txt"
[ "$ra" = 0 ] && [ "$rb" = 0 ] && [ "$a" = LIBRE ] && [ "$b" = LIBRE ] || para "A8: las dos consultas deben dar ssh rc 0 y LIBRE (bastión rc $ra «$a», Sensor1 rc $rb «$b»)"
echo "A8 CONFORME: bastión y Sensor1 con ssh rc 0 y LIBRE" | tee -a "$EJ/A8.txt"
date -u +%FT%TZ
echo "RESULTADO_A2 $F rc=0"
