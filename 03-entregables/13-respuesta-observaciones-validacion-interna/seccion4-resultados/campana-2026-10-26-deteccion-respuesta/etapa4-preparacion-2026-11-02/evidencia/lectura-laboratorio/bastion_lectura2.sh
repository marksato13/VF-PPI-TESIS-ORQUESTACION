#!/usr/bin/env bash
# Segunda tanda: guion del rele (enmascarado), srv-dmz (fechas del agente), cliente (perfiles) y Kali (solo estado). Sin sudo.
set +e
echo "== rele: guion (enmascarado)"; sed -E 's/(([A-Za-z_]*(KEY|TOKEN|PASS|SECRET)[A-Za-z_]*)=)[^ "]*/\1***/Ig' ~/relay-feed.sh
ls -la ~/relay; stat -c '%y %n' ~/relay/feed.json
ls -la ~/.ssh | awk '{print $1, $3, $NF}'
echo; echo "== srvdmz: fechas"
ssh -o BatchMode=yes srvdmz 'stat -c "%y %s %n" ~/enforce/* ~/enforce/*/* 2>/dev/null | head -20; systemctl show ppi-enforce-agent.timer -p UnitFileState -p ActiveState -p LastTriggerUSec -p InactiveEnterTimestamp | cat; systemctl show ppi-brute-lab -p UnitFileState -p ActiveState -p InactiveEnterTimestamp | cat; cat ~/ppi-enforce-agent.service | grep -vE "^\s*#"; ls -la /usr/local/sbin | grep -i cf; ls /etc/cyberflow /opt/cyberflow 2>&1 | head; getent passwd cffeed cfagente; echo fin'
echo; echo "== cliente (admin 10.10.20.20): perfiles"
ssh -o BatchMode=yes -o ConnectTimeout=8 admin 'hostname; date -u +%FT%TZ; uptime; systemctl list-units --all --no-legend --plain "cyberflow*" "perfil*" "ppi-*" | cat; systemctl list-unit-files --no-legend "cyberflow*" | cat; systemctl show cyberflow-lab.target -p ActiveState -p UnitFileState -p ActiveEnterTimestamp -p Wants | cat; timedatectl | grep -E "Time zone|synchronized|Universal"'
echo; echo "== kali: solo estado"
ssh -o BatchMode=yes -o ConnectTimeout=6 kali 'hostname; uptime; pgrep -a -f "nmap|hydra|dnsperf|hping|gobuster|ab |wrk|curl" | head -5; echo fin' 2>&1
