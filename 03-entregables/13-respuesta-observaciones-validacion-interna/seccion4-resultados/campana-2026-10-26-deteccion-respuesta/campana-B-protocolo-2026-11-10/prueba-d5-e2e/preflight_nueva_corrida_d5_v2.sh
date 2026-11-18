#!/bin/bash
# PREFLIGHT v2 de la nueva corrida con D5 (fin de episodio + 75 s) — SOLO LECTURA; como gadmin en el bastión. NO lanza nada.
# Cada compuerta: OK / FALLA / PENDIENTE (PENDIENTE = falta una medición o decisión que aún no se autorizó). rc 0 solo sin FALLA ni PENDIENTE.
# v2 (11-nov): distingue la solicitud ACTIVA de los registros históricos por ID y estado; comprueba la instalación del bastión y de la instrumentación, el generador
# instrumentado de la Kali (hashes), g01c, la auditoría (m4rk:m4rk, rotate 30) y marca como PENDIENTES la medición de la puerta y la observación de logrotate.
set -u
ok=0; fa=0; pe=0
G(){ case "$2" in 1) echo "OK        $1"; ok=$((ok+1));; 0) echo "FALLA     $1"; fa=$((fa+1));; *) echo "PENDIENTE $1"; pe=$((pe+1));; esac; }
SN(){ timeout 40 ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11 "$@" 2>&1; }
S1(){ timeout 30 ssh -n -i ~/.ssh/cyberflow-d5-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null -o IdentitiesOnly=yes m4rk@10.10.60.11 "$@" 2>&1; }
H(){ h=$1; shift; timeout 40 ssh -n -o BatchMode=yes -o ConnectTimeout=8 $h "$@" 2>&1; }
J(){ python3 -I -c "import json,sys;d=json.loads(sys.argv[1]);print(d.get(sys.argv[2]))" "$1" "$2" 2>/dev/null; }
echo "##### preflight v2 nueva corrida D5 (espera de fin = 75 s) $(date -u +%FT%TZ)"

echo "=== 1. D5 activo en el Sensor1 y SOLICITUD ACTIVA vs HISTÓRICOS (por id y estado)"
U=ppi-publicar-feed-v2.service
CL=$(SN "tr '\0' ' ' < /proc/\$(systemctl show $U -p MainPID --value)/cmdline")
G "publicador con --control-d5 --d5-origen 10.10.20.30 --d5-auditoria" $(case "$CL" in *"--control-d5 /home/m4rk/feed-v2/d5/control/control.json"*"--d5-origen 10.10.20.30"*"--d5-auditoria"*) echo 1;; *) echo 0;; esac)
G "publicador sin --aplicar, política if_senal" $(case "$CL" in *"--politica if_senal"*) echo 1;; *) echo 0;; esac)
echo "   PID/NRestarts/inicio: $(SN "systemctl show $U -p MainPID -p NRestarts -p ActiveEnterTimestamp | paste -sd' '")"
G "control.json AUSENTE (no hay solicitud pendiente de consumir)" $(SN '[ ! -e ~/feed-v2/d5/control/control.json ] && echo 1 || echo 0')
ACT=0; HIS=0
for id in $(SN 'ls ~/feed-v2/d5/control/solicitudes 2>/dev/null' | sed 's/\.json$//' | grep -E '^[0-9a-f]{32}$'); do
  R=$(S1 "resultado --id $id"); E=$(J "$R" estado)
  case "$E" in acuse|rechazado) HIS=$((HIS+1)); echo "   solicitud $id -> $E (secuencia $(J "$R" secuencia)): HISTÓRICA";;
               *) ACT=$((ACT+1)); echo "   solicitud $id -> $E: ACTIVA/INCIERTA  $R";; esac; done
G "solicitudes ACTIVAS o inciertas = $ACT (históricas con acuse = $HIS: la prueba D5 del 11-nov)" $([ $ACT = 0 ] && echo 1 || echo 0)
G "ningún bloqueo de puerta ni pendiente de la puerta en el bastión (puerta-bloqueo.json ausente en ~/cf-e4/4c)" $([ ! -e ~/cf-e4/4c/compuerta/puerta-bloqueo.json ] && echo 1 || echo 0)

echo "=== 2. auditoría D5 en la ruta instalada (m4rk:m4rk, rotate 30)"
AU=$(SN 'stat -c "%U:%G %a" ~/feed-v2/d5/auditoria/d5-auditoria.jsonl; stat -c "%U:%G %a" ~/feed-v2/d5/auditoria')
echo "   fichero / directorio: $(echo "$AU" | paste -sd' ')"
G "auditoría y directorio con propietario m4rk:m4rk" $(echo "$AU" | awk '{n+=($1=="m4rk:m4rk")} END{print (n==2)?1:0}')
LR=$(SN 'cat /etc/logrotate.d/cf-d5-auditoria 2>&1; sha256sum /etc/logrotate.d/cf-d5-auditoria | cut -c1-64')
G "logrotate: ruta /home/m4rk/feed-v2/d5/auditoria/d5-auditoria.jsonl, su m4rk m4rk, rotate 30, sha 445efe82…" $(echo "$LR" | grep -q 'd5-auditoria.jsonl' && echo "$LR" | grep -q 'su m4rk m4rk' && echo "$LR" | grep -q 'rotate 30' && echo "$LR" | grep -q '^445efe82897bc7d7ffa78a8d0560c1cf75db91bc59062a155f688c79f0997b4b' && echo 1 || echo 0)
echo "   timer logrotate: $(SN 'systemctl list-timers logrotate.timer --no-pager --plain | sed -n 2p' | cut -c1-120)"
G "ejecución DIARIA real de logrotate sobre la auditoría (observada con una rotación; el fichero aún no se rotó)" 2

echo "=== 3. srv-dmz en sombra, sin generadores ni campaña"
SD=$(H srvdmz "systemctl show ppi-enforce-agent-v2-dmz -p MainPID -p NRestarts --value | paste -sd/; systemctl show ppi-enforce-agent-v2-dmz -p ExecStart --value | grep -c -- --aplicar; systemctl is-active ppi-brute-lab" | paste -sd' ')
echo "   agente (PID/NR, nº --aplicar), brute-lab: $SD"
G "agente de srv-dmz sin --aplicar" $(echo "$SD" | awk '{print ($2==0)?1:0}')
G "ppi-brute-lab inactivo" $(echo "$SD" | grep -q 'inactive' && echo 1 || echo 0)
ST=$(H srvdmz "python3 -I -c \"import sys;sys.dont_write_bytecode=True;sys.path.insert(0,'/home/adminsrvdmz/cf-b/instrumentacion');import muestreador_set as m;print(m.listar(['sudo','-n','/usr/local/sbin/cf-nft-helper']))\"")
echo "   lectura real del muestreador: $ST"
G "muestreador de srv-dmz: lectura real de los sets OK y sets vacíos (sin sudo adicional de Mark)" $(echo "$ST" | grep -q "'ok': True" && echo "$ST" | grep -q "'bloqueados': {}" && echo "$ST" | grep -q "'limitados': {}" && echo 1 || echo 0)
KP=$(H kali "ps -eo args | grep -v 'bash -c' | grep -cE '[g]enerar_campana|[h]ydra|[i]nundacion|[n]map'")
G "Kali sin generadores ($KP)" $([ "$KP" = 0 ] && echo 1 || echo 0)
BP=$(ps -eo args | grep -v 'bash -c' | grep -cE '[o]rquestar_b|[c]ompuerta_b|[v]igia_4c|[l]anzador_puerta')
G "bastión sin orquestador, compuerta, vigía ni lanzador ($BP)" $([ "$BP" = 0 ] && echo 1 || echo 0)
G "sin carpeta ~/cf-e4/4c viva en el bastión" $([ ! -e ~/cf-e4/4c ] && echo 1 || echo 0)

echo "=== 4. relojes (|desfase| + u <= 1 s respecto del bastión; mejor de 5 por RTT mínimo)"
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
print("   %-8s desfase %+.3f s  u=%.3f s  %s"%(h,off,rtt/2,"OK" if abs(off)+rtt/2<=1 else "FUERA"))' "$h" $M
done); echo "$CK"
G "los 4 hosts dentro de 1 s" $(echo "$CK" | grep -q 'FUERA\|ILEGIBLE' && echo 0 || echo 1)

echo "=== 5. instalación en el bastión (hash = paquete)"
HB=$HOME/cf-b/herramientas
G "bastión: transporte, lanzador, hacer_d5 y d5_episodio_banco = 2dc8d7eb… c2ec10b4… 65511cc1… 27b63c41…" $([ "$(sha256sum $HB/transporte_bastion.py $HB/lanzador_puerta_banco.py $HB/hacer_d5_episodio_banco.py $HB/d5_episodio_banco.py 2>/dev/null | cut -c1-8 | tr '\n' ' ')" = "2dc8d7eb c2ec10b4 65511cc1 27b63c41 " ] && echo 1 || echo 0)
G "bastión: originales intactos (d5_episodio 85c71124, compuerta_b 32e1f3ef, orquestar_b babc528b, analizar_b 611d4b16)" $([ "$(sha256sum $HB/d5_episodio.py $HB/compuerta_b.py $HB/orquestar_b.py $HB/analizar_b.py | cut -c1-8 | tr '\n' ' ')" = "85c71124 32e1f3ef babc528b 611d4b16 " ] && echo 1 || echo 0)
G "clave dedicada 0600 y known_hosts_d5 (huella xHCL2/…)" $([ "$(stat -c %a ~/.ssh/cyberflow-d5-sensor)" = 600 ] && ssh-keygen -lf ~/.ssh/known_hosts_d5 | grep -q 'xHCL2/TSa7S8QE' && echo 1 || echo 0)
G "g01b intacto (96f4f69d…) y g01c presente (b5891d5a…) y con sintaxis válida" $([ "$(sha256sum ~/cf-b/guiones/g01b_lanzar_bateria_b.sh ~/cf-b/guiones/g01c_lanzar_bateria_b_d5.sh | cut -c1-8 | tr '\n' ' ')" = "96f4f69d b5891d5a " ] && bash -n ~/cf-b/guiones/g01c_lanzar_bateria_b_d5.sh && echo 1 || echo 0)

echo "=== 6. instrumentación y generador instrumentado"
G "Kali: inundacion_instrumentada.sh 7ac53358…" $(H kali 'sha256sum ~/cf-b/instrumentacion/inundacion_instrumentada.sh | cut -c1-8' | grep -qx 7ac53358 && echo 1 || echo 0)
G "clientes: clientes_factor1_tx.py d86c7edc…" $(H clientes 'sha256sum ~/cf-b/instrumentacion/clientes_factor1_tx.py | cut -c1-8' | grep -qx d86c7edc && echo 1 || echo 0)
G "srv-dmz: muestreador_set.py 410759c2…" $(H srvdmz 'sha256sum ~/cf-b/instrumentacion/muestreador_set.py | cut -c1-8' | grep -qx 410759c2 && echo 1 || echo 0)
KV=$(H kali 'cd / && sha256sum -c --quiet ~/cf-e4-4c/sha256-esperado-i.txt >/dev/null 2>&1 && echo i_ok || echo i_FALLA; sha256sum -c --quiet ~/cf-e4-4c/sha256-esperado.txt >/dev/null 2>&1 && echo orig_ok || echo orig_FALLA; sha256sum ~/cf-campana-A/scripts-4c-i/esquema_campana.py ~/cf-campana-A/scripts-4c-i/generar_campana_b.py ~/cf-campana-A/escenarios/escenarios-4c-i.json | cut -c1-8 | tr "\n" " "; echo; ls -A ~/cf-e4-4c/intentos | wc -l; ls -d ~/cf-e4-4c/corrida 2>&1 | head -1')
echo "$KV" | sed 's/^/   /'
G "Kali: lista firmada instrumentada y la original verifican" $(echo "$KV" | grep -q i_ok && echo "$KV" | grep -q orig_ok && echo 1 || echo 0)
G "Kali: generador instrumentado c51efd6e… 3ec6a05b… b891674a…" $(echo "$KV" | grep -q 'c51efd6e 3ec6a05b b891674a' && echo 1 || echo 0)
G "Kali: directorio de registros vacío y sin ~/cf-e4-4c/corrida previa" $(echo "$KV" | grep -qx '0' && echo "$KV" | grep -q 'No existe\|cannot access' && echo 1 || echo 0)

echo "=== 7. criterio E3 y lanzador"
echo "   E3 fijado en CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md (bloque 1 s, K 5/3, B0 10 bloques ≥ 5/s, θ 0,5, SPAN o salida; rama BLOCK aclarada). e3_v2 LIMIT+BLOCK: 21 pruebas, 9 de BLOCK."
G "DECISIÓN de Mark: fuerza_bruta_http (BLOCK) sin salida con hora -> aceptar SPAN-solo en los 15 episodios BLOCK, o instrumentarla" 2
G "MEDICIÓN de la duración real de la puerta (fin+75 s + puerta) frente al hueco mínimo de 210 s: requiere UNA solicitud real adicional" 2
echo "##### resumen: $ok OK, $fa FALLAN, $pe PENDIENTES"; [ $fa -eq 0 ] && [ $pe -eq 0 ]
