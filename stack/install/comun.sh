# Utilidades compartidas por los instaladores. No se ejecuta suelto.
set -euo pipefail
rojo(){ printf '\033[31m%s\033[0m\n' "$*"; }
verde(){ printf '\033[32m%s\033[0m\n' "$*"; }
aviso(){ printf '\033[33m%s\033[0m\n' "$*"; }
paso(){ printf '\n\033[1m── %s\033[0m\n' "$*"; }

exige_root(){
  [ "$(id -u)" -eq 0 ] || { rojo "Este script necesita root. Ejecuta:  sudo $0"; exit 1; }
}

# Instala solo lo que falte. Repetir el script no reinstala ni rompe nada.
apt_faltantes(){
  local faltan=()
  for p in "$@"; do
    dpkg -s "$p" >/dev/null 2>&1 || faltan+=("$p")
  done
  if [ ${#faltan[@]} -eq 0 ]; then
    verde "  ya instalado: $*"
    return 0
  fi
  echo "  faltan: ${faltan[*]}"
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${faltan[@]}"
}

# El usuario real, no root. Con sudo llega en SUDO_USER; con pkexec solo
# llega el UID en PKEXEC_UID y USER vale "root". Sin este caso, un
# `usermod -aG docker` anhadiria root al grupo en vez del usuario: inutil y
# ademas un permiso de mas.
usuario_real(){
  if [ -n "${SUDO_USER:-}" ]; then echo "$SUDO_USER"
  elif [ -n "${PKEXEC_UID:-}" ]; then id -nu "$PKEXEC_UID"
  else echo "${USER:-root}"; fi
}
