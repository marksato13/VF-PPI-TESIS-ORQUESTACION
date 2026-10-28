#!/usr/bin/env bash
# PREP 26 — bastion: trae (solo lectura) acumular_v3.py del sensor y el codigo de los perfiles de clientes.
set -u
cd ~/cf-prep-sensor
scp -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cyberflow/scripts/features/acumular_v3.py . </dev/null
scp -q -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20:laboratorio/clientes_config.py adminclientes@10.10.20.20:laboratorio/clientes_lab.py . </dev/null
sha256sum acumular_v3.py clientes_config.py clientes_lab.py
ssh -n -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'timedatectl | grep -E "Time zone|Local time"'
