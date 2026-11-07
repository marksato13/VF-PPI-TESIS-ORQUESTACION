#!/usr/bin/env bash
# [CLIENTES adminclientes] Comprobador estricto de la variante r5. SOLO LECTURA. VERSION 2026-11-07.1
#   comprobar_forzar_host.sh con    las seis unidades tienen exactamente el drop-in y el argv de la variante
#   comprobar_forzar_host.sh sin    las seis unidades han vuelto al argv original, sin drop-in
#   comprobar_forzar_host.sh vivo   los seis procesos en marcha llevan exactamente el argv de la variante
# generadores.sh `configuracion` acepta opciones añadidas y no distingue la variante: esto sí la distingue. El AVISO de
# clientes_lab.py no sirve de evidencia porque las unidades llevan StandardOutput=null.
# rc: 0 CUMPLE · 1 NO_CUMPLE · 3 ERROR, nunca se aprueba · 2 uso
set -u -o pipefail
MODO=${1:-}
RAIZ=${CF_RAIZ:-}; PROC=${CF_PROC:-/proc}; SC=${CF_SYSTEMCTL:-systemctl}
GEN=/home/adminclientes/laboratorio/clientes_lab.py
GEN_LOCAL=${CF_GEN:-$GEN}
HASH=${CF_HASH:-ae5134a778e66d90f5c3fbcd47323e328f3422cf4ba8d5197649f402c1d4cdc3}
PERFILES="ofimatica:10.10.20.21 navegacion:10.10.20.22 descargas:10.10.20.23 aplicacion:10.10.20.24 ligero:10.10.20.25 erratico:10.10.20.26"
CONF=10-forzar-laborable-r5.conf
[ "$MODO" = con ] || [ "$MODO" = sin ] || [ "$MODO" = vivo ] || { echo "uso: comprobar_forzar_host.sh con|sin|vivo"; exit 2; }
malo=0; err=0
no() { echo "NO_CUMPLE $*"; malo=1; }
fallo() { echo "ERROR $*"; err=1; }
echo "INFO forzar $MODO $(id -un) $(hostname) $(date -u +%FT%TZ)"
h=$(sha256sum < "$GEN_LOCAL" 2>/dev/null | cut -c1-64)
[ -n "$h" ] || fallo "generador ilegible"
[ -z "$h" ] || [ "$h" = "$HASH" ] || no "generador $h distinto de $HASH"
for p in $PERFILES; do
  n=${p%%:*}; ip=${p#*:}; u=cyberflow-lab-$n.service
  base="/usr/bin/python3 $GEN --perfil $n --origen $ip --servidor 10.10.30.10 --dns 10.10.10.20"
  c="$RAIZ/etc/systemd/system/$u.d/$CONF"
  e=$($SC show -p ExecStart --value "$u" 2>&1); r=$?
  dp=$($SC show -p DropInPaths --value "$u" 2>&1); r2=$?
  if [ $r != 0 ] || [ $r2 != 0 ]; then fallo "$u: systemctl show rc $r/$r2"; continue; fi
  [ "$(grep -c 'argv\[\]=' <<<"$e")" = 1 ] || { no "$u: no hay exactamente un ExecStart"; continue; }
  a=$(sed -E 's/^.*argv\[\]=(.*) ; ignore_errors=.*$/\1/' <<<"$e")
  case $MODO in
    con)
      [ "$a" = "$base --forzar-laborable" ] && [ "$dp" = "$c" ] && [ -f "$c" ] && echo "OK $u con --forzar-laborable" \
        || no "$u: argv «$a», drop-ins «$dp»" ;;
    sin)
      [ "$a" = "$base" ] && [ -z "$dp" ] && [ ! -e "${c%/*}" ] && echo "OK $u original" \
        || no "$u: argv «$a», drop-ins «$dp»" ;;
    vivo)
      pid=$($SC show -p MainPID --value "$u" 2>&1) || { fallo "$u: MainPID"; continue; }
      [[ $pid =~ ^[1-9][0-9]*$ ]] || { no "$u: sin proceso (MainPID=$pid)"; continue; }
      v=$(tr '\0' ' ' < "$PROC/$pid/cmdline" 2>/dev/null) || { fallo "$u: cmdline de $pid ilegible"; continue; }
      [ "${v% }" = "$base --forzar-laborable" ] && echo "OK $u pid $pid con --forzar-laborable" || no "$u: proceso con argv «${v% }»" ;;
  esac
done
if [ $err = 1 ]; then echo "REQ FORZAR.$MODO ERROR"; echo "FIN_FORZAR rc=3"; exit 3; fi
if [ $malo = 1 ]; then echo "REQ FORZAR.$MODO NO_CUMPLE"; echo "FIN_FORZAR rc=1"; exit 1; fi
echo "REQ FORZAR.$MODO CUMPLE"; echo "FIN_FORZAR rc=0"; exit 0
