#!/usr/bin/env bash
# PASO3A s01 — sensor: estado real, solo lectura. Crea el directorio exclusivo y guarda copias (no modifica nada).
set -u
ID=20261101T0523Z; B=$HOME/cf-paso3a-$ID; E=$B/estado-inicial
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$E"; cd "$HOME/cyberflow"
echo "## s01 $(hostname) $(date -u +%FT%T.%3NZ) -> $B"
echo "  directorios cf-* (no se tocan): $(ls -d $HOME/cf-* | tr '\n' ' ')"
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard ppi-publicar-feed.timer cyberflow-limpieza.timer cyberflow-acumular.timer cyberflow-aprendizaje.timer; do
  echo "  $u $(systemctl show -p ActiveState,SubState,MainPID,NRestarts,UnitFileState,ActiveEnterTimestamp $u | tr '\n' ' ')"
done | tee "$E/servicios.txt"
P=$(systemctl show -p MainPID --value ppi-motor)
tr '\0' ' ' < /proc/$P/cmdline > "$E/argv-motor.txt"; echo >> "$E/argv-motor.txt"
echo "  argv motor: $(cat $E/argv-motor.txt)"
echo "  --enforce: '$(grep -o -- --enforce $E/argv-motor.txt)'  (unidad: '$(systemctl cat ppi-motor | grep -o -- --enforce)')"
diff <(tr ' ' '\n' < $E/argv-motor.txt) <(tr ' ' '\n' < $HOME/cf-paso2-20261101T0254Z/argv-motor-tras-reinicio.txt 2>/dev/null) >/dev/null && echo "  argv IDENTICO al del paso 2 tras el reinicio" || echo "  argv DISTINTO del paso 2 (ver diff)"
systemctl cat ppi-motor > "$E/unidad-ppi-motor.txt" 2>&1
sha256sum scripts/engine/motor_decision.py scripts/engine/motor_incremental.py scripts/engine/heuristicos.py \
  scripts/features/extract_multilayer_v2.py scripts/features/extract_multilayer_v3.py configs/features/multilayer-v2.json \
  configs/cyberflow.toml configs/cyberflow.local.toml scripts/engine/publicar_feed.py \
  artifacts/preliminar/limpio-2026-10/*.joblib artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json > "$E/sha256-implementacion.txt"
sed 's/^/  /' "$E/sha256-implementacion.txt"
echo "## arranque vigente del motor"
grep '"motor_startup"\|"event": "startup"\|procesamiento' logs/motor_decision.log | tail -1 | cut -c1-900 > "$E/ultimo-arranque.json"
python3 - "$E/ultimo-arranque.json" <<'PY'
import json, sys
try:
    d = json.loads(open(sys.argv[1]).read())
    print("  ", {k: d.get(k) for k in ("event", "detector_name", "threshold", "history_seconds", "step_seconds", "procesamiento", "enforce", "logged_at") if k in d})
except Exception as e:
    print("   (no se pudo leer el registro de arranque:", e, ")")
PY
echo "## registros"
ls -la --time-style=+%FT%T logs/motor_decision.log* logs/_state/ciclos.jsonl* | sed 's/^/  /'
echo "  ultimo ciclo: $(tail -n1 logs/_state/ciclos.jsonl | cut -c1-200)"
echo "  journal motor desde el arranque: $(sudo -n journalctl --no-pager -u ppi-motor --since "@$(cut -d. -f1 $HOME/cf-paso2-20261101T0254Z/reinicio.t)" | grep -ciE 'traceback|exception') trazas"
echo "## suricata: puertos HTTP / detection-ports y stats"
grep -n -iE 'detection-ports|dp: *"?80|18081|HTTP_PORTS' /etc/suricata/suricata.yaml | head -10 | sed 's/^/  /'
tail -n 400 /var/log/suricata/stats.log | grep -E 'capture.kernel_(packets|drops)|^Date' | tail -3 | sed 's/^/  /'
echo "## interfaz ens37"
ip -s -s link show ens37 | sed 's/^/  /' | tee "$E/ip-s-s-ens37.txt"
cat /sys/class/net/ens37/statistics/{rx_packets,rx_dropped,rx_missed_errors,rx_nohandler,rx_errors,rx_fifo_errors} 2>/dev/null | paste -sd' ' | sed 's/^/  rx_packets rx_dropped rx_missed rx_nohandler rx_errors rx_fifo: /'
ethtool -S ens37 2>/dev/null | grep -iE 'drop|miss|fifo|nobuf|error' | grep -v ': 0$' | head -12 | sed 's/^/  ethtool /'
echo "  driver: $(ethtool -i ens37 2>/dev/null | head -2 | tr '\n' ' ')  promisc: $(cat /sys/class/net/ens37/flags)"
echo "## feed y escalada (copia sin modificar)"
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json "$E/" && sha256sum $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json | tee "$E/sha256-feed.txt" | sed 's/^/  /'
stat -c '  %n %U:%G %a %s %y' $HOME/feed/*
echo "## logrotate y respaldo del paso 2"
ls -la $HOME/cf-paso2-20261101T0254Z/logrotate/ | grep -i mark | sed 's/^/  /'
ls -la /etc/logrotate.d/ | sed 's/^/  /'
sha256sum /etc/logrotate.d/cyberflow | sed 's/^/  /'
echo "## memoria y disco"
free -m | sed 's/^/  /'; df -h / /home | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
