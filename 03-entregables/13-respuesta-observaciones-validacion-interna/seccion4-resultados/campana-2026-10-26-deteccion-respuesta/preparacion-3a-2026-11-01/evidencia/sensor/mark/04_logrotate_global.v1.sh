#!/usr/bin/env bash
# PASO3A mark/04 — lo ejecuta Mark (necesita sudo con contraseña). SOLO LECTURA: `logrotate -d` es modo depuración,
# no rota ni modifica nada. Comprueba la validez GLOBAL de /etc/logrotate.conf (incluye /etc/logrotate.d/*) tras el
# cambio del paso 2 y guarda rc y salida COMPLETA. No toca /etc.
#   [BASTIÓN gadmin] ssh -t sensor1 'bash ~/cf-paso3a-20261101T0523Z/mark/04_logrotate_global.sh'
set -u
D=$HOME/cf-paso3a-20261101T0523Z/mark; L=$D/mark-04-logrotate-global.log
{
  echo "## mark/04 $(date -u +%FT%T.%3NZ) usuario=$(id -un) host=$(hostname)"
  sha256sum /etc/logrotate.conf /etc/logrotate.d/* 2>&1
  echo "## sudo logrotate -d /etc/logrotate.conf (salida completa)"
} > $L
sudo logrotate -d /etc/logrotate.conf >> $L 2>&1
rc=$?
{
  echo "## rc=$rc"
  echo "## lineas con error: $(grep -ciE '^error|: error' $L)"
  grep -iE '^error|: error' $L | sed 's/^/   /'
  echo "## fin $(date -u +%FT%T.%3NZ)"
} >> $L
sha256sum $L
tail -6 $L
