#!/usr/bin/env bash
# PASO2 s01 — sensor: estado inicial ANTES de tocar nada. Solo lectura del sistema; escribe unicamente en el
# directorio exclusivo nuevo ~/cf-paso2-20261101T0254Z/estado-inicial (aborta si ya existe).
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; D=$B/estado-inicial
[ -e "$B" ] && { echo "ABORTO: ya existe $B"; exit 2; }
mkdir -p "$D"
echo "## s01 sensor $(hostname) $(date -u +%FT%T.%3NZ) destino=$D"
echo "  directorios cf-* existentes (no se tocan): $(ls -d $HOME/cf-* 2>/dev/null | tr '\n' ' ')"
for u in ppi-motor ppi-motor-capture suricata ppi-publicar-feed ppi-dashboard cyberflow-acumular cyberflow-limpieza cyberflow-aprendizaje; do
  systemctl cat $u.service > "$D/unidad-$u.service.txt" 2>&1
  systemctl show $u.service -p MainPID,NRestarts,ActiveState,SubState,UnitFileState,ActiveEnterTimestamp > "$D/show-$u.txt" 2>&1
  echo "  $u: $(tr '\n' ' ' < "$D/show-$u.txt")"
done
systemctl list-timers --all --no-pager > "$D/timers.txt" 2>&1; grep -iE 'ppi|cyber' "$D/timers.txt" | sed 's/^/  timer /'
P=$(systemctl show -p MainPID --value ppi-motor); tr '\0' ' ' < /proc/$P/cmdline > "$D/argv-motor.txt"; echo >> "$D/argv-motor.txt"
P2=$(systemctl show -p MainPID --value ppi-motor-capture); tr '\0' ' ' < /proc/$P2/cmdline > "$D/argv-captura.txt"; echo >> "$D/argv-captura.txt"
P3=$(systemctl show -p MainPID --value suricata); tr '\0' ' ' < /proc/$P3/cmdline > "$D/argv-suricata.txt" 2>/dev/null; echo >> "$D/argv-suricata.txt"
echo "  argv motor:    $(cat "$D/argv-motor.txt")"
echo "  argv captura:  $(cat "$D/argv-captura.txt")"
echo "  argv suricata: $(cat "$D/argv-suricata.txt")"
echo "  --enforce unidad='$(systemctl cat ppi-motor.service | grep -o -- '--enforce' || true)' argv='$(grep -o -- '--enforce' "$D/argv-motor.txt" || true)'"
echo "  suricata version: $(suricata -V 2>&1 | head -1)   tcpdump: $(tcpdump --version 2>&1 | head -1)"
echo "  python venv: $($HOME/cyberflow/.venv/bin/python -c 'import sys,sklearn,numpy;print(sys.version.split()[0],"sklearn",sklearn.__version__,"numpy",numpy.__version__)' 2>&1)"
echo "## hashes de implementacion"
( cd $HOME/cyberflow && sha256sum scripts/engine/*.py scripts/features/*.py configs/features/*.json configs/*.toml \
    artifacts/preliminar/limpio-2026-10/* 2>/dev/null ) > "$D/sha256-implementacion.txt"
grep -E 'motor_decision|motor_incremental|heuristicos|extract_multilayer_v[23]|multilayer-v2|publicar_feed|joblib|manifest|\.toml' "$D/sha256-implementacion.txt" | cut -c1-16,65- | sed 's/^/  /'
ls -la $HOME/cyberflow/scripts/engine/ > "$D/ls-engine.txt"; grep -E 'motor_' "$D/ls-engine.txt" | sed 's/^/  /'
( cd $HOME/cyberflow && git log -1 --format='%H %ad %s' --date=iso 2>&1; git status --short 2>&1 | head -30 ) > "$D/git-sensor.txt"
echo "  git sensor: $(head -1 "$D/git-sensor.txt")"
echo "## modelo y umbral en el registro de arranque vigente"
grep '"motor_startup"' $HOME/cyberflow/logs/motor_decision.log | tail -1 > "$D/ultimo-motor-startup.json"
python3 - "$D/ultimo-motor-startup.json" <<'PY'
import json,sys
r=json.loads(open(sys.argv[1]).read())
print("  ", {k:r.get(k) for k in ("logged_at","model_name","model_path","threshold","threshold_source","history_seconds","window_sizes","procesamiento","enforce","schema_path")})
print("   claves:", sorted(r)[:60])
PY
echo "## registros"
ls -la --time-style=full-iso $HOME/cyberflow/logs/ $HOME/cyberflow/logs/_state/ > "$D/ls-logs.txt" 2>&1; sed 's/^/  /' "$D/ls-logs.txt" | head -40
tail -n 1 $HOME/cyberflow/logs/motor_decision.log | cut -c1-260 | sed 's/^/  ultimo: /'
echo "  ahora=$(date +%s.%N)"
echo "## feed y escalada (copias, sin modificar)"
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json "$D/" 2>&1 && echo "  copiados"
sha256sum "$D"/feed.json "$D"/feed.sig "$D"/estado.json 2>&1 | sed "s#$D/##;s/^/  /"
python3 - "$D/feed.json" "$D/estado.json" <<'PY'
import json,sys,time
f=json.load(open(sys.argv[1])); e=json.load(open(sys.argv[2]))
print("  feed generado=%s (hace %.0f s) umbrales=%s entradas=%d" % (f.get("generado"), time.time()-float(f.get("generado",0)), f.get("umbrales"), len(f.get("entradas",[]))))
for x in f.get("entradas",[])[:10]: print("    ", json.dumps(x)[:200])
print("  escalada: %d entidades" % len(e), {k:(v.get("bloqueos") if isinstance(v,dict) else v) for k,v in list(e.items())[:10]})
PY
echo "## recursos"
nproc | sed 's/^/  nucleos=/'; free -m | sed 's/^/  /'; swapon --show 2>&1 | sed 's/^/  /'
df -hP $HOME /var/lib /tmp 2>&1 | sed 's/^/  /'
cat /proc/pressure/memory 2>/dev/null | sed 's/^/  psi-mem /'; uptime | sed 's/^/  /'
ps -eo pid,etime,pcpu,rss,args --sort=-pcpu | head -12 | cut -c1-180 | sed 's/^/  /'
echo "  replay/arnes vivos: $(ps -eo args | grep -cE '[r]eplay_motor|[c]orridas.sh|[f]ase_c')   tmux: $(tmux ls 2>&1 | tr '\n' ' ')"
echo "  ens37: $(awk '/ens37/{print "rx_packets="$3" rx_drop="$5}' /proc/net/dev)   anillo: $(ls /var/lib/ppi-motor-capture/*.pcap 2>/dev/null | wc -l) pcap"
echo "## sudo sin contrasena (lista)"
sudo -n -l 2>&1 | sed 's/^/  /' | tee "$D/sudo-n-l.txt" | head -30
echo "## logrotate (lectura sin sudo)"
ls -la --time-style=full-iso /etc/logrotate.d/ | sed 's/^/  /'; grep -n "include" /etc/logrotate.conf | sed 's/^/  /'
for f in cyberflow cyberflow.anterior suricata suricata.orig-cyberflow; do
  echo "  -- /etc/logrotate.d/$f  $(stat -c '%U:%G %a %s %y' /etc/logrotate.d/$f 2>&1)  sha=$(sha256sum /etc/logrotate.d/$f 2>/dev/null | cut -c1-64)"
  cp -p /etc/logrotate.d/$f "$D/logrotate.d-$f" 2>/dev/null; sed 's/^/     | /' /etc/logrotate.d/$f 2>&1
done
echo "## archivador y comandos de captura disponibles"
ls -la $HOME/bin/ 2>&1 | sed 's/^/  /'; sha256sum $HOME/bin/archivar_captura.sh 2>&1 | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
