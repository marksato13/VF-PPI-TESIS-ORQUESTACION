#!/bin/bash
# Prueba controlada ÚNICA de D5 de punta a punta (bastión -> Sensor1), limitada a 10.10.20.30. Se ejecuta como gadmin en el bastión.
# Envía UN solo `solicitar` (NUNCA reintenta: si el envío o la espera dan resultado incierto, solo LEE y se detiene).
# Escrituras: únicamente las del propio D5 en el Sensor1 (control, registro de la solicitud, acuse, auditoría, feed). Nada más.
set -u
RD=$(cat <<'RDEOF'
B=$HOME/feed-v2; U=ppi-publicar-feed-v2.service; K=$HOME/cyberflow/artifacts/feed-keys/pub.pem
echo "PID=$(systemctl show $U -p MainPID --value)"; echo "NR=$(systemctl show $U -p NRestarts --value)"; echo "AE=$(systemctl show $U -p ActiveEnterTimestamp --value)"
echo "FEEDSEQ=$(python3 -I -c "import json;d=json.load(open('$B/feed.json'));print(d['secuencia'])" 2>/dev/null)"
echo "FEEDKALI=$(python3 -I -c "import json;d=json.load(open('$B/feed.json'));print(len([e for e in d['entradas'] if e.get('ip')=='10.10.20.30']))" 2>/dev/null)"
echo "VIGENTES=$(python3 -I -c "import json;d=json.load(open('$B/estado.json'));print(len(d.get('vigentes',{})), 'seq', d['secuencia'])" 2>/dev/null)"
echo "CTL=$([ -e $B/d5/control/control.json ] && echo presente || echo ausente)"
echo "ACKFILE=$([ -e $B/d5/control/control.json.ack ] && echo presente || echo ausente)"
echo "N_SOL=$(ls $B/d5/control/solicitudes 2>/dev/null | wc -l)"
echo "ACK=$(cat $B/d5/control/control.json.ack 2>/dev/null)"
echo "SOL=$(cat $B/d5/control/solicitudes/$ID.json 2>/dev/null)"
echo "AUDFILES=$(ls $B/d5/auditoria 2>/dev/null | paste -sd,)"
for l in $(cat $B/d5/auditoria/d5-auditoria.jsonl 2>/dev/null | grep -F "$ID" | tr ' ' '~'); do echo "AUD=$(echo $l | tr '~' ' ')"; done
echo "AUDTOTAL=$(cat $B/d5/auditoria/d5-auditoria.jsonl 2>/dev/null | wc -l)"
echo "FIRMA=$(openssl pkeyutl -verify -pubin -inkey $K -rawin -in $B/feed.json -sigfile $B/feed.sig 2>&1 | head -1)"
echo "AUDMODE=$(stat -c '%a %U' $B/d5/auditoria/d5-auditoria.jsonl 2>/dev/null)"
RDEOF
)
S1(){ timeout 30 ssh -n -i ~/.ssh/cyberflow-d5-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null -o IdentitiesOnly=yes m4rk@10.10.60.11 "$@" 2>&1; }
LEER(){ local s; s=$(printf 'ID=%s\n%s\n' "$ID" "$RD" | base64 -w0); timeout 40 ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11 "bash -c \"\$(echo $s | base64 -d)\"" 2>&1; }
V(){ echo "$1" | grep -m1 "^$2=" | cut -d= -f2-; }
J(){ python3 -I -c "import json,sys;d=json.loads(sys.argv[1]);print(d.get(sys.argv[2]))" "$1" "$2" 2>/dev/null; }
ok=0; fa=0; c(){ if [ "$2" = 1 ]; then echo "OK    $1"; ok=$((ok+1)); else echo "FALLA $1"; fa=$((fa+1)); fi; }
ID=$(python3 -I -c "import uuid;print(uuid.uuid4().hex)")
echo "##### prueba D5 e2e $(date -u +%FT%TZ)  ID=$ID  origen=10.10.20.30"

echo "=== A. ANTES (lectura)"; A=$(LEER); echo "$A"
PID0=$(V "$A" PID); NR0=$(V "$A" NR); SEQ0=$(V "$A" FEEDSEQ)
if [ "$(V "$A" CTL)" != ausente ] || [ "$(V "$A" ACKFILE)" != ausente ] || [ "$(V "$A" N_SOL)" != 0 ]; then echo "ABORTO ANTES DE ENVIAR: hay control, acuse o solicitudes previas"; exit 3; fi
echo "Kali en el feed antes: $(V "$A" FEEDKALI) entradas (0 = ya estaba limpia)"
[ "${SECO:-0}" = 1 ] && { echo "(modo SECO: solo la lectura previa; no se envía nada)"; exit 0; }

echo "=== B. UN SOLO solicitar  ($(date -u +%FT%TZ))"
T0=$(date +%s); R=$(S1 "solicitar --id $ID --origen 10.10.20.30"); RC=$?
echo "rc=$RC  respuesta: $R"
if [ $RC -ne 0 ] || [ "$(J "$R" estado)" != recibida ]; then
  echo "ENVÍO INCIERTO O RECHAZADO: NO se reenvía. Solo lectura:"; S1 "resultado --id $ID"; LEER; echo "DETENIDO (evidencia conservada en el Sensor1)"; exit 4; fi

echo "=== C. espera del acuse (solo 'resultado'; hasta 150 s)"
EST=""; ULT=""
for n in $(seq 1 75); do RES=$(S1 "resultado --id $ID"); EST=$(J "$RES" estado)
  [ "$EST" != "$ULT" ] && { echo "t+$(( $(date +%s)-T0 ))s estado=$EST  $RES"; ULT=$EST; }
  case "$EST" in acuse|rechazado|sin_acuse) break;; esac; sleep 2; done
echo "resultado final: $RES"

echo "=== D. DESPUÉS (lectura)"; sleep 22; Z=$(LEER); echo "$Z"
PID1=$(V "$Z" PID); NR1=$(V "$Z" NR); SEQ1=$(V "$Z" FEEDSEQ)
if [ "$EST" != acuse ]; then echo "RESULTADO INCIERTO ($EST): NO se reenvía; evidencia conservada (control/ack/solicitud/auditoría en el Sensor1)."; fi

echo "=== E. comprobaciones"
c "acuse recibido con el MISMO id" $([ "$EST" = acuse ] && [ "$(J "$RES" id)" = "$ID" ] && echo 1 || echo 0)
ACK=$(V "$Z" ACK); ACKSEQ=$(J "$ACK" secuencia)
c "acuse: ok=True, id igual, duplicada=False, quitado=$(J "$ACK" quitado), secuencia=$ACKSEQ" $([ "$(J "$ACK" ok)/$(J "$ACK" id)/$(J "$ACK" duplicada)" = "True/$ID/False" ] && echo 1 || echo 0)
NC=$(echo "$Z" | grep -c '^AUD=.*"evento": "consumido"'); NP=$(echo "$Z" | grep -c '^AUD=.*"evento": "publicado"'); NF=$(echo "$Z" | grep -c '^AUD=.*ack_fallido')
c "auditoría con el mismo id: consumido=$NC publicado=$NP ack_fallido=$NF (se exige 1/1/0)" $([ "$NC" = 1 ] && [ "$NP" = 1 ] && [ "$NF" = 0 ] && echo 1 || echo 0)
AUDSEQ=$(echo "$Z" | grep '^AUD=.*"evento": "publicado"' | head -1 | python3 -I -c "import sys,json;print(json.loads(sys.stdin.read().split('=',1)[1])['secuencia'])" 2>/dev/null)
c "secuencia de la auditoría ($AUDSEQ) = secuencia del acuse ($ACKSEQ)" $([ -n "$AUDSEQ" ] && [ "$AUDSEQ" = "$ACKSEQ" ] && echo 1 || echo 0)
c "feed posterior: secuencia $SEQ1 > previa $SEQ0 y >= acuse $ACKSEQ" $([ "$SEQ1" -gt "$SEQ0" ] 2>/dev/null && [ "$SEQ1" -ge "$ACKSEQ" ] 2>/dev/null && echo 1 || echo 0)
c "firma ed25519 del feed posterior: $(V "$Z" FIRMA)" $([ "$(V "$Z" FIRMA)" = "Signature Verified Successfully" ] && echo 1 || echo 0)
c "feed sin entradas de Kali tras el acuse ($(V "$Z" FEEDKALI))" $([ "$(V "$Z" FEEDKALI)" = 0 ] && echo 1 || echo 0)
c "control consumido (control.json ausente)" $([ "$(V "$Z" CTL)" = ausente ] && echo 1 || echo 0)
c "registro de la solicitud presente (N_SOL=$(V "$Z" N_SOL))" $([ "$(V "$Z" N_SOL)" = 1 ] && echo 1 || echo 0)
c "PID continuo ($PID0 -> $PID1)" $([ "$PID0" = "$PID1" ] && echo 1 || echo 0)
c "NRestarts continuo ($NR0 -> $NR1)" $([ "$NR0" = "$NR1" ] && echo 1 || echo 0)
echo "auditoría: fichero $(V "$Z" AUDFILES) modo $(V "$Z" AUDMODE), $(V "$Z" AUDTOTAL) líneas en total"
echo "##### resumen: $ok OK, $fa FALLAN  (ID=$ID)"; [ $fa -eq 0 ]
