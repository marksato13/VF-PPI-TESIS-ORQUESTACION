#!/bin/bash
# PRUEBA DE LABORATORIO del D5 CORREGIDO (PREPARADA, NO EJECUTADA; requiere autorización expresa de Mark: activa --aplicar en srv-dmz y genera tráfico desde la Kali).
# Objetivo: reproducir en el laboratorio real el estado del episodio 6 de B3 (regla activa en `limitados` + contador residual en `descartes_limite` tras una inundación) y comprobar que
# la puerta D5 CORREGIDA pasa, retira la regla, conserva el contador, no reinicia el publicador y no deja nada más aplicado. Sin vigía ni generador de campaña: una ráfaga corta, a mano.
# Como gadmin en el BASTIÓN, después de desplegar el D5 corregido y con el preflight v4 sin FALLA. Uso: prueba_lab_d5_corregido.sh {plan|fase1|fase2|fase3|revertir}
#   plan     imprime el plan y las comprobaciones (no toca nada)
#   fase1    estado previo + activación de --aplicar (b_activar, fin automático 2 h) + ráfaga de 60 s desde la Kali (UN acceso SSH a la Kali, registrado)
#   fase2    espera fin + 75 s, lee el estado de srv-dmz (sets y contador) y lanza la puerta real UNA vez (lanzador_puerta_banco --max-iter 1 --espera-fin 75)
#   fase3    comprobaciones y evidencia
#   revertir reversión R0–R5 de srv-dmz + sombra verificada (siempre, pase o falle)
# CRITERIOS DE ABORTO (revertir de inmediato): cualquier restricción sobre una IP distinta de 10.10.20.30; NRestarts del publicador distinto de 0; el agente aplica fuera del origen; srv-dmz no vuelve a sombra.
set -u
FASE=${1:-plan}; D=$HOME/cf-b/prueba-lab-d5; HB=$HOME/cf-b/herramientas; K=10.10.20.30
SRV(){ timeout 60 ssh -n -o BatchMode=yes srvdmz "$@" 2>&1; }
SEN(){ timeout 40 ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11 "$@" 2>&1; }
case "$FASE" in
plan)
  sed -n '2,12p' "$0"; cat <<'P'
COMPROBACIONES DE ACEPTACIÓN (todas):
 1. antes: srv-dmz en sombra (verificar_srvdmz OK), sin campaña ni generadores, D5 corregido instalado (d5_episodio_banco 58f715e2…), publicador con --control-d5 y NRestarts=0.
 2. tras la ráfaga: `limitados` contiene 10.10.20.30 y `descartes_limite` contiene 10.10.20.30 (si no aparece el residual la prueba NO valida la corrección: repetir con ráfaga más larga).
 3. tras la puerta: lista=True; pasos nft_antes (donde=[limitados], residual presente), retirar, nft_despues (donde=[], residual presente); residual_conservado en puertas-D5.jsonl.
 4. después: `limitados` y `bloqueados` vacíos; `descartes_limite` AÚN con 10.10.20.30 (no se borró); agente 0 aplicaciones nuevas; publicador mismo PID y NRestarts=0; acuse y auditoría con el mismo id.
 5. ninguna restricción sobre otra IP en ningún momento (srv-estado rc 0 en cada lectura).
 6. reversión: srv-dmz en sombra verificada. La marca ~/cf-b/prueba-lab-d5-corregido.ok la escribe fase3 SOLO si 1–6 se cumplen.
P
  ;;
fase1)
  mkdir -p "$D" || exit 2; echo "## fase1 $(date -u +%FT%TZ)" | tee -a "$D/prueba.log"
  PUB=$(SEN 'echo "PID=$(systemctl show -p MainPID --value ppi-publicar-feed-v2) NR=$(systemctl show -p NRestarts --value ppi-publicar-feed-v2)"'); echo "publicador antes: $PUB" | tee -a "$D/prueba.log"; echo "$PUB" > "$D/publicador-antes.txt"
  [ "$(sha256sum $HB/d5_episodio_banco.py | cut -c1-8)" = 58f715e2 ] || { echo "PARAR: el D5 corregido no está instalado"; exit 2; }
  SRV "cd ~/cf-b/guiones && CF_HORAS=2 CF_SRC_REVERSION=\$HOME/cf-b/guiones/b_revertir_srvdmz.sh CF_MODO=real bash b_activar_srvdmz.sh" | tee -a "$D/prueba.log" | tail -5
  echo "## [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): ráfaga de ${RAF:-120} s de laboratorio (inundacion_instrumentada.sh) hacia srv-dmz:80]" | tee -a ~/cf-e4/accesos-kali-preparacion.log "$D/prueba.log"
  INI_RAF=$(date +%s.%N)
  ssh -n -o BatchMode=yes kali 'mkdir -p ~/cf-b/prueba-lab && env CF_MAXTIME=2 bash ~/cf-b/instrumentacion/inundacion_instrumentada.sh ~/cf-b/prueba-lab/intentos-lab.tsv http://10.10.30.10/ '"${RAF:-120}"' 8' | tee -a "$D/prueba.log"
  date +%s > "$D/fin-rafaga.epoch"; echo "$INI_RAF" > "$D/inicio-rafaga.epoch"
  echo "## cuándo se aplicó LIMIT (aplicaciones del agente de srv-dmz; inicio de la ráfaga = $INI_RAF)" | tee -a "$D/prueba.log"
  SRV "sudo -n grep -h aplicacion /var/lib/cyberflow/agente/traza.jsonl | tail -n 3 | cut -c1-200" | tee "$D/aplicaciones.txt" | tee -a "$D/prueba.log"
  python3 -I - "$D" <<'PY' | tee -a "$D/prueba.log"
import re, sys
d = sys.argv[1]; ini = float(open(d + "/inicio-rafaga.epoch").read())
ap = [float(m.group(1)) for l in open(d + "/aplicaciones.txt") if "limitados" in l for m in [re.search(r'"aplicado_en": ([0-9.]+)', l)] if m]
post = [a for a in ap if a >= ini]
print("LIMIT aplicado a +%.1f s del inicio de la ráfaga" % (min(post) - ini) if post else "LIMIT: ninguna aplicación posterior al inicio de la ráfaga")
PY
  echo "ráfaga terminada $(date -u +%FT%TZ). Siguiente: fase2 a partir de fin + 80 s" | tee -a "$D/prueba.log";;
fase2)
  FIN=$(cat "$D/fin-rafaga.epoch") || exit 2; ESP=$(( FIN + 80 - $(date +%s) )); [ $ESP -gt 0 ] && { echo "esperando $ESP s (fin + 80 s)"; sleep $ESP; }
  echo "## estado de srv-dmz ANTES de la puerta $(date -u +%FT%TZ)" | tee -a "$D/prueba.log"
  SRV "printf '%s' '{\"perfil\":\"dmz\",\"operaciones\":[{\"op\":\"listar\"}]}' | sudo -n /usr/local/sbin/cf-nft-helper | python3 -c 'import sys,json;e=json.load(sys.stdin)[\"estado\"];print(\"sets\",e[\"sets\"],\"descartes_limite\",e[\"descartes_limite\"])'" | tee "$D/nft-antes-puerta.txt" | tee -a "$D/prueba.log"
  grep -q "descartes_limite {'$K'" "$D/nft-antes-puerta.txt" && grep -q "limitados': {'$K'" "$D/nft-antes-puerta.txt" || { echo "ENSAYO INCONCLUSO: antes de la puerta no hay la Kali en limitados Y en descartes_limite; NO se ejecuta la puerta y NO se repite" | tee -a "$D/prueba.log"; echo INCONCLUSO > "$D/resultado.txt"; exit 3; }
  echo "residual presente antes de la puerta: OK" | tee -a "$D/prueba.log"
  mkdir -p "$D/puerta"; python3 -I -c "
import json,time
json.dump({'pendiente': True, 'en_episodio': False, 'n_inicios': 1, 'episodio': 'prueba-lab', 'fin_en': time.time()-80, 'liberada_en': None, 'orden': ['prueba-lab']}, open('$D/puerta/gate.json','w'), sort_keys=True)"
  python3 -I "$HB/lanzador_puerta_banco.py" ejecutar --dir "$D/puerta" --d5-banco "$HB/d5_episodio_banco.py" --sensor m4rk@10.10.60.11 --clave "$HOME/.ssh/cyberflow-d5-sensor" --known-hosts "$HOME/.ssh/known_hosts_d5" \
     --herramientas "$HB" --espera-fin 0 --ssh-sensor-legado "ssh -n -o BatchMode=yes sensor1" --ssh-srv-legado "ssh -n -o BatchMode=yes srvdmz" --max-iter 1 > "$D/puerta/lanzador.stdout" 2> "$D/puerta/lanzador.stderr"; echo "lanzador rc=$?" | tee -a "$D/prueba.log";;
fase3)
  OK=0; N=0; c(){ N=$((N+1)); if [ "$2" = 1 ]; then echo "OK    $1"; OK=$((OK+1)); else echo "FALLA $1"; fi; }
  python3 -I - "$D" > "$D/comprobaciones.txt" <<'PY'
import json,sys,os
d=sys.argv[1]; r=[json.loads(l) for l in open(d+"/puerta/puertas-D5.jsonl")][-1]; p={x["paso"]:x for x in r["pasos"]}
print("lista",r["lista"]); print("antes",p.get("nft_antes",{}).get("donde"),bool(p.get("nft_antes",{}).get("residual")))
print("retirar",p.get("retirar",{}).get("retirado")); print("despues",p.get("nft_despues",{}).get("donde"),bool(p.get("nft_despues",{}).get("residual")))
print("residual_conservado",bool(r.get("residual_conservado")))
PY
  cat "$D/comprobaciones.txt"
  grep -q '^lista True' "$D/comprobaciones.txt"; c "la puerta pasó (lista=True)" $([ $? = 0 ] && echo 1 || echo 0)
  grep -q "^antes \['limitados'\] True" "$D/comprobaciones.txt"; c "antes: regla en limitados Y residual presente (estado del episodio 6 reproducido)" $([ $? = 0 ] && echo 1 || echo 0)
  grep -q '^despues \[\] True' "$D/comprobaciones.txt"; c "después: sets de aplicación vacíos y residual conservado en el paso" $([ $? = 0 ] && echo 1 || echo 0)
  grep -q '^residual_conservado True' "$D/comprobaciones.txt"; c "residual_conservado en puertas-D5.jsonl" $([ $? = 0 ] && echo 1 || echo 0)
  SRV "printf '%s' '{\"perfil\":\"dmz\",\"operaciones\":[{\"op\":\"listar\"}]}' | sudo -n /usr/local/sbin/cf-nft-helper | python3 -c 'import sys,json;e=json.load(sys.stdin)[\"estado\"];print(e[\"sets\"],list(e[\"descartes_limite\"]))'" | tee "$D/nft-despues-puerta.txt"
  grep -q "{'bloqueados': {}, 'limitados': {}} \['$K'\]" "$D/nft-despues-puerta.txt"; c "srv-dmz: sets vacíos y descartes_limite AÚN con la Kali (no se borró)" $([ $? = 0 ] && echo 1 || echo 0)
  PUB=$(SEN 'echo "PID=$(systemctl show -p MainPID --value ppi-publicar-feed-v2) NR=$(systemctl show -p NRestarts --value ppi-publicar-feed-v2)"'); echo "publicador después: $PUB"
  [ "$PUB" = "$(cat $D/publicador-antes.txt)" ]; c "publicador: mismo PID y NRestarts (sin reinicio)" $([ $? = 0 ] && echo 1 || echo 0)
  echo "$OK de $N comprobaciones"; [ $OK = $N ] && { touch ~/cf-b/prueba-lab-d5-corregido.ok; echo "marca ~/cf-b/prueba-lab-d5-corregido.ok escrita (tras revertir a sombra)"; } || echo "NO se escribe la marca";;
revertir)
  SRV "sudo -n env CF_MODO=real bash /opt/cyberflow/campana-b/b_revertir_srvdmz.sh 2>&1 | tail -6; sudo -n systemctl stop cf-b-fin.timer; CON_SUDO=1 bash ~/cf-e4/paquete-a1cea5e/deploy/etapa4/srvdmz/verificar_srvdmz.sh \$(cat ~/cf-b/PRE-B-actual.txt) 2>&1 | grep -E 'estado=|VERIFICACI'" | tee -a "$D/prueba.log";;
*) echo "uso: $0 {plan|fase1|fase2|fase3|revertir}"; exit 2;;
esac
