#!/bin/bash
# PREFLIGHT v4 del TRAMO 7–25 (continuación de B3) con D5 CORREGIDO (fin de episodio + 75 s). FASE=control para ejecutarlo con el control ya declarado (~/cf-e4/4c existe) — SOLO LECTURA; como gadmin en el bastión. NO lanza nada.
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
echo "##### preflight v4 TRAMO 7-25 D5 corregido (espera de fin = 75 s) $(date -u +%FT%TZ)"

echo "=== 1. D5 activo en el Sensor1 y SOLICITUD ACTIVA vs HISTÓRICOS (por id y estado)"
U=ppi-publicar-feed-v2.service
CL=$(SN "tr '\0' ' ' < /proc/\$(systemctl show $U -p MainPID --value)/cmdline")
G "publicador con --control-d5 --d5-origen 10.10.20.30 --d5-auditoria" $(case "$CL" in *"--control-d5 /home/m4rk/feed-v2/d5/control/control.json"*"--d5-origen 10.10.20.30"*"--d5-auditoria"*) echo 1;; *) echo 0;; esac)
G "publicador sin --aplicar, política if_senal" $(case "$CL" in *"--politica if_senal"*) echo 1;; *) echo 0;; esac)
echo "   PID/NRestarts/inicio: $(SN "systemctl show $U -p MainPID -p NRestarts -p ActiveEnterTimestamp | paste -sd' '")"
G "control.json AUSENTE (no hay solicitud pendiente de consumir)" $(SN '[ ! -e ~/feed-v2/d5/control/control.json ] && echo 1 || echo 0')
ACT=0; HIS=0
for id in $(SN 'ls ~/feed-v2/d5/control/solicitudes 2>/dev/null' | sed 's/\.json$//' | grep -E '^[0-9a-f]{32}$'); do
  R=$(S1 "resultado --id $id"); E=$(J "$R" estado); CAT=$(J "$R" categoria); DET=$(J "$R" determinada)
  # HISTÓRICA = ya resuelta: `acuse`/`rechazado` (es el último control) o, si una solicitud posterior sobrescribió el acuse, `sin_acuse` con categoría
  # `consumida_y_publicada` DETERMINADA (auditoría con consumido+publicado y la publicación confirmada). Todo lo demás (pendiente, no consumida, incierta) es ACTIVA.
  if [ "$E" = acuse ] || [ "$E" = rechazado ]; then HIS=$((HIS+1)); echo "   solicitud $id -> $E (secuencia $(J "$R" secuencia)): HISTÓRICA"
  elif [ "$E" = sin_acuse ] && [ "$CAT" = consumida_y_publicada ] && [ "$DET" = True ] && [ "$(J "$R" publicacion)" = confirmada ]; then HIS=$((HIS+1)); echo "   solicitud $id -> $E/$CAT (publicación confirmada, secuencia $(J "$R" secuencia); el acuse fue sobrescrito por una solicitud posterior): HISTÓRICA"
  else ACT=$((ACT+1)); echo "   solicitud $id -> $E/$CAT determinada=$DET: ACTIVA/INCIERTA  $R"; fi; done
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
if [ "${FASE:-pre}" = control ]; then G "ppi-brute-lab ACTIVO (control declarado: endpoint del control)" $(echo "$SD" | grep -q 'inactive' && echo 0 || echo 1); else G "ppi-brute-lab inactivo" $(echo "$SD" | grep -q 'inactive' && echo 1 || echo 0); fi
ST=$(H srvdmz "python3 -I -c \"import sys;sys.dont_write_bytecode=True;sys.path.insert(0,'/home/adminsrvdmz/cf-b/instrumentacion');import muestreador_set as m;print(m.listar(['sudo','-n','/usr/local/sbin/cf-nft-helper']))\"")
echo "   lectura real del muestreador: $ST"
G "muestreador de srv-dmz: lectura real de los sets OK y sets vacíos (sin sudo adicional de Mark)" $(echo "$ST" | grep -q "'ok': True" && echo "$ST" | grep -q "'bloqueados': {}" && echo "$ST" | grep -q "'limitados': {}" && echo 1 || echo 0)
KP=$(H kali "ps -eo args | grep -v 'bash -c' | grep -cE '[g]enerar_campana|[h]ydra|[i]nundacion|[n]map'")
G "Kali sin generadores ($KP)" $([ "$KP" = 0 ] && echo 1 || echo 0)
KH=$(H kali "ps -eo args | grep -v 'bash -c' | grep -cE '[h]ttp.server|[c]f-carga'")
G "Kali sin servidores ni restos de las pruebas de carga locales ($KH; /dev/shm/cf-carga ausente)" $([ "$KH" = 0 ] && H kali '[ ! -e /dev/shm/cf-carga ] && echo 1 || echo 0' | grep -qx 1 && echo 1 || echo 0)
BP=$(ps -eo args | grep -v 'bash -c' | grep -cE '[o]rquestar_b|[c]ompuerta_b|[v]igia_4c|[l]anzador_puerta')
G "bastión sin orquestador, compuerta, vigía ni lanzador ($BP)" $([ "$BP" = 0 ] && echo 1 || echo 0)
if [ "${FASE:-pre}" = control ]; then G "control declarado en el bastión (~/cf-e4/4c/control-declarado.json) y sin vigía/generador vivos" $([ -f ~/cf-e4/4c/control-declarado.json ] && [ ! -e ~/cf-e4/4c/vigia/vigia.jsonl ] && echo 1 || echo 0)
else G "sin carpeta ~/cf-e4/4c viva en el bastión (antes del control)" $([ ! -e ~/cf-e4/4c ] && echo 1 || echo 0); fi
echo "=== B3 conservada: evidencia parcial apartada en los 5 hosts (no se mezcla con el tramo)"
G "bastión: 4c-B3-parcial-6ep-* presente" $(ls -d ~/cf-e4/4c-B3-parcial-6ep-* >/dev/null 2>&1 && echo 1 || echo 0)
G "Sensor1: 4c-B3-parcial-6ep-* con COPIAS-COMPLETAS.ok" $(SN "ls ~/cf-e4/4c-B3-parcial-6ep-*/copias/COPIAS-COMPLETAS.ok" | grep -q COMPLETAS && echo 1 || echo 0)
G "clientes: 4c-B3-parcial-6ep-* presente" $(H clientes "ls -d ~/cf-e4/4c-B3-parcial-6ep-*" | grep -q B3-parcial && echo 1 || echo 0)
G "Kali: cf-e4-4c-B3-parcial-6ep-*/corrida/marcas.jsonl sha 1d129f0b…" $(H kali "sha256sum ~/cf-e4-4c-B3-parcial-6ep-*/corrida/marcas.jsonl | cut -c1-8" | grep -qx 1d129f0b && echo 1 || echo 0)

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
HD=$(sha256sum $HB/transporte_bastion.py $HB/lanzador_puerta_banco.py $HB/hacer_d5_episodio_banco.py $HB/d5_episodio_banco.py 2>/dev/null | cut -c1-8 | tr '\n' ' ')
G "bastión: transporte, lanzador (CON --remoto-srv) y hacer_d5 = 2dc8d7eb… 4600b8b8… 65511cc1… con d5_episodio_banco CORREGIDO 58f715e2… (si sigue 27b63c41… = D5 viejo: PENDIENTE de desplegar)" $([ "$HD" = "2dc8d7eb 4600b8b8 65511cc1 58f715e2 " ] && echo 1 || { [ "$HD" = "2dc8d7eb c2ec10b4 65511cc1 27b63c41 " ] && echo 2 || echo 0; })
G "bastión: originales intactos (d5_episodio 85c71124, compuerta_b 32e1f3ef, orquestar_b babc528b, analizar_b 611d4b16)" $([ "$(sha256sum $HB/d5_episodio.py $HB/compuerta_b.py $HB/orquestar_b.py $HB/analizar_b.py | cut -c1-8 | tr '\n' ' ')" = "85c71124 32e1f3ef babc528b 611d4b16 " ] && echo 1 || echo 0)
G "srv-dmz: d5_episodio_corregido.py = 00c1bb2922d30138 (el que usa SshRunners.srv por --remoto-srv) y el original d5_episodio.py = 85c71124098cb7cb intacto" $([ "$(ssh -n -o BatchMode=yes srvdmz "cd ~/cf-b/herramientas && sha256sum d5_episodio_corregido.py d5_episodio.py | cut -c1-16 | tr '\n' ' '")" = "00c1bb2922d30138 85c71124098cb7cb " ] && echo 1 || echo 0)
G "bastión: g01d pasa --remoto-srv al lanzador real y comprueba el hash del archivo remoto" $([ "$(grep -c -- "--remoto-srv" ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh)" -ge 1 ] && [ "$(grep -c 00c1bb2922d30138 ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh)" -ge 1 ] && echo 1 || echo 0)
G "feed del Sensor1 sin entradas de la Kali (el control de 30 min debe empezar limpio)" $([ "$(ssh -n -o BatchMode=yes sensor1 "python3 -I -c 'import json;f=json.load(open(chr(47)+\"home\"+chr(47)+\"m4rk\"+chr(47)+\"feed-v2\"+chr(47)+\"feed.json\"));print(len([e for e in f[\"entradas\"] if e.get(\"ip\")==\"10.10.20.30\"]))'")" = 0 ] && echo 1 || echo 0)
G "clave dedicada 0600 y known_hosts_d5 (huella xHCL2/…)" $([ "$(stat -c %a ~/.ssh/cyberflow-d5-sensor)" = 600 ] && ssh-keygen -lf ~/.ssh/known_hosts_d5 | grep -q 'xHCL2/TSa7S8QE' && echo 1 || echo 0)
G "g01b (96f4f69d…) y g01c (b5891d5a…) intactos" $([ "$(sha256sum ~/cf-b/guiones/g01b_lanzar_bateria_b.sh ~/cf-b/guiones/g01c_lanzar_bateria_b_d5.sh | cut -c1-8 | tr '\n' ' ')" = "96f4f69d b5891d5a " ] && echo 1 || echo 0)
G "g01d (81dd7003…, con --remoto-srv) presente en el bastión y con sintaxis válida" $([ -f ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh ] && [ "$(sha256sum ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh | cut -c1-8)" = 81dd7003 ] && bash -n ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh && echo 1 || echo 2)

echo "=== 6. instrumentación y generador instrumentado"
G "Kali: inundacion_instrumentada.sh v2 (sin procesos extra por iteración) 8e9b49b1…" $(H kali 'sha256sum ~/cf-b/instrumentacion/inundacion_instrumentada.sh ~/cf-b/paquete-despliegue/inundacion_instrumentada.sh | cut -c1-8 | tr "\n" " "' | grep -qx "8e9b49b1 8e9b49b1 " && echo 1 || echo 0)
G "clientes: clientes_factor1_tx.py d86c7edc…" $(H clientes 'sha256sum ~/cf-b/instrumentacion/clientes_factor1_tx.py | cut -c1-8' | grep -qx d86c7edc && echo 1 || echo 0)
G "srv-dmz: muestreador_set.py 410759c2…" $(H srvdmz 'sha256sum ~/cf-b/instrumentacion/muestreador_set.py | cut -c1-8' | grep -qx 410759c2 && echo 1 || echo 0)
KV=$(H kali 'cd / && sha256sum -c --quiet ~/cf-e4-4c/sha256-esperado-i.txt >/dev/null 2>&1 && echo i_ok || echo i_FALLA; sha256sum -c --quiet ~/cf-e4-4c/sha256-esperado.txt >/dev/null 2>&1 && echo orig_ok || echo orig_FALLA; sha256sum ~/cf-campana-A/scripts-4c-i/esquema_campana.py ~/cf-campana-A/scripts-4c-i/generar_campana_b.py ~/cf-campana-A/escenarios/escenarios-4c-i.json | cut -c1-8 | tr "\n" " "; echo; ls -A ~/cf-e4-4c/intentos | wc -l; ls -d ~/cf-e4-4c/corrida 2>&1 | head -1')
echo "$KV" | sed 's/^/   /'
G "Kali: lista firmada instrumentada y la original verifican" $(echo "$KV" | grep -q i_ok && echo "$KV" | grep -q orig_ok && echo 1 || echo 0)
G "Kali: generador instrumentado vigente (B3) c51efd6e… 3ec6a05b… b891674a… intacto" $(echo "$KV" | grep -q 'c51efd6e 3ec6a05b b891674a' && echo 1 || echo 0)
KT=$(H kali 'cd / && sha256sum -c --quiet ~/cf-e4-4c/sha256-esperado-ii.txt >/dev/null 2>&1 && echo ii_ok || echo ii_FALLA; sha256sum ~/cf-campana-A/scripts-4c-ii/generar_campana_b.py ~/cf-campana-A/scripts-4c-ii/esquema_campana.py ~/cf-campana-A/escenarios/escenarios-4c-i.json 2>/dev/null | cut -c1-8 | tr "\n" " "')
echo "$KT" | sed 's/^/   /'
G "Kali: generador del TRAMO 0705751a… (esquema c51efd6e…, config b891674a…) y sha256-esperado-ii.txt verifica (si falta: PENDIENTE de desplegar)" $(echo "$KT" | grep -q ii_ok && echo "$KT" | grep -q '0705751a c51efd6e b891674a' && echo 1 || echo 2)
G "Kali: directorio de registros vacío y sin ~/cf-e4-4c/corrida previa" $(echo "$KV" | grep -qx '0' && echo "$KV" | grep -q 'No existe\|cannot access' && echo 1 || echo 0)

echo "=== 7. criterio E3 y lanzador"
echo "   E3 fijado en CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md: LIMIT = SPAN o salida con hora; BLOCK (15 episodios) = SPAN ÚNICA fuente, K=3, 0 respuestas, ≥ 1 intento/bloque de 1 s, indeterminado si SPAN no lo verifica (BLOCK_ADMITE_SALIDA=False; 23 pruebas). B2 conservado."
EP=$(ls -d ~/cf-b/ensayo-puerta-* 2>/dev/null | tail -1); echo "   ensayo de la puerta: $EP"; grep -E "duración total|MARGEN|margen" $EP/informe.txt 2>/dev/null | sed 's/^/   /'
MG=$(sed -n 's/.*MARGEN = \([0-9.]*\) s.*/\1/p' $EP/informe.txt 2>/dev/null | head -1)
G "puerta medida con el lanzador real: liberada y con margen ${MG:-?} s > 45 s frente al hueco mínimo de 210 s" $(grep -q 'liberada' $EP/informe.txt 2>/dev/null && [ -n "$MG" ] && awk -v m="$MG" 'BEGIN{exit !(m>45)}' && echo 1 || echo 0)
G "PRUEBA DE LABORATORIO del D5 corregido (residual real con --aplicar, Kali) hecha y aceptada: marca ~/cf-b/prueba-lab-d5-corregido.ok" $([ -f ~/cf-b/prueba-lab-d5-corregido.ok ] && echo 1 || echo 2)
G "decisiones de Mark APROBADAS (11-nov): B4 = corrida nueva (enmienda), CF_PLANIFICADOS=19, --desde-episodio, reporte B3/B4 por separado" 1
echo "##### resumen: $ok OK, $fa FALLAN, $pe PENDIENTES"; [ $fa -eq 0 ] && [ $pe -eq 0 ]
