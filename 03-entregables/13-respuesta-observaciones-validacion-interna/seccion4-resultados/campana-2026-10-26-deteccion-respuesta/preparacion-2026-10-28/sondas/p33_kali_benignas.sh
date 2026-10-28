#!/usr/bin/env bash
# PREP 33 — Kali: pruebas benignas minimas en modo sombra (1 resolucion lab-ppi, SOA, 1 GET :80, 3 GET /auth :18081
# sin credencial / ficticia / control). Agente de usuario identificable: cf-preparacion-2026-10-28. No es un escenario.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
UA="cf-preparacion-2026-10-28"
echo "## p33 kali  inicio=$(ts)  host=$(hostname)"
N="preparacion-$(date +%s).lab-ppi"
t=$(ts); echo "  [$t] dig @10.10.10.20 $N A:"; dig +time=3 +tries=1 @10.10.10.20 "$N" A 2>&1 | grep -E 'status:|^[^;].*IN\s+A' | sed 's/^/    /'
t=$(ts); echo "  [$t] dig @10.10.10.20 lab-ppi SOA: $(dig +time=3 +tries=1 @10.10.10.20 lab-ppi SOA +short 2>&1 | head -1)"
t=$(ts); echo "  [$t] GET http://10.10.30.10/ -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}s' http://10.10.30.10/)"
t=$(ts); echo "  [$t] GET :18081/auth sin credencial -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth fake:incorrecta -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u fake:preparacion-incorrecta -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth control:*** -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u control:control123 -w '%{http_code}' http://10.10.30.10:18081/auth)"
echo "## fin=$(ts)"
