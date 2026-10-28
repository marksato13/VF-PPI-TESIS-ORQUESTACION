#!/usr/bin/env bash
# PREFLIGHT 16 — sensor: cuantifica, en las ultimas 2 h, la relacion entre el retraso de evaluacion del motor
# (logged_at - window_end) y las ventanas sin paquetes vivos, cruzando con las features por lotes (acumular).
# Solo lectura.
set -u
L=$HOME/cyberflow/logs/motor_decision.log; C=$HOME/cyberflow/artifacts/linea-base/multilayer-v3.csv
echo "## p16  $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
python3 - "$L" "$C" <<'PY'
import sys,json,csv,datetime,collections
desde="2026-10-28T05:10"; hasta="2026-10-28T07:00"   # rango ya cubierto por acumular
feat={}
for r in csv.DictReader(open(sys.argv[2])):
    if desde<=r["window_end_utc"]<hasta: feat[(r["window_end_utc"],r["entity_ip"])]=int(float(r["packet_count_10s"] or 0))
b=collections.Counter(); perd=collections.Counter(); tot=collections.Counter()
for l in open(sys.argv[1]):
    try: r=json.loads(l)
    except Exception: continue
    w=r.get("window_end_utc","")
    if not (desde<=w<hasta): continue
    lag=float(r["logged_at"])-datetime.datetime.fromisoformat(w).timestamp()
    k="<5s" if lag<5 else ("5-15s" if lag<15 else ">=15s")
    tot[k]+=1
    fp=feat.get((w,r["entity_ip"]))
    if fp and fp>0:
        b[k]+=1
        if int(r.get("packet_count_10s") or 0)==0: perd[k]+=1
print("  rango de ventanas: [%s, %s)"%(desde,hasta))
for k in ("<5s","5-15s",">=15s"):
    print("  retraso %-6s decisiones=%5d | con trafico segun features=%4d | de ellas el motor vio 0 paquetes=%4d (%.0f%%)"%(
        k,tot[k],b[k],perd[k],100*perd[k]/b[k] if b[k] else 0))
print("  total ventanas-entidad con trafico (features) evaluadas con 0 paquetes vivos: %d de %d"%(sum(perd.values()),sum(b.values())))
PY
echo "## publicador del feed 07:03:30-07:08 (10.10.20.30 / LIMIT / BLOCK)"
sudo -n journalctl -u ppi-publicar-feed.service --since '2026-10-28 07:03:30' --until '2026-10-28 07:08:00' --no-pager 2>&1 | grep -E '10\.10\.20\.30|LIMIT|BLOCK|entrad' | head -n 10 | sed 's/^/    /'
echo "  lineas totales del journal en ese intervalo: $(sudo -n journalctl -u ppi-publicar-feed.service --since '2026-10-28 07:03:30' --until '2026-10-28 07:08:00' --no-pager 2>&1 | wc -l)"
