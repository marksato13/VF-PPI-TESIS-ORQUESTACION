#!/usr/bin/env bash
# PASO3B s20 — sensor (solo lectura): condiciones 1-4 de la seccion 3 bis del protocolo para poder cerrar el archivo.
# Uso: s20_verificar_cierre.sh <fin_ultimo_epoch>. Sale 0 si se cumplen las cuatro; 1 si no.
#  1) PCAP con OK cuyo inicio + 15 >= fin_ultimo + 180     2) archivar.log sin FALLO ni PERDIDO
#  3) EVE con eventos posteriores a fin_ultimo + 180       4) decisiones en vivo con window_end >= fin_ultimo + 60
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; D=$B/archivo-pcap; F=${1:?fin_ultimo epoch}
python3 - "$F" "$D/archivar.log" <<'PY'
import sys, re, json, time, os
from datetime import datetime, timezone
F = float(sys.argv[1]); log = open(sys.argv[2]).read().splitlines()
ok_names = [m.group(1) for l in log for m in [re.search(r" OK (live-(\d{14})\.pcap)", l)] if m]
def t(n): return datetime.strptime(n[5:19], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
ult = max(ok_names, key=t) if ok_names else None
c1 = ult is not None and t(ult) + 15 >= F + 180
fallos = [l for l in log if " FALLO " in l or "PERDIDO" in l]
c2 = not fallos
# EVE: ultimo timestamp en los ultimos 2 MB
with open("/var/log/suricata/eve.json", "rb") as f:
    f.seek(0, 2); f.seek(max(0, f.tell() - 2_000_000)); ls = f.read().splitlines()[1:]
ts = []
for l in ls[-2000:]:
    try:
        ts.append(datetime.strptime(json.loads(l)["timestamp"][:26], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp())
    except Exception:
        pass
eve_max = max(ts) if ts else 0
c3 = eve_max > F + 180
with open(os.path.expanduser("~/cyberflow/logs/motor_decision.log"), "rb") as f:
    f.seek(0, 2); f.seek(max(0, f.tell() - 3_000_000)); ls = f.read().splitlines()[1:]
we = [datetime.fromisoformat(json.loads(l)["window_end_utc"]).timestamp() for l in ls if b'"window_end_utc"' in l]
we_max = max(we) if we else 0
c4 = we_max >= F + 60
iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%FT%T.%fZ")[:-4] + "Z"
print("## s20 %s  fin_ultimo=%s" % (iso(time.time()), iso(F)))
print("  1) ultimo PCAP OK %s -> inicio+15=%s  >= fin+180=%s : %s" % (ult, iso(t(ult) + 15) if ult else None, iso(F + 180), c1))
print("  2) archivar.log FALLO/PERDIDO: %d lineas : %s %s" % (len(fallos), c2, fallos[:3]))
print("  3) EVE ultimo evento %s > fin+180 : %s" % (iso(eve_max), c3))
print("  4) motor: window_end maximo %s >= fin+60=%s : %s" % (iso(we_max), iso(F + 60), c4))
print("  RESULTADO 1-4: %s" % ("CUMPLE" if all((c1, c2, c3, c4)) else "NO CUMPLE (el archivo sigue abierto)"))
sys.exit(0 if all((c1, c2, c3, c4)) else 1)
PY
