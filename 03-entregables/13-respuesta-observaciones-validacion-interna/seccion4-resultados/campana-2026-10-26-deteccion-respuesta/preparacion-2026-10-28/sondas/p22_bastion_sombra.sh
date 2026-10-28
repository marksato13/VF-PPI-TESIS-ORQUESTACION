#!/usr/bin/env bash
# PREP 22 — bastion: (a) copia desde el SENSOR feed.json/feed.sig/estado.json (escalada residual) y las lleva a srv-dmz;
# (b) estado previo en srv-dmz; (c) activa la SOMBRA con el script revisado (HEAD e6a676a) usando FEED_DIR = la copia
# traida del sensor (no se consulta una ruta del sensor desde srv-dmz); (d) verificacion independiente.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
SK=~/.ssh/cyberflow-to-sensor; RK=~/.ssh/cyberflow-to-srv; SRV=adminsrvdmz@10.10.30.10
T=$(date -u +%Y%m%d-%H%M%S); L=~/cf-prep-sensor/feed-$T; mkdir -p "$L"
echo "## p22  inicio=$(ts)"
echo "--- (a) feed y escalada desde el sensor ($(ts))"
scp -q -p -i $SK m4rk@10.10.60.11:feed/feed.json m4rk@10.10.60.11:feed/feed.sig m4rk@10.10.60.11:feed/estado.json "$L/" </dev/null || { echo "ABORTO: no se pudo copiar el feed del sensor"; exit 2; }
( cd "$L" && sha256sum feed.json feed.sig estado.json ) | sed 's/^/  /'
python3 -c "import json;f=json.load(open('$L/feed.json'));e=json.load(open('$L/estado.json'));print('  feed entradas=%d generado=%s | escalada=%s'%(len(f['entradas']),f['generado'],{k:v['bloqueos'] for k,v in e.items()}))"
ssh -n -i $RK $SRV "mkdir -p ~/cf-campana/feed-sensor-$T" && scp -q -p -i $RK "$L"/* $SRV:cf-campana/feed-sensor-$T/ </dev/null || { echo "ABORTO: no se pudo llevar el feed a srv-dmz"; exit 2; }
echo "--- (b) srv-dmz antes ($(ts))"
ssh -n -i $RK $SRV 'for u in ppi-enforce-agent.timer ppi-enforce-agent.service; do echo "  $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u)"; done
for s in cyberflow_bloqueados cyberflow_limitados; do o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?; echo "  $s rc=$rc $(echo "$o" | tr "\n" " " | grep -oE "elements = \{[^}]*\}" || echo "(sin elements)")"; done
sudo -n nft list table inet cyberflow > /tmp/nft-antes-sombra.txt 2>&1; echo "  tabla inet cyberflow: $(wc -l < /tmp/nft-antes-sombra.txt) lineas"'
echo "--- (c) ACTIVAR SOMBRA ($(ts))"
ssh -n -i $RK $SRV "cd ~/cf-campana && sha256sum modo_sombra.sh && FEED_DIR=\$HOME/cf-campana/feed-sensor-$T bash ./modo_sombra.sh --ejecutar --motor-verificado; echo \"  rc modo_sombra=\$?\""
echo "--- (d) verificacion independiente ($(ts))"
ssh -n -i $RK $SRV 'for u in ppi-enforce-agent.timer ppi-enforce-agent.service; do echo "  $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u)"; done
for s in cyberflow_bloqueados cyberflow_limitados; do o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?; echo "  $s rc=$rc $(echo "$o" | tr "\n" " " | grep -oE "elements = \{[^}]*\}" || echo "(sin elements)")"; echo "$o" | sed "s/^/      /"; done
U=$(cat /opt/cf-sombra-estado/ultimo); echo "  estado guardado: /opt/cf-sombra-estado/$U"; sudo -n ls -la /opt/cf-sombra-estado/$U | sed "s/^/    /"
sudo -n sha256sum /opt/cf-sombra-estado/$U/escalada-estado.json | sed "s/^/    /"
echo "  timers listados:"; systemctl list-timers --all --no-legend "ppi-enforce*" | sed "s/^/    /"'
echo "## fin=$(ts)"
