#!/usr/bin/env bash
# Base: herramientas comunes. Sin esto no corre nada mas.
. "$(dirname "$0")/comun.sh"
exige_root
paso "Base del sistema"
apt-get update -qq
apt_faltantes git curl ca-certificates jq python3-venv python3-pip pipx sqlite3
verde "Base lista."
