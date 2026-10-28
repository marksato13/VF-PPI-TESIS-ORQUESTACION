#!/usr/bin/env bash
# PREP 31 — sensor: fase de rotacion del anillo (segundos de creacion de los ultimos ficheros) y estado de ambos motores.
set -u
echo "## p31  $(date -u +%FT%T.%3NZ)"
ls -1 /var/lib/ppi-motor-capture/live-*.pcap | tail -8 | sed 's#.*/live-##; s/\.pcap//' | awk '{s=substr($1,13,2); printf "  %s  seg=%s  fase15=%d\n",$1,s,s%15}'
C=$HOME/cf-prep-20261028/candidato
echo "  candidato vivo=$(kill -0 $(cat $C/motor.pid) 2>/dev/null && echo SI || echo NO) lineas=$(wc -l < $C/logs/motor_decision.log) | produccion NRestarts=$(systemctl show -p NRestarts --value ppi-motor)"
