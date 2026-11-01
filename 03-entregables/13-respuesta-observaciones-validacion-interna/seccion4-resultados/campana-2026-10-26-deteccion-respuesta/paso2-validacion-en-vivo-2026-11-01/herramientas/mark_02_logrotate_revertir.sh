#!/usr/bin/env bash
# PASO2 — REVERSION de logrotate (solo si hiciera falta). [SENSOR1 m4rk] -> lo ejecuta Mark (sudo).
#   bash ~/cf-paso2-20261101T0254Z/mark/02_logrotate_revertir.sh
# Devuelve /etc/logrotate.d a su estado previo: configuracion activa original y los dos respaldos en su sitio.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; L=$B/logrotate; K=/var/backups/cyberflow-paso2-$ID; D=/etc/logrotate.d
exec > >(tee -a "$L/mark-02-revertir.log") 2>&1
echo "== revertir logrotate $(date -u +%FT%T.%3NZ)"
sudo -v || exit 1
sudo install -m 0644 -o root -g root "$K/logrotate.d-cyberflow.antes-paso2" $D/cyberflow
sudo test -e "$K/logrotate.d-cyberflow.anterior" && sudo cp -p "$K/logrotate.d-cyberflow.anterior" $D/cyberflow.anterior
sudo test -e "$K/logrotate.d-suricata.orig-cyberflow" && sudo cp -p "$K/logrotate.d-suricata.orig-cyberflow" $D/suricata.orig-cyberflow
sudo sha256sum $D/cyberflow $D/cyberflow.anterior $D/suricata.orig-cyberflow "$K"/*
sudo logrotate -d /etc/logrotate.conf > "$L/global-revertido.txt" 2>&1; echo "rc=$?" | tee "$L/global-revertido.rc"
echo "== FIN (el respaldo de $K se conserva)"
