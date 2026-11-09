VGD=$HOME/cf-e4/vigia-20261106
B=$HOME/cf-e4/4c-cancelada-20261109T1058Z
echo "## paso 6 corregido: intervalo ANTERIOR a la primera muestra de salud $(date -u +%FT%TZ)"
python3 -I - <<PY
import json
m = open("$B/salud/muestras.jsonl").read().splitlines()
import datetime as dt
f = lambda x: dt.datetime.fromtimestamp(json.loads(x)["t"], dt.timezone.utc).strftime("%H:%M:%SZ")
print("   muestras de la corrida cancelada:", f(m[0]), "->", f(m[-1]), f"({len(m)})")
PY
python3 -I $VGD/vigia_4c.py sensor --archivador $B/archivo-pcap --muestras $B/salud/muestras.jsonl --lista-blanca 10.10.10.20,10.10.30.10 --origen 10.10.20.30 --journalctl "sudo -n journalctl --no-pager" --eve-cursor -1 --clasificar sin_muestras-0600:1794204000.000:1794204090.000 | python3 -I -c "
import json,sys
c=json.load(sys.stdin)['clases']
for n,v in c.items(): print('  ',n,v.get('clase'),'motivos=',v.get('motivos') or v.get('motivo'),'suricata=',v.get('suricata'))"
