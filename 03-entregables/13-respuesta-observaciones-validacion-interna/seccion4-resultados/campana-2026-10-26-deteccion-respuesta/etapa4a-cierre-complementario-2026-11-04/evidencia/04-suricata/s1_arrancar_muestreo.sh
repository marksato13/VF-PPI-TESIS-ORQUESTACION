set -u
# [Sensor1 m4rk] Estado previo + arranque de los muestreadores del cierre 4A. Solo lectura del sistema.
C=/home/m4rk/cf-e4/cierre4a; H=$C/herr; PY=/home/m4rk/cyberflow/.venv/bin/python
[ -e $C/salud ] && { echo "PARADA $C/salud ya existe"; exit 1; }
mkdir -p $C/salud $C/previo
cp $H/CRITERIOS-ENSAYO-ANILLO.md $C/previo/
date -u +%FT%T.%NZ > $C/previo/criterios-declarados-en.txt
sha256sum $C/previo/CRITERIOS-ENSAYO-ANILLO.md >> $C/previo/criterios-declarados-en.txt
cat $C/previo/criterios-declarados-en.txt
# estado previo
L=/home/m4rk/cyberflow/logs/motor_decision.log
tail -n 400 $L | grep '"event": "decision"' | tail -n 1 | $PY -c 'import json,sys; d=json.loads(sys.stdin.read()); print("ultima_decision", d.get("decision_id"), "pcaps_ilegibles", d.get("pcaps_ilegibles"), d.get("pcaps_ilegibles_motivo"))' | tee $C/previo/pcaps-ilegibles-antes.txt
echo "PermissionError en el registro del motor: $(grep -c PermissionError $L)" | tee -a $C/previo/pcaps-ilegibles-antes.txt
ls -la --time-style=full-iso /var/lib/ppi-motor-capture | tail -n 4 | tee $C/previo/pcap-dir.txt
stat -c '%n %y' /home/m4rk/feed/feed.json /home/m4rk/feed/acuses/srv-dmz.json 2>&1 | tee $C/previo/feed-v1-mtime.txt
for u in ppi-publicar-feed.timer ppi-publicar-feed.service ppi-publicar-feed-v2.service ppi-motor.service ppi-motor-capture.service \
         ppi-dashboard.service ppi-via-rapida@ens37.service suricata.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID --value | tr '\n' ' '; echo
done | tee $C/previo/unidades.txt
ps -eo pid,user,lstart,args | grep -E 'publicar_feed|acuse|enforce' | grep -v grep | tee $C/previo/procesos-v1.txt
sudo -n nft list ruleset 2>/dev/null | sha256sum | tee $C/previo/nft.sha256
grep -E '^Date:|capture.kernel_(packets|drops)' /var/log/suricata/stats.log | tail -n 3 | tee $C/previo/suricata-contadores.txt
# muestreador 10 s (mismos argumentos que la 4A)
setsid nohup $PY -I /home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py muestrear \
  --salida $C/salud/muestras.jsonl \
  --suricata-stats /var/log/suricata/stats.log --interfaz ens37 \
  --unidad ppi-motor --unidad ppi-motor-capture --unidad ppi-via-rapida@ens37 \
  --unidad ppi-publicar-feed-v2 --unidad suricata \
  --anillo /var/lib/ppi-motor-capture \
  --resumen-rapida /home/m4rk/feed-v2/via-rapida-resumen.jsonl \
  --ciclos /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl \
  --hijos-de-unidad ppi-via-rapida@ens37 --intervalo 10 \
  > $C/salud/muestrear.out 2>&1 < /dev/null &
echo $! > $C/salud/muestrear.pid
# muestreador fino 1 s
setsid nohup $PY -I $H/muestreo_fino.py --salida $C/salud/fino.jsonl --intervalo 1 > $C/salud/fino.out 2>&1 < /dev/null &
echo $! > $C/salud/fino.pid
date -u +%FT%TZ > $C/salud/inicio-muestreo.txt
sleep 25
for n in muestrear fino; do echo "$n pid $(cat $C/salud/$n.pid) vivo: $(kill -0 $(cat $C/salud/$n.pid) 2>/dev/null && echo si || echo NO)"; done
wc -l $C/salud/muestras.jsonl $C/salud/fino.jsonl; tail -n 3 $C/salud/muestrear.out $C/salud/fino.out
tail -n 1 $C/salud/fino.jsonl | $PY -c 'import json,sys; d=json.loads(sys.stdin.read()); print("fino: nic", d["nic"], "hilos", len((d["suricata"] or {}).get("hilos", {})), "rss", (d["suricata"] or {}).get("rss_kb"), "mem", d["mem_disponible_kb"], "errores", d.get("errores"))'
