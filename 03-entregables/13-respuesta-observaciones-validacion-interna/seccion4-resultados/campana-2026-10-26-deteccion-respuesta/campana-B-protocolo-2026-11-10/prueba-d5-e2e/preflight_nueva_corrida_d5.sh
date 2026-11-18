#!/bin/bash
# PREFLIGHT de la nueva corrida con D5 a fin de episodio + 75 s (SOLO LECTURA; como gadmin en el bastión). NO lanza nada.
# Cada compuerta da OK / FALLA / PENDIENTE (PENDIENTE = falta una instalación o decisión que aún no se autorizó). rc 0 solo si no hay FALLA ni PENDIENTE.
set -u
ok=0; fa=0; pe=0
G(){ case "$2" in 1) echo "OK        $1"; ok=$((ok+1));; 0) echo "FALLA     $1"; fa=$((fa+1));; *) echo "PENDIENTE $1"; pe=$((pe+1));; esac; }
SN(){ timeout 40 ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11 "$@" 2>&1; }
H(){ h=$1; shift; timeout 40 ssh -n -o BatchMode=yes -o ConnectTimeout=8 $h "$@" 2>&1; }
echo "##### preflight nueva corrida D5 (espera de fin = 75 s) $(date -u +%FT%TZ)"

echo "=== 1. D5 activo y aceptado en el Sensor1"
U=ppi-publicar-feed-v2.service
CL=$(SN "tr '\0' ' ' < /proc/\$(systemctl show $U -p MainPID --value)/cmdline")
G "publicador en marcha con --control-d5 --d5-origen 10.10.20.30 --d5-auditoria" $(case "$CL" in *"--control-d5 /home/m4rk/feed-v2/d5/control/control.json"*"--d5-origen 10.10.20.30"*"--d5-auditoria"*) echo 1;; *) echo 0;; esac)
G "publicador: sin --aplicar, política if_senal (sombra del publicador)" $(case "$CL" in *"--politica if_senal"*) echo 1;; *) echo 0;; esac)
echo "   PID/NRestarts/inicio: $(SN "systemctl show $U -p MainPID -p NRestarts -p ActiveEnterTimestamp | paste -sd' '")"
G "prueba E2E de D5 registrada (acuse + auditoría con el mismo id)" $(SN 'grep -c "\"evento\": \"publicado\"" ~/feed-v2/d5/auditoria/d5-auditoria.jsonl' | grep -qx '[1-9][0-9]*' && echo 1 || echo 0)
G "sin control, ni solicitudes pendientes (control.json ausente)" $(SN '[ ! -e ~/feed-v2/d5/control/control.json ] && echo 1 || echo 0')

echo "=== 2. srv-dmz en sombra, sin generadores ni campaña"
SD=$(H srvdmz "systemctl show ppi-enforce-agent-v2-dmz -p MainPID -p NRestarts --value | paste -sd/; systemctl show ppi-enforce-agent-v2-dmz -p ExecStart --value | grep -c -- --aplicar; systemctl is-active ppi-brute-lab" | paste -sd' ')
echo "   agente (PID/NR, nº --aplicar), brute-lab: $SD"
G "agente de srv-dmz sin --aplicar" $(echo "$SD" | awk '{print ($2==0)?1:0}')
G "ppi-brute-lab inactivo" $(echo "$SD" | grep -q 'inactive' && echo 1 || echo 0)
KP=$(H kali "ps -eo args | grep -cE '[g]enerar_campana|[h]ydra|[i]nundacion|[n]map'")
G "Kali sin generadores ($KP)" $([ "$KP" = 0 ] && echo 1 || echo 0)
BP=$(ps -eo args | grep -v 'bash -c' | grep -cE '[o]rquestar_b|[c]ompuerta_b|[v]igia_4c|[l]anzador_puerta')
G "bastión sin orquestador, compuerta, vigía ni lanzador ($BP)" $([ "$BP" = 0 ] && echo 1 || echo 0)
G "sin carpeta ~/cf-e4/4c viva en el bastión" $([ ! -e ~/cf-e4/4c ] && echo 1 || echo 0)

echo "=== 3. relojes (|desfase| <= 1 s respecto del bastión; u = RTT/2 de la medición)"
CK=$(for h in sensor1 kali srvdmz clientes; do
  M=""
  for k in 1 2 3 4 5; do
    t0=$(date +%s.%N)
    if [ $h = sensor1 ]; then r=$(SN 'date +%s.%N'); else r=$(H $h 'date +%s.%N'); fi
    t1=$(date +%s.%N); M="$M $t0,$t1,$(echo "$r" | tail -1)"
  done
  python3 -I -c '
import sys
h=sys.argv[1]; best=None
for m in sys.argv[2:]:
    try: t0,t1,r=[float(x) for x in m.split(",")]
    except ValueError: continue
    rtt=t1-t0; off=r-(t0+t1)/2
    if best is None or rtt<best[0]: best=(rtt,off)
if best is None: print("   %-8s ILEGIBLE"%h); sys.exit(0)
rtt,off=best
print("   %-8s desfase %+.3f s  u=%.3f s (mejor de 5, RTT mínimo)  %s"%(h,off,rtt/2,"OK" if abs(off)+rtt/2<=1 else "FUERA"))' "$h" $M
done); echo "$CK"
G "los 4 hosts dentro de 1 s" $(echo "$CK" | grep -q 'FUERA\|ILEGIBLE' && echo 0 || echo 1)

echo "=== 4. herramientas del bastión para D5 sin reinicio (cf_d5_bastion.sh instalar)"
for f in transporte_bastion.py lanzador_puerta_banco.py hacer_d5_episodio_banco.py d5_episodio_banco.py; do
  G "bastión ~/cf-b/herramientas/$f" $([ -e ~/cf-b/herramientas/$f ] && echo 1 || echo 2); done
G "clave dedicada y known_hosts_d5 presentes" $([ -s ~/.ssh/cyberflow-d5-sensor ] && [ -s ~/.ssh/known_hosts_d5 ] && echo 1 || echo 0)

echo "=== 5. instrumentación de E3/E4 (cf_d5_instrumentacion.sh ... instalar)"
G "Kali: inundacion_instrumentada.sh instalado" $(H kali '[ -x ~/cf-b/instrumentacion/inundacion_instrumentada.sh ] && echo 1 || echo 2')
G "clientes: clientes_factor1_tx.py instalado" $(H clientes '[ -x ~/cf-b/instrumentacion/clientes_factor1_tx.py ] && echo 1 || echo 2')
G "srv-dmz: muestreador_set.py instalado" $(H srvdmz '[ -x ~/cf-b/instrumentacion/muestreador_set.py ] && echo 1 || echo 2')
G "srv-dmz: el muestreador puede ejecutar el helper nft con sudo -n (NOPASSWD)" $(H srvdmz 'sudo -n -l 2>&1 | grep -q cf-nft-helper && echo 1 || echo 2')

echo "=== 6. lanzador de la corrida"
G "g01 con la puerta nueva (lanzador_puerta_banco --espera-fin 75) preparado y ensayado" 2
echo "   (el criterio E3 fijado está en CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md; no es estado de host)"
echo "##### resumen: $ok OK, $fa FALLAN, $pe PENDIENTES"; [ $fa -eq 0 ] && [ $pe -eq 0 ]
