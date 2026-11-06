#!/usr/bin/env bash
# [LAPTOP Docker, sin red] Reproduce la causa del P11=NO_CUMPLE del P0 r2 anticipado (06-nov 23:24Z) SIN muestreadores:
# la función procesos() de sensor1_muestreadores.sh hace «pgrep -af PATRON». pgrep se excluye a sí mismo, pero NO al
# bash que lo ejecuta. Con el mecanismo sin escritura del P0 r2 (bash -c "$txt"), la línea de órdenes de ese bash ES
# el texto del guion, que contiene el patrón -> pgrep coincide con su propio intérprete -> «ya hay muestreadores».
# Ejecutado desde un fichero (bash guion.sh) la línea de órdenes no contiene el patrón y no hay coincidencia.
set -u
P="salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py|muestreo_s14.py"
txt='procesos() { local o rc; o=$(pgrep -af "$1" 2>&1); rc=$?; case $rc in 0) grep -v pgrep <<<"$o"; return 0;; 1) return 1;; *) return 2;; esac; }
procesos "salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py|muestreo_s14.py"; rc=$?
case $rc in 1) echo "RESULTADO ningún muestreador en marcha";; 0) echo "RESULTADO ya hay muestreadores en marcha";; *) echo "RESULTADO pgrep falló";; esac'
echo "== sin ningún muestreador: pgrep real (patrón con clases de caracteres)"
pgrep -af "salud_captura[.]py muestrear|muestreo_fin[o][.]py|obs_pca[p][.]py|muestreo_s1[4][.]py"; echo "pgrep_rc=$?"
echo "== A. como en el P0 r2: bash -c \"\$txt\""
bash -c "$txt"
echo "== B. el mismo texto desde un fichero: bash fichero.sh"
f=$(mktemp); printf '%s\n' "$txt" > "$f"; bash "$f"; rm -f "$f"
