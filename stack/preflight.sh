#!/usr/bin/env bash
# Comprobaciones ANTES de instalar. No necesita root y no modifica nada.
. "$(dirname "$0")/install/comun.sh"
cd "$(dirname "$0")/.."

fallos=0; avisos=0
paso "Recursos"
cpu=$(nproc); ram=$(free -g | awk '/Mem:/{print $2}')
disco=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
printf "  %-22s %s\n" "vCPU" "$cpu"; printf "  %-22s %s GB\n" "RAM" "$ram"
printf "  %-22s %s GB libres en /\n" "disco" "$disco"
[ "$cpu" -lt 4 ]   && { aviso "  menos de 4 vCPU"; avisos=$((avisos+1)); }
[ "$ram" -lt 8 ]   && { rojo  "  menos de 8 GB de RAM: Docker + Postgres iran justos"; fallos=$((fallos+1)); }
[ "$disco" -lt 20 ] && { rojo "  menos de 20 GB libres: LaTeX solo ocupa ~2 GB"; fallos=$((fallos+1)); }

paso "Red"
for h in archive.ubuntu.com download.docker.com github.com; do
  if getent hosts "$h" >/dev/null 2>&1; then verde "  DNS resuelve $h"
  else rojo "  DNS NO resuelve $h"; fallos=$((fallos+1)); fi
done

paso "Requisitos que ya estan"
for c in git python3; do
  if command -v "$c" >/dev/null; then verde "  $c"; else rojo "  falta $c"; fallos=$((fallos+1)); fi
done
# El indice usa el modulo sqlite3 de Python, no el binario. El binario solo
# sirve para inspeccionar la base a mano: util, pero no bloquea.
python3 -c 'import sqlite3' 2>/dev/null \
  && verde "  modulo sqlite3 de python" \
  || { rojo "  falta el modulo sqlite3 de python"; fallos=$((fallos+1)); }
command -v sqlite3 >/dev/null \
  && verde "  cliente sqlite3 (opcional)" \
  || { aviso "  sin cliente sqlite3 (opcional: solo para inspeccion manual)"; avisos=$((avisos+1)); }
python3 - <<'PY' || exit 1
import sys
v = sys.version_info
print(f"  python {v.major}.{v.minor}.{v.micro}", "OK" if v >= (3, 9) else "DEMASIADO ANTIGUO")
sys.exit(0 if v >= (3, 9) else 1)
PY

paso "El nucleo funciona sin instalar nada"
if ./stack/bin/ppi-trace ingest >/dev/null 2>&1 && ./stack/bin/ppi-trace check >/dev/null 2>&1; then
  verde "  ppi-trace indexa y verifica"
else
  aviso "  ppi-trace reporta inconsistencias: revisa con  stack/bin/ppi-trace check"
  avisos=$((avisos+1))
fi
./stack/bin/ppi-secrets --todo >/dev/null 2>&1 \
  && verde "  ppi-secrets: sin secretos" \
  || { rojo "  ppi-secrets ENCONTRO secretos"; fallos=$((fallos+1)); }

echo
if [ "$fallos" -eq 0 ]; then
  verde "Preflight OK${avisos:+ (con $avisos aviso/s)}. Puedes instalar:  sudo stack/install.sh"
else
  rojo "Preflight con $fallos fallo(s). Resuelvelos antes de instalar."
fi
exit "$fallos"
