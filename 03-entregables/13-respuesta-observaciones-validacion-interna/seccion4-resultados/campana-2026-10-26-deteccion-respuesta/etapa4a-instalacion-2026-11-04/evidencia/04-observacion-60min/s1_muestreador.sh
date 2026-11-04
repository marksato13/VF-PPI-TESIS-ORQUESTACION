set -u
D=/home/m4rk/cf-e4/4a
[ ! -e $D ] && mkdir -p $D/salud || { echo "PARADA $D ya existe"; exit 1; }
date -u +%FT%TZ > $D/inicio-observacion.txt
setsid nohup /home/m4rk/cyberflow/.venv/bin/python -I \
  /home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py muestrear \
  --salida $D/salud/muestras.jsonl \
  --suricata-stats /var/log/suricata/stats.log --interfaz ens37 \
  --unidad ppi-motor --unidad ppi-motor-capture --unidad ppi-via-rapida@ens37 \
  --unidad ppi-publicar-feed-v2 --unidad suricata \
  --anillo /var/lib/ppi-motor-capture \
  --resumen-rapida /home/m4rk/feed-v2/via-rapida-resumen.jsonl \
  --ciclos /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl \
  --hijos-de-unidad ppi-via-rapida@ens37 --intervalo 10 \
  > $D/salud/muestrear.out 2>&1 < /dev/null &
echo $! > $D/salud/muestrear.pid
sleep 65
echo "pid $(cat $D/salud/muestrear.pid) vivo: $(kill -0 $(cat $D/salud/muestrear.pid) && echo si)"
wc -l < $D/salud/muestras.jsonl; cat $D/salud/muestrear.out | tail -3
tail -1 $D/salud/muestras.jsonl | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print({k:(v.get("ok") if isinstance(v,dict) else v) for k,v in d.items()})'
