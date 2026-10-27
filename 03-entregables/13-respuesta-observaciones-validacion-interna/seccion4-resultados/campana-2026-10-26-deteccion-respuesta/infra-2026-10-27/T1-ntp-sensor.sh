#!/bin/bash
# T1 - NTP del sensor CyberFlow (10.10.60.11). RESUELTO 2026-10-27. |offset| -47.8 s -> 0.18 s.
#
# HALLAZGO: reiniciar systemd-timesyncd (lo que pedia la orden) NO bastaba. Habia dos fallos
# encadenados, y ninguno es "esperar mas":
#   1) El servidor NTP configurado era 10.10.10.30 (el bastion), que NO sirve NTP y ademas es
#      inalcanzable desde la VLAN 60 -> Packet count: 0, nunca sincroniza.
#   2) Al corregir la fuente al gateway (10.10.60.1, que SI sirve NTP via pfSense), faltaba la
#      regla de firewall VLAN60 -> gateway en 123/udp: el unico permiso del sensor al gateway
#      era ICMP (por eso el ping pasaba y el NTP no).
#
# Acceso: m4rk@10.10.60.11 con clave cyberflow-to-sensor (sudo pide contrasena -> pasos de operador).

# --- PASO 1  [SENSOR m4rk, sudo]  (hecho) : apuntar el NTP al gateway ---
sudo sed -i.bak-ntp 's/^NTP=.*/NTP=10.10.60.1/' /etc/systemd/timesyncd.conf
#   reversion: sudo mv /etc/systemd/timesyncd.conf.bak-ntp /etc/systemd/timesyncd.conf

# --- PASO 2  [pfSense-A root, operador]  (hecho) : permitir 123/udp sensor -> gateway ---
#   easyrule pass opt8 udp 10.10.60.11 10.10.60.1 123
#   (opt8 = VLAN60. Regla persistente "Passed via EasyRule"; se revierte borrandola en
#    Firewall > Rules > VLAN60.)

# --- PASO 3  [SENSOR m4rk, sudo]  (hecho) : forzar sondeo ---
sudo systemctl restart systemd-timesyncd
sleep 6
timedatectl timesync-status | grep -iE 'Server|Packet'
timedatectl | grep -i synchronized

# --- EVIDENCIA medida (offset sensor - bastion, 3 muestras) ---
#   ANTES : -47.798 / -47.795 / -47.803 s   (synchronized: no, Packet count 0)
#   DESPUES: 0.172 / 0.181 / 0.177 s         (synchronized: yes, Packet count 1, Server 10.10.60.1)
