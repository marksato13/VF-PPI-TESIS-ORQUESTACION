#!/usr/bin/env bash
# PREP 41 — sensor: despliega el motor corregido (producto 7b275b8, sha256 e2b2eb53…) EN SOMBRA y fuera de campana.
# Respaldo del motor anterior (4c41ec44…), comprobacion de sudo, reinicio registrado y verificacion del arranque.
# Reversion: cp -p $R/motor_decision.py.4c41ec44 ~/cyberflow/scripts/engine/motor_decision.py && sudo -n systemctl restart ppi-motor
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
E=$HOME/cyberflow/scripts/engine; H=$HOME/cf-prep-20261028/herramientas; R=$HOME/cf-prep-20261028/respaldo-motor
NUEVO=e2b2eb535091ea0fb7aa08054aa8cc4eff295a4e678269cba5d4a5ee5d95bc73; VIEJO=4c41ec44
echo "## p41  inicio=$(ts)"
sudo -n -l 2>/dev/null | grep -E 'ppi-motor|ALL' | sed 's/^/  sudo: /'
[ "$(sha256sum $H/motor_decision.7b275b8.py | cut -c1-64)" = "$NUEVO" ] || { echo "ABORTO: copia subida no coincide"; exit 2; }
[ "$(sha256sum $E/motor_decision.py | cut -c1-8)" = "$VIEJO" ] || { echo "ABORTO: el motor instalado no es $VIEJO"; exit 2; }
P0=$(systemctl show -p MainPID --value ppi-motor); echo "  antes: PID=$P0 NRestarts=$(systemctl show -p NRestarts --value ppi-motor) desde=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)"
echo "  lineas del log antes: $(wc -l < $HOME/cyberflow/logs/motor_decision.log)"
mkdir -p $R && cp -p $E/motor_decision.py $R/motor_decision.py.4c41ec44 && sha256sum $R/motor_decision.py.4c41ec44 | sed 's/^/  respaldo: /'
cp $H/motor_decision.7b275b8.py $E/motor_decision.py.nuevo && mv $E/motor_decision.py.nuevo $E/motor_decision.py
echo "  instalado: $(sha256sum $E/motor_decision.py)"
[ "$(sha256sum $E/motor_decision.py | cut -c1-64)" = "$NUEVO" ] || { echo "ERROR: sha instalado distinto; revierto"; cp -p $R/motor_decision.py.4c41ec44 $E/motor_decision.py; exit 3; }
T=$(ts); echo "  [$T] REINICIO sudo -n systemctl restart ppi-motor"
if ! sudo -n systemctl restart ppi-motor; then echo "  ERROR: reinicio rechazado; revierto el fichero"; cp -p $R/motor_decision.py.4c41ec44 $E/motor_decision.py; exit 4; fi
sleep 45
P1=$(systemctl show -p MainPID --value ppi-motor)
echo "  [$(ts)] despues: $(systemctl is-active ppi-motor) PID=$P1 NRestarts=$(systemctl show -p NRestarts --value ppi-motor) desde=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)"
echo "  argv: $(tr '\0' ' ' < /proc/$P1/cmdline | cut -c1-400)"
grep '"motor_startup"' $HOME/cyberflow/logs/motor_decision.log | tail -1 | cut -c1-700 | sed 's/^/  arranque: /'
echo "  journal desde el reinicio (errores): $(journalctl -u ppi-motor --since "$(date -u -d "$T" '+%F %T')" --no-pager -q | grep -ciE 'error|traceback')"
tail -1 $HOME/cyberflow/logs/motor_decision.log | cut -c1-500 | sed 's/^/  ultima: /'
echo "## fin=$(ts)"
