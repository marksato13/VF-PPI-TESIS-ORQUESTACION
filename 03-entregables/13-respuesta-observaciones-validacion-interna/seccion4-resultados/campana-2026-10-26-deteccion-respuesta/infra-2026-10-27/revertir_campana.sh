#!/bin/bash
# Reversion de los cambios de la campana A en la infra de Franco's (A, B, DC1).
# Se ejecuta DESDE EL BASTION (tiene clave a A, B y DC1).
# ¡NO ejecutar hasta que la campana haya TERMINADO! Quita la regla :18081 (A y B)
# y la zona DNS lab-ppi (DC1); si la campana no ha corrido, la ROMPE.
if [ "$1" != "CONFIRMAR" ]; then
  echo "GUARDA: esto REVIERTE A, B y DC1 y rompe la campana si aun no termino."
  echo "  - pfSense-A y B: quita la regla pass :18081 (lab_b4_vlan20_18081.php quitar)"
  echo "  - DC1: borra la zona DNS lab-ppi"
  echo "Cuando la campana haya CERRADO, ejecuta:  bash /tmp/revertir_campana.sh CONFIRMAR"
  exit 0
fi
echo "=== pfSense-A: quitar regla T3 :18081 ==="
ssh -o BatchMode=yes root@10.10.10.2 "php -f /tmp/lab_b4_vlan20_18081.php quitar"
echo "=== pfSense-B: quitar regla T3 :18081 ==="
ssh -o BatchMode=yes root@10.10.10.3 "php -f /tmp/lab_b4_vlan20_18081.php quitar"
echo "=== DC1: borrar zona lab-ppi ==="
ssh -o BatchMode=yes dcadmin@10.10.10.20 "sudo samba-tool dns zonedelete 127.0.0.1 lab-ppi -P"
echo
echo "OPCIONAL (GUI, no incluido aqui): quitar en pfSense-A la regla 'Easy Rule' NTP"
echo "  10.10.60.11 -> 10.10.60.1:123 en Firewall > Rules > VLAN60."
echo "  O dejarla documentada: es sincronizacion horaria legitima del sensor."
echo "=== REVERSION HECHA. Avisa a infra para verificar A/B/DC1. ==="
