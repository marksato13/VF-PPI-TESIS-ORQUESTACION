#!/bin/bash
# PRUEBA CONTROLADA del D5 corregido por INYECCIÓN (separada de B4; solo Kali 10.10.20.30; como gadmin en el bastión). UNA sola ejecución; revierte siempre.
# Diferencia con los ensayos 1 y 2: el agente de srv-dmz sigue en SOMBRA (nadie renueva el LIMIT ni destruye el contador). Se crea la tabla y UN solo LIMIT con el helper (asegurar + anadir),
# se lanza una ráfaga CORTA de 3 s desde la Kali (≈ 450 peticiones < 600/60 s: no dispara `http_abuse`) y se verifica que `limitados` Y `descartes_limite` contienen a la Kali.
# Si no, INCONCLUSO (la puerta no se ejecuta y no se repite). Si sí: puerta real D5 corregida UNA vez (lanzador_puerta_banco, fin+0), comprobaciones y reversión R0–R5.
set -u
D=$HOME/cf-b/prueba-lab-d5-inyeccion-2; HB=$HOME/cf-b/herramientas; K=10.10.20.30; ID=$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')
mkdir -p $D; L(){ echo "$@" | tee -a $D/prueba.log; }
SRV(){ timeout 60 ssh -n -o BatchMode=yes srvdmz "$@" 2>&1; }
SEN(){ timeout 40 ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11 "$@" 2>&1; }
HLP(){ SRV "printf '%s' '$1' | sudo -n /usr/local/sbin/cf-nft-helper"; }
LISTAR(){ HLP '{"perfil":"dmz","operaciones":[{"op":"listar"}]}' | python3 -c "import sys,json;e=json.load(sys.stdin)['estado'];print(json.dumps({'sets':e['sets'],'descartes_limite':e['descartes_limite']},sort_keys=True))"; }
L "## prueba por inyección $(date -u +%FT%TZ) id-LIMIT=$ID"
# --- 0. previos
PUB0=$(SEN 'echo "PID=$(systemctl show -p MainPID --value ppi-publicar-feed-v2) NR=$(systemctl show -p NRestarts --value ppi-publicar-feed-v2)"'); L "publicador antes: $PUB0"; echo "$PUB0" > $D/publicador-antes.txt
FEEDK=$(SEN "python3 -I -c \"import json;print(len([e for e in json.load(open('/home/m4rk/feed-v2/feed.json'))['entradas'] if e.get('ip')=='$K']))\""); L "entradas de la Kali en el feed antes: $FEEDK"
SOMB=$(SRV 'echo "agente $(systemctl is-active ppi-enforce-agent-v2-dmz) --aplicar=$(systemctl show -p ExecStart --value ppi-enforce-agent-v2-dmz | grep -c -- --aplicar) tablas=$(sudo -n nft list tables | grep -c cyberflow)"'); L "srv-dmz antes: $SOMB"
[ "$(sha256sum $HB/d5_episodio_banco.py | cut -c1-8)" = 58f715e2 ] || { L "PARAR: D5 corregido no instalado"; exit 2; }
[ "$(sha256sum $HB/lanzador_puerta_banco.py | cut -c1-8)" = 4600b8b8 ] || { L "PARAR: lanzador sin --remoto-srv"; exit 2; }
[ "$(SRV "sha256sum ~/cf-b/herramientas/d5_episodio_corregido.py" | cut -c1-8)" = 00c1bb29 ] || { L "PARAR: d5 corregido ausente en srv-dmz"; exit 2; }
echo "$SOMB" | grep -q 'agente active --aplicar=0 tablas=0' || { L "PARAR: srv-dmz no está en sombra limpia"; exit 2; }
# --- 1. UN solo LIMIT por el helper
L "## [$(date -u +%FT%T.%3NZ)] helper: asegurar"; HLP '{"perfil":"dmz","operaciones":[{"op":"asegurar"}]}' | tee -a $D/prueba.log
T_LIMIT=$(date +%s.%N); L "## [$(date -u +%FT%T.%3NZ)] helper: anadir LIMIT limitados $K timeout 300 id $ID"; HLP "{\"perfil\":\"dmz\",\"operaciones\":[{\"op\":\"anadir\",\"set\":\"limitados\",\"ip\":\"$K\",\"timeout\":300,\"id\":\"$ID\"}]}" | tee -a $D/prueba.log
echo "$T_LIMIT" > $D/t-limit.epoch; L "LIMIT aplicado (helper) a t=$T_LIMIT; estado: $(LISTAR)"
# --- 2. ráfaga corta (UN acceso a la Kali, registrado)
echo "## [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): ráfaga de 3 s (inundacion_instrumentada.sh) para la prueba por inyección]" | tee -a ~/cf-e4/accesos-kali-preparacion.log $D/prueba.log
T_RAF=$(date +%s.%N)
ssh -n -o BatchMode=yes kali 'mkdir -p ~/cf-b/prueba-lab && env CF_MAXTIME=2 bash ~/cf-b/instrumentacion/inundacion_instrumentada.sh ~/cf-b/prueba-lab/intentos-inyeccion.tsv http://10.10.30.10/ 3 8' | tee -a $D/prueba.log
L "ráfaga: inicio +$(python3 -c "print(round($T_RAF-$T_LIMIT,1))") s tras el LIMIT; fin $(date -u +%FT%T.%3NZ)"; sleep 2
# --- 3. verificación previa a la puerta
ANTES=$(LISTAR); echo "$ANTES" > $D/nft-antes-puerta.json; L "ANTES de la puerta: $ANTES"
OKPRE=$(python3 -c "
import json;e=json.loads('''$ANTES'''); print(1 if '$K' in e['sets']['limitados'] and '$K' in e['descartes_limite'] else 0)")
if [ "$OKPRE" != 1 ]; then L "ENSAYO INCONCLUSO: la Kali no está a la vez en limitados y en descartes_limite; NO se ejecuta la puerta y NO se repite"; echo INCONCLUSO > $D/resultado.txt
else
  L "estado reproducido: la Kali en limitados Y en descartes_limite (antes de ejecutar D5)"
  mkdir -p $D/puerta; python3 -I -c "
import json,time
json.dump({'pendiente': True, 'en_episodio': False, 'n_inicios': 1, 'episodio': 'prueba-inyeccion', 'fin_en': time.time()-80, 'liberada_en': None, 'orden': ['prueba-inyeccion']}, open('$D/puerta/gate.json','w'), sort_keys=True)"
  python3 -I $HB/lanzador_puerta_banco.py ejecutar --dir $D/puerta --d5-banco $HB/d5_episodio_banco.py --sensor m4rk@10.10.60.11 --clave $HOME/.ssh/cyberflow-d5-sensor --known-hosts $HOME/.ssh/known_hosts_d5 \
     --herramientas $HB --espera-fin 0 --ssh-sensor-legado "ssh -n -o BatchMode=yes sensor1" --ssh-srv-legado "ssh -n -o BatchMode=yes srvdmz" --remoto-srv "python3 -I ~/cf-b/herramientas/d5_episodio_corregido.py" --max-iter 1 > $D/puerta/lanzador.stdout 2> $D/puerta/lanzador.stderr; L "lanzador rc=$?"
  DESP=$(LISTAR); echo "$DESP" > $D/nft-despues-puerta.json; L "DESPUÉS de la puerta: $DESP"
  PUB1=$(SEN 'echo "PID=$(systemctl show -p MainPID --value ppi-publicar-feed-v2) NR=$(systemctl show -p NRestarts --value ppi-publicar-feed-v2)"'); L "publicador después: $PUB1"
  python3 -I - $D "$DESP" "$PUB0" "$PUB1" > $D/comprobaciones.txt <<'PY'
import json, sys
d, desp, p0, p1 = sys.argv[1:5]; K = "10.10.20.30"
e = json.loads(desp); r = [json.loads(l) for l in open(d + "/puerta/puertas-D5.jsonl")][-1]; p = {x["paso"]: x for x in r["pasos"]}
c = lambda n, ok: print(("OK    " if ok else "FALLA ") + n)
c("la puerta se liberó (lista=True)", r["lista"] is True)
c("nft_antes: la Kali solo en limitados (restriccion) y residual registrado aparte", p["nft_antes"]["donde"] == ["limitados"] and bool(p["nft_antes"].get("residual")))
c("la regla se retiró (retirar.retirado)", p["retirar"].get("retirado") is True)
c("nft_despues: sets de aplicación sin la Kali y residual registrado", p["nft_despues"]["donde"] == [] and bool(p["nft_despues"].get("residual")))
c("limitados y bloqueados quedaron vacíos para la Kali", K not in e["sets"]["limitados"] and K not in e["sets"]["bloqueados"])
c("el contador residual se conservó en descartes_limite", K in e["descartes_limite"])
c("residual_conservado en puertas-D5.jsonl", bool(r.get("residual_conservado")))
c("publicador: mismo PID y NRestarts (sin reinicio)", p0 == p1 and "NR=0" in p1)
PY
  cat $D/comprobaciones.txt | tee -a $D/prueba.log
  grep -q FALLA $D/comprobaciones.txt && echo "FALLA" > $D/resultado.txt || echo "VALIDA" > $D/resultado.txt
fi
# --- 4. reversión SIEMPRE
L "## reversión $(date -u +%FT%TZ)"
SRV "sudo -n env CF_MODO=real bash /opt/cyberflow/campana-b/b_revertir_srvdmz.sh 2>&1 | tail -6" | tee -a $D/prueba.log
SRV "CON_SUDO=1 bash ~/cf-e4/paquete-a1cea5e/deploy/etapa4/srvdmz/verificar_srvdmz.sh \$(cat ~/cf-b/PRE-B-actual.txt) 2>&1 | grep -E 'estado=|VERIFICACI'" | tee -a $D/prueba.log
SRV 'echo "agente $(systemctl is-active ppi-enforce-agent-v2-dmz) NR=$(systemctl show -p NRestarts --value ppi-enforce-agent-v2-dmz) --aplicar=$(systemctl show -p ExecStart --value ppi-enforce-agent-v2-dmz | grep -c -- --aplicar) dropin=$(ls /etc/systemd/system/ppi-enforce-agent-v2-dmz.service.d 2>/dev/null | wc -l) tablas=$(sudo -n nft list tables | grep -c cyberflow) cf-b-fin=$(systemctl is-active cf-b-fin.timer)"' | tee -a $D/prueba.log
L "publicador final: $(SEN 'echo PID=$(systemctl show -p MainPID --value ppi-publicar-feed-v2) NR=$(systemctl show -p NRestarts --value ppi-publicar-feed-v2)')"
L "RESULTADO: $(cat $D/resultado.txt)"
[ "$(cat $D/resultado.txt)" = VALIDA ] && touch ~/cf-b/prueba-lab-d5-corregido.ok && L "marca ~/cf-b/prueba-lab-d5-corregido.ok escrita"
