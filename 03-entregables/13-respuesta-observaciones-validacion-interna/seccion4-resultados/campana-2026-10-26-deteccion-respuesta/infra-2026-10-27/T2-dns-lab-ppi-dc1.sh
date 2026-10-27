#!/bin/bash
# T2 - Zona DNS local lab-ppi en DC1 (10.10.10.20) para contener *.lab-ppi dentro del lab.
# EJECUTA: en DC1 como dcadmin. El Claude de infra tiene LECTURA pero el clasificador le
#          bloquea los cambios de DNS -> lo aplicas tu.
# ESTADO PREVIO (medido 2026-10-27): zona lab-ppi NO existe; forwarder global = 10.10.10.1.
# IMPORTANTE: NO tocar el forwarder global. La zona local autoritativa ya gana sobre el
#             reenvio para *.lab-ppi; retirar el forwarder romperia la resolucion externa.
set -e
sudo samba-tool dns zonecreate 127.0.0.1 lab-ppi -P
sudo samba-tool dns add 127.0.0.1 lab-ppi '*' A 10.10.30.10 -P
echo "== verificacion local (debe devolver 10.10.30.10) =="
dig @10.10.10.20 probe-$(date +%s).lab-ppi +short

# ---- REVERSION ----
# sudo samba-tool dns zonedelete 127.0.0.1 lab-ppi -P
