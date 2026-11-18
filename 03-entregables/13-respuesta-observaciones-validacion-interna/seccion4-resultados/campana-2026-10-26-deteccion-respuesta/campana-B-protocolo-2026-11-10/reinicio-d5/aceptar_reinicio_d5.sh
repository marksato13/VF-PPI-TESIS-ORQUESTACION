#!/bin/bash
# Aceptación del reinicio controlado del publicador con D5 (SOLO LECTURA; se ejecuta como m4rk en el Sensor1).
#   MODO=pre   : toma la referencia (PID, secuencia, estado de las demás entidades) y NO afirma nada.
#   MODO=post  : exige PRE_PID y PRE_SEQ (de la referencia tomada justo antes) y comprueba el nuevo arranque.
# No usa sudo, no toca la clave privada; su única escritura es una copia temporal del feed alterado en /dev/shm (control negativo), borrada al instante. Una línea por comprobación: OK / FALLA / INFO.
set -u
MODO=${MODO:-post}; PRE_PID=${PRE_PID:-0}; PRE_SEQ=${PRE_SEQ:-0}
U=ppi-publicar-feed-v2.service; B=$HOME/feed-v2; K=$HOME/cyberflow/artifacts/feed-keys/pub.pem
FP_ESPERADA=baf897a513b1beb37d3565a1cf403fe1b1f9a68d8a2b62e320fa3dfbaee1af3e   # SPKI de la pública que usa el agente de srv-dmz
ok=0; fa=0
c(){ if [ "$2" = 1 ]; then echo "OK    $1"; ok=$((ok+1)); else echo "FALLA $1"; fa=$((fa+1)); fi; }
i(){ echo "INFO  $1"; }
seq_feed(){ python3 -I -c "import json,sys;d=json.load(open(sys.argv[1]));print(d['secuencia'],d['generado'],d['expira'],d.get('version'))" $B/feed.json 2>/dev/null; }
verifica(){ openssl pkeyutl -verify -pubin -inkey $K -rawin -in $B/feed.json -sigfile $B/feed.sig 2>&1 | head -1; }

echo "##### aceptación reinicio D5 ($MODO) $(date -u +%FT%TZ) $(hostname)"
P=$(systemctl show $U -p MainPID --value); NR=$(systemctl show $U -p NRestarts --value); AE=$(systemctl show $U -p ActiveEnterTimestamp --value)
read S G E V <<<"$(seq_feed)"
i "PID=$P  NRestarts=$NR  ActiveEnter=$AE  etimes=$(ps -o etimes= -p $P | tr -d ' ')"
i "feed: secuencia=${S:-?} generado=${G:-?} expira=${E:-?} version=${V:-?}  estado.json: $(python3 -I -c "import json;print(json.load(open('$B/estado.json'))['secuencia'])" 2>/dev/null)"
for u in ppi-motor.service ppi-dashboard.service ppi-motor-capture.service ppi-via-rapida@ens37.service; do i "$u PID=$(systemctl show $u -p MainPID --value) NRestarts=$(systemctl show $u -p NRestarts --value)"; done
if [ "$MODO" = pre ]; then echo "(referencia tomada; usar: MODO=post PRE_PID=$P PRE_SEQ=${S:-0})"; exit 0; fi

echo "--- 1. nuevo arranque"
c "unidad active (running)" $([ "$(systemctl show $U -p ActiveState --value)/$(systemctl show $U -p SubState --value)" = active/running ] && echo 1 || echo 0)
c "PID nuevo ($P) distinto del previo ($PRE_PID)" $([ "$P" != "$PRE_PID" ] && [ "$P" != 0 ] && echo 1 || echo 0)
i "NRestarts=$NR (no se exige que cambie: un 'systemctl restart' manual no cuenta como reinicio automático)"
CL=$(tr '\0' ' ' < /proc/$P/cmdline 2>/dev/null)
echo "--- 2. proceso con los argumentos D5"
for a in "/home/m4rk/cf-b/d5/publicar_feed_v2_d5.py" "--control-d5 /home/m4rk/feed-v2/d5/control/control.json" "--d5-origen 10.10.20.30" "--d5-auditoria /home/m4rk/feed-v2/d5/auditoria/d5-auditoria.jsonl" "--seguir" "--politica if_senal" "--vigencia-segundos 60" "--refresco-segundos 20"; do
  c "argumento: $a" $(case "$CL" in *"$a"*) echo 1;; *) echo 0;; esac); done
c "NO es el publicador original (engine/publicar_feed_v2.py)" $(case "$CL" in *"/engine/publicar_feed_v2.py"*) echo 0;; *) echo 1;; esac)
c "PYTHONPATH del proceso = engine de ec78ca5" $(tr '\0' '\n' < /proc/$P/environ 2>/dev/null | grep -qx 'PYTHONPATH=/home/m4rk/cyberflow-e4/ec78ca5/scripts/engine' && echo 1 || echo 0)

echo "--- 3. publicación continua (espera hasta 60 s a una secuencia nueva)"
n=0; while [ $n -lt 30 ]; do read S G E V <<<"$(seq_feed)"; [ -n "${S:-}" ] && [ "$S" -gt "$PRE_SEQ" ] && break; sleep 2; n=$((n+1)); done
c "secuencia ($S) > referencia previa ($PRE_SEQ); salto=$(( ${S:-0} - PRE_SEQ ))" $([ -n "${S:-}" ] && [ "$S" -gt "$PRE_SEQ" ] && echo 1 || echo 0)
NOW=$(date +%s)
c "generado reciente (<40 s)" $(python3 -I -c "import sys;print(1 if $NOW-float('${G:-0}')<40 else 0)")
c "vigencia expira-generado = 60 s" $(python3 -I -c "import sys;print(1 if abs((float('${E:-0}')-float('${G:-0}'))-60)<1 else 0)")
c "feed versión 2" $([ "${V:-}" = 2 ] && echo 1 || echo 0)
c "secuencia de estado.json >= secuencia del feed (continuidad persistida)" $(python3 -I -c "import json;print(1 if json.load(open('$B/estado.json'))['secuencia']>=${S:-0} else 0)" 2>/dev/null || echo 0)

echo "--- 4. firma ed25519 verificada con openssl (feed.json + feed.sig, pública del Sensor1)"
FP=$(openssl pkey -pubin -in $K -pubout -outform DER 2>/dev/null | sha256sum | cut -c1-64)
c "huella SPKI de la pública = la del agente de srv-dmz ($FP)" $([ "$FP" = "$FP_ESPERADA" ] && echo 1 || echo 0)
okv=0; for t in 1 2 3 4; do r=$(verifica); [ "$r" = "Signature Verified Successfully" ] && okv=$((okv+1)); sleep 1; done
c "firma válida en $okv/4 lecturas sucesivas (feed y firma se reescriben por separado; se esperan 4/4 o 3/4)" $([ $okv -ge 3 ] && echo 1 || echo 0)
# control negativo: la misma firma NO debe validar un feed alterado
T=$(mktemp -p /dev/shm cf-neg.XXXXXX); cp $B/feed.json $T; sed -i 's/secuencia/secuenciX/' $T
NEG=$(openssl pkeyutl -verify -pubin -inkey $K -rawin -in $T -sigfile $B/feed.sig 2>&1 | head -1); rm -f $T
c "control negativo: copia ALTERADA del feed (en /dev/shm, borrada) NO verifica ($NEG)" $(case "$NEG" in *"Signature Verification Failure"*) echo 1;; *) echo 0;; esac)

echo "--- 5. conservación de las demás entidades (valores de la referencia 11-nov 02:48Z)"
chk(){ c "$1 PID $2 sin cambios y NRestarts $3" $([ "$(systemctl show $1 -p MainPID --value)/$(systemctl show $1 -p NRestarts --value)" = "$2/$3" ] && echo 1 || echo 0); }
chk ppi-motor.service 1472 0; chk ppi-dashboard.service 1473 0; chk ppi-motor-capture.service 1441 0; chk ppi-via-rapida@ens37.service 1475 0
c "timer cf-tcpdump-estadisticas activo" $([ "$(systemctl show cf-tcpdump-estadisticas.timer -p ActiveState --value)" = active ] && echo 1 || echo 0)
c "authorized_keys sha 28a8b124… (sin cambios)" $([ "$(sha256sum $HOME/.ssh/authorized_keys | cut -c1-64)" = 28a8b1245122096e44d146f1b481605e440789310a90eb9ab7ca54808c35a198 ] && echo 1 || echo 0)
c "publicador original 5733f17d… intacto" $([ "$(sha256sum $HOME/cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py | cut -c1-64)" = 5733f17d39bfa5fe667ee13aecd133ea4859834899c5f4f6ea21360ebe4002a2 ] && echo 1 || echo 0)
c "derivado 58e2a0b2… intacto" $([ "$(sha256sum $HOME/cf-b/d5/publicar_feed_v2_d5.py | cut -c1-64)" = 58e2a0b2b06908922f017199987f6e9b28bc8a808b174962d270832909b25451 ] && echo 1 || echo 0)
c "ec78ca5 verifica contra SHA256SUMS" $( (cd $HOME/cyberflow-e4/ec78ca5 && sha256sum -c SHA256SUMS --quiet >/dev/null 2>&1) && echo 1 || echo 0)

echo "--- 6. canal D5 sin solicitudes y arranque limpio"
c "sin control.json, lock ni solicitudes/ (ninguna solicitud creada)" $([ ! -e $B/d5/control/control.json ] && [ ! -e $B/d5/control/solicitudes ] && echo 1 || echo 0)
c "directorio control 0700 y auditoria 0750" $([ "$(stat -c %a $B/d5/control)/$(stat -c %a $B/d5/auditoria)" = 700/750 ] && echo 1 || echo 0)
i "auditoría: $(ls -l $B/d5/auditoria 2>&1 | tail -n +2 | awk '{print $5" B "$9}' | head -2 | paste -sd' ') (puede no existir hasta la primera consumición)"
JL=$(journalctl -u $U --since "-3min" --no-pager 2>&1)
c "journal sin Traceback/Error desde el arranque" $(echo "$JL" | grep -qiE 'traceback|error|exception' && echo 0 || echo 1)
echo "$JL" | tail -4 | cut -c1-170 | sed 's/^/      journal: /'
echo "--- 7. estabilidad (20 s)"; sleep 20
c "mismo PID tras 20 s (sin reinicio en bucle)" $([ "$(systemctl show $U -p MainPID --value)" = "$P" ] && echo 1 || echo 0)
echo "##### resumen: $ok OK, $fa FALLAN"; [ $fa -eq 0 ]
