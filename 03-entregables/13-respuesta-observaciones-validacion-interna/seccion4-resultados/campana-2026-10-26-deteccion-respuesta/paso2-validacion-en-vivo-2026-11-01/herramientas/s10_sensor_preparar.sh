#!/usr/bin/env bash
# PASO2 s10 — sensor: prepara la candidata en el directorio exclusivo (sin instalar), pruebas especificas,
# estrofa de logrotate generada con --mostrar, y los guiones que Mark ejecutara con sudo. No toca /etc ni el motor.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; P=$B/producto-24f8a80; L=$B/logrotate; M=$B/mark
echo "## s10 $(date -u +%FT%T.%3NZ)"
[ -e "$P" ] && { echo "ABORTO: ya existe $P"; exit 2; }
mkdir -p "$P" "$L" "$M"
sha256sum "$B/candidato-24f8a80.tgz" | sed 's/^/  tgz /'
tar -xzf "$B/candidato-24f8a80.tgz" -C "$P"
( cd "$P" && sha256sum scripts/engine/motor_decision.py scripts/engine/motor_incremental.py scripts/setup/cyberflow_config.py ) | tee "$B/sha256-candidata.txt" | sed 's/^/  /'
grep -q '^6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e  scripts/engine/motor_decision.py' "$B/sha256-candidata.txt" \
 && grep -q '^a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168  scripts/engine/motor_incremental.py' "$B/sha256-candidata.txt" \
 && echo "  HASHES APROBADOS: OK" || { echo "  HASHES NO COINCIDEN: PARAR"; exit 3; }
echo "## dependencias no modificadas: desplegado vs candidata"
for f in scripts/engine/heuristicos.py scripts/features/extract_multilayer_v2.py scripts/features/extract_multilayer_v3.py configs/features/multilayer-v2.json; do
  printf '  %-45s desplegado=%s candidata=%s\n' $f "$(sha256sum $HOME/cyberflow/$f | cut -c1-16)" "$(sha256sum $P/$f | cut -c1-16)"; done
echo "## compilacion y pruebas especificas (venv del motor)"
cd "$P"
$HOME/cyberflow/.venv/bin/python -m py_compile scripts/engine/motor_decision.py scripts/engine/motor_incremental.py && echo "  py_compile OK"
nice -n 10 $HOME/cyberflow/.venv/bin/python -m unittest tests.test_motor_incremental tests.test_cyberflow_config > "$B/pruebas-especificas.txt" 2>&1; echo "  unittest rc=$?"
tail -4 "$B/pruebas-especificas.txt" | sed 's/^/  /'
echo "## estrofa de logrotate (--mostrar; NO --escribir)"
python3 "$P/scripts/setup/cyberflow_config.py" --config $HOME/cyberflow/configs/cyberflow.toml --mostrar > "$L/cyberflow_config-mostrar.txt" 2>&1; echo "  --mostrar rc=$?"
awk '/^### \/etc\/logrotate.d\/cyberflow$/{p=1; getline; next} p && /^=+$/{exit} p' "$L/cyberflow_config-mostrar.txt" \
  | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "$L/logrotate-cyberflow.nuevo"
sha256sum "$L/logrotate-cyberflow.nuevo" | sed 's/^/  /'
diff /etc/logrotate.d/cyberflow "$L/logrotate-cyberflow.nuevo" > "$L/diff-cyberflow-vigente-nuevo.txt"; echo "  diff rc=$?"; sed 's/^/  | /' "$L/diff-cyberflow-vigente-nuevo.txt"
echo "## temporizador de logrotate y estado EVE"
systemctl list-timers logrotate.timer --no-pager | sed 's/^/  /'
stat -c '  eve.json %s bytes inode=%i mtime=%y' /var/log/suricata/eve.json; ls -la /var/log/suricata/ | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
