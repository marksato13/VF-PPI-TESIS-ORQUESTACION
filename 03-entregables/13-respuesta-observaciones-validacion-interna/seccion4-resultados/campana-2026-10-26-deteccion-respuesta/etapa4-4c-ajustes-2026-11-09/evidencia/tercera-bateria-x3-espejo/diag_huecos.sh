echo "## $(date -u +%FT%TZ)"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd /var/lib/ppi-motor-capture && ls | sed -n "s/^live-\(2026[0-9]*\)\.pcap$/\1/p" | python3 -c "
import sys, datetime as dt
t=sorted(dt.datetime.strptime(l.strip(),\"%Y%m%d%H%M%S\") for l in sys.stdin if l.strip())
print(\"ring:\", t[0].strftime(\"%H:%M:%S\"), \"->\", t[-1].strftime(\"%H:%M:%S\"), len(t), \"ficheros\")
g=[(a,b,int((b-a).total_seconds())) for a,b in zip(t,t[1:]) if (b-a).total_seconds()>7]
print(len(g), \"huecos > 7 s; inicios:\")
print(\" \".join(f\"{a.strftime(chr(37)+\"H:\"+chr(37)+\"M:\"+chr(37)+\"S\")}(+{d}s)\" for a,b,d in g))
"; echo "-- huecos en el archivo permanente de hoy (desde 13:54Z):"; ls ~/cf-e4/4c/archivo-pcap 2>/dev/null | head -0'
echo "-- marcas de episodios en la Kali (inicio/fin) de hoy:"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali 'python3 - <<PY
import json
for l in open("/home/adminatacante/cf-e4-4c/corrida/marcas.jsonl"):
    j = json.loads(l)
    if j.get("evento") in ("inicio", "fin"):
        print(j["evento"], j.get("episodio_id"), (j.get("reloj") or {}).get("pared_utc", "")[11:19])
PY' 2>&1 | tail -12
