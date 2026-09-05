#!/usr/bin/env bash
# Copias cifradas. El plan exige algo mas que hacer backup: probar la
# restauracion. Ver stack/bin/ppi-restore-test.
. "$(dirname "$0")/comun.sh"
exige_root
paso "Restic y age"
apt-get update -qq
apt_faltantes restic age
verde "Restic listo."
echo "  configura el destino en stack/.env (no versionado) antes de usar ppi-backup"
