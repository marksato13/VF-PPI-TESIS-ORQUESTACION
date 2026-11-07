#!/usr/bin/env bash
# [LAPTOP Git Bash] Fase A, pasos A6–A8, de la franja indicada. SOLO LECTURA en los hosts. VERSION 2026-11-07.1
#   lanzar_a2.sh r6|r5
# No arranca antes de la hora del P0. En la r6, A7b ESPERA hasta las 19:35 de Perú (00:35Z) antes de ejecutarse.
# Se detiene en el primer paso que no da rc 0. rc: 0 lecturas de la puerta G conformes · 1 algún paso · 2 uso o antes de hora
set -u -o pipefail
F=${1:-}
E24=evidencia/24-c1-registro-franja-domingo; E25=evidencia/25-franja-r6-20h
case "$F" in
  r6) P0=1794097800; B=1794099000; A7B=1794098100; DR="$E25/p0-r3w"; X=ecarga-v2-ejecucion-20261108T0100Z;;
  r5) P0=1794105000; B=1794106200; A7B=0; DR="$E24/p0-r3v"; X=ecarga-v2-ejecucion-20261108T0300Z;;
  *) echo "uso: lanzar_a2.sh r6|r5"; exit 2;;
esac
R="${CF_R:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06}"
EJ="$R/evidencia/14-ecarga-ejecucion"
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
if [ "$F" = r6 ]; then
  while [ "$(date +%s)" -lt "$A7B" ]; do sleep 5; done
  echo "INFO A7b lanzado en $(date +%s), mínimo $A7B"
  bash "$C/$E25/herramientas/comprobar_rotacion.sh" aprendizaje "$EJ/A7b-aprendizaje"; r=$?
  echo "A7b rc=$r"; [ "$r" = 0 ] || para "A7b rc=$r"
fi
S="[ ! -e ~/cf-e4/$X ] && echo LIBRE || echo OCUPADA"
O="-n -o BatchMode=yes -i"
a=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$S"); b=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh $O ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '$S'")
{ date -u +%FT%TZ; echo "bastion $a"; echo "sensor1 $b"; } | tee "$EJ/A8.txt"
[ "$a" = LIBRE ] && [ "$b" = LIBRE ] || para "A8: carpeta X no libre"
date -u +%FT%TZ
echo "RESULTADO_A2 $F rc=0"
