#!/usr/bin/env bash
# [SENSOR1 m4rk] Muestreadores de E-carga v2 en Sensor1 (solo lectura, sin sudo): salud_captura muestrear (10 s),
# muestreo_fino (1 s) y obs_pcap (lectura de cada PCAP del anillo). Herramientas:
#   salud_captura.py  ~/cyberflow-e4/herramientas-20261106 (VERSION 2026-11-06.1, la de §3.3; se comprueba que es
#                     idéntica a la del paquete ae2900e)
#   muestreo_fino.py, obs_pcap.py, evaluar_ecarga.py   ~/cf-e4/paquete-ae2900e
#
#   sensor1_muestreadores.sh comprobar DIR FIN_EPOCH FIN_ISO   comprobaciones previas + obs_pcap --en-seco
#   sensor1_muestreadores.sh arrancar  DIR FIN_EPOCH FIN_ISO   lanza los tres (terminan solos en FIN); PID en DIR/pids
#   sensor1_muestreadores.sh parar     DIR                     TERM a los PID de DIR/pids cuya cmdline coincide
#   sensor1_muestreadores.sh estado    DIR
# arrancar no sobrescribe: si DIR/muestras.jsonl o DIR/pids existen, aborta.
set -u
ORDEN=${1:?orden}; O=${2:?DIR}
P="$HOME/cf-e4/paquete-ae2900e"; H="$HOME/cyberflow-e4/herramientas-20261106"
PY="$HOME/cyberflow/.venv/bin/python"; ANILLO=/var/lib/ppi-motor-capture; EVE=/var/log/suricata/eve.json
EV_ESPERADO=53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f
ok() { echo "OK    $*"; }; no() { echo "FALLO $*"; fallo=1; }
fallo=0
comprobar() {
  local FIN=$1 ISO=$2
  (cd "$P" && sha256sum -c --strict --quiet SHA256SUMS) && ok "paquete-ae2900e: SHA256SUMS verifica" || no "paquete-ae2900e"
  [ "$(sha256sum < "$P/deploy/etapa4/sensor1/evaluar_ecarga.py" | cut -c1-64)" = "$EV_ESPERADO" ] \
    && ok "evaluar_ecarga.py sha256 = publicado" || no "evaluar_ecarga.py sha256"
  v=$(python3 -I -c 'import importlib.util as u,sys;s=u.spec_from_file_location("e",sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m);print(m.VERSION)' "$P/deploy/etapa4/sensor1/evaluar_ecarga.py")
  [ "$v" = 2026-11-06.4 ] && ok "evaluar_ecarga VERSION $v" || no "evaluar_ecarga VERSION $v"
  (cd "$H" && sha256sum -c --strict --quiet SHA256SUMS) && ok "herramientas-20261106: SHA256SUMS verifica" || no "herramientas-20261106"
  cmp -s "$H/salud_captura.py" "$P/scripts/etapa4/salud_captura.py" && ok "salud_captura.py de herramientas = paquete ae2900e" \
    || no "salud_captura.py de herramientas distinto del paquete"
  [ -x "$PY" ] && ok "python del venv: $("$PY" -V 2>&1)" || no "python del venv"
  for f in "$P/deploy/etapa4/cierre/muestreo_fino.py" "$P/deploy/etapa4/sensor1/obs_pcap.py" "$P/deploy/etapa4/sensor1/clasificar_periodo.py" \
           "$P/deploy/etapa4/sensor1/comparar_suricata.py" "$P/deploy/etapa4/sensor1/verificar_sensor1.sh"; do
    [ -r "$f" ] && ok "legible $(basename "$f")" || no "no legible $f"; done
  [ -r "$EVE" ] && ok "eve.json legible ($(stat -c %s "$EVE") B)" || no "eve.json no legible"
  ls "$EVE".1* >/dev/null 2>&1 && ok "rotado legible: $(ls -1 "$EVE".1* | head -1)" || echo "INFO  sin eve.json.1 (no hace falta si no rota)"
  [ -r "$ANILLO" ] && [ -x "$ANILLO" ] && ok "anillo legible ($(ls -1 "$ANILLO" | wc -l) ficheros)" || no "anillo no legible"
  [ -r /proc/net/softnet_stat ] && ok "softnet_stat legible" || no "softnet_stat"
  for u in ppi-motor-capture ppi-via-rapida@ens37; do
    n=$(journalctl --no-pager -u "$u" --since "-10min" 2>/dev/null | grep -c "packets captured")
    [ "$n" -gt 0 ] && ok "journal de $u legible ($n lecturas SIGUSR1 en 10 min)" || no "journal de $u sin lecturas SIGUSR1"; done
  libre=$(df --output=avail -k /home | tail -1 | tr -d ' ')
  [ "$libre" -ge 2097152 ] && ok "/home libre $((libre/1024)) MiB (>= 2 GiB)" || no "/home libre $libre kB"
  mem=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  [ "$mem" -ge 1048576 ] && ok "MemAvailable $((mem/1024)) MiB (>= 1 GiB)" || no "MemAvailable $mem kB"
  mkdir -p "$(dirname "$O")" && [ -w "$(dirname "$O")" ] && ok "destino de evidencia escribible: $(dirname "$O")" || no "destino $O"
  [ -e "$O" ] && no "DIR $O ya existe (no se reutiliza)" || ok "DIR $O libre"
  ps -eo args | grep -E -- "--(enforce|aplicar)( |$)" | grep -vq grep && no "hay procesos con --aplicar/--enforce" || ok "0 procesos con --aplicar/--enforce"
  pgrep -af "salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py" | grep -v pgrep && no "ya hay muestreadores en marcha" || ok "ningún muestreador en marcha"
  echo "== obs_pcap --en-seco"
  python3 -I "$P/deploy/etapa4/sensor1/obs_pcap.py" --dir "$ANILLO" --salida "$O-seco-obs_pcap" --hasta-epoch "$FIN" --hasta-iso "$ISO" --en-seco
  rc=$?; [ $rc = 0 ] && ok "obs_pcap --en-seco rc 0" || no "obs_pcap --en-seco rc $rc"
  [ -e "$O-seco-obs_pcap" ] && no "obs_pcap en seco creó $O-seco-obs_pcap" || ok "obs_pcap en seco no creó salida"
  echo "fallo=$fallo"; return $fallo
}
arrancar() {
  local FIN=$1 ISO=$2
  { [ -e "$O/muestras.jsonl" ] || [ -e "$O/pids" ]; } && { echo "ABORTA: $O ya tiene muestras o pids"; exit 2; }
  mkdir -p "$O"
  (cd "$H" && sha256sum -c --strict --quiet SHA256SUMS) || { echo "ABORTA: herramientas-20261106"; exit 2; }
  (setsid nohup "$PY" -I "$H/salud_captura.py" muestrear --salida "$O/muestras.jsonl" --suricata-stats /var/log/suricata/stats.log \
     --interfaz ens37 --unidad ppi-motor --unidad ppi-motor-capture --unidad ppi-via-rapida@ens37 --unidad ppi-publicar-feed-v2 \
     --unidad suricata --anillo "$ANILLO" --resumen-rapida "$HOME/feed-v2/via-rapida-resumen.jsonl" \
     --ciclos "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl" --hijos-de-unidad ppi-via-rapida@ens37 --intervalo 10 --hasta "$ISO" \
     > "$O/muestrear.out" 2>&1 < /dev/null & echo "$! salud_captura.py muestrear" >> "$O/pids")
  (setsid nohup python3 -I "$P/deploy/etapa4/cierre/muestreo_fino.py" --salida "$O/fino.jsonl" --intervalo 1 --hasta "$FIN" \
     > "$O/fino.out" 2>&1 < /dev/null & echo "$! muestreo_fino.py" >> "$O/pids")
  (setsid nohup python3 -I "$P/deploy/etapa4/sensor1/obs_pcap.py" --dir "$ANILLO" --salida "$O/obs_pcap" --hasta-epoch "$FIN" \
     --hasta-iso "$ISO" > "$O/obs_pcap.log" 2>&1 < /dev/null & echo "$! obs_pcap.py" >> "$O/pids")
  echo "$(date -u +%FT%TZ) arrancados (fin $FIN = $ISO)" >> "$O/eventos.log"
  sleep 3; estado
}
estado() {
  [ -r "$O/pids" ] || { echo "sin $O/pids"; return 1; }
  while read -r pid nombre; do
    if [ -r /proc/$pid/cmdline ] && tr '\0' ' ' < /proc/$pid/cmdline | grep -q "$nombre"; then echo "vivo   $pid $nombre"
    else echo "parado $pid $nombre"; fi
  done < "$O/pids"
  for f in muestras.jsonl fino.jsonl obs_pcap/pcap.jsonl; do [ -e "$O/$f" ] && echo "fichero $f $(wc -l < "$O/$f") líneas"; done
}
parar() {
  [ -r "$O/pids" ] || { echo "sin $O/pids"; return 1; }
  while read -r pid nombre; do
    if [ -r /proc/$pid/cmdline ] && tr '\0' ' ' < /proc/$pid/cmdline | grep -q "$nombre"; then kill -TERM "$pid" && echo "TERM $pid $nombre"; fi
  done < "$O/pids"
  echo "$(date -u +%FT%TZ) parada manual" >> "$O/eventos.log"; sleep 3; estado
}
case "$ORDEN" in
  comprobar) comprobar "${3:?FIN_EPOCH}" "${4:?FIN_ISO}" ;;
  arrancar)  arrancar "${3:?FIN_EPOCH}" "${4:?FIN_ISO}" ;;
  estado)    estado ;;
  parar)     parar ;;
  *) echo "orden no válida"; exit 2 ;;
esac
