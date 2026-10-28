#!/usr/bin/env bash
# PREFLIGHT 03 — sensor: fuentes de evidencia (anillo PCAP, EVE, decisiones, caracteristicas) y rotaciones. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
R=/var/lib/ppi-motor-capture; L=/home/m4rk/cyberflow/logs/motor_decision.log
echo "## p03 sensor fuentes  inicio=$(ts)  epoch=$(date +%s.%N)"
echo "## anillo $R"
ls -ld "$R" | sed 's/^/  /'
n=$(ls -1 "$R"/live-*.pcap 2>/dev/null | wc -l); echo "  ficheros=$n  tamano_total=$(du -sh "$R" 2>/dev/null | cut -f1)"
echo "  mas antiguo: $(ls -1tr "$R"/live-*.pcap | head -1 | xargs -I{} stat -c '%n %s B mtime=%y' {})"
echo "  ultimos 4:"; ls -1t "$R"/live-*.pcap | head -4 | xargs -I{} stat -c '    %n %s B mtime=%y owner=%U:%G mode=%a' {}
act=$(ls -1t "$R"/live-*.pcap | head -1); cer=$(ls -1t "$R"/live-*.pcap | sed -n 3p)
echo "  activo (no se toca como cerrado): $(basename "$act")"
echo "## lectura de un PCAP CERRADO: $(basename "$cer") (edad $(( $(date +%s) - $(stat -c%Y "$cer") )) s)"
tcpdump -ttnr "$cer" 2>/tmp/pf_td_err | awk '
 {n++; if(n==1)f=$1; l=$1; for(i=2;i<=NF;i++){ if($i=="IP"||$i=="IP6"){s=$(i+1); d=$(i+3); sub(/\.[0-9]+$/,"",s); sub(/\.[0-9]+:?$/,"",d); sub(/:$/,"",d); src[s]++; break} } }
 END{printf "  paquetes=%d primer=%.6f ultimo=%.6f dur=%.1fs\n",n,f,l,l-f; m=0; for(k in src)m++; printf "  origenes_IP_distintos=%d\n",m;
     for(k in src) if(k ~ /^10\.10\.20\.(2[1-6]|30)$/ || k=="10.10.10.30" || k=="10.10.10.20" || k=="10.10.30.10") printf "    %s: %d pkts\n",k,src[k] }'
echo "  stderr tcpdump: $(cat /tmp/pf_td_err | tr '\n' ' ')"; rm -f /tmp/pf_td_err
echo "  continuidad entre los 6 ultimos cerrados (por marca de paquete):"
for f in $(ls -1t "$R"/live-*.pcap | sed -n '2,7p' | sort); do
  a=$(tcpdump -ttnr "$f" 2>/dev/null | head -1 | awk '{print $1}'); b=$(tcpdump -ttnr "$f" 2>/dev/null | tail -1 | awk '{print $1}')
  echo "    $(basename "$f") primer=$a ultimo=$b"
done
echo "## poda (cyberflow-limpieza)"; systemctl cat cyberflow-limpieza.service 2>/dev/null | grep -E '^ExecStart' | sed 's/^/  /'
echo "## EVE /var/log/suricata/eve.json"
ls -la /var/log/suricata/ 2>&1 | grep -E 'eve|total' | sed 's/^/  /'
if [ -r /var/log/suricata/eve.json ]; then echo "  legible directamente por $(id -un): SI"; else echo "  legible directamente: NO"; fi
echo "  ultimo evento: $(tail -n1 /var/log/suricata/eve.json | cut -c1-60)"
tail -n 20000 /var/log/suricata/eve.json | python3 -c '
import sys,json,collections
c=collections.Counter(); t0=t1=None; bad=0; srcs=collections.Counter()
for l in sys.stdin:
  try: e=json.loads(l)
  except Exception: bad+=1; continue
  c[e.get("event_type")]+=1; ts=e.get("timestamp"); t0=t0 or ts; t1=ts
  s=e.get("src_ip","");
  if s.startswith("10.10.20.") or s in ("10.10.10.30","10.10.30.10","10.10.10.20"): srcs[s]+=1
print("  ultimas 20000 lineas: desde",t0,"hasta",t1,"| no-JSON:",bad)
print("  event_type:",dict(c.most_common(12)))
print("  src_ip de interes:",dict(sorted(srcs.items())))'
echo "  logrotate suricata:"; cat /etc/logrotate.d/suricata 2>/dev/null | grep -vE '^\s*#|^\s*$' | sed 's/^/    /'
echo "## motor_decision.log"
ls -la /home/m4rk/cyberflow/logs/ 2>&1 | grep -E 'motor_decision|total' | sed 's/^/  /'
echo "  lineas=$(wc -l < "$L")"
tail -n 3000 "$L" | python3 -c '
import sys,json,collections,time
req=("logged_at","entity_ip","window_end_utc","decision","packet_count_10s")
ev=collections.Counter(); dec=collections.Counter(); falt=collections.Counter(); thr=collections.Counter(); det=collections.Counter(); heur=collections.Counter()
lag=[]; ult=None; ents=set(); kali=0; n=0
from datetime import datetime
for l in sys.stdin:
  try: r=json.loads(l)
  except Exception: ev["no-JSON"]+=1; continue
  ev[r.get("event")]+=1
  if r.get("event")!="decision": continue
  n+=1
  for k in req:
    if k not in r: falt[k]+=1
  thr["clave_ausente" if "threshold" not in r else repr(r["threshold"])]+=1
  det[r.get("detector_name")]+=1; dec[r.get("decision")]+=1
  h=r.get("heuristico")
  if h: heur[(h.get("heuristico") if isinstance(h,dict) else str(h))]+=1
  ents.add(r.get("entity_ip")); kali+= r.get("entity_ip")=="10.10.20.30"
  try: lag.append(float(r["logged_at"])-datetime.fromisoformat(r["window_end_utc"].replace("Z","+00:00")).timestamp()); ult=r
  except Exception: pass
print("  ultimas 3000 lineas: eventos",dict(ev),"| decisiones",dict(dec))
print("  campos REQ_MOTOR ausentes:",dict(falt) or "ninguno","| threshold:",dict(thr),"| detector_name:",dict(det))
print("  heuristicos registrados:",dict(heur) or "ninguno","| entidades distintas:",len(ents),"| filas de 10.10.20.30:",kali)
if lag:
  lag.sort(); print("  logged_at - window_end (s): min %.2f mediana %.2f max %.2f"%(lag[0],lag[len(lag)//2],lag[-1]))
if ult:
  print("  ultimo registro: logged_at",ult["logged_at"],"(hace %.1f s)"%(time.time()-float(ult["logged_at"])),"window_end",ult["window_end_utc"])
  print("  claves del registro:",sorted(ult.keys()))'
echo "  registros ALERT en todo el log: $(grep -c '"decision": *"ALERT"' "$L")"
echo "  ultima ALERT: $(grep '"decision": *"ALERT"' "$L" | tail -1 | cut -c1-260)"
echo "  ¿rotacion del log del motor?"; ls /etc/logrotate.d/ 2>/dev/null | tr '\n' ' '; echo; grep -l motor_decision /etc/logrotate.d/* 2>/dev/null | sed 's/^/    config: /'
echo "## caracteristicas (acumulador)"
C=/home/m4rk/cyberflow/artifacts/linea-base/multilayer-v3.csv
stat -c '  %n %s B mtime=%y' "$C"
echo "  cabecera (n columnas): $(head -1 "$C" | tr ',' '\n' | wc -l)"
tail -n 2000 "$C" | python3 -c '
import sys,csv
h=open("'"$C"'").readline().strip().split(",")
rows=list(csv.reader(sys.stdin))
i_w=h.index("window_end_utc") if "window_end_utc" in h else None
i_e=h.index("entity_ip") if "entity_ip" in h else None
ws=[r[i_w] for r in rows if i_w is not None and len(r)>i_w]
print("  ultimas 2000 filas: window_end desde",min(ws) if ws else None,"hasta",max(ws) if ws else None)
if i_e is not None: print("  entidades distintas:",len({r[i_e] for r in rows if len(r)>i_e}))
print("  columnas clave presentes:",[c for c in ("campaign_id","entity_ip","window_end_utc","eligible_training","http_request_count_60s","http_auth_failure_ratio_60s","dns_query_count_60s") if c in h])'
systemctl cat cyberflow-acumular.service 2>/dev/null | grep -E '^ExecStart' | sed 's/^/  acumular: /'
echo "## fin=$(ts)"
