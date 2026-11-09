echo "## $(date -u +%FT%TZ)"
V=~/cf-e4/4c/vigia/vigia.jsonl
python3 - <<'PY'
import json, os, datetime as dt
V = os.path.expanduser("~/cf-e4/4c/vigia/vigia.jsonl")
rs = [json.loads(l) for l in open(V)]
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%SZ")
for r in rs[-4:]:
    print(f(r["epoch"]), r["permiso"]["estado"], r["permiso"]["causas"], "marcas_nuevas", r.get("marcas_nuevas"))
c = [r for r in rs if r["permiso"]["estado"] == "cancelar"]
print("primera cancelación:", f(c[0]["epoch"]) if c else None)
print(json.dumps(c[0].get("sensor") or {}, ensure_ascii=False)[:900] if c else "")
PY
echo "== Kali: marcas recientes y estado del generador"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali 'K=/home/adminatacante/cf-e4-4c; echo "generador.rc: $(cat $K/generador.rc 2>/dev/null)"; echo "vivo: $(pgrep -fc "[g]enerar_campana.py --config")"; echo "permiso: $(head -c 300 $K/permiso.json)"; tail -n 6 $K/corrida/marcas.jsonl | cut -c1-230; echo "-- stdout"; tail -n 4 $K/generador.stdout | cut -c1-200; echo "-- resolv"; cat /etc/resolv.conf | grep -v "^#"' 2>&1
