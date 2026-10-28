#!/usr/bin/env bash
# PREFLIGHT 06 — Kali: identidad, reloj, herramientas, copias de campana, validacion de los 5 escenarios con sus
# herramientas reales (sin ejecutar ningun escenario) y pruebas benignas minimas: 1 resolucion lab-ppi, 1 GET :80,
# 3 GET /auth :18081 (sin credencial, ficticia, control). Agente de usuario identificable: cf-preflight-2026-10-28.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
UA="cf-preflight-2026-10-28"
echo "## p06 kali  inicio=$(ts)  host=$(hostname)  user=$(id -un)  uptime=$(uptime -p)"
echo "## direcciones"; ip -br addr | sed 's/^/  /'
echo "## reloj"; timedatectl 2>&1 | grep -E 'Universal|synchronized|NTP service' | sed 's/^/  /'
timedatectl show-timesync 2>/dev/null | grep -E 'ServerName|ServerAddress' | sed 's/^/  /'; command -v chronyc >/dev/null && chronyc tracking 2>/dev/null | grep -E 'Reference|System time' | sed 's/^/  /'
echo "## herramientas"
for t in python3 dig curl nmap timeout setsid; do printf '  %-8s %s\n' "$t" "$(command -v $t || echo NO)"; done
echo "  $(python3 -V 2>&1) | $(dig -v 2>&1 | head -1) | $(curl --version | head -1 | cut -c1-40) | $(nmap --version | head -1)"
echo "## copias de campana presentes en la Kali (busqueda en ~ y /opt, profundidad 4)"
find ~ /opt -maxdepth 4 \( -name 'generar_campana.py' -o -name 'esquema_campana.py' -o -name 'escenarios.json' -o -name 'marcas.jsonl' -o -name 'corrida*' -o -name 'campana-A*' \) 2>/dev/null | while read -r f; do echo "  $(sha256sum "$f" 2>/dev/null | cut -c1-64)  $f"; done
echo "  (fin de busqueda)"
echo "## procesos de campana en curso"; ps -eo pid,args --no-headers | grep -E 'generar_campana|nmap|dig |curl ' | grep -v grep | sed 's/^/  /' || true
echo "  (procesos: $(ps -eo args --no-headers | grep -E 'generar_campana|nmap ' | grep -vc grep))"
echo "## validacion de escenarios con herramientas reales (copia TEMPORAL de HEAD, se borra al terminar)"
T=$(mktemp -d /tmp/cf-preflight-XXXXXX)
echo '@@ESQ@@' | base64 -d > "$T/esquema_campana.py"; echo '@@ESC@@' | base64 -d > "$T/escenarios.json"
echo "  esquema sha256=$(sha256sum "$T/esquema_campana.py" | cut -c1-64) (esperado @@H_ESQ@@)"
echo "  escenarios sha256=$(sha256sum "$T/escenarios.json" | cut -c1-64) (esperado @@H_ESC@@)"
( cd "$T" && python3 - <<'PY'
import json, esquema_campana as e
cfg = json.load(open("escenarios.json"))
p = e.validar(cfg, exigir_herramientas=True)
print("  validar(exigir_herramientas=True):", "SIN PROBLEMAS" if not p else p)
for s in cfg["escenarios"]:
    print("  %-18s habilitado=%s destino=%s  comando(no se ejecuta): %s" % (s["id"], s["habilitado"], s["destino"], " ".join(e.comando_de(cfg, s))[:150]))
PY
)
rm -rf "$T"; echo "  copia temporal borrada: $([ -e "$T" ] && echo NO || echo SI)"
echo "## pruebas benignas minimas"
N="preflight-$(date +%s).lab-ppi"
t=$(ts); echo "  [$t] dig @10.10.10.20 $N A:"; dig +time=3 +tries=1 @10.10.10.20 "$N" A 2>&1 | grep -E 'status:|flags:|^[^;].*IN\s+A' | sed 's/^/    /'
t=$(ts); echo "  [$t] dig @10.10.10.20 lab-ppi SOA:"; dig +time=3 +tries=1 @10.10.10.20 lab-ppi SOA +short 2>&1 | sed 's/^/    /'
t=$(ts); echo "  [$t] GET http://10.10.30.10/ -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}s' http://10.10.30.10/)"
t=$(ts); echo "  [$t] GET :18081/auth sin credencial -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth fake:incorrecta -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u fake:preflight-incorrecta -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth control:*** -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u control:control123 -w '%{http_code}' http://10.10.30.10:18081/auth)"
echo "## fin=$(ts)  epoch=$(date +%s.%N)"
