set -u
# [BASTIÓN gadmin] Comprobación previa y EN SECO de E-carga v2. NO arranca generadores, NO abre ninguna ventana de
# observación, no instala ni reinicia nada. La prueba de mecanismo de los muestreadores solo lee y dura < 2 min; su
# carpeta se rotula «seco» y no es evidencia del ensayo.
TS=$(date -u +%Y%m%dT%H%M%SZ)
G=cf-e4/ecarga-v2-guiones-c7f24510; P=cf-e4/paquete-ae2900e
SECO=cf-e4/ecarga-v2-seco-$TS
SO="-o BatchMode=yes -o ConnectTimeout=10"
SEN="ssh -n $SO -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
SRV="ssh -n $SO -i $HOME/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"
CLI="ssh -n $SO -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
echo "######## comprobación en seco $TS (carpeta de prueba $SECO, rotulada seco)"
echo "######## relojes"
echo "bastion $(date -u +%FT%T.%3NZ) $(timedatectl show -p NTPSynchronized --value 2>/dev/null)"
$SEN 'echo "sensor1 $(date -u +%FT%T.%3NZ) ntp=$(timedatectl show -p NTPSynchronized --value) tz=$(timedatectl show -p Timezone --value)"'
$SRV 'echo "srvdmz  $(date -u +%FT%T.%3NZ) ntp=$(timedatectl show -p NTPSynchronized --value)"'
$CLI 'echo "clientes $(date -u +%FT%T.%3NZ) ntp=$(timedatectl show -p NTPSynchronized --value) tz=$(timedatectl show -p Timezone --value)"'
echo "######## guiones versionados"
(cd ~/$G && sha256sum -c --strict --quiet SHA256SUMS && echo "bastion: $G verifica")
echo "######## verificadores (paquete ae2900e, solo lecturas)"
bash ~/$P/deploy/etapa4/bastion/verificar_bastion.sh > /tmp/vb.$$ 2>&1; rc=$?; grep -c '^OK' /tmp/vb.$$ | sed 's/^/bastion OK=/'; grep '^FALLO' /tmp/vb.$$; echo "verificar_bastion rc=$rc"; rm -f /tmp/vb.$$
$SEN "bash ~/$P/deploy/etapa4/sensor1/verificar_sensor1.sh > /tmp/vs.\$\$ 2>&1; rc=\$?; echo sensor1 OK=\$(grep -c '^OK' /tmp/vs.\$\$); grep '^FALLO' /tmp/vs.\$\$; echo verificar_sensor1 rc=\$rc; rm -f /tmp/vs.\$\$"
$SRV "CON_SUDO=1 bash ~/$P/deploy/etapa4/srvdmz/verificar_srvdmz.sh /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z > /tmp/vd.\$\$ 2>&1; rc=\$?; echo srvdmz OK=\$(grep -c '^OK' /tmp/vd.\$\$); grep '^FALLO' /tmp/vd.\$\$; echo verificar_srvdmz rc=\$rc; rm -f /tmp/vd.\$\$"
echo "######## Sensor1: comprobaciones previas + obs_pcap --en-seco (fin propuesto 1794197760 = 2026-11-09T04:16:00Z)"
$SEN "bash ~/$G/sensor1_muestreadores.sh comprobar ~/$SECO/sensor1-comprobar 1794197760 2026-11-09T04:16:00Z; echo rc=\$?"
echo "######## Sensor1: prueba de mecanismo de arranque y parada (solo lectura, fin a +120 s, parada manual a ~25 s)"
$SEN "F=\$((\$(date +%s)+120)); I=\$(date -u -d @\$F +%FT%TZ); D=~/$SECO/sensor1-mecanismo
bash ~/$G/sensor1_muestreadores.sh arrancar \$D \$F \$I; sleep 22; echo '-- antes de parar'; bash ~/$G/sensor1_muestreadores.sh estado \$D
echo '-- parar'; bash ~/$G/sensor1_muestreadores.sh parar \$D; sleep 2; echo '-- después'; bash ~/$G/sensor1_muestreadores.sh estado \$D
pgrep -af 'salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py' | grep -v pgrep || echo 'ningún muestreador vivo'
echo '-- protección: arrancar en el mismo DIR debe abortar'; bash ~/$G/sensor1_muestreadores.sh arrancar \$D \$F \$I; echo rc=\$?"
echo "######## clientes: estado y permisos de los generadores (sin arrancar ni parar)"
$CLI "bash ~/$G/generadores.sh permisos"
echo "######## bastión: muestreo + guardia en modo SECO (fin +75 s, «parada» simulada a +45 s; no para nada)"
F=$(( $(date +%s) + 75 )); PA=$(( $(date +%s) + 45 ))
bash ~/$G/muestreo_bastion.sh ~/$SECO/bastion $F $PA seco > /dev/null 2>&1; echo "muestreo_bastion rc=$?"
echo "muestras: $(grep -c '^### ' ~/$SECO/bastion/muestras.txt)"
grep '^C ' ~/$SECO/bastion/muestras.txt | sort | uniq -c
echo "-- guardia (última evaluación)"; tail -1 ~/$SECO/bastion/guardia.jsonl
echo "-- eventos"; cat ~/$SECO/bastion/eventos.log
echo "-- protección: el mismo DIR debe abortar"; bash ~/$G/muestreo_bastion.sh ~/$SECO/bastion $F $PA seco; echo "rc=$?"
echo "######## generadores después (deben seguir parados)"
$CLI "bash ~/$G/generadores.sh estado"
echo "######## fin $(date -u +%FT%TZ)"
