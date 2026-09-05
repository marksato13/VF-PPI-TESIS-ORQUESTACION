#!/usr/bin/env bash
# Docker desde los repositorios de Ubuntu 26.04 (docker.io 29.x + compose v2).
# No se anhade repositorio de terceros: menos superficie y menos mantenimiento.
. "$(dirname "$0")/comun.sh"
exige_root
paso "Docker y Compose v2"
apt-get update -qq
apt_faltantes docker.io docker-compose-v2
systemctl enable --now docker
u="$(usuario_real)"
if id -nG "$u" | tr ' ' '\n' | grep -qx docker; then
  verde "  $u ya esta en el grupo docker"
else
  usermod -aG docker "$u"
  aviso "  $u anhadido al grupo docker."
  aviso "  Cierra sesion y vuelve a entrar, o ejecuta:  newgrp docker"
fi
docker --version && docker compose version
verde "Docker listo."
