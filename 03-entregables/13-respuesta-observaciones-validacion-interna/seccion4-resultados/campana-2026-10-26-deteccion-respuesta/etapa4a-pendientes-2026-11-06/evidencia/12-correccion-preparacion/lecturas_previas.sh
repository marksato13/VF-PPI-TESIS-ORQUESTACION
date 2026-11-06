#!/usr/bin/env bash
# [LAPTOP Git Bash] -> [BASTIÓN gadmin] Lecturas previas con el paquete a12deae. SOLO LECTURA: no arranca ni para ningún
# generador ni muestreador y no ejecuta E-carga.
#   clientes: generadores.sh configuracion y estado (systemctl show + /proc), por stdin desde el bastión
#   Sensor1:  sensor1_muestreadores.sh comprobar en una carpeta NUEVA ~/cf-e4/ecarga-v2-seco-<ts> (incluye
#             obs_pcap --en-seco, que no crea salidas) y lectura directa de la retención del anillo y de PSI
#   clientes: aviso SUSTITUIDO junto a la copia antigua de los guiones (sin tocar su contenido)
set -uo pipefail
K="$HOME/.ssh/id_ed25519"; B="gadmin@10.10.10.30"; SO="-o BatchMode=yes -o ConnectTimeout=10"
ssh $SO -i "$K" "$B" 'bash -s' <<'BASTION'
set -u
E=~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga
O="-o BatchMode=yes -o ConnectTimeout=10"
CLI="ssh $O -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
SEN="ssh $O -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
echo "##### $(date -u +%FT%TZ) clientes: generadores.sh configuracion (a12deae)"
$CLI 'bash -s configuracion' < $E/generadores.sh; echo "rc=$?"
echo "##### clientes: generadores.sh estado"
$CLI 'bash -s estado' < $E/generadores.sh; echo "rc=$?"
echo "##### clientes: PartOf / ExecStart tal cual (systemctl show)"
$CLI 'for p in ofimatica navegacion descargas aplicacion ligero erratico; do systemctl show -p Id -p LoadState -p PartOf -p WantedBy -p UnitFileState cyberflow-lab-$p.service | tr "\n" " "; echo; done; systemctl show -p Id -p Wants -p ConsistsOf -p UnitFileState cyberflow-lab.target | tr "\n" " "; echo' < /dev/null
echo "##### clientes: aviso junto a la copia sustituida"
$CLI 'cd ~/cf-e4 2>/dev/null && for v in ecarga-v2-guiones-c7f24510; do [ -d $v ] || continue; [ -e $v.SUSTITUIDO.txt ] && echo "aviso ya presente" || { printf "%s\n" "$v SUSTITUIDO: generadores.sh llega por stdin desde ~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga del bastión (PREPARACION-ECARGA-v2-r2). No usar." > $v.SUSTITUIDO.txt && echo "aviso creado"; }; (cd $v && sha256sum -c --strict --quiet SHA256SUMS && echo "$v intacto"); done; ls -1 ~/cf-e4' < /dev/null
TS=$(date -u +%Y%m%dT%H%M%SZ)
echo "##### Sensor1: sensor1_muestreadores.sh comprobar en ~/cf-e4/ecarga-v2-seco-$TS (sin carga)"
$SEN "bash ~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga/sensor1_muestreadores.sh comprobar ~/cf-e4/ecarga-v2-seco-$TS 1794197760 2026-11-09T04:16:00Z" < /dev/null; echo "rc=$?"
echo "##### Sensor1: anillo y PSI (lectura directa)"
$SEN 'a=/var/lib/ppi-motor-capture; n=$(ls -1 $a | wc -l); v=$(ls -1tr $a | head -1); echo "anillo ficheros=$n mas_antiguo=$v edad_s=$(( $(date +%s) - $(stat -c %Y $a/$v) ))"; for r in cpu io memory; do echo "psi $r: $(tr "\n" " " < /proc/pressure/$r)"; done; uname -r' < /dev/null
BASTION
