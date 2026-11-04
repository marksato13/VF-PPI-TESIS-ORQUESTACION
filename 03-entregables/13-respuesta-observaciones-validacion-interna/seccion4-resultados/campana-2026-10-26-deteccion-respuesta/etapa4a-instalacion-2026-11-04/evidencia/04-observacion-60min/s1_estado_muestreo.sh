D=/home/m4rk/cf-e4/4a
date -u +%FT%TZ; cat $D/inicio-observacion.txt
p=$(cat $D/salud/muestrear.pid); echo "pid $p vivo: $(kill -0 $p 2>/dev/null && echo si || echo NO)"; ps -o pid,ppid,sid,etime,cmd -p $p | cut -c1-150
wc -l < $D/salud/muestras.jsonl; tail -3 $D/salud/muestrear.out
tail -1 $D/salud/muestras.jsonl | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print({k:(v.get("ok") if isinstance(v,dict) else v) for k,v in d.items()})'
