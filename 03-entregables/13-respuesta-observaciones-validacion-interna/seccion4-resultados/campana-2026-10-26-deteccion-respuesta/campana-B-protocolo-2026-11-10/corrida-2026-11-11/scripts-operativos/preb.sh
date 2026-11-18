set -u
T=$(date -u +%Y%m%dT%H%M%SZ); D=/var/lib/cyberflow/reversion-B/PRE-B-$T
sudo -n sh -c "mkdir -p $D && cd $D && systemctl show ppi-enforce-agent-v2-dmz -p Id -p ActiveState -p NRestarts -p MainPID -p ExecStart -p DropInPaths -p ActiveEnterTimestamp > agente-show.txt && sha256sum /opt/cyberflow/agente-v2/* /usr/local/sbin/cf-nft-helper > codigo.sha256 && cp -p /var/lib/cyberflow/agente/estado.json estado.json && printf '%s' '{\"perfil\":\"dmz\",\"operaciones\":[{\"op\":\"listar\"}]}' | /usr/local/sbin/cf-nft-helper > listar.json && nft list ruleset > ruleset.nft && nft list tables > tablas.txt && cp -p /var/lib/cyberflow/agente/traza.jsonl traza.jsonl && systemctl cat ppi-enforce-agent-v2-dmz > unidad-agente.txt && sha256sum * > SHA256SUMS"
echo "PRE-B: $D"; sudo -n sh -c "cd $D && sha256sum -c SHA256SUMS | grep -vc ': OK$'; ls; wc -c ruleset.nft tablas.txt | head -2"
echo "$D" > ~/cf-b/PRE-B-actual.txt
echo "--- verificar_srvdmz CON_SUDO contra el PRE-B"
CON_SUDO=1 bash ~/cf-e4/paquete-a1cea5e/deploy/etapa4/srvdmz/verificar_srvdmz.sh $D 2>&1 | tail -14; echo "rc=${PIPESTATUS[0]}"
