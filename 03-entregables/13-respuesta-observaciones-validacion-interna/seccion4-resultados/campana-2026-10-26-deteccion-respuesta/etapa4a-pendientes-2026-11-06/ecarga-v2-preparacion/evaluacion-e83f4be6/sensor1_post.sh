#!/usr/bin/env bash
# [SENSOR1 m4rk] Análisis posterior de E-carga v2 (solo lecturas; no antes de 1794198600 = 04:30Z en la franja propuesta,
# para que Suricata haya emitido los flujos de la ventana: flow-timeouts TCP 600 + 60 s).
#   sensor1_post.sh DIR DESDE HASTA
# DIR es la carpeta de los muestreadores (muestras.jsonl, obs_pcap/pcap.jsonl). Escribe en DIR/post (si existe, aborta).
# Salidas: clasificacion/ (clasificar_periodo --suricata-eve), comparar.json (K1–K3), perfiles.json + perfiles.rc (K4a,
# K4b informativo), pcap_s.json (S2, S3), suricata-ls.txt (rotación de eve.json), ruleset-despues.txt, SHA256SUMS.
set -u
O=${1:?DIR}; D=${2:?DESDE}; A=${3:?HASTA}
P="$HOME/cf-e4/paquete-ae2900e"; H="$HOME/cyberflow-e4/herramientas-20261106"; E="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/cyberflow/.venv/bin/python"; S="$O/post"
[ -e "$S" ] && { echo "ABORTA: $S ya existe"; exit 2; }
mkdir -p "$S"
echo "######## post $(date -u +%FT%TZ) ventana $D–$A"
pgrep -af "salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py" | grep -v pgrep && echo "AVISO: muestreadores aún vivos" || echo "muestreadores terminados"
ls -la --time-style=+%FT%T /var/log/suricata/ > "$S/suricata-ls.txt" 2>&1
EVES=(/var/log/suricata/eve.json)
for f in /var/log/suricata/eve.json.1 /var/log/suricata/eve.json.1.gz; do
  [ -f "$f" ] && [ "$(stat -c %Y "$f")" -ge "${D%.*}" ] && EVES=("$f" "${EVES[@]}") && echo "eve rotó en la ventana: $f"
done
SE=(); SV=(); for e in "${EVES[@]}"; do SE+=(--suricata-eve "$e"); SV+=(--stats-eve "$e" --eve "$e"); done
EP=(); for e in "${EVES[@]}"; do EP+=(--eve "$e"); done
echo "--- clasificar_periodo (clase, motivos, medida EVE: K5, S4, S5, S12, S13 y bloque suricata)"
"$PY" -I "$H/clasificar_periodo.py" --salud-captura "$H/salud_captura.py" --muestras "$O/muestras.jsonl" \
  --salida "$S/clasificacion" --desde "$D" --hasta "$A" "${SE[@]}" > "$S/clasificar.out" 2>&1; echo "rc=$?" | tee -a "$S/clasificar.out"
tail -3 "$S/clasificar.out"
echo "--- comparar_suricata (K1, K2, K3)"
python3 -I "$P/deploy/etapa4/sensor1/comparar_suricata.py" "${SV[@]}" --desde "$D" --hasta "$A" --etiqueta ecarga-v2 \
  > "$S/comparar.json" 2> "$S/comparar.err"; echo "rc=$?"
python3 -I -c 'import json,sys;c=json.load(open(sys.argv[1]));print({k:c.get(k) for k in ("paquetes","rafagas_ge_umbral","flujos_eve","flujos_grandes","reinicios_suricata_en_ventana","hueco_max_entre_bloques_s")})' "$S/comparar.json"
echo "--- evaluar_ecarga perfiles (K4a; K4b informativo)"
python3 -I "$P/deploy/etapa4/sensor1/evaluar_ecarga.py" perfiles "${EP[@]}" --desde "$D" --hasta "$A" > "$S/perfiles.json" 2>&1
echo $? > "$S/perfiles.rc"; echo "rc=$(cat "$S/perfiles.rc")"
echo "--- derivar_pcap (S2, S3)"
python3 -I "$E/derivar_pcap.py" "$O/obs_pcap/pcap.jsonl" "$D" "$A" > "$S/pcap_s.json" 2>&1; echo "rc=$?"
python3 -I -c 'import json,sys;c=json.load(open(sys.argv[1]));print("S2",c.get("S2",{}).get("valor"),"S3",c.get("S3",{}).get("valor"),"ficheros",c.get("ficheros"))' "$S/pcap_s.json"
echo "--- ruleset de Sensor1 después"
sudo -n nft list ruleset | sed -E "s/counter packets [0-9]+ bytes [0-9]+/counter/" | sha256sum | cut -c1-16 | tee "$S/ruleset-despues.txt"
(cd "$S" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS) && echo "sellado $S/SHA256SUMS"
