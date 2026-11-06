#!/usr/bin/env bash
# [LAPTOP Git Bash] Diagnóstico de SOLO LECTURA del P11 (Sensor1): ¿hay muestreadores reales en marcha?
# El patrón usa clases de caracteres ([o], [.]) para que la propia orden no coincida consigo misma.
# Guarda sensor1-<TS>.stdout|stderr|rc aquí. No detiene, arranca ni modifica nada.
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
TS=$(date -u +%Y%m%dT%H%M%SZ); O="-o BatchMode=yes -o ConnectTimeout=10"
R='date -u +%FT%TZ; echo "== pgrep (patrón de comprobar, sin autocoincidencia)"; pgrep -af "salud_captura[.]py muestrear|muestreo_fin[o][.]py|obs_pca[p][.]py|muestreo_s1[4][.]py"; echo "pgrep_rc=$?"; echo "== ps: procesos de python o bash de m4rk"; ps -o pid,ppid,etimes,user,args -u m4rk | grep -E "[p]ython|[b]ash" | cut -c1-200; echo "== unidades systemd con muestre en el nombre"; systemctl list-units --all --no-pager --plain "*muestre*" 2>&1 | head -5'
ssh $O -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '$R'" < /dev/null \
  > "$AQUI/sensor1-$TS.stdout" 2> "$AQUI/sensor1-$TS.stderr"; echo $? > "$AQUI/sensor1-$TS.rc"
cat "$AQUI/sensor1-$TS.stdout"; echo "-- stderr"; cat "$AQUI/sensor1-$TS.stderr"; echo "rc=$(cat "$AQUI/sensor1-$TS.rc")"
