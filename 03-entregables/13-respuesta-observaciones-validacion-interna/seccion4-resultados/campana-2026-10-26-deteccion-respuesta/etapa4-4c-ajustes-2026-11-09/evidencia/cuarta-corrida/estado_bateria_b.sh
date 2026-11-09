#!/usr/bin/env bash
# [BASTIÓN gadmin] SOLO LECTURA LOCAL: estado de la batería 4C sin abrir ninguna conexión de red (ni a Kali, ni al sensor, ni a srv-dmz).
# Lee solo ficheros del bastión que ya escribe el vigía: vigia/vigia.jsonl y corrida/marcas.jsonl. Uso: estado_bateria_b.sh [nombre de carpeta dentro de ~/cf-e4]  (por defecto 4c)
D=$HOME/cf-e4/${1:-4c}
python3 - "$D" <<'PY'
import json, os, sys, time, subprocess, datetime as dt
D = sys.argv[1]
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%SZ")
try:
    rs = [json.loads(l) for l in open(f"{D}/vigia/vigia.jsonl")]
except OSError as e:
    print("sin vigia.jsonl:", e); sys.exit(0)
rondas = [r for r in rs if r.get("evento") == "ronda"]
u = rondas[-1] if rondas else {}
p = u.get("permiso") or {}
fin = [r for r in rs if r.get("evento") == "vigia_fin"]
ini = fin_ = 0; ult = ""
try:
    for l in open(f"{D}/corrida/marcas.jsonl"):
        j = json.loads(l); ev = j.get("evento")
        if ev == "inicio": ini += 1; ult = j.get("episodio_id", "")
        elif ev == "fin": fin_ += 1
except OSError:
    # sin corrida/marcas.jsonl en el bastión (solo existe tras b20): marcas recibidas por el vigía = campana_inicio + (inicio+fin) por episodio
    tot = sum(r.get("marcas_nuevas") or 0 for r in rondas if isinstance(r.get("marcas_nuevas"), int))
    ini = max(0, (tot - 1 + 1) // 2); fin_ = max(0, (tot - 1) // 2); ult = f"~{tot} marcas vía vigía"
cl = (fin[-1].get("clases") if fin else u.get("clases")) or {}
malos = sum(1 for v in cl.values() if v in ("C2", "C3"))
vivo = subprocess.run(["pgrep", "-fc", "[v]igia_4c.py bucle"], capture_output=True, text=True).stdout.strip()
edad = time.time() - u.get("epoch", 0) if u else -1
print(f"{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z ronda#{len(rondas)} ({f(u['epoch']) if u else '-'}, hace {edad:.0f}s) permiso: {p.get('estado')} {';'.join(p.get('causas') or [])[:140]} | episodios iniciados {ini}/25, terminados {fin_} (último {ult}) | clasificados {len(cl)} (C2/C3: {malos}) | vigía vivo: {vivo} | sensor_ok={u.get('sensor_ok')} kali_rc={u.get('kali_rc')}")
if fin: print("   vigia_fin:", fin[-1].get("campana_fin"))
PY
