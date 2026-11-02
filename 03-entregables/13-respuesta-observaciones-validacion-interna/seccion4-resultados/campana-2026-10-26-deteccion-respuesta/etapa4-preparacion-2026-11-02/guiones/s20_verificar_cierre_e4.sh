#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s20 — solo lectura. Uso: s20_verificar_cierre_e4.sh <4b|4c> <fin_ultimo_epoch>
# Condiciones 1-4 del cierre del archivo (PROTOCOLO-4C §6; la 5 es el replay, s30). Cambios frente al 3B:
# ficheros de 5 s (inicio + 5) y margen de 300 s (fin_ultimo + 300) en lugar de 180.
#  1) PCAP con OK cuyo inicio + 5 >= fin_ultimo + 300     2) archivar.log sin FALLO ni PERDIDO
#  3) EVE con eventos posteriores a fin_ultimo + 300       4) decisiones en vivo con window_end >= fin_ultimo + 60
# En la 4B, fin_ultimo es el HASTA del control. Sale 0 si se cumplen las cuatro; 1 si no (el archivo sigue abierto).
set -u
FASE=${1:?fase}; F=${2:?fin_ultimo epoch}
B=$HOME/cf-e4/$FASE; D=$B/archivo-pcap
python3 - "$F" "$D/archivar.log" <<'PY'
import sys, re, json, time, os
from datetime import datetime, timezone
ROT, MARGEN = 5, 300
F = float(sys.argv[1]); log = open(sys.argv[2]).read().splitlines()
ok_names = [m.group(1) for l in log for m in [re.search(r" OK (live-(\d{14})\.pcap)", l)] if m]
def t(n): return datetime.strptime(n[5:19], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
ult = max(ok_names, key=t) if ok_names else None
c1 = ult is not None and t(ult) + ROT >= F + MARGEN
fallos = [l for l in log if " FALLO " in l or "PERDIDO" in l]
c2 = not fallos
with open("/var/log/suricata/eve.json", "rb") as f:
    f.seek(0, 2); f.seek(max(0, f.tell() - 2_000_000)); ls = f.read().splitlines()[1:]
ts = []
for l in ls[-2000:]:
    try:
        ts.append(datetime.strptime(json.loads(l)["timestamp"][:26], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp())
    except Exception:
        pass
eve_max = max(ts) if ts else 0
c3 = eve_max > F + MARGEN
with open(os.path.expanduser("~/cyberflow/logs/motor_decision.log"), "rb") as f:
    f.seek(0, 2); f.seek(max(0, f.tell() - 3_000_000)); ls = f.read().splitlines()[1:]
we = []
for l in ls:
    if b'"window_end_utc"' in l:
        try:
            we.append(datetime.fromisoformat(json.loads(l)["window_end_utc"].replace("Z", "+00:00")).timestamp())
        except Exception:
            pass
we_max = max(we) if we else 0
c4 = we_max >= F + 60
iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%FT%T.%fZ")[:-4] + "Z"
print("## s20-e4 %s  fin_ultimo=%s" % (iso(time.time()), iso(F)))
print("  1) ultimo PCAP OK %s -> inicio+%d=%s  >= fin+%d=%s : %s" % (ult, ROT, iso(t(ult) + ROT) if ult else None, MARGEN, iso(F + MARGEN), c1))
print("  2) archivar.log FALLO/PERDIDO: %d lineas : %s %s" % (len(fallos), c2, fallos[:3]))
print("  3) EVE ultimo evento %s > fin+%d : %s" % (iso(eve_max), MARGEN, c3))
print("  4) motor: window_end maximo %s >= fin+60=%s : %s" % (iso(we_max), iso(F + 60), c4))
print("  RESULTADO 1-4: %s" % ("CUMPLE" if all((c1, c2, c3, c4)) else "NO CUMPLE (el archivo sigue abierto)"))
sys.exit(0 if all((c1, c2, c3, c4)) else 1)
PY
