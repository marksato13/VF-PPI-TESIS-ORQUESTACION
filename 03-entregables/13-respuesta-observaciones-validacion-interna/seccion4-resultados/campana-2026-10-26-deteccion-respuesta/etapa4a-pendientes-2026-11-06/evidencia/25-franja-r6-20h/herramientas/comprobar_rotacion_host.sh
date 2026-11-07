#!/usr/bin/env bash
# [SENSOR1 m4rk] Rotación de eve.json y reentrenamiento nocturno de la franja r6. SOLO LECTURA. VERSION 2026-11-07.1
#   comprobar_rotacion_host.sh rotacion EPOCH_MIN      logrotate terminó bien después de EPOCH_MIN, Suricata activo y eve.json recibe eventos
#   comprobar_rotacion_host.sh aprendizaje EPOCH_MIN   cyberflow-aprendizaje terminó bien después de EPOCH_MIN
# Espera CF_ESPERA segundos entre dos lecturas de eve.json. No toca la rotación ni el temporizador.
# rc: 0 CUMPLE · 1 NO_CUMPLE · 3 ERROR · 2 uso
set -u -o pipefail
export LC_ALL=C
M=${1:-}; R=${2:-}
EVE=${CF_EVE:-/var/log/suricata/eve.json}; ESPERA=${CF_ESPERA:-20}; EDAD=${CF_MAX_EDAD:-60}; EDAD_STATS=${CF_MAX_STATS:-120}
fin() { echo "REQ ROTACION.$M $1 $2"; echo "FIN_ROTACION rc=$3"; exit "$3"; }
case "$M" in rotacion|aprendizaje) ;; *) echo "uso: rotacion|aprendizaje EPOCH_MIN"; exit 2;; esac
[[ "$R" =~ ^[0-9]+$ ]] || { echo "uso: EPOCH_MIN numérico"; exit 2; }
echo "INFO rotacion $M $(hostname) $(date -u +%FT%TZ) epoch $(date +%s) minimo $R ($(date -u -d @"$R" +%FT%TZ))"

servicio() {  # nombre: deja ACT RES EST INI FIN
  local s; s=$(systemctl show "$1" -p ActiveState -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p InactiveEnterTimestamp --no-pager) || return 3
  printf '%s\n' "$s" | sed 's/^/INFO   /'
  ACT=$(sed -n 's/^ActiveState=//p' <<<"$s"); RES=$(sed -n 's/^Result=//p' <<<"$s"); EST=$(sed -n 's/^ExecMainStatus=//p' <<<"$s")
  INI=$(date -u -d "$(sed -n 's/^ExecMainStartTimestamp=//p' <<<"$s")" +%s 2>/dev/null) || INI=0
  FIN=$(date -u -d "$(sed -n 's/^InactiveEnterTimestamp=//p' <<<"$s")" +%s 2>/dev/null) || FIN=0
  [ -n "$ACT" ] && [ "$INI" != 0 ] || return 3
}
exige_fin() {  # nombre
  servicio "$1" || fin ERROR "no se pudo leer $1" 3
  [ "$ACT" = inactive ] || fin NO_CUMPLE "$1 sigue en estado $ACT" 1
  [ "$INI" -ge "$R" ] || fin NO_CUMPLE "$1 no ha corrido desde el mínimo (último inicio $(date -u -d @"$INI" +%FT%TZ))" 1
  [ "$FIN" -ge "$INI" ] || fin NO_CUMPLE "$1 sin fin posterior a su inicio" 1
  [ "$RES" = success ] && [ "$EST" = 0 ] || fin NO_CUMPLE "$1 terminó con Result=$RES status=$EST" 1
  echo "OK    $1 de $(date -u -d @"$INI" +%T) a $(date -u -d @"$FIN" +%T), $((FIN - INI)) s"
}

if [ "$M" = aprendizaje ]; then
  exige_fin cyberflow-aprendizaje.service
  fin CUMPLE "reentrenamiento nocturno terminado; prepara y evalúa, no cambia el modelo en uso" 0
fi

exige_fin logrotate.service
[ -r "$EVE" ] || fin ERROR "no se puede leer $EVE" 3
GZ="$EVE.1.gz"; [ -e "$GZ" ] || fin NO_CUMPLE "no existe $GZ" 1
m=$(stat -c %Y "$GZ") || fin ERROR "stat $GZ" 3
[ "$m" -ge "$R" ] || fin NO_CUMPLE "$GZ es anterior al mínimo ($(date -u -d @"$m" +%FT%TZ))" 1
echo "OK    $GZ de $(date -u -d @"$m" +%FT%TZ)"
s=$(systemctl is-active suricata 2>&1); [ "$s" = active ] || fin NO_CUMPLE "suricata en estado $s" 1
echo "OK    suricata activo"

lee() {  # imprime: epoch del último evento y epoch del último stats
  tail -c 8388608 "$EVE" | python3 -I -c '
import datetime, json, sys
ult = st = 0
for l in sys.stdin.buffer:
    try:
        e = json.loads(l)
        t = int(datetime.datetime.strptime(e["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp())
    except Exception:
        continue
    ult = max(ult, t)
    if e.get("event_type") == "stats":
        st = max(st, t)
print(ult, st)'
}
s1=$(stat -c %s "$EVE") || fin ERROR "stat eve" 3; read -r u1 _ < <(lee) || fin ERROR "lectura eve" 3
sleep "$ESPERA"
s2=$(stat -c %s "$EVE") || fin ERROR "stat eve" 3; read -r u2 st < <(lee) || fin ERROR "lectura eve" 3
ahora=$(date +%s)
echo "INFO eve tamaño $s1 → $s2; último evento $u1 → $u2 (ahora $ahora); último stats $st"
[ "$s2" -gt "$s1" ] || fin NO_CUMPLE "eve.json no creció en ${ESPERA} s" 1
[ "$u2" -gt "$u1" ] || fin NO_CUMPLE "sin eventos nuevos en ${ESPERA} s" 1
[ $((ahora - u2)) -le "$EDAD" ] || fin NO_CUMPLE "último evento con $((ahora - u2)) s" 1
[ "$st" -ge "$R" ] && [ $((ahora - st)) -le "$EDAD_STATS" ] || fin NO_CUMPLE "sin stats recientes (último $st)" 1
fin CUMPLE "rotación terminada y eve.json recibe eventos nuevos" 0
