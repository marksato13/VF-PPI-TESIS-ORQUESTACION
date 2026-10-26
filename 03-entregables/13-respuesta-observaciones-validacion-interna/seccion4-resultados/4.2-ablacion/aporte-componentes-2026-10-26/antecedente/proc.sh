#!/usr/bin/env bash
# Proceso de UN episodio en el sensor: selecciona PCAP del anillo en [LO,HI],
# recorta el eve a la ventana, extrae features, dedup del PCAP y puntua
# (modelo + heuristico). Imprime una linea RESULT. Deja dedup.pcap en el dir.
set -uo pipefail
ID=$1; LO=$2; HI=$3; CS=$4; T0=$5; HIISO=$6
W=/home/m4rk/piloto/$ID
mkdir -p "$W"
V=/home/m4rk/cyberflow/.venv/bin/python
CF=/home/m4rk/cyberflow
for f in /var/lib/ppi-motor-capture/live-*.pcap; do
  ts=$(basename "$f" | sed 's@live-@@; s@\.pcap@@')
  if [ "$ts" -ge "$LO" ] && [ "$ts" -le "$HI" ]; then cp "$f" "$W"/ 2>/dev/null; fi
done
CS="$CS" HIISO="$HIISO" W="$W" "$V" - <<'PY'
import os
cs=os.environ['CS'][:19]; hi=os.environ['HIISO'][:19]; W=os.environ['W']
o=open(W+'/eve.json','w')
try:
    lines=open('/var/log/suricata/eve.json').readlines()[-80000:]
except Exception:
    lines=[]
k='"timestamp":"'
for l in lines:
    i=l.find(k)
    if i<0: continue
    ts=l[i+len(k):i+len(k)+19]
    if cs<=ts<=hi: o.write(l)
o.close()
PY
"$V" "$CF"/scripts/features/extract_multilayer_v2.py --pcap "$W"/live-*.pcap --eve "$W"/eve.json --campaign-id "$ID" --output "$W"/features.csv --schema "$CF"/configs/features/multilayer-v2.json --entity-network 10.10.0.0/16 --capture-start "$CS" 2>"$W"/ext.log || { echo "RESULT $ID EXTRACT_FAIL"; exit 0; }
"$V" /home/m4rk/piloto/dedup_merge.py "$W"/dedup.pcap "$W"/live-*.pcap >/dev/null 2>&1
W="$W" T0="$T0" ID="$ID" "$V" /home/m4rk/piloto/score.py
