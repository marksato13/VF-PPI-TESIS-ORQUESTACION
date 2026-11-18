#!/bin/bash
# Aceptación del recorrido bastión–Sensor1 tras el reinicio (SOLO LECTURA; como gadmin en el bastión).
# Usa la clave dedicada (comando forzado) y solo órdenes de lectura: NO se emite ninguna solicitud de limpieza.
#   PRE_SEQ = secuencia previa al reinicio.
set -u
PRE_SEQ=${PRE_SEQ:-0}; ok=0; fa=0
c(){ if [ "$2" = 1 ]; then echo "OK    $1"; ok=$((ok+1)); else echo "FALLA $1"; fa=$((fa+1)); fi; }
S1(){ timeout 25 ssh -n -i ~/.ssh/cyberflow-d5-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null -o IdentitiesOnly=yes m4rk@10.10.60.11 "$@" 2>&1; }
echo "##### bastión→Sensor1 $(date -u +%FT%TZ)"
DESDE=$(( $(date +%s) - 120 ))
R=$(S1 "feed --desde $DESDE"); echo "feed: $R"
J(){ python3 -I -c "import json,sys;d=json.loads(sys.argv[1]);print(d.get(sys.argv[2]))" "$1" "$2" 2>/dev/null; }
c "feed: ok=True fresco=True vigente=True limpio=True" $([ "$(J "$R" ok)/$(J "$R" fresco)/$(J "$R" vigente)/$(J "$R" limpio)" = True/True/True/True ] && echo 1 || echo 0)
c "feed: secuencia ($(J "$R" secuencia)) > previa ($PRE_SEQ)" $([ "$(J "$R" secuencia)" -gt "$PRE_SEQ" ] 2>/dev/null && echo 1 || echo 0)
R=$(S1 "resultado --id 00000000000000000000000000000000"); echo "resultado: $R"
c "resultado de un id inexistente = desconocida (sin crear nada)" $([ "$(J "$R" estado)" = desconocida ] && echo 1 || echo 0)
R=$(S1 "cat /etc/passwd"); echo "orden fuera de lista: $R"
c "orden fuera de la lista blanca rechazada" $(echo "$R" | grep -q rechazada && echo 1 || echo 0)
R=$(S1 "solicitar --id 00000000000000000000000000000001 --origen 10.10.20.99"); echo "origen ajeno: $R"
c "origen distinto de 10.10.20.30 rechazado (no se creó solicitud)" $(echo "$R" | grep -qiE 'rechazad|origen' && echo 1 || echo 0)
echo "--- demás entidades"
c "relé ppi-relay-eventos PID 70246, NRestarts 0" $([ "$(systemctl show ppi-relay-eventos.service -p MainPID --value)/$(systemctl show ppi-relay-eventos.service -p NRestarts --value)" = 70246/0 ] && echo 1 || echo 0)
SD=$(timeout 25 ssh -n -o BatchMode=yes -o ConnectTimeout=8 srvdmz "systemctl show ppi-enforce-agent-v2-dmz -p MainPID -p NRestarts --value | paste -sd/; systemctl show ppi-enforce-agent-v2-dmz -p ExecStart --value | grep -c -- --aplicar" 2>&1 | paste -sd' ')
echo "agente srv-dmz (PID/NRestarts, nº de --aplicar en ExecStart): $SD"
c "agente de srv-dmz: PID 815326, NRestarts 0, sin --aplicar (sombra)" $([ "$SD" = "815326/0 0" ] && echo 1 || echo 0)
echo "##### resumen: $ok OK, $fa FALLAN"; [ $fa -eq 0 ]
