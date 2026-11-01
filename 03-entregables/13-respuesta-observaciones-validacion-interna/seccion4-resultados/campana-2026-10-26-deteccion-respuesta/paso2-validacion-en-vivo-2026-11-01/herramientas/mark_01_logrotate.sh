#!/usr/bin/env bash
# PASO2 — logrotate. [SENSOR1 m4rk] -> lo ejecuta Mark (sudo pide su contrasena; Claude no la tiene).
#   bash ~/cf-paso2-20261101T0254Z/mark/01_logrotate.sh
# Hace, en este orden, y guarda TODA la salida en ~/cf-paso2-20261101T0254Z/logrotate/:
#   1. linea base: sudo logrotate -d /etc/logrotate.conf (salida completa + rc)
#   2. respaldo exclusivo /var/backups/cyberflow-paso2-20261101T0254Z/ (root:root 0700):
#        - copia de /etc/logrotate.d/cyberflow (configuracion activa)
#        - TRASLADO (mv, sin borrar) de los dos respaldos redundantes que hoy rompen la configuracion global:
#          /etc/logrotate.d/cyberflow.anterior y /etc/logrotate.d/suricata.orig-cyberflow
#        - permisos, propietario, fechas y sha256 antes y despues
#   3. comprobacion global sin los respaldos (se espera rc=0)
#   4. instala la estrofa nueva (motor_decision.log + _state/ciclos.jsonl) y comprueba de nuevo (se espera rc=0)
# No usa --force, no provoca ninguna rotacion (-d = depuracion, no cambia ficheros ni el estado).
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; L=$B/logrotate; K=/var/backups/cyberflow-paso2-$ID
D=/etc/logrotate.d; N=$L/logrotate-cyberflow.nuevo
ok(){ echo "  [$(date -u +%T)] $*"; }
echo "== PASO2 logrotate $(date -u +%FT%T.%3NZ)" | tee "$L/mark-01.log"
exec > >(tee -a "$L/mark-01.log") 2>&1
sudo -v || { echo "sudo no autorizado: no se hizo nada"; exit 1; }
[ "$(sha256sum "$N" | cut -c1-64)" = 183e7bc469122ed9e2d517d0561adde2afa589a97dce3365e291d9b185fce094 ] || { echo "PARAR: la estrofa nueva no es la revisada"; exit 2; }
sudo test -e "$K" && { echo "PARAR: ya existe $K"; exit 2; }

echo "-- 1. linea base"
sudo logrotate -d /etc/logrotate.conf > "$L/global-1-antes.txt" 2>&1; echo "rc=$?" > "$L/global-1-antes.rc"; ok "antes $(cat "$L/global-1-antes.rc")"

echo "-- 2. respaldo exclusivo y traslado"
sudo stat -c '%n %U:%G %a %s %y' $D/cyberflow $D/cyberflow.anterior $D/suricata $D/suricata.orig-cyberflow > "$L/stat-antes.txt" 2>&1
sudo sha256sum $D/cyberflow $D/cyberflow.anterior $D/suricata $D/suricata.orig-cyberflow > "$L/sha-antes.txt" 2>&1
cat "$L/stat-antes.txt" "$L/sha-antes.txt"
sudo install -d -m 0700 -o root -g root "$K" && ok "creado $K"
sudo cp -p $D/cyberflow "$K/logrotate.d-cyberflow.antes-paso2" && ok "copiada configuracion activa"
sudo mv -n $D/cyberflow.anterior "$K/logrotate.d-cyberflow.anterior" && ok "trasladado cyberflow.anterior"
sudo mv -n $D/suricata.orig-cyberflow "$K/logrotate.d-suricata.orig-cyberflow" && ok "trasladado suricata.orig-cyberflow"
sudo stat -c '%n %U:%G %a %s %y' "$K" "$K"/* > "$L/stat-respaldo.txt" 2>&1
sudo sha256sum "$K"/* > "$L/sha-respaldo.txt" 2>&1
cat "$L/stat-respaldo.txt" "$L/sha-respaldo.txt"
ls -la $D > "$L/ls-logrotate.d-tras-traslado.txt"

echo "-- 3. comprobacion global sin los respaldos"
sudo logrotate -d /etc/logrotate.conf > "$L/global-2-sin-respaldos.txt" 2>&1; echo "rc=$?" > "$L/global-2-sin-respaldos.rc"; ok "sin respaldos $(cat "$L/global-2-sin-respaldos.rc")"
if [ "$(cat "$L/global-2-sin-respaldos.rc")" != "rc=0" ]; then
  echo "PARAR: la configuracion global sigue fallando sin los respaldos; NO se instala la estrofa nueva."
  echo "Revertir el traslado: bash $B/mark/02_logrotate_revertir.sh"; exit 3
fi

echo "-- 4. estrofa nueva con ciclos.jsonl"
sudo install -m 0644 -o root -g root "$N" $D/cyberflow && ok "instalada"
sudo sha256sum $D/cyberflow | tee "$L/sha-cyberflow-nuevo-instalado.txt"
sudo logrotate -d /etc/logrotate.conf > "$L/global-3-despues.txt" 2>&1; echo "rc=$?" > "$L/global-3-despues.rc"; ok "despues $(cat "$L/global-3-despues.rc")"
ls -la $D > "$L/ls-logrotate.d-final.txt"
echo "== resumen: $(cat "$L/global-1-antes.rc") -> $(cat "$L/global-2-sin-respaldos.rc") -> $(cat "$L/global-3-despues.rc")"
echo "== FIN $(date -u +%FT%T.%3NZ). Avisa a Claude: ya puede seguir."
