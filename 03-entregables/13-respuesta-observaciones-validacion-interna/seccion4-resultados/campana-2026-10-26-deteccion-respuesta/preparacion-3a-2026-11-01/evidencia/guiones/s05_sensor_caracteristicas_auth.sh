#!/usr/bin/env bash
# PASO3A s05 — sensor (solo lectura): recalcula las 28 caracteristicas de las ventanas de la Kali alrededor de la
# preparacion de auth (05:27:00-05:27:02) con recalcular_caracteristicas.py (version de la campana A, sin cambios)
# para comprobar que la extraccion recibe los 401/200. La "marca" es de PREPARACION, no de un episodio.
set -u
B=$HOME/cf-paso3a-20261101T0523Z; H=$B/herramientas; P=$B/preparacion-auth
cat > $P/marcas-preparacion-auth.jsonl <<'J'
{"evento": "inicio", "episodio_id": "preparacion-auth-paso3a", "escenario": "preparacion_auth", "repeticion": 0, "destino": "10.10.30.10", "reloj": {"pared_utc": "2026-11-01T05:27:00.976Z"}}
{"evento": "fin", "episodio_id": "preparacion-auth-paso3a", "estado": "completo", "reloj": {"pared_utc": "2026-11-01T05:27:01.081Z"}}
J
ARR=$(date -d "$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)" +%s)
echo "## s05 $(date -u +%FT%T.%3NZ) arranque motor=$ARR"
grep '"entity_ip": "10.10.20.30"' $HOME/cyberflow/logs/motor_decision.log | grep -E '"window_end_utc": "2026-11-01T05:2[6-9]' > $P/motor-kali-0526-0529.log
cd $H && $HOME/cyberflow/.venv/bin/python recalcular_caracteristicas.py --marcas $P/marcas-preparacion-auth.jsonl \
  --motor $P/motor-kali-0526-0529.log --pcap-dir /var/lib/ppi-motor-capture --eve /var/log/suricata/eve.json \
  --arranque-motor $ARR --salida $P/caracteristicas-recalculadas.jsonl 2>&1 | tail -5
python3 - $P/caracteristicas-recalculadas.jsonl <<'PY'
import json, sys
for l in open(sys.argv[1]):
    r = json.loads(l)
    f = r.get("caracteristicas") or r.get("features") or {}
    print("  wend=%s pk10_reg=%s score_reg=%s score_recalc=%s coincide=%s" % (r.get("window_end_utc", "")[11:19], r.get("pk10_registrado"), r.get("score_registrado"), r.get("score_recalculado"), r.get("coincide")))
    print("     ", {k: v for k, v in f.items() if k.startswith("http_") or k.startswith("dns_")})
PY
echo "## fin"
