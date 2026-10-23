#!/bin/bash
# 4.3 - Replay por episodio: Suricata vs CyberFlow (modelo LIMPIO) sobre el MISMO PCAP.
# SE EJECUTA EN EL SENSOR (tiene el extractor y el modelo). Trocea el PCAP de la campana
# por episodio con los tiempos de marcas.jsonl y corre 22-correr-piloto.py (nota 19) con
# los parametros del modelo limpio. Reusa el pipeline existente; no reentrena ni toca nada.
#
# Prerequisitos en el sensor: suricata (ET Open congelado), tshark, y copiados aqui:
#   22-correr-piloto.py y 20-puntuar-por-ventana.py (del repo comparacion-cyberflow-suricata).
#
# Uso:  bash correr_replay_suricata.sh marcas.jsonl campana.pcap [outdir]
set -u
MARCAS="${1:?uso: correr_replay_suricata.sh marcas.jsonl campana.pcap [outdir]}"
PCAP="${2:?falta el PCAP de la campana}"
OUT="${3:-resultados-campana-limpio}"

PY=/home/m4rk/cyberflow/.venv/bin/python3
EXTRACTOR=/home/m4rk/cyberflow/scripts/features/extract_multilayer_v2.py
SCHEMA=/home/m4rk/cyberflow/configs/features/multilayer-v2.json
MODELO=/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib
MANIFEST=/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json
RUNNER="${RUNNER:-./22-correr-piloto.py}"
SCORER="${SCORER:-./20-puntuar-por-ventana.py}"
mkdir -p "$OUT/pcaps"

# Extraer (id, familia, t0, t_fin) de marcas.jsonl
"$PY" - "$MARCAS" > "$OUT/episodios.tsv" <<'PYEOF'
import json, sys
ini={}; fin={}; fam={}
for ln in open(sys.argv[1], encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    m = json.loads(ln)
    if m.get("familia") == "clock":
        continue
    eid = m["id"]; fam[eid] = m["familia"]
    if m["fase"] == "inicio":
        ini[eid] = float(m["wall"])
    elif m["fase"] == "fin":
        fin[eid] = float(m["wall"])
for eid in sorted(ini, key=lambda k: ini[k]):
    print("%s\t%s\t%.3f\t%.3f" % (eid, fam.get(eid, ""), ini[eid], fin.get(eid, ini[eid])))
PYEOF

while IFS=$'\t' read -r id fam t0 tfin; do
  [ -z "$id" ] && continue
  lo=$(awk "BEGIN{print $t0-2}")
  hi=$(awk "BEGIN{print $tfin+120}")
  epcap="$OUT/pcaps/episodio-$id.pcap"
  echo "[$id] troceando [$lo, $hi]"
  tshark -r "$PCAP" -Y "frame.time_epoch >= $lo && frame.time_epoch <= $hi" -w "$epcap" 2>/dev/null
  t0iso=$("$PY" -c "import datetime,sys;print(datetime.datetime.utcfromtimestamp(float(sys.argv[1])).strftime('%Y-%m-%dT%H:%M:%S+00:00'))" "$t0")
  "$PY" "$RUNNER" --id "$id" --pcap "$epcap" --t-inicio "$t0iso" --familia "$fam" \
    --extractor "$EXTRACTOR" --schema "$SCHEMA" --modelo "$MODELO" --manifest "$MANIFEST" \
    --detector-name if_limpio_2026_10 --scorer "$SCORER" --entity-network 10.10.0.0/16 \
    --outdir "$OUT" >/dev/null 2>&1 || echo "  (aviso: fallo el runner en $id; revisa $OUT/$id)"
done < "$OUT/episodios.tsv"

echo "== Tabla 9 (crudo) en $OUT/resultados.csv =="
[ -f "$OUT/resultados.csv" ] && cat "$OUT/resultados.csv"
