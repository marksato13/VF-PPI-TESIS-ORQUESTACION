set -u
# [Sensor1 m4rk] Para los dos muestreadores de este cierre (procesos propios) y empaqueta su salida. No borra nada.
C=/home/m4rk/cf-e4/cierre4a
for n in muestrear fino; do P=$(cat $C/salud/$n.pid); ps -o pid,args -p $P | tail -n 1; kill $P && echo "$n ($P) parado"; done
sleep 2; date -u +%FT%TZ > $C/salud/fin-muestreo.txt
wc -l $C/salud/muestras.jsonl $C/salud/fino.jsonl
cd $C && tar -czf /tmp/cierre4a-salud-ensayo.tgz salud ensayo && sha256sum /tmp/cierre4a-salud-ensayo.tgz && ls -la /tmp/cierre4a-salud-ensayo.tgz
