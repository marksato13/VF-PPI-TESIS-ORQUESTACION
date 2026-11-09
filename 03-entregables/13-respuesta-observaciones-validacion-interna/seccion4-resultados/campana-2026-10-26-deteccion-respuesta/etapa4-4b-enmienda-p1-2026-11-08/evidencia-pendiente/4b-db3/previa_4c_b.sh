#!/usr/bin/env bash
# SOLO LECTURA. Repetición corregida de las lecturas dudosas de la verificación previa de la 4C.
cd "$HOME" || exit 2
ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'echo "## $(date -u +%FT%TZ)"
echo "== BASTION procesos reales (sin autocoincidencia):"
echo "   k20 canal: $(pgrep -f "[k]20_canal_control" | wc -l) | vigilancia b01: $(pgrep -af "[v]igilancia|[b]01_" | cut -c1-110)"
tail -1 ~/cf-e4/4b/vigilancia.log | cut -c1-120
echo "== KALI procesos reales:"
ssh -o BatchMode=yes -o ConnectTimeout=10 kali "ps -eo pid,etimes,args | grep -E \"[n]map|[h]ydra|[g]enerar_campana|[m]edusa\" | cut -c1-120; echo \"conteo=\$(ps -eo args | grep -cE \"[n]map|[h]ydra|[g]enerar_campana|[m]edusa\")\"" 2>&1
echo "== CLIENTES (desde el bastion):"
ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 "echo target=\$(systemctl is-active cyberflow-lab.target); systemctl is-active cyberflow-lab-ofimatica cyberflow-lab-navegacion cyberflow-lab-descargas cyberflow-lab-aplicacion cyberflow-lab-ligero cyberflow-lab-erratico | tr \"\n\" \" \"" 2>&1
echo
ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "bash -s" <<"EOS"
SC=$HOME/cyberflow-e4/herramientas-20261106/salud_captura.py
echo "== I5 por EVE (ventana 30 min; incluye eve.json y el rotado .1 por si la rotacion cae en la ventana):"
python3 $SC i5 --eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json.1 > /tmp/i5.$$ 2>&1; rc=$?
python3 -c "
import json
j=json.load(open('/tmp/i5.$$'))
print({k:v for k,v in j.items() if not isinstance(v,(list,dict))})" 2>&1 | cut -c1-400
echo "   rc de salud_captura i5 = $rc (0 cumple, 1 no cumple, 2 no demostrable)"; rm -f /tmp/i5.$$
ls -la /var/log/suricata/eve.json* | awk '{print "   "$5, $9}' | head -4
EOS' 2>&1
