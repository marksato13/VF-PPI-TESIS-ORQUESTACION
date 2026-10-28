#!/usr/bin/env bash
# PREP 21 — bastion: distribuye las copias de HEAD (e6a676a) a srv-dmz (~/cf-campana/) y Kali (~/cf-campana-A/)
# por scp y verifica sha256 EN cada destino. No ejecuta nada de lo copiado.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
S="-i $HOME/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"; K="-i $HOME/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
echo "## p21  inicio=$(ts)"
ssh -n $S 'mkdir -p ~/cf-campana && ls -la ~/cf-campana' | sed 's/^/  srv antes: /'
scp -q -i ~/.ssh/cyberflow-to-srv ~/cf-prep-copias/srv/modo_sombra.sh ~/cf-prep-copias/srv/restaurar_enforcement.sh adminsrvdmz@10.10.30.10:cf-campana/ </dev/null
ssh -n $S 'chmod 750 ~/cf-campana/*.sh; cd ~/cf-campana && sha256sum modo_sombra.sh restaurar_enforcement.sh; ls -la' | sed 's/^/  srv: /'
ssh -n $K 'mkdir -p ~/cf-campana-A/scripts ~/cf-campana-A/escenarios && ls -laR ~/cf-campana-A | head -12' | sed 's/^/  kali antes: /'
scp -q -i ~/.ssh/cyberflow-to-atacante ~/cf-prep-copias/kali/scripts/generar_campana.py ~/cf-prep-copias/kali/scripts/esquema_campana.py adminatacante@10.10.20.30:cf-campana-A/scripts/ </dev/null
scp -q -i ~/.ssh/cyberflow-to-atacante ~/cf-prep-copias/kali/escenarios/escenarios.json adminatacante@10.10.20.30:cf-campana-A/escenarios/ </dev/null
ssh -n $K 'cd ~/cf-campana-A && sha256sum scripts/generar_campana.py scripts/esquema_campana.py escenarios/escenarios.json' | sed 's/^/  kali: /'
echo "## fin=$(ts)"
