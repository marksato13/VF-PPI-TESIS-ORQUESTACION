#!/usr/bin/env bash
# [BASTIÓN gadmin] ETAPA4 g01 — uso: g01_lanzar_bateria_e4.sh <HASTA_CONTROL_ISO>. Lanza la batería 4C (25 episodios,
# escenarios-4c.json, semilla 20261102) DESPUÉS del control de 30 min. Igual que g01 del 3B, con la sombra de la
# Etapa 4 (motor candidato sin --enforce, agente v2 sin --aplicar y sin eventos 'aplicacion', agente v1 inactivo,
# sin tablas cyberflow) y SIN la segunda comprobación programada del endpoint (se verifica después en brute.log).
#  1) hora: aborta antes del fin del control;  2) sombra (lecturas; sudo -n de lectura en srv-dmz, como en el 3B);
#  3) c05 mínima;  4) relojes;  5) UNA sesión SSH a la Kali para lanzar el generador (setsid nohup) y salir.
# Resultado esperado: "comando: …escenarios-4c.json…" y un PID. Parada: cualquier "PARAR".
set -u
HASTA=${1:?HASTA del control (ISO)}
B=$HOME/cf-e4/4c; G=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
h=$(date -d "$HASTA" +%s) || exit 2
[ "$(date +%s)" -ge "$h" ] || { echo "PARAR: el control termina a las $HASTA; ahora $(date -u +%T)"; exit 2; }
[ -f "$B/control-declarado.json" ] || { echo "PARAR: no hay control declarado (b01)"; exit 2; }
echo "## g01-e4 $(date -u +%FT%T.%3NZ)"
echo "## sombra (sensor)"
S=$(ssh -n -o BatchMode=yes sensor1 'P=$(systemctl show -p MainPID --value ppi-motor); C=$(tr "\0" " " < /proc/$P/cmdline)
  echo "ppi-motor $(systemctl is-active ppi-motor) PID=$P NR=$(systemctl show -p NRestarts --value ppi-motor) candidato=$(echo "$C" | grep -c "cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py .*--disparo eventos") enforce=$(echo "$C" | grep -c -- --enforce)"')
echo "  $S"; echo "$S" | grep -q 'candidato=1 enforce=0' || { echo "PARAR: el motor no es el candidato en sombra"; exit 2; }
echo "## sombra (srv-dmz)"
R=$(ssh -n -o BatchMode=yes srvdmz 'echo "v1 timer=$(systemctl is-active ppi-enforce-agent.timer)/$(systemctl is-enabled ppi-enforce-agent.timer) servicio=$(systemctl is-active ppi-enforce-agent.service) v2=$(systemctl is-active ppi-enforce-agent-v2-dmz) aplicar_en_procesos=$(pgrep -af agente_enforce | grep -c -- --aplicar) tablas_cyberflow=$(sudo -n nft list tables | grep -c cyberflow) eventos_aplicacion=$(sudo -n grep -c "\"evento\": \"aplicacion\"" /var/lib/cyberflow/agente/traza.jsonl)"')
echo "  $R"
echo "$R" | grep -q 'v1 timer=inactive/disabled servicio=inactive v2=active aplicar_en_procesos=0 tablas_cyberflow=0 eventos_aplicacion=0' \
  || { echo "PARAR: srv-dmz no está en sombra demostrada"; exit 2; }
bash "$HOME/cf-e4/c05_brute_prep_e4.sh" minima | tee -a "$B/brute-pre.log"
grep -qE ' 401 t=' "$B/brute-pre.log" || { echo "PARAR: el endpoint de fuerza bruta no responde 401"; exit 2; }
echo "## relojes (p10b)"; bash "$HOME/cf-e4/p10b_relojes.sh" | tee -a "$B/relojes-4c.log"
grep -q '|desfase|<=1 s: NO' "$B/relojes-4c.log" && { echo "PARAR: desfase de reloj > 1 s"; exit 2; }
echo "## lanzamiento en la Kali [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): lanzar el generador]" | tee -a "$B/accesos-kali.log"
ssh -o BatchMode=yes kali 'set -u; K=$HOME/cf-e4-4c; cd $HOME/cf-campana-A/scripts
sha256sum -c $K/sha256-esperado.txt | sed "s/^/  /"; sha256sum -c --quiet $K/sha256-esperado.txt || { echo "PARAR: hashes"; exit 2; }
[ -e $K/corrida ] && { echo "PARAR: ya existe $K/corrida"; exit 2; }
CMD="python3 -u /home/adminatacante/cf-campana-A/scripts/generar_campana.py --config /home/adminatacante/cf-campana-A/escenarios/escenarios-4c.json --salida-dir $K/corrida --autorizado"
echo "$CMD" > $K/comando.txt; date -u +%FT%T.%3NZ > $K/lanzado.txt
setsid nohup bash -c "$CMD > $K/generador.stdout 2> $K/generador.stderr; echo \$? > $K/generador.rc; date -u +%FT%T.%3NZ > $K/terminado.txt" > /dev/null 2>&1 < /dev/null &
sleep 3; echo "  comando: $CMD"; echo "  pid(s): $(pgrep -f "generar_campana.py --config" | tr "\n" " ")"; head -3 $K/generador.stdout | sed "s/^/  | /"'
echo "## fin acceso Kali $(date -u +%FT%T.%3NZ)" | tee -a "$B/accesos-kali.log"
echo "## fin $(date -u +%FT%T.%3NZ)  (guion en ${G:-?})"
