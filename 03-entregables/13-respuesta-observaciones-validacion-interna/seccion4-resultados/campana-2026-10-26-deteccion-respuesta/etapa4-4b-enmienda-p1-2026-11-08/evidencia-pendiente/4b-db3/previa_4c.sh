#!/usr/bin/env bash
# [LAPTOP Git Bash -> BASTION gadmin -> SENSOR1 m4rk / SRV-DMZ / KALI] SOLO LECTURA. Verificación PREVIA de la Campaña A (4C). No lanza nada ni escribe en los hosts.
cd "$HOME" || exit 2
K=~/.ssh/id_ed25519; BA=gadmin@10.10.10.30
echo "## $(date -u +%FT%TZ)"
ssh -o BatchMode=yes -o ConnectTimeout=15 -i $K $BA 'echo "== BASTION: $(hostname)"; bash ~/cf-e4/paquete-a1cea5e/deploy/etapa4/bastion/verificar_bastion.sh 2>&1 | grep -E "^(FALLO|AVISO)|VERIFICACI" | tail -4
echo "== relojes: $(bash ~/cf-e4/p10b_relojes.sh 2>&1 | grep -E "desfase" | sed -E "s/.*\] ([a-z-]+) +mejor desfase=([^ ]+).*\|desfase\|<=1 s: ([A-Z]+).*/\1 \2 \3/" | tr "\n" ";")"
echo "== canal k20 de la 4B: $(pgrep -fc k20_canal) procesos (debe ser 0); vigilancia b01 viva: $(pgrep -fc vigilancia | head -1)"
echo "== Kali (solo lectura): procesos de ataque/carga"
ssh -o BatchMode=yes -o ConnectTimeout=10 kali "echo \"hostname=\$(hostname) NTP=\$(timedatectl show -p NTPSynchronized --value)\"; echo \"nmap/hydra/generadores: \$(pgrep -fc \"nmap|hydra|generar_campana|medusa\") ; permisos continuar: \$(ls ~/cf-campana-A/permisos 2>/dev/null | wc -l)\"; ls ~/cf-campana-A 2>&1 | head -8" 2>&1
echo "== SRV-DMZ sin sudo: ppi-brute-lab=$(ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 "systemctl is-active ppi-brute-lab; systemctl is-enabled ppi-brute-lab" 2>&1 | tr "\n" "/")"
ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "bash -s" <<"EOS"
SC=$HOME/cyberflow-e4/herramientas-20261106/salud_captura.py; N=$(date +%s)
echo "== SENSOR1: servicios: motor=$(systemctl is-active ppi-motor) NR=$(systemctl show -p NRestarts --value ppi-motor) cap=$(systemctl is-active ppi-motor-capture) via=$(systemctl is-active ppi-via-rapida@ens37) feed2=$(systemctl is-active ppi-publicar-feed-v2) suricata=$(systemctl is-active suricata) stats.timer=$(systemctl is-active cf-tcpdump-estadisticas.timer)"
echo "   --enforce en argv del motor: [$(tr "\0" " " < /proc/$(systemctl show -p MainPID --value ppi-motor)/cmdline | grep -o -- --enforce)]"
echo "   logrotate.timer=$(systemctl is-active logrotate.timer) | list-timers: $(systemctl list-timers logrotate.timer --no-pager 2>/dev/null | sed -n 2p | cut -c1-100)"
echo "   eve.json: inodo $(stat -c %i /var/log/suricata/eve.json), $(stat -c %s /var/log/suricata/eve.json) B, modif $(stat -c %y /var/log/suricata/eve.json | cut -c1-19)"
echo "   I5 (0 kernel_drops en 30 min, por EVE):"; python3 $SC i5 --eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json.1 2>&1 | python3 -c "import sys,json;t=sys.stdin.read()
try:
    j=json.loads(t); print('     ',{k:j[k] for k in j if not isinstance(j[k],(list,dict))})
except Exception: print('     ',t[:300])"
echo "   (rc de i5 = $? solo del ultimo pipe; 0 cumple, 1 no cumple, 2 no demostrable)"
echo "   disco: $(df -h /home | tail -1 | awk "{print \$4\" libres (\"\$5\" usado)\"}"); 4B archivo-pcap: $(du -sh $HOME/cf-e4/4b/archivo-pcap 2>/dev/null | cut -f1)"
echo "   archivador/muestreadores vivos de la 4B (deben ser 0): $(pgrep -fc "archivador|muestrear|muestreo")"
echo "   carpeta cf-e4/4c existe? $([ -e $HOME/cf-e4/4c ] && echo SI-s10-4c-abortaria || echo no)"
echo "   estado de los clientes: target=$(ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 "systemctl is-active cyberflow-lab.target" 2>&1 | head -1) (el 4c los pone a factor 1,0 con k01)"
EOS' 2>&1
