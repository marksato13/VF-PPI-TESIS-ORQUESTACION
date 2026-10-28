#!/usr/bin/env bash
# PREP 23 — bastion -> srv-dmz: (a) instala modo_sombra.sh corregido (sha bc2742f8…) conservando el anterior como
# modo_sombra.sh.e6a676a; (b) devuelve el timer del agente a su estado ORIGINAL (active/enabled, registrado en
# /opt/cf-sombra-estado/20261028-072923 por el intento fallido) para que el respaldo nuevo sea el estado real;
# (c) activa la SOMBRA con el script corregido; (d) verificacion independiente.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
RK=~/.ssh/cyberflow-to-srv; SRV=adminsrvdmz@10.10.30.10
echo "## p23  inicio=$(ts)"
ssh -n -i $RK $SRV 'cd ~/cf-campana && cp -p modo_sombra.sh modo_sombra.sh.e6a676a' || { echo ABORTO; exit 2; }
scp -q -i $RK ~/cf-prep-copias/srv/modo_sombra.v2.sh $SRV:cf-campana/modo_sombra.sh </dev/null || { echo ABORTO; exit 2; }
ssh -n -i $RK $SRV 'cd ~/cf-campana && chmod 750 modo_sombra.sh && sha256sum modo_sombra.sh modo_sombra.sh.e6a676a restaurar_enforcement.sh | sed "s/^/  /"
echo "  respaldo del intento fallido (estado ORIGINAL):"; for f in agent-timer.active agent-timer.enabled agent-service.enabled; do echo "    $f=$(sudo -n cat /opt/cf-sombra-estado/20261028-072923/$f)"; done
echo "--- (b) timer a su estado original ($(date -u +%T))"
echo "  antes: timer active=$(systemctl is-active ppi-enforce-agent.timer) enabled=$(systemctl is-enabled ppi-enforce-agent.timer)"
sudo -n systemctl start ppi-enforce-agent.timer && echo "  start rc=0"
echo "  ahora: timer active=$(systemctl is-active ppi-enforce-agent.timer) enabled=$(systemctl is-enabled ppi-enforce-agent.timer) service=$(systemctl is-enabled ppi-enforce-agent.service)"
echo "--- (c) ACTIVAR SOMBRA con el script corregido ($(date -u +%T))"
T=$(ls -1d ~/cf-campana/feed-sensor-* | tail -1); echo "  FEED_DIR=$T"
FEED_DIR=$T bash ./modo_sombra.sh --ejecutar --motor-verificado; echo "  rc modo_sombra=$?"
echo "--- (d) verificacion independiente ($(date -u +%T))"
for u in ppi-enforce-agent.timer ppi-enforce-agent.service; do echo "  $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u)"; done
for s in cyberflow_bloqueados cyberflow_limitados; do o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?; echo "  $s rc=$rc $(echo "$o" | grep -q elements && echo "CON ELEMENTOS: $(echo "$o" | grep elements)" || echo "sin elements")"; done
U=$(sudo -n cat /opt/cf-sombra-estado/ultimo); echo "  ultimo=$U"; sudo -n sh -c "cd /opt/cf-sombra-estado/$U && for f in *; do echo \"    \$f: \$(head -c 120 \$f | tr \"\n\" \" \")\"; done"
sudo -n sha256sum /opt/cf-sombra-estado/$U/escalada-estado.json /opt/cf-sombra-estado/$U/nft-antes.txt | sed "s/^/    /"
echo "  timers:"; systemctl list-timers --all --no-legend "ppi-enforce*" | sed "s/^/    /"'
echo "## fin=$(ts)"
