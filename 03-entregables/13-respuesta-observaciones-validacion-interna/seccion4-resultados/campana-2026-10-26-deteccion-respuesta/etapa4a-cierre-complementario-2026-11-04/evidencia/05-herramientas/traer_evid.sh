set -eu
# Trae al portátil (vía bastión) la evidencia de las fases A/B, previo y la del bastión. Solo lectura remota.
DST="$1"; mkdir -p "$DST"
K="-i $HOME/.ssh/id_ed25519 -o BatchMode=yes"
ssh $K gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd /home/m4rk/cf-e4/cierre4a && tar -cf - previo sudo-A-* sudo-B-* base-4a-suricata.json base-4a-suricata-eve.json base-03nov-suricata.json base-04nov-suricata.json calentamiento-suricata-eve.json'" > "$DST/sensor1.tar"
ssh $K gadmin@10.10.10.30 "cd /home/gadmin/cierre4a && tar -cf - sudo-bastion-*" > "$DST/bastion.tar"
mkdir -p "$DST/sensor1" "$DST/bastion"
tar -xf "$DST/sensor1.tar" -C "$DST/sensor1"; tar -xf "$DST/bastion.tar" -C "$DST/bastion"
for d in "$DST"/sensor1/sudo-* "$DST"/bastion/sudo-*; do (cd "$d" && sha256sum -c --quiet SHA256SUMS && echo "$(basename "$d"): SHA256SUMS OK") || echo "$(basename "$d"): DIFERENCIAS (ver arriba)"; done
ls -R "$DST" | head -n 80
