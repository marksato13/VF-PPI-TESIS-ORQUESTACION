#!/bin/bash
# ENSAYO de la puerta D5 a fin de episodio + 75 s con el lanzador REAL (bastión -> Sensor1 por SSH, srv-dmz en sombra) y MEDICIÓN de su duración frente al hueco mínimo de 210 s.
# EXIGE UNA SOLICITUD REAL de limpieza (reset_origen de 10.10.20.30) al Sensor1 — por eso requiere autorización expresa. Kali ya está limpia (quitado = vacío).
# Se ejecuta como gadmin en el bastión; sin sudo. Solo lecturas en srv-dmz (sets, traza del agente); no genera tráfico; no toca la Kali. Un directorio de ensayo nuevo, sin tocar ~/cf-e4/4c.
# Uso: ensayo_puerta_75.sh            (lanza el ensayo en segundo plano y vuelve; el informe queda en <dir>/informe.txt)
set -u
HB=$HOME/cf-b/herramientas; T=$(date -u +%Y%m%dT%H%M%SZ); D=$HOME/cf-b/ensayo-puerta-$T
[ -e ~/cf-e4/4c ] && { echo "PARAR: hay una campaña viva (~/cf-e4/4c)"; exit 2; }
ps -eo args | grep -v 'bash -c' | grep -qE '[l]anzador_puerta|[c]ompuerta_b' && { echo "PARAR: ya hay una puerta en marcha"; exit 2; }
mkdir -p "$D" && echo "ensayo en $D"
python3 -I -c "
import json, time
json.dump({'pendiente': True, 'en_episodio': False, 'n_inicios': 1, 'episodio': 'ensayo-puerta', 'fin_en': time.time(), 'liberada_en': None, 'orden': ['ensayo-puerta']}, open('$D/gate.json', 'w'), sort_keys=True)
print('gate.json: puerta pendiente con fin_en = ahora')"
cat > "$D/correr.sh" <<'EOS'
D="$1"; HB=$HOME/cf-b/herramientas
T0=$(date +%s.%N); echo "inicio (fin de episodio simulado) $(date -u +%FT%T.%3NZ)" > "$D/informe.txt"
python3 -I "$HB/lanzador_puerta_banco.py" ejecutar --dir "$D" --d5-banco "$HB/d5_episodio_banco.py" --sensor m4rk@10.10.60.11 \
  --clave "$HOME/.ssh/cyberflow-d5-sensor" --known-hosts "$HOME/.ssh/known_hosts_d5" --herramientas "$HB" --espera-fin 75 \
  --ssh-sensor-legado "ssh -n -o BatchMode=yes sensor1" --ssh-srv-legado "ssh -n -o BatchMode=yes srvdmz" --max-iter 1 > "$D/lanzador.stdout" 2> "$D/lanzador.stderr"
RC=$?; T1=$(date +%s.%N)
python3 -I - "$D" "$T0" "$T1" "$RC" >> "$D/informe.txt" <<'PY'
import json, sys, os
d, t0, t1, rc = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
tot = t1 - t0
print("lanzador rc=%s" % rc)
print("compuerta.log:", open(d + "/compuerta.log").read().strip() if os.path.exists(d + "/compuerta.log") else "(vacío)")
print("gate.json final:", open(d + "/gate.json").read())
for f in ("puerta-banco.jsonl",):
    p = d + "/" + f
    if os.path.exists(p):
        print("--- %s" % f)
        for l in open(p):
            print("  " + l.strip()[:300])
print("--- MEDICIÓN")
print("duración total desde el fin simulado: %.1f s (espera 75,0 s + puerta %.1f s)" % (tot, tot - 75.0))
print("hueco mínimo entre episodios: 210 s  ->  MARGEN = %.1f s" % (210.0 - tot))
print("hueco tras un DNS: 330 s  ->  margen = %.1f s" % (330.0 - tot))
PY
cat "$D/lanzador.stderr" | tail -5 >> "$D/informe.txt"
echo "FIN" >> "$D/informe.txt"
EOS
setsid nohup bash "$D/correr.sh" "$D" > /dev/null 2>&1 < /dev/null &
echo "lanzado en segundo plano (PID $!); duración esperada ≈ 75 s + 35–90 s. Informe: $D/informe.txt"
