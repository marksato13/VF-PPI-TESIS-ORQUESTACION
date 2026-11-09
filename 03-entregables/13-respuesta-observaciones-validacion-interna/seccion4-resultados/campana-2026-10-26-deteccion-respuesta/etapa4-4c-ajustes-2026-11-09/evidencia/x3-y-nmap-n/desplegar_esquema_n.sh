cd "$HOME"
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4-4c-ajustes-2026-11-09"
H=45f743d2ef35f7691ecaa8aeda47eb22445d5a288d2ed559aa30709d14943cee
[ "$(sha256sum "$R/scripts-4c-n/esquema_campana.py" | cut -d' ' -f1)" = "$H" ] || { echo "PARO: hash local"; exit 3; }
BA="ssh -n -o BatchMode=yes -i $HOME/.ssh/id_ed25519 gadmin@10.10.10.30"
KA="ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
echo "== 1) respaldo de scripts-4c en la Kali (cp -a, sin borrar)"
$BA "$KA 'cd ~/cf-campana-A && [ ! -e scripts-4c-previo-e762e604 ] && cp -a scripts-4c scripts-4c-previo-e762e604; ls -d scripts-4c*; sha256sum scripts-4c-previo-e762e604/esquema_campana.py | cut -c1-16'"
echo "== 2) copia del esquema nuevo vía bastión"
ssh -o BatchMode=yes -i $HOME/.ssh/id_ed25519 gadmin@10.10.10.30 'mkdir -p ~/cf-e4/esquema-n && cat > ~/cf-e4/esquema-n/esquema_campana.py' < "$R/scripts-4c-n/esquema_campana.py"
$BA "sha256sum ~/cf-e4/esquema-n/esquema_campana.py | cut -c1-16"
$BA "cat ~/cf-e4/esquema-n/esquema_campana.py | ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'cat > ~/cf-campana-A/scripts-4c/esquema_campana.py.nuevo'"
$BA "$KA 'cd ~/cf-campana-A/scripts-4c && [ \"\$(sha256sum esquema_campana.py.nuevo | cut -d\" \" -f1)\" = $H ] && mv -f esquema_campana.py.nuevo esquema_campana.py; sha256sum esquema_campana.py generar_campana.py | cut -c1-16; ls'"
