#!/usr/bin/env bash
# PASO2 s11 — sensor: verifica logrotate, respaldo operativo exclusivo, instala la candidata (sin sudo: ficheros
# de m4rk) y reinicia ppi-motor con el permiso NOPASSWD existente. Argumentos y unidad sin cambios.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; L=$B/logrotate; P=$B/producto-24f8a80; R=$B/respaldo-operativo
E=$HOME/cyberflow/scripts/engine
echo "## s11 $(date -u +%FT%T.%3NZ)"
echo "-- logrotate: rc y errores"
cat $L/global-1-antes.rc $L/global-2-sin-respaldos.rc $L/global-3-despues.rc | tr '\n' ' '; echo
for f in global-1-antes global-2-sin-respaldos global-3-despues; do echo "  $f: lineas=$(wc -l < $L/$f.txt) error:=$(grep -ci 'error' $L/$f.txt)"; done
grep -n -i error $L/global-1-antes.txt | sed 's/^/   antes| /'
grep -n -E 'ciclos.jsonl|motor_decision.log' $L/global-3-despues.txt | head -8 | sed 's/^/   despues| /'
diff $L/global-2-sin-respaldos.txt $L/global-3-despues.txt > $L/diff-2-3.txt; echo "  diff 2->3 lineas: $(wc -l < $L/diff-2-3.txt)"; sed 's/^/   | /' $L/diff-2-3.txt | head -30
ls -la /etc/logrotate.d/ | grep -E 'cyberflow|suricata' | sed 's/^/  /'
echo "-- comprobaciones previas"
[ "$(sha256sum $E/motor_decision.py | cut -c1-64)" = e2b2eb535091ea0fb7aa08054aa8cc4eff295a4e678269cba5d4a5ee5d95bc73 ] || { echo "PARAR: motor desplegado no es e2b2eb53"; exit 2; }
[ -e $E/motor_incremental.py ] && { echo "PARAR: ya existe motor_incremental.py"; exit 2; }
stat -c '  ultima rotacion motor_decision.log.1: %y' $HOME/cyberflow/logs/motor_decision.log.1
[ -e "$R" ] && { echo "PARAR: existe $R"; exit 2; }
mkdir -p "$R"
echo "-- respaldo operativo exclusivo en $R"
cp -p $E/motor_decision.py "$R/motor_decision.py.7b275b8-e2b2eb53"
cp -p $HOME/cyberflow/configs/cyberflow.toml $HOME/cyberflow/configs/cyberflow.local.toml $HOME/cyberflow/configs/features/multilayer-v2.json "$R/"
systemctl cat ppi-motor.service > "$R/ppi-motor.service.txt"
systemctl show ppi-motor.service -p ExecStart,User,ReadWritePaths,ProtectSystem,Restart > "$R/ppi-motor.show.txt"
cp -p /etc/logrotate.d/cyberflow "$R/logrotate.d-cyberflow.instalado" 2>/dev/null
cp -p $B/estado-inicial/logrotate.d-* "$R/" 2>/dev/null
ls -la --time-style=full-iso $E > "$R/ls-engine-antes.txt"
( cd "$R" && sha256sum * ) > "$R/SHA256SUMS"; stat -c '%n %U:%G %a %s %y' "$R"/* > "$R/STAT.txt"; sed 's/^/  /' "$R/SHA256SUMS"
echo "-- instalacion"
install -m 0664 $P/scripts/engine/motor_incremental.py $E/motor_incremental.py
install -m 0664 $P/scripts/engine/motor_decision.py $E/motor_decision.py
sha256sum $E/motor_decision.py $E/motor_incremental.py | tee $B/sha256-instalado.txt | sed 's/^/  /'
grep -q '^6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e ' $B/sha256-instalado.txt && grep -q '^a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168 ' $B/sha256-instalado.txt \
  || { echo "PARAR: hashes instalados no coinciden; revertir"; install -m 0664 "$R/motor_decision.py.7b275b8-e2b2eb53" $E/motor_decision.py; rm -f $E/motor_incremental.py; exit 3; }
stat -c '  %n %U:%G %a' $E/motor_decision.py $E/motor_incremental.py
$HOME/cyberflow/.venv/bin/python -m py_compile $E/motor_decision.py $E/motor_incremental.py && echo "  py_compile OK"
$HOME/cyberflow/.venv/bin/python $E/motor_decision.py --help | grep -E "ciclos-path|verificar-equivalencia" | sed 's/^/  /'
echo "-- reinicio"
tail -n1 $HOME/cyberflow/logs/motor_decision.log | cut -c1-120 | sed 's/^/  ultimo antes: /'
echo "  PID antes=$(systemctl show -p MainPID --value ppi-motor)"
T0=$(date +%s.%N); echo "$T0" > $B/reinicio.t
sudo -n systemctl restart ppi-motor; echo "  restart rc=$? t=$T0 ($(date -u +%FT%T.%3NZ))"
sleep 45
echo "  activo=$(systemctl is-active ppi-motor) PID=$(systemctl show -p MainPID --value ppi-motor) NRestarts=$(systemctl show -p NRestarts --value ppi-motor)"
P2=$(systemctl show -p MainPID --value ppi-motor); tr '\0' ' ' < /proc/$P2/cmdline > $B/argv-motor-tras-reinicio.txt; echo >> $B/argv-motor-tras-reinicio.txt
diff $B/estado-inicial/argv-motor.txt $B/argv-motor-tras-reinicio.txt > /dev/null && echo "  argumentos IDENTICOS a los iniciales" || echo "  ARGUMENTOS DISTINTOS"
sudo -n journalctl --no-pager -u ppi-motor --since "@${T0%.*}" -o short-iso > $B/journal-motor-arranque.txt 2>&1
echo "  journal: $(wc -l < $B/journal-motor-arranque.txt) lineas, Traceback/Error: $(grep -ciE 'traceback|error|exception' $B/journal-motor-arranque.txt)"; tail -5 $B/journal-motor-arranque.txt | cut -c1-220 | sed 's/^/   | /'
grep '"motor_startup"' $HOME/cyberflow/logs/motor_decision.log | tail -1 > $B/motor-startup-candidata.json
python3 - $B/motor-startup-candidata.json <<'PY'
import json,sys
r=json.loads(open(sys.argv[1]).read())
print("  startup:", {k:r.get(k) for k in ("logged_at","procesamiento","ciclos_path","detector_name","threshold","history_seconds","step_seconds","enforce","schema")})
PY
C=$HOME/cyberflow/logs/_state/ciclos.jsonl; echo "  ciclos.jsonl: $(wc -l < $C 2>/dev/null) registros"; tail -n2 $C 2>/dev/null | cut -c1-400 | sed 's/^/   | /'
echo "## fin $(date -u +%FT%T.%3NZ)"
