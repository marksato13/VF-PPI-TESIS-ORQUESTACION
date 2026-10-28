#!/usr/bin/env bash
# PREFLIGHT 13b — sensor: (1) por que el filtro BPF 'host X' dio 0 en el PCAP archivado (tipo de enlace / VLAN);
# (2) detalle de las 2 ALERT del IF para 10.10.20.30 tras las transacciones benignas del preflight; (3) estado del feed
# para 10.10.20.30; (4) filas de features. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
DST=$(cat "$HOME/cf-preflight-20261028/ULTIMA_PRUEBA"); L=$HOME/cyberflow/logs/motor_decision.log
echo "## p13b  inicio=$(ts)"
F=$(ls -1 "$DST"/live-*.pcap | sort)
f1=$(ls -1 "$DST"/live-*.pcap | sort | head -1)
echo "## (1) tipo de enlace y encapsulado"
tcpdump -nr "$f1" -c 3 -e 2>&1 | sed 's/^/    /' | cut -c1-200
echo "  tramas con 802.1Q en el primer fichero: $(tcpdump -nr "$f1" vlan 2>/dev/null | wc -l) de $(tcpdump -nr "$f1" 2>/dev/null | wc -l)"
cnt(){ local flt="$1"; local s=0 c; for f in $F; do c=$(tcpdump -nr "$f" "$flt" 2>/dev/null | wc -l); s=$((s+c)); done; echo $s; }
v(){ echo "($1) or (vlan and ($1))"; }
echo "  con filtro consciente de VLAN:"
echo "    Kali->DC udp/53:      $(cnt "$(v 'src host 10.10.20.30 and dst host 10.10.10.20 and udp port 53')")"
echo "    Kali<->srv tcp/80:    $(cnt "$(v 'host 10.10.20.30 and host 10.10.30.10 and tcp port 80')")"
echo "    Kali<->srv tcp/18081: $(cnt "$(v 'host 10.10.20.30 and host 10.10.30.10 and tcp port 18081')")"
echo "    respuestas HTTP :18081:"; for f in $F; do tcpdump -nAr "$f" "$(v 'src host 10.10.30.10 and tcp src port 18081')" 2>/dev/null | grep -oE 'HTTP/1\.[01] [0-9]{3}'; done | sort | uniq -c | sed 's/^/      /'
echo "    nombres DNS del preflight:"; for f in $F; do tcpdump -nr "$f" "$(v 'udp port 53 and host 10.10.20.30')" 2>/dev/null | grep -oE '(pfmarca[0-9]|preflight)-[0-9]+\.lab-ppi'; done | sort -u | sed 's/^/      /'
echo "    User-Agent cf-preflight en el PCAP: $(for f in $F; do tcpdump -nAr "$f" "$(v 'host 10.10.20.30 and tcp')" 2>/dev/null | grep -c 'cf-preflight-2026-10-28'; done | paste -sd+ | bc)"
for i in 21 22 23 24 25 26; do echo "    10.10.20.$i origen: $(cnt "$(v "src host 10.10.20.$i")") paquetes"; done
echo "## (2) decisiones del motor para 10.10.20.30 desde 06:58"
python3 - "$L" <<'PY'
import sys,json
for l in open(sys.argv[1]):
    try: r=json.loads(l)
    except Exception: continue
    if r.get("entity_ip")=="10.10.20.30" and r.get("window_end_utc","")>="2026-10-28T06:58":
        print("   ",r.get("window_end_utc"),"logged",r.get("logged_at"),r.get("decision"),r.get("detector_name"),
              "score",r.get("score",r.get("anomaly_score")),"thr",r.get("threshold"),"pk10",r.get("packet_count_10s"))
PY
echo "## (3) feed / estado para 10.10.20.30 ahora"
python3 - <<'PY'
import json,os
h=os.path.expanduser("~/feed")
f=json.load(open(h+"/feed.json")); e=json.load(open(h+"/estado.json"))
ent=f.get("entries", f.get("entradas", f if isinstance(f,list) else []))
print("    feed.json entradas:",len(ent), [x for x in ent if "10.10.20.30" in json.dumps(x)])
print("    feed generado:", f.get("generated_at", f.get("generado", "?")) if isinstance(f,dict) else "?")
est=e.get("ips",e) if isinstance(e,dict) else e
print("    estado 10.10.20.30:", json.dumps(est.get("10.10.20.30")) if isinstance(est,dict) else "?")
PY
echo "## (4) features (multilayer-v3.csv) 10.10.20.30 y .21-.26 desde 06:58"
C=$(ls -1t $HOME/cyberflow/data/*multilayer-v3*.csv 2>/dev/null | head -1); [ -z "$C" ] && C=$(find $HOME/cyberflow -name 'multilayer-v3.csv' 2>/dev/null | head -1)
echo "    csv=$C"
python3 - "$C" <<'PY'
import sys,csv
rd=csv.DictReader(open(sys.argv[1])); cols=rd.fieldnames
k=[c for c in cols if "window" in c.lower() or "time" in c.lower()][:2]; ipc=[c for c in cols if "ip" in c.lower()][:1]
print("    columnas de tiempo/ip:",k,ipc)
sel=[c for c in cols if any(s in c for s in ("http_request","auth_fail","dns_q","packet_count"))][:5]
for r in rd:
    ip=r.get(ipc[0],"") if ipc else ""
    if (ip=="10.10.20.30" or ip in ["10.10.20.%d"%i for i in range(21,27)]) and r.get(k[0],"")>="2026-10-28T06:58" or (ip and r.get(k[0],"").startswith("2026-10-28 06:5")):
        print("   ",r.get(k[0]),ip,{c:r[c] for c in sel})
PY
echo "## fin=$(ts)"
