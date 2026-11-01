#!/usr/bin/env bash
# Vigilancia durante una inundacion: una linea cada ~15 s durante N segundos (solo lectura). Uso: v_durante.sh N
N=${1:-300}; fin=$(( $(date +%s) + N ))
while [ $(date +%s) -lt $fin ]; do
  ssh -o BatchMode=yes -o ConnectTimeout=8 gadmin@10.10.10.30 "ssh sensor1 'bash -s'" <<'EOS' 2>&1 | tr '\n' ' '; echo
python3 - <<'PY'
import json, time
c = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/_state/ciclos.jsonl").readlines()[-3:]]
m = json.loads(open("/home/m4rk/cf-paso2-20261101T0254Z/recursos/muestras.jsonl").readlines()[-1])
print(time.strftime("%H:%M:%S", time.gmtime()), "dur", [round(x["duracion_s"], 1) for x in c], "pend", [x["ventanas_pendientes"] for x in c],
      "edad_ult_ciclo %.0f" % (time.time() - c[-1]["fin_ciclo"]), "memavail %.0fMB" % (m["memavail_kb"] / 1024), "rss %.0fMB" % (m["rss_kb"] / 1024), "pswpout", m["pswpout"])
PY
systemctl is-active ppi-motor
EOS
  sleep 12
done
