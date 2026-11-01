#!/usr/bin/env bash
# PASO3B c01 — sensor (solo lectura): crea el directorio EXCLUSIVO de la ejecucion y guarda el estado inicial.
# No toca motor, captura, Suricata ni servicios. Compara hashes con config-campana-3b.json (codigo) y referencias 3A.
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; E=$B/estado-inicial
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$E"; cd "$HOME/cyberflow"
echo "## c01 $(hostname) $(date -u +%FT%T.%3NZ) -> $B"
echo "  directorios cf-* previos (no se tocan): $(ls -d $HOME/cf-* | grep -v "$B" | tr '\n' ' ')"
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard ppi-publicar-feed.timer cyberflow-limpieza.timer cyberflow-acumular.timer cyberflow-aprendizaje.timer; do
  echo "  $u $(systemctl show -p ActiveState,SubState,MainPID,NRestarts,UnitFileState,ActiveEnterTimestamp $u | tr '\n' ' ')"
done | tee "$E/servicios-resumen.txt"
systemctl show -p Id,MainPID,NRestarts,ActiveState,ActiveEnterTimestamp ppi-motor.service ppi-motor-capture.service suricata.service ppi-publicar-feed.timer > "$E/servicios.txt"
P=$(systemctl show -p MainPID --value ppi-motor)
tr '\0' ' ' < /proc/$P/cmdline > "$E/argv-motor.txt"; echo >> "$E/argv-motor.txt"
echo "  argv motor: $(cat $E/argv-motor.txt)"
echo "  --enforce argv: '$(grep -o -- --enforce $E/argv-motor.txt)'  unidad: '$(systemctl cat ppi-motor | grep -o -- --enforce)'"
diff <(tr ' ' '\n' < $E/argv-motor.txt) <(tr ' ' '\n' < $HOME/cf-paso3a-20261101T0523Z/estado-inicial/argv-motor.txt) >/dev/null \
  && echo "  argv IDENTICO al del estado inicial 3A" || echo "  ATENCION: argv DISTINTO del 3A"
systemctl cat ppi-motor > "$E/unidad-ppi-motor.txt" 2>&1
cat > "$E/sha256-esperado.txt" <<'EOF'
6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e  scripts/engine/motor_decision.py
a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168  scripts/engine/motor_incremental.py
10deb05d22fa0215e5f5f37bc6f05225cda31b806c67051a6584d878e25ed6a2  scripts/engine/heuristicos.py
7130edae65afefa2fd82a9314e20194adec684f4b2c3c35c2337880d8e636ccb  scripts/features/extract_multilayer_v2.py
5adbfbf4845554430a3e8b5a4c00eb1e45c2216cae73532da73d9d3f4898fa7f  scripts/features/extract_multilayer_v3.py
b4d36adb3f29b21693eb0cd964515aed42b3965910379616f1af27441793baba  scripts/engine/feed.py
e032a1a28650d438ae707c93b3045801770b3a069b4395426077af3bbd2b0e33  configs/features/multilayer-v2.json
f7bc4c7d8e7ac0cd958f3936d55a5782285e59509919d82bf2998fbb70acc03d  scripts/engine/publicar_feed.py
7d80ab4a926457efb37f4c6c9778e53eda67a5840ca255ff4504f333ca638479  scripts/engine/escalada.py
df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60  artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib
b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7  artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json
EOF
echo "## hashes de la implementacion frente a config-campana-3b.json (codigo)"
sha256sum -c "$E/sha256-esperado.txt" 2>&1 | sed 's/^/  /' | tee "$E/sha256-implementacion-check.txt"
sha256sum $(awk '{print $2}' "$E/sha256-esperado.txt") > "$E/sha256-implementacion.txt"
echo "## herramientas del 3B (sensor) frente a REFERENCIAS-Y-HASHES"
cat > "$E/sha256-herramientas-esperado.txt" <<EOF
27e67fd1620762d7ec7cb172ea45465ad6edb7db77cf8d69c7c8102c8167050f  $HOME/cf-paso3a-20261101T0523Z/herramientas3b/analizar_3b.py
71674908e4fc7f938fc9687cf4b7ad2e4c2b77ad35ff20c0c0fcf59ec92c763a  $HOME/cf-paso3a-20261101T0523Z/herramientas3b/analizar.py
7b140ae42905428e0a2b615c8de88ff9d036c0c7021e2bc096b921597d33511b  $HOME/cf-paso3a-20261101T0523Z/herramientas3b/poblacion.py
d63ca6e96e8de90aec0ee8cd6274d91f006511248223c48658ad3535b642046d  $HOME/cf-paso3a-20261101T0523Z/herramientas3b/calidad_fuentes.py
48d13aba2082a044a311a1966817bd6ec62be0c3759bbd1618e5f2dd5b3d508c  $HOME/cf-paso3a-20261101T0523Z/herramientas3b/extraer_evidencia_destino.py
2181af5f8406e3aa4f41a26e24d7ec83bfaf72eee06aa3ee564e2dbba5639eb6  $HOME/bin/archivar_captura.sh
EOF
sha256sum -c "$E/sha256-herramientas-esperado.txt" 2>&1 | sed 's/^/  /'
R=$HOME/cf-paso2-20261101T0254Z/producto-24f8a80/scripts/engine/replay_motor.py
echo "  replay_motor.py (paso 2): $(sha256sum $R 2>&1 | cut -c1-64)  motor_incremental del arnes: $(sha256sum $HOME/cf-paso2-20261101T0254Z/producto-24f8a80/scripts/engine/motor_incremental.py 2>&1 | cut -c1-16)"
echo "## registros actualizandose"
now=$(date +%s)
for f in logs/motor_decision.log logs/_state/ciclos.jsonl /var/log/suricata/eve.json /var/log/suricata/stats.log; do
  echo "  $f edad=$(( now - $(stat -c %Y $f) )) s tam=$(stat -c %s $f)"
done
NEW=$(ls -1t /var/lib/ppi-motor-capture/live-*.pcap | head -1); echo "  anillo: $(ls /var/lib/ppi-motor-capture | wc -l) ficheros, mas reciente $(basename $NEW) edad=$(( now - $(stat -c %Y $NEW) )) s"
tail -n 6 logs/_state/ciclos.jsonl | python3 -c '
import sys, json
for l in sys.stdin:
    c = json.loads(l); print("  ciclo dur=%.2f pend=%s fin=%.0f" % (c["duracion_s"], c["ventanas_pendientes"], c["fin_ciclo"]))'
echo "  journal motor (trazas desde arranque): $(sudo -n journalctl --no-pager -u ppi-motor --since "$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)" 2>&1 | grep -ciE 'traceback|exception')"
tail -n 400 /var/log/suricata/stats.log | grep -E 'capture.kernel_(packets|drops)|^Date' | tail -3 | sed 's/^/  /'
echo "## procesos de otras campañas"
echo "  archivadores: $(pgrep -fa archivar_captura | grep -v pgrep || echo ninguno)"
echo "  muestreadores: $(pgrep -fa sensor_muestrear | grep -v pgrep || echo ninguno)"
echo "  replay: $(pgrep -fa replay_motor | grep -v pgrep || echo ninguno)  cf-capturar: $(pgrep -fa cf-capturar | grep -v pgrep || echo ninguno)"
echo "## feed y escalada (copia sin modificar)"
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json "$E/" && sha256sum $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json | tee "$E/sha256-feed.txt" | sed 's/^/  /'
python3 -c "import json;d=json.load(open('$HOME/feed/estado.json'));print('  estado.json:', json.dumps(d)[:400])"
echo "## memoria y disco"
free -m | sed 's/^/  /'; df -h / /home | sed 's/^/  /'
echo "  logrotate cyberflow: $(sha256sum /etc/logrotate.d/cyberflow | cut -c1-16) (esperado 183e7bc4...)"
grep -A3 'motor_decision' /etc/logrotate.d/cyberflow | head -8 | sed 's/^/  | /'
echo "  eve.json: inodo $(stat -c %i /var/log/suricata/eve.json) tam $(stat -c %s /var/log/suricata/eve.json); motor_decision.log tam $(stat -c %s logs/motor_decision.log)"
echo "## fin $(date -u +%FT%T.%3NZ)"
