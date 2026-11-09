#!/usr/bin/env bash
# [BASTIÓN gadmin] ETAPA4 g01 v3 (2026-11-09) — uso: g01_lanzar_bateria_e4.sh <HASTA_CONTROL_ISO> <RESPALDO_SRVDMZ>
#   RESPALDO_SRVDMZ = nombre del directorio del respaldo de srv-dmz (srvdmz-<UTC>, PROCEDIMIENTO §3).
# Lanza la batería 4C (25 episodios, escenarios-4c.json, semilla 20261102) DESPUÉS del control de 30 min, con la
# COMPUERTA de permiso (2026-11-02, corrección del defecto 3): el generador no lanza un episodio sin un permiso válido
# del vigía (vigia_4c.py bucle), que evalúa P1–P5 y X1–X3 cada minuto.
#  1) hora: aborta antes del fin del control;  2) sombra del sensor (motor candidato sin --enforce);
#  3) sombra de srv-dmz con estado_sombra.py --alcance completo --respaldo (rc 0 obligatorio; 1 aplicando,
#     2 desconocido, 3 no conforme: PARAR);  4) c05 mínima;  5) relojes;
#  6) canal de control con la Kali: UNA conexión SSH persistente (ControlMaster) para lanzar y para los permisos;
#     cada uso queda en accesos-kali.log;  7) vigía en segundo plano con un nonce nuevo (primer permiso antes de
#     lanzar);  8) generador con --permiso/--nonce.
# Resultado esperado: "estado=sombra", "comando: …scripts-4c/generar_campana.py…--permiso…", un PID del generador
# y "vigía PID". Parada: cualquier "PARAR".
# v2: el vigía lee los registros de tcpdump con `sudo -n journalctl --no-pager` (la ÚNICA forma que el sudoers de m4rk permite: con
#     `journalctl -u … --no-pager` sudo pide contraseña, la lectura SIGUSR1 falla y se pausa, P4).
# v3: la comprobación «ya hay un generador» usaba `pgrep -fc 'generar_campana.py --config'` DENTRO de un `bash -c` cuyo propio texto contiene ese patrón:
#     se contaba a sí misma (1 sin ningún generador) y g01 paraba con «PARAR: ya hay un generador». Ahora `[g]enerar_campana.py --config`: el patrón no
#     coincide con su propia línea de comandos y sigue detectando un generador real. Cambios frente a la v1: la orden del sensor (OS=) y este patrón.
set -u
HASTA=${1:?HASTA del control (ISO)}; RSRV=${2:?directorio del respaldo de srv-dmz (srvdmz-<UTC>)}
B=$HOME/cf-e4/4c; G=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
K=/home/adminatacante/cf-e4-4c; KS=/home/adminatacante/cf-campana-A/scripts-4c
PQ=$HOME/cf-e4/paquete
h=$(date -d "$HASTA" +%s) || exit 2
[ "$(date +%s)" -ge "$h" ] || { echo "PARAR: el control termina a las $HASTA; ahora $(date -u +%T)"; exit 2; }
[ -f "$B/control-declarado.json" ] || { echo "PARAR: no hay control declarado (b01)"; exit 2; }
[ -e "$B/vigia/vigia.jsonl" ] && { echo "PARAR: ya hay un vigía de otra corrida en $B/vigia (no se reutiliza)"; exit 2; }
[ -f "$PQ/scripts/etapa4/vigia_4c.py" ] || { echo "PARAR: falta $PQ/scripts/etapa4/vigia_4c.py"; exit 2; }
echo "## g01-e4 $(date -u +%FT%T.%3NZ)"
echo "## sombra (sensor)"
S=$(ssh -n -o BatchMode=yes sensor1 'P=$(systemctl show -p MainPID --value ppi-motor); C=$(tr "\0" " " < /proc/$P/cmdline)
  echo "ppi-motor $(systemctl is-active ppi-motor) PID=$P NR=$(systemctl show -p NRestarts --value ppi-motor) candidato=$(echo "$C" | grep -c "cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py .*--disparo eventos") enforce=$(echo "$C" | grep -c -- --enforce)"')
echo "  $S"; echo "$S" | grep -q 'candidato=1 enforce=0' || { echo "PARAR: el motor no es el candidato en sombra"; exit 2; }
echo "## sombra (srv-dmz): estado_sombra.py --alcance completo"
ESR="python3 -I ~/cf-e4/paquete/deploy/etapa4/srvdmz/estado_sombra.py --alcance completo --respaldo ~/respaldos-etapa4/$RSRV"
ssh -n -o BatchMode=yes srvdmz "$ESR" | sed 's/^/  /'
rc=${PIPESTATUS[0]}
case $rc in
  0) ;;
  1) echo "PARAR: srv-dmz con indicios de aplicación (X2): revertir (PROCEDIMIENTO §7)"; exit 2 ;;
  2) echo "PARAR: estado de srv-dmz DESCONOCIDO (lectura fallida): no se presume sombra"; exit 2 ;;
  3) echo "PARAR: srv-dmz sin aplicación pero no conforme (v2 inactivo o v1 activo/habilitado)"; exit 2 ;;
  *) echo "PARAR: estado_sombra.py rc=$rc (SSH u otro fallo)"; exit 2 ;;
esac
bash "$HOME/cf-e4/c05_brute_prep_e4.sh" minima | tee -a "$B/brute-pre.log"
grep -qE ' 401 t=' "$B/brute-pre.log" || { echo "PARAR: el endpoint de fuerza bruta no responde 401"; exit 2; }
echo "## relojes (p10b)"; bash "$HOME/cf-e4/p10b_relojes.sh" | tee -a "$B/relojes-4c.log"
grep -q '|desfase|<=1 s: NO' "$B/relojes-4c.log" && { echo "PARAR: desfase de reloj > 1 s"; exit 2; }

# canal de control con la Kali: una sola conexión TCP persistente para el lanzamiento y los permisos
mkdir -p "$B/vigia"; chmod 0700 "$B/vigia"
CTL="-o BatchMode=yes -o ControlMaster=auto -o ControlPath=$B/vigia/ctl-kali -o ControlPersist=5h -o ServerAliveInterval=30"
NONCE="4c-$(date -u +%Y%m%dT%H%M%SZ)-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
echo "$NONCE" > "$B/vigia/nonce.txt"
echo "## lanzamiento en la Kali [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): abrir canal de control y lanzar el generador; nonce $NONCE]" | tee -a "$B/accesos-kali.log"
ssh $CTL kali "set -u; K=$K; KS=$KS
[ -e \$K/corrida ] && { echo 'PARAR: ya existe '\$K/corrida; exit 2; }
[ -e \$K/permiso.json ] && { echo 'PARAR: hay un permiso de otra corrida en '\$K/permiso.json; exit 2; }
sha256sum -c \$K/sha256-esperado.txt | sed 's/^/  /'; sha256sum -c --quiet \$K/sha256-esperado.txt || { echo 'PARAR: hashes'; exit 2; }
[ \$(pgrep -fc '[g]enerar_campana.py --config') = 0 ] || { echo 'PARAR: ya hay un generador'; exit 2; }" || exit 2

# vigía: orden del sensor (solo lectura), de srv-dmz (estado_sombra) y del canal de la Kali (instala el permiso
# que llega por stdin de forma atómica e imprime su reloj y las marcas nuevas)
OS="python3 -I ~/cf-e4/paquete/scripts/etapa4/vigia_4c.py sensor --archivador ~/cf-e4/4c/archivo-pcap --muestras ~/cf-e4/4c/salud/muestras.jsonl --lista-blanca 10.10.10.20,10.10.30.10 --origen 10.10.20.30 --journalctl 'sudo -n journalctl --no-pager'"
OK_="umask 077; cat > $K/permiso.json.tmp && mv -f $K/permiso.json.tmp $K/permiso.json && date +%s.%N && { tail -n +{N} $K/corrida/marcas.jsonl 2>/dev/null || true; }"
setsid nohup python3 -I "$PQ/scripts/etapa4/vigia_4c.py" bucle --dir "$B/vigia" --nonce "$NONCE" --planificados 25 \
  --ssh-sensor "ssh -o BatchMode=yes -o ConnectTimeout=10 sensor1" --orden-sensor "$OS" \
  --ssh-srvdmz "ssh -o BatchMode=yes -o ConnectTimeout=10 srvdmz" --orden-srvdmz "$ESR" \
  --ssh-kali "ssh $CTL -o ConnectTimeout=10 kali" --orden-kali "$OK_" \
  > "$B/vigia/vigia.stdout" 2> "$B/vigia/vigia.stderr" < /dev/null &
echo $! > "$B/vigia/vigia.pid"
for i in $(seq 1 30); do
  [ -s "$B/vigia/vigia.jsonl" ] && grep -q '"evento": "ronda"' "$B/vigia/vigia.jsonl" && break; sleep 2
done
grep -q '"evento": "ronda"' "$B/vigia/vigia.jsonl" 2>/dev/null || { echo "PARAR: el vigía no completó su primera ronda"; kill "$(cat "$B/vigia/vigia.pid")"; exit 2; }
E1=$(tail -1 "$B/vigia/vigia.jsonl" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["permiso"]["estado"], "|", "; ".join(r["permiso"]["causas"]), "| kali_rc", r["kali_rc"])')
echo "  vigía PID $(cat "$B/vigia/vigia.pid"): primer permiso: $E1"
case "$E1" in
  continuar*"kali_rc 0") ;;
  *) echo "PARAR: el primer permiso no es 'continuar' con la Kali alcanzable: $E1"; kill "$(cat "$B/vigia/vigia.pid")"; exit 2 ;;
esac

ssh $CTL kali "set -u; K=$K; KS=$KS
CMD=\"python3 -u \$KS/generar_campana.py --config /home/adminatacante/cf-campana-A/escenarios/escenarios-4c.json --salida-dir \$K/corrida --autorizado --permiso \$K/permiso.json --nonce $NONCE\"
echo \"\$CMD\" > \$K/comando.txt; date -u +%FT%T.%3NZ > \$K/lanzado.txt
setsid nohup bash -c \"\$CMD > \$K/generador.stdout 2> \$K/generador.stderr; echo \\\$? > \$K/generador.rc; date -u +%FT%T.%3NZ > \$K/terminado.txt\" > /dev/null 2>&1 < /dev/null &
sleep 3; echo \"  comando: \$CMD\"; echo \"  pid(s): \$(pgrep -f 'generar_campana.py --config' | tr '\n' ' ')\"; head -3 \$K/generador.stdout | sed 's/^/  | /'"
echo "## lanzado $(date -u +%FT%T.%3NZ); el canal de control sigue abierto para el vigía (accesos-kali.log)" | tee -a "$B/accesos-kali.log"
echo "## fin $(date -u +%FT%T.%3NZ)  (guion en ${G:-?})"
