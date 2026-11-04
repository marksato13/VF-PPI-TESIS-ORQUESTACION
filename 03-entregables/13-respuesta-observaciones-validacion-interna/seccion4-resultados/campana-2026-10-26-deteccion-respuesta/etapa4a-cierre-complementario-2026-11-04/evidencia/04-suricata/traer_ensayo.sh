set -eu
DST="$1"; K="-i $HOME/.ssh/id_ed25519 -o BatchMode=yes"
ssh $K gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cat /tmp/cierre4a-salud-ensayo.tgz'" > "$DST/cierre4a-salud-ensayo.tgz"
sha256sum "$DST/cierre4a-salud-ensayo.tgz"
mkdir -p "$DST/x" && tar -xzf "$DST/cierre4a-salud-ensayo.tgz" -C "$DST/x" && (cd "$DST/x/ensayo" && sha256sum -c --quiet SHA256SUMS && echo "ensayo SHA256SUMS OK")
ls -la "$DST/x/salud" "$DST/x/ensayo"
ssh $K gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'sudo -n grep -m3 rechazo /var/lib/cyberflow/agente/traza.jsonl'" | cut -c1-400
