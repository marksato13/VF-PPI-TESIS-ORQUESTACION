#!/bin/sh
# Devuelve al grupo del directorio (setgid) el PRIMER fichero de cada arranque de tcpdump.
# Causa: con -Z, tcpdump crea ese fichero como root y luego le hace chown a <usuario>:<grupo
# primario del usuario> (tcpdump:tcpdump); los siguientes los crea ya como tcpdump y heredan el
# grupo del directorio setgid. Con 0640 y grupo tcpdump, el usuario del motor no lo puede leer.
# Uso: primer_pcap.sh DIRECTORIO GRUPO   (lo ejecuta root desde ExecStartPost)
# Solo toca live-*.pcap de ESE directorio con propietario tcpdump y grupo tcpdump; no cambia
# modos ni propietarios. Espera como máximo 10 s a que aparezca; nunca hace fallar la unidad.
D="$1"; G="$2"; i=0
while [ $i -lt 100 ]; do
  if find "$D" -maxdepth 1 -name 'live-*.pcap' -user tcpdump -group tcpdump 2>/dev/null | grep -q .; then
    find "$D" -maxdepth 1 -name 'live-*.pcap' -user tcpdump -group tcpdump -print -exec chgrp "$G" {} + \
      | sed 's#^#primer_pcap: grupo corregido en #'
    exit 0
  fi
  i=$((i + 1)); sleep 0.1
done
echo "primer_pcap: AVISO: en 10 s no apareció ningún live-*.pcap tcpdump:tcpdump en $D"
exit 0
