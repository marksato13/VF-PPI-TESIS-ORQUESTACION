C=/home/m4rk/cf-e4/cierre4a; PY=/home/m4rk/cyberflow/.venv/bin/python
$PY -I $C/herr/analizar_fino.py --fino $C/salud/fino.jsonl --desde $(date -ud 2026-11-04T06:16:55Z +%s) --hasta $(date -ud 2026-11-04T06:26:55Z +%s)
$PY -I $C/herr/analizar_fino.py --fino $C/salud/fino.jsonl --desde $(date -ud 2026-11-04T06:05:00Z +%s) --hasta $(date -ud 2026-11-04T06:12:40Z +%s) | head -n 40
