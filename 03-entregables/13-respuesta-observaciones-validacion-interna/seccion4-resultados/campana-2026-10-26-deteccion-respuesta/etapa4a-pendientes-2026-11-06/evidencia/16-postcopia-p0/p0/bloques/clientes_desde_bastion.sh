# Bloque P0 puntos 4, 5 y 10 (solo lectura), ejecutado en el bastión: generadores.sh de paquete-902991e en clientes
# (configuracion, estado, comprobar-parado, permisos: ninguno arranca ni para nada), hash del generador, zona y reloj.
E=~/cf-e4/paquete-902991e/deploy/etapa4/ecarga
O="-o BatchMode=yes -o ConnectTimeout=10"
CLI="ssh $O -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
max=0
sha256sum "$E/generadores.sh"; grep -m1 '^VERSION=' "$E/generadores.sh"
for o in configuracion estado comprobar-parado permisos; do
  echo "######## generadores.sh $o"
  $CLI "bash -s $o" < "$E/generadores.sh"; r=$?
  echo "rc_$o=$r"; [ $r -gt $max ] && max=$r
done
echo "######## clientes: generador, zona, reloj, unidades y procesos"
$CLI 'echo "epoch $(date -u +%s.%N)"; sha256sum ~/laboratorio/clientes_lab.py; echo "timezone=$(cat /etc/timezone 2>&1)"
timedatectl show -p Timezone -p NTP -p NTPSynchronized 2>&1
for p in ofimatica navegacion descargas aplicacion ligero erratico; do systemctl show -p Id -p LoadState -p ActiveState -p UnitFileState -p MainPID -p PartOf -p ExecStart cyberflow-lab-$p.service | tr "\n" " " | cut -c1-400; echo; done
systemctl show -p Id -p ActiveState -p UnitFileState cyberflow-lab.target | tr "\n" " "; echo
pgrep -af clientes_lab.py; r=$?; echo "rc_pgrep=$r (1 = ningún proceso)"; [ $r -le 1 ]' < /dev/null
r=$?; echo "rc_lecturas=$r"; [ $r -gt $max ] && max=$r
exit $max
