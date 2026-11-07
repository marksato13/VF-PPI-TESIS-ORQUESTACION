#!/usr/bin/env bash
# [SENSOR1 m4rk] P12 de E-carga v2 (PROTOCOLO-CARGA-v2 r4 §3.5, punto 12): «los muestreadores (incluido S14) arrancados
# ANTES de T_g - 300 s». SOLO LECTURA: no arranca, no para y no escribe nada. VERSION 2026-11-07.1
#   comprobar_p12_host.sh DIR_EJECUCION      (p. ej. /home/m4rk/cf-e4/ecarga-v2-ejecucion-20261109T0300Z)
# Lee tres marcas reales que deja el arranque (ninguna se fabrica aquí):
#   1. DIR/arrancar-muestreadores.txt  transcripción de «sensor1_muestreadores.sh arrancar» con su última línea
#      «FIN_ARRANCAR epoch=<date -u +%s al volver> rc=<rc de arrancar>» (la escribe el paso B2 del procedimiento);
#   2. DIR/sensor1/eventos.log         primera línea «<ISO UTC> arrancados …» (la escribe sensor1_muestreadores.sh);
#   3. DIR/sensor1/s14.jsonl           primera línea {"inicio": <epoch>, …} (la escribe muestreo_s14.py al empezar).
# Resultado (una línea «REQ P12 <estado> <detalle>» y «FIN_P12 rc=N»):
#   CUMPLE     rc 0: arrancar rc 0, ARRANQUE_CONFIRMADO con 4 «vivo», y las tres marcas < LIMITE
#   NO_CUMPLE  rc 1: arrancar rc != 0 (no quedaron los 4 confirmados) o alguna marca >= LIMITE (tarde)
#   ERROR      rc 3: falta o no se puede leer una marca, o son incoherentes entre sí (nunca se aprueba)
# LIMITE = T_g - 300 s = 1794192900 (2026-11-09T02:55:00Z), constante del protocolo r4 §3.2/§3.6.1: no se cambia aquí.
set -u -o pipefail
export LC_ALL=C
LIMITE=1794192900
X=${1:?uso: comprobar_p12_host.sh DIR_EJECUCION}
T="$X/arrancar-muestreadores.txt"; EVL="$X/sensor1/eventos.log"; S14="$X/sensor1/s14.jsonl"
fin() { echo "REQ P12 $1 $2"; echo "FIN_P12 rc=$3"; exit "$3"; }
utc() { date -u -d "@$1" +%FT%TZ 2>/dev/null || echo "?"; }
echo "INFO p12 $(id -un) $(hostname) ahora=$(date -u +%s) limite=$LIMITE ($(utc $LIMITE)) dir=$X"
[ -r "$T" ] || fin ERROR "no legible $T" 3
l=$(grep -E '^FIN_ARRANCAR epoch=[0-9]+ rc=[0-9]+$' "$T"); r=$?
[ $r -le 1 ] || fin ERROR "no se pudo leer $T (grep rc $r)" 3
n=$(printf '%s' "$l" | grep -c .)
[ "$n" = 1 ] || fin ERROR "la transcripción debe tener exactamente una línea FIN_ARRANCAR y tiene $n" 3
fe=$(sed -E 's/^FIN_ARRANCAR epoch=([0-9]+) rc=[0-9]+$/\1/' <<<"$l"); frc=$(sed -E 's/^FIN_ARRANCAR epoch=[0-9]+ rc=([0-9]+)$/\1/' <<<"$l")
conf=$(grep -c '^ARRANQUE_CONFIRMADO: 4 muestreadores vivos$' "$T"); vivos=$(grep -cE '^vivo +[0-9]+ ' "$T")
echo "INFO arrancar rc=$frc fin=$fe ($(utc "$fe")) ARRANQUE_CONFIRMADO=$conf vivos=$vivos"
if [ "$frc" != 0 ]; then fin NO_CUMPLE "arrancar rc $frc (ARRANQUE_CONFIRMADO=$conf, vivos=$vivos): los 4 muestreadores no quedaron confirmados" 1; fi
[ "$conf" = 1 ] && [ "$vivos" = 4 ] || fin ERROR "incoherente: arrancar rc 0 pero ARRANQUE_CONFIRMADO=$conf y vivos=$vivos" 3
[ -r "$EVL" ] || fin ERROR "no legible $EVL" 3
ev=$(grep -m1 -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z arrancados ' "$EVL"); r=$?
[ $r = 0 ] || fin ERROR "sin línea «arrancados» en $EVL (grep rc $r)" 3
ee=$(date -u -d "${ev%% *}" +%s 2>/dev/null) || fin ERROR "fecha ilegible en eventos.log: ${ev%% *}" 3
[ -r "$S14" ] || fin ERROR "no legible $S14" 3
p=$(head -1 "$S14" | grep -oE '^\{"inicio": *[0-9]+(\.[0-9]+)?' | grep -oE '[0-9]+(\.[0-9]+)?$')
[ -n "$p" ] || fin ERROR "la primera línea de s14.jsonl no empieza por {\"inicio\": <epoch>" 3
se=${p%%.*}
echo "INFO eventos.log arrancados=$ee ($(utc "$ee")) · s14 inicio=$p ($(utc "$se"))"
# coherencia: las dos marcas de arranque son anteriores (o del mismo segundo) a la vuelta de «arrancar»
[ "$ee" -le "$fe" ] && [ "$se" -le "$fe" ] || fin ERROR "incoherente: marcas de arranque posteriores a la vuelta de arrancar ($ee, $se > $fe)" 3
m=$fe; [ "$ee" -gt "$m" ] && m=$ee; [ "$se" -gt "$m" ] && m=$se
d="arrancados $(utc "$ee"), s14 inicio $(utc "$se"), confirmados $(utc "$fe"); límite T_g-300 $(utc $LIMITE)"
[ "$m" -lt "$LIMITE" ] && fin CUMPLE "$d (margen $((LIMITE - m)) s)" 0
fin NO_CUMPLE "$d: alguna marca no es anterior al límite (exceso $((m - LIMITE + 1)) s)" 1
