#!/bin/bash
# Solo lectura: extrae la estrofa de logrotate generada y la compara con la instalada.
C=~/cf-p1/candidato
python3 $C/scripts/setup/cyberflow_config.py --config ~/cyberflow/configs/cyberflow.toml --mostrar \
  | awk '/^### \/etc\/logrotate.d\/cyberflow$/{p=1; getline; next} p && /^=+$/{exit} p' \
  | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > /tmp/logrotate-cyberflow.nuevo
diff /etc/logrotate.d/cyberflow /tmp/logrotate-cyberflow.nuevo; echo "diff rc=$?"
/usr/sbin/logrotate -d /tmp/logrotate-cyberflow.nuevo 2>&1 | grep -i -E "error|considering|rotating pattern" | head
rm -f /tmp/logrotate-cyberflow.nuevo
