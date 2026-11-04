#!/usr/bin/env bash
# [BASTIÓN gadmin] ETAPA4 k20 — canal de control SIMULADO con la Kali (reconciliación 2026-11-03).
#   uso: k20_canal_control_simulado.sh <4b|4c> <HASTA_ISO>
# Para que el control (4B, y el control de 30 min previo a la batería 4C) tenga en las ventanas de la Kali el
# MISMO tráfico de gestión que la batería: una conexión SSH persistente (ControlMaster, ServerAliveInterval=30)
# y, cada 60 s, una sesión por ese canal que escribe un JSON del tamaño del permiso del vigía e imprime la hora,
# como `vigia_4c.py bucle --orden-kali`. NO lanza nada, NO escribe el permiso real (permiso.json) ni toca la
# corrida: escribe ~/cf-e4-canal-<fase>/permiso-simulado.json. Cada uso queda en accesos-kali.log, como en g01.
# Se cierra solo al llegar a HASTA (y, en la 4C, antes de que g01 abra el canal real). Corre en segundo plano:
#   setsid nohup bash k20_canal_control_simulado.sh 4b <HASTA_ISO> > ~/cf-e4/4b/canal-simulado.out 2>&1 < /dev/null &
set -u
F=${1:?fase 4b|4c}; HASTA=${2:?HASTA ISO}
case "$F" in 4b|4c) ;; *) echo "PARAR: fase $F"; exit 2;; esac
h=$(date -d "$HASTA" +%s) || exit 2
B=$HOME/cf-e4/$F; D=$B/canal-simulado; mkdir -p "$D"; chmod 0700 "$D"
[ -e "$D/ctl-kali" ] && { echo "PARAR: ya hay un canal simulado abierto ($D/ctl-kali)"; exit 2; }
CTL="-o BatchMode=yes -o ControlMaster=auto -o ControlPath=$D/ctl-kali -o ControlPersist=9h -o ServerAliveInterval=30"
KD=cf-e4-canal-$F
ORDEN="mkdir -p ~/$KD && umask 077 && cat > ~/$KD/permiso-simulado.json.tmp && mv -f ~/$KD/permiso-simulado.json.tmp ~/$KD/permiso-simulado.json && date +%s.%N"
echo "## [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): abrir canal de control SIMULADO ($F) hasta $HASTA]" | tee -a "$B/accesos-kali.log"
PER=${K20_PERIODO:-60}   # 60 s como el vigía; solo el banco lo acorta
n=0
while [ "$(date +%s)" -lt "$h" ]; do
  n=$((n + 1)); t0=$(date +%s.%N)
  printf '{"nonce": "simulado-%s", "estado": "continuar", "causas": [], "secuencia": %d, "emitido": %s, "valido_hasta": %s}\n' \
    "$F" "$n" "$t0" "$(awk -v t="$t0" 'BEGIN { printf "%.6f", t + 150 }')" \
    | ssh $CTL -o ConnectTimeout=10 kali "$ORDEN" > "$D/ultima.txt" 2>&1
  rc=$?
  echo "$(date -u +%FT%T.%3NZ) canal de control SIMULADO (ronda #$n) rc=$rc" >> "$B/accesos-kali.log"
  printf '{"evento": "ronda_simulada", "n": %d, "epoch": %s, "kali_rc": %d}\n' "$n" "$t0" "$rc" >> "$D/canal.jsonl"
  ahora=$(date +%s); s=$(( PER - (ahora - ${t0%.*}) )); resto=$(( h - ahora ))
  [ "$resto" -lt "$s" ] && s=$resto
  [ "$s" -gt 0 ] && sleep "$s"
done
ssh $CTL -O exit kali > /dev/null 2>&1
echo "## [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): canal de control SIMULADO ($F) cerrado tras $n rondas]" | tee -a "$B/accesos-kali.log"
