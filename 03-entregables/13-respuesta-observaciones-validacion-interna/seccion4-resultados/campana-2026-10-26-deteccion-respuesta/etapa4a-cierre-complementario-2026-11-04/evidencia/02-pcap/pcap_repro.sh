set -u
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null && apt-get install -y -qq tcpdump iputils-ping strace util-linux >/dev/null 2>&1
tcpdump --version 2>&1 | head -2
id tcpdump || useradd -r tcpdump
userdel -r ubuntu 2>/dev/null; useradd -m -u 1000 m4rk; id m4rk
D=/var/lib/ppi-motor-capture
lanzar() {  # $1 = etiqueta
  rm -rf $D; install -d -o tcpdump -g m4rk -m 2750 $D
  ( ping -i 0.2 -c 40 127.0.0.1 >/dev/null & )
  ( umask 0027; exec strace -f -qq -e trace=openat,chown,fchown,setgid,setuid,setgroups,capset -o /tmp/strace-$1.txt \
      tcpdump -i lo -n -s 0 -U -B 65536 -Z tcpdump -w $D/live-%Y%m%d%H%M%S.pcap -G 1 2>/tmp/tcpdump-$1.err ) &
  sleep 4.5; pkill -INT -x tcpdump; sleep 0.5
}
echo "===== 1) unidad actual (root + -Z tcpdump)"
lanzar actual
ls -l --time-style=+%T $D
echo "--- llamadas relevantes del arranque (en orden):"
grep -nE 'live-|chown|setgid|setuid|setgroups' /tmp/strace-actual.txt | head -12
echo "--- ¿m4rk puede leer cada fichero?"
for f in $D/*.pcap; do su -s /bin/sh m4rk -c "head -c 24 $f > /dev/null" 2>/dev/null && echo "legible   $(basename $f)" || echo "ILEGIBLE  $(basename $f)"; done

echo "===== 2) corrección propuesta: ExecStartPost (root) que devuelve el grupo del directorio al primer fichero"
rm -rf $D; install -d -o tcpdump -g m4rk -m 2750 $D
( ping -i 0.2 -c 40 127.0.0.1 >/dev/null & )
( umask 0027; exec tcpdump -i lo -n -s 0 -U -B 65536 -Z tcpdump -w $D/live-%Y%m%d%H%M%S.pcap -G 1 2>/dev/null ) &
# --- mismo cuerpo que el ExecStartPost del drop-in ---
sh /s/primer_pcap.sh $D m4rk; echo "ExecStartPost rc=$?"
sleep 4; pkill -INT -x tcpdump; sleep 0.5
ls -l --time-style=+%T $D
for f in $D/*.pcap; do su -s /bin/sh m4rk -c "head -c 24 $f > /dev/null" 2>/dev/null && echo "legible   $(basename $f)" || echo "ILEGIBLE  $(basename $f)"; done
echo "--- PCAP válidos (tcpdump -r como m4rk):"
for f in $D/*.pcap; do n=$(su -s /bin/sh m4rk -c "tcpdump -nr $f 2>/dev/null | wc -l"); echo "$(basename $f): $n paquetes"; done
echo "--- permisos y propietarios finales:"; stat -c '%U:%G %a %n' $D $D/* | sed "s#$D/##"
echo "===== 3) caso límite: sin tráfico el primer fichero se crea igual (lo crea tcpdump al arrancar)"
rm -rf $D; install -d -o tcpdump -g m4rk -m 2750 $D
( umask 0027; exec tcpdump -i lo -n -s 0 -U -Z tcpdump -w $D/live-%Y%m%d%H%M%S.pcap -G 1 'port 9' 2>/dev/null ) &
sh /s/primer_pcap.sh $D m4rk; echo "ExecStartPost rc=$?"
sleep 1.5; pkill -INT -x tcpdump; sleep 0.3; stat -c '%U:%G %a %n' $D/* | sed "s#$D/##"
