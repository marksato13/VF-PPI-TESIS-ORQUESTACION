V=~/cf-e4/4c/vigia/vigia.jsonl
UL=$(tail -1 $V)
P=$(echo "$UL" | python3 -c "import sys,json; r=json.load(sys.stdin); p=r['permiso']; print(p['estado'], '|', ';'.join(p['causas'])[:200])" 2>&1)
N=$(wc -l < $V)
K=$(ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali "grep -c episodio_id /home/adminatacante/cf-e4-4c/corrida/marcas.jsonl; ls /home/adminatacante/cf-e4-4c/generador.rc 2>/dev/null | wc -l; pgrep -fc generar_campana.py" 2>&1 | tr '\n' ' ')
M=$(ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali "tail -n 1 /home/adminatacante/cf-e4-4c/generador.stdout | cut -c1-40" 2>&1)
echo "$(date -u +%T)Z rondas=$N permiso: $P | marcas(inicio+fin)/rc/procs: $K | ultimo: $M"
