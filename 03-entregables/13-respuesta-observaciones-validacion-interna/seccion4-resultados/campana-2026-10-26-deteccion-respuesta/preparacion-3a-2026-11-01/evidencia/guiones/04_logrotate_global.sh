#!/usr/bin/env bash
# PASO3A mark/04 (v2, 2026-11-01) — lo ejecuta Mark (sudo con contraseña). SOLO LECTURA: `logrotate -d` es modo
# depuración; no rota ni modifica nada. Comprueba la validez GLOBAL de /etc/logrotate.conf (incluye
# /etc/logrotate.d/*) y guarda rc y salida COMPLETA en un registro con marca de tiempo (no sobrescribe otros).
#   [BASTIÓN gadmin] ssh -t sensor1 'bash ~/cf-paso3a-20261101T0523Z/mark/04_logrotate_global.sh'; echo "rc_ssh=$?"
# Código de salida del guion (y de ssh):
#   0  logrotate rc=0 y ninguna línea "error:" en la salida  -> comprobación cerrada
#   1  logrotate rc!=0, o rc=0 con líneas de error de configuración
#   2  no se pudo ejecutar (sudo rechazado o logrotate ausente)
# v1 terminaba con `tail`, así que su código de salida era el de tail y no el de logrotate.
set -u
D=$HOME/cf-paso3a-20261101T0523Z/mark; mkdir -p "$D"
T=$(date -u +%Y%m%dT%H%M%SZ); L=$D/mark-04-logrotate-global-$T.log; S=$D/mark-04-logrotate-global-$T.salida
{
  echo "## mark/04 v2 $(date -u +%FT%T.%3NZ) usuario=$(id -un) host=$(hostname)"
  echo "## logrotate: $(command -v logrotate) $(logrotate --version 2>&1 | head -1)"
  echo "## sha256 de la configuración evaluada"
  sha256sum /etc/logrotate.conf /etc/logrotate.d/* 2>&1
} > "$L"
if ! command -v logrotate >/dev/null; then echo "## RESULTADO: NO EJECUTADO (logrotate ausente)" | tee -a "$L"; exit 2; fi
if ! sudo -v; then echo "## RESULTADO: NO EJECUTADO (sudo rechazado)" | tee -a "$L"; exit 2; fi
sudo logrotate -d /etc/logrotate.conf > "$S" 2>&1
rc=$?
nerr=$(grep -ciE '(^|[[:space:]])error:' "$S")
nwarn=$(grep -ciE '(^|[[:space:]])warning:' "$S")
{
  echo "## salida completa de 'sudo logrotate -d /etc/logrotate.conf' ($(wc -l < "$S") líneas, sha256 $(sha256sum "$S" | cut -c1-64))"
  cat "$S"
  echo "## rc_logrotate=$rc"
  echo "## lineas_error=$nerr"; grep -iE '(^|[[:space:]])error:' "$S" | sed 's/^/   /'
  echo "## lineas_warning=$nwarn (se informan; no cierran ni bloquean por sí solas)"; grep -iE '(^|[[:space:]])warning:' "$S" | sed 's/^/   /'
} >> "$L"
if [ "$rc" -eq 0 ] && [ "$nerr" -eq 0 ]; then res=OK; code=0; else res=FALLO; code=1; fi
echo "## RESULTADO: $res (rc_logrotate=$rc, errores=$nerr, warnings=$nwarn) $(date -u +%FT%T.%3NZ)" >> "$L"
sha256sum "$L" "$S"
grep -E '^## (rc_logrotate|lineas_error|lineas_warning|RESULTADO)' "$L"
exit $code
