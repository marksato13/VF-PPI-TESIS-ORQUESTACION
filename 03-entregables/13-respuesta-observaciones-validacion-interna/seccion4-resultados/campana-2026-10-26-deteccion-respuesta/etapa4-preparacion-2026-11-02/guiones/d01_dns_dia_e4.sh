#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 d01 — uso: d01_dns_dia_e4.sh <YYYY-MM-DD> [dir_suricata]. Observación DNS de 7 días
# (OBSERVACION-DNS-ETAPA4.md). SOLO LECTURA de /var/log/suricata (eve.json*, stats.log*, también .gz) y escritura en
# ~/cf-e4/dns/. Sin sudo, sin reglas, sin procesos persistentes. Para el día LOCAL (Lima, UTC−5) indicado:
#  - eve-dns-<día>.json.gz: los eventos event_type=dns con timestamp en el día (para observacion_dns.py)
#  - continuidad-<día>.json: nº de eventos de CUALQUIER tipo, primer/último, hueco máximo entre eventos consecutivos
#    y huecos > 300 s (P3); kernel_packets/drops de stats.log al principio y al final del día (diferencias, reinicios)
# Se lee eve.json y sus rotaciones porque la rotación es diaria + maxsize 500M (un día puede quedar en 2-3 ficheros).
# Una ausencia de eventos DNS NO prueba continuidad: la continuidad sale de TODOS los eventos y de stats.log.
# Resultado esperado: "dns=<n> eventos=<n> hueco_max_s=<x> drops=<d>/<p>". Parada: ya existe la salida del día.
set -u
DIA=${1:?día YYYY-MM-DD}; S=${2:-/var/log/suricata}; O=$HOME/cf-e4/dns
[[ "$DIA" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || { echo "PARAR: día $DIA"; exit 2; }
[ -e "$O/eve-dns-$DIA.json.gz" ] && { echo "PARAR: ya existe $O/eve-dns-$DIA.json.gz"; exit 2; }
mkdir -p "$O"
python3 -I - "$DIA" "$S" "$O" <<'PY'
import glob, gzip, json, os, re, sys
from datetime import datetime, timedelta, timezone
dia, sdir, out = sys.argv[1:4]
tz = timezone(timedelta(hours=-5))
d0 = datetime.fromisoformat(dia).replace(tzinfo=tz).timestamp(); d1 = d0 + 86400
def abrir(p):
    return gzip.open(p, "rt", errors="replace") if p.endswith(".gz") else open(p, errors="replace")
def ts(s):
    return datetime.strptime(s[:26] + s[26:].replace(":", ""), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
ficheros = sorted(glob.glob(os.path.join(sdir, "eve.json*")))
tiempos, n_dns = [], 0
tmp = os.path.join(out, f".eve-dns-{dia}.json.gz.tmp")
with gzip.open(tmp, "wt") as g:
    for f in ficheros:
        for ln in abrir(f):
            m = re.search(r'"timestamp":\s*"([^"]+)"', ln)
            if not m:
                continue
            try:
                t = ts(m.group(1))
            except ValueError:
                continue
            if not d0 <= t < d1:
                continue
            tiempos.append(t)
            if '"event_type":"dns"' in ln.replace(" ", ""):
                g.write(ln if ln.endswith("\n") else ln + "\n"); n_dns += 1
os.replace(tmp, os.path.join(out, f"eve-dns-{dia}.json.gz"))
tiempos = sorted(set(tiempos))
huecos = [(b - a, a) for a, b in zip(tiempos, tiempos[1:])]
grandes = [{"desde_utc": datetime.fromtimestamp(a, timezone.utc).isoformat(), "s": round(h, 1)} for h, a in huecos if h > 300]
borde = []
if tiempos:
    borde = [round(tiempos[0] - d0, 1), round(d1 - tiempos[-1], 1)]
st, cur = [], None
for f in sorted(glob.glob(os.path.join(sdir, "stats.log*"))):
    for ln in abrir(f):
        m = re.match(r"Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)", ln)
        if m:
            mo, d, y, hh, mi, ss = map(int, m.groups())
            # stats.log escribe la hora LOCAL del sensor; Sensor1 está en Etc/UTC (lectura s1_detalle.txt, 2-nov)
            cur = {"t": datetime(y, mo, d, hh, mi, ss, tzinfo=timezone.utc).timestamp()}; continue
        m = re.match(r"capture\.kernel_(packets|drops)\s*\|\s*Total\s*\|\s*(\d+)", ln)
        if m and cur is not None:
            cur[m.group(1)] = int(m.group(2))
            if "packets" in cur and "drops" in cur:
                if d0 <= cur["t"] < d1:
                    st.append(cur)
                cur = None
st.sort(key=lambda x: x["t"])
paq = drp = 0; reinicios = 0
for a, b in zip(st, st[1:]):
    if b["packets"] < a["packets"] or b["drops"] < a["drops"]:
        reinicios += 1; continue  # contador reiniciado: ese tramo no se suma (y se informa)
    paq += b["packets"] - a["packets"]; drp += b["drops"] - a["drops"]
res = {"dia_local": dia, "zona": "UTC-5", "ficheros_eve": ficheros, "eventos": len(tiempos), "dns": n_dns,
       "hueco_max_s": round(max(huecos)[0], 1) if huecos else None, "huecos_mayores_300s": grandes,
       "sin_eventos_al_inicio_y_al_final_s": borde, "muestras_stats": len(st),
       "kernel_packets": paq if len(st) > 1 else None, "kernel_drops": drp if len(st) > 1 else None,
       "drops_pct": round(100 * drp / paq, 4) if len(st) > 1 and paq else None, "reinicios_contador": reinicios,
       "nota": "sin medida no es cero: kernel_* null si hay menos de dos muestras de stats.log en el día"}
json.dump(res, open(os.path.join(out, f"continuidad-{dia}.json"), "w"), indent=1)
print(f"  dns={n_dns} eventos={len(tiempos)} hueco_max_s={res['hueco_max_s']} huecos>300s={len(grandes)} "
      f"drops={res['kernel_drops']}/{res['kernel_packets']} reinicios={reinicios}")
PY
sha256sum "$O/eve-dns-$DIA.json.gz" "$O/continuidad-$DIA.json"
