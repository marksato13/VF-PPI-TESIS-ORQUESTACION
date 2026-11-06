#!/usr/bin/env bash
# [CLIENTES adminclientes] Generadores legítimos de E-carga (cyberflow-lab.target, 6 perfiles .21–.26).
#   generadores.sh estado     solo lectura: target, unidades, procesos de perfiles y hash del generador (una línea)
#   generadores.sh permisos   solo lectura: sudo -n -l para start/stop del target (sin ejecutarlos)
#   generadores.sh arrancar   sudo -n systemctl start cyberflow-lab.target   (SOLO con orden explícita de Mark)
#   generadores.sh parar      sudo -n systemctl stop  cyberflow-lab.target y comprueba que no queda nada vivo
# Nunca modifica el generador ni las unidades ni las habilita.
set -u
GEN="$HOME/laboratorio/clientes_lab.py"
HASH_ESPERADO=ae5134a7
estado() {
  local u n
  n=$(pgrep -fc "clientes_lab.py" || true)
  u=$(systemctl list-units --all --no-legend --plain 'cyberflow-lab-*' 2>/dev/null | awk '{printf "%s=%s ", $1, $3}')
  echo "gen target=$(systemctl is-active cyberflow-lab.target) habilitado=$(systemctl is-enabled cyberflow-lab.target 2>&1) procesos=$n hash=$(sha256sum < "$GEN" | cut -c1-8) unidades: $u"
}
case "${1:-}" in
  estado) estado ;;
  permisos)
    sudo -n -l 2>&1 | grep -E 'systemctl (start|stop) cyberflow-lab\.target|ALL' || echo "sin permiso sudo -n visible para el target"
    echo "zona=$(cat /etc/timezone 2>/dev/null || timedatectl show -p Timezone --value) ahora_utc=$(date -u +%FT%TZ) hash_generador=$(sha256sum < "$GEN" | cut -c1-64)"
    estado ;;
  arrancar)
    [ "$(sha256sum < "$GEN" | cut -c1-8)" = "$HASH_ESPERADO" ] || { echo "ABORTA: hash del generador distinto"; exit 2; }
    sudo -n systemctl start cyberflow-lab.target; echo "start rc=$?"; sleep 5; estado ;;
  parar)
    sudo -n systemctl stop cyberflow-lab.target; echo "stop rc=$?"; sleep 3
    estado
    [ "$(systemctl is-active cyberflow-lab.target)" != active ] && [ "$(pgrep -fc clientes_lab.py || true)" = 0 ] \
      && echo "parados: target inactivo y 0 procesos" || { echo "QUEDAN PROCESOS O TARGET ACTIVO"; exit 1; } ;;
  *) echo "uso: generadores.sh estado|permisos|arrancar|parar"; exit 2 ;;
esac
