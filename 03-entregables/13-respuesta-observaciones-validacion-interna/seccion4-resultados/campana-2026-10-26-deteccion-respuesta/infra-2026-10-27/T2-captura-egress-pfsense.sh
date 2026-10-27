#!/bin/bash
# Evidencia T2 - captura de egress 53/udp en el borde (pfSense-A, WAN = vmx1) durante una
# consulta *.lab-ppi. EJECUTA desde el bastion (10.10.10.30). Solo lectura (captura de paquetes).
ssh -o BatchMode=yes root@10.10.10.2 'tcpdump -ni vmx1 -l udp port 53 >/tmp/t2_cap.txt 2>&1 & sleep 1; echo lanzado'
P="probe-$(date +%s)"
echo "PROBE=$P.lab-ppi"
dig @10.10.10.20 "$P.lab-ppi" +short 2>&1 || true
sleep 3
ssh -o BatchMode=yes root@10.10.10.2 'pkill -f "tcpdump -ni vmx1" 2>/dev/null; echo === lineas_con_lab-ppi ===; grep -i lab-ppi /tmp/t2_cap.txt; echo === total_udp53 ===; wc -l </tmp/t2_cap.txt'

# LINEA BASE 2026-10-27 (ANTES de crear la zona), medida por el Claude de infra:
#   172.17.25.83.17325 > 192.58.128.30.53: 24896% [1au] A? lab-ppi. (36)
#   (192.58.128.30 = j.root-servers.net -> la consulta SALIO a Internet)
# Tras crear la zona lab-ppi en DC1, "lineas_con_lab-ppi" debe ser 0.
