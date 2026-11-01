#!/usr/bin/env bash
# PASO2 — verificacion del respaldo de logrotate (solo lectura con sudo). [SENSOR1 m4rk] -> lo ejecuta Mark.
#   bash ~/cf-paso2-20261101T0254Z/mark/03_verificar_respaldo.sh
# El guion 01 no registro permisos ni hashes DENTRO del respaldo: el comodin lo expandia el shell de m4rk, que no
# puede leer un directorio root 0700. Aqui el listado lo hace root (sudo find), sin comodines del shell.
set -u
ID=20261101T0254Z; L=$HOME/cf-paso2-$ID/logrotate; K=/var/backups/cyberflow-paso2-$ID
exec > >(tee "$L/mark-03-verificar-respaldo.log") 2>&1
echo "== verificar respaldo $(date -u +%FT%T.%3NZ)"
sudo -v || exit 1
sudo stat -c '%n %U:%G %a %s %y' "$K"
sudo find "$K" -maxdepth 1 -type f -exec stat -c '%n %U:%G %a %s %y' {} +
sudo find "$K" -maxdepth 1 -type f -exec sha256sum {} +
echo "-- esperado: antes-paso2 y cyberflow.anterior = 7832acf2..., suricata.orig-cyberflow = f95789a4..."
echo "-- /etc/logrotate.d actual:"; ls -la /etc/logrotate.d/
echo "== FIN"
