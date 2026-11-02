#!/usr/bin/env bash
# Tercera tanda (sin sudo): perfiles del cliente, helper cf-capturar de Sensor1, DC1 por SSH si hay llave.
set +e
echo "== cliente: unidades de perfil y curva horaria"
ssh -o BatchMode=yes admin 'for u in ofimatica navegacion descargas aplicacion ligero erratico; do echo "---- $u"; systemctl cat cyberflow-lab-$u.service | grep -vE "^\s*#"; systemctl show cyberflow-lab-$u.service -p ActiveEnterTimestamp -p NRestarts -p MainPID | cat; done; systemctl cat cyberflow-lab.target | grep -vE "^\s*#"'
echo "== cliente: ficheros de configuracion de perfiles (sin secretos)"
ssh -o BatchMode=yes admin 'for f in $(systemctl cat "cyberflow-lab-*.service" 2>/dev/null | grep -oE "(/[^ ]+\.(py|json|toml|yaml|conf|env))" | sort -u); do echo "# $f $(sha256sum "$f" 2>/dev/null | cut -c1-64)"; done'
echo "== sensor1: cf-capturar"
ssh -o BatchMode=yes sensor1 'ls -la /usr/local/sbin/ | cat; sed -n "1,80p" /usr/local/sbin/cf-capturar 2>&1'
echo "== DC1 (intento de lectura con llaves existentes)"
for d in dcadmin@10.10.10.2 dcadmin@10.10.10.3 dcadmin@10.10.10.10; do
  echo "-- $d"; ssh -o BatchMode=yes -o ConnectTimeout=5 "$d" 'hostname; systemctl list-units --all --no-legend --plain "ppi-*" | cat; ls /etc/cyberflow /opt/cyberflow 2>&1 | head -3' 2>&1 | head -8
done
