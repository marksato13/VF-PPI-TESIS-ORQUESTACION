#!/usr/bin/env bash
# Modo seco de los guiones del paquete v3 sobre un ESPEJO LOCAL de los hosts reales (contenedor; NINGÚN fichero se crea en los hosts). El espejo reproduce, con las rutas REALES
# (/home/m4rk, /home/gadmin, …), lo leído en solo lectura el 11-nov: publicador original (hash verificado en el Sensor1), ExecStart tal como lo devuelve `systemctl cat`,
# authorized_keys con sus opciones (claves sustituidas), árbol candidato de solo lectura, herramientas del bastión. Se comprueba que el modo seco no cambia el espejo.
set -u
PQ=/pq; OUT=/salida; mkdir -p "$OUT"
snap() { find /home -mindepth 1 \( -type f -o -type d \) -printf '%y %m %u %p\n' -exec sha256sum {} \; 2>/dev/null | sort | sha256sum | cut -d' ' -f1; }
# ---------------- espejo Sensor1
S=/home/m4rk; E=$S/cyberflow-e4/ec78ca5/scripts/engine
mkdir -p "$E" $S/.ssh $S/feed-v2/d5-auditoria $S/cf-b/herramientas
cp /producto-etapa3/scripts/engine/publicar_feed_v2.py "$E/"; chmod 555 "$E" "$S/cyberflow-e4/ec78ca5" 2>/dev/null
printf 'ssh-ed25519 <clave> vm-gestion-to-cyberflow\ncommand="/usr/local/bin/cf-feed-ssh.sh servir /home/m4rk/feed-v2",restrict ssh-ed25519 <clave> cyberflow-feed-v2-rele\n' > $S/.ssh/authorized_keys; chmod 600 $S/.ssh/authorized_keys; chmod 700 $S/.ssh
cat > /tmp/execstart <<'EOF'
ExecStart=/home/m4rk/cyberflow/.venv/bin/python /home/m4rk/cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py \
    --log /home/m4rk/cyberflow/logs/motor_decision.log \
    --estado /home/m4rk/feed-v2/estado.json \
    --clave-privada /home/m4rk/cyberflow/artifacts/feed-keys/priv.pem \
    --salida-feed /home/m4rk/feed-v2/feed.json \
    --salida-firma /home/m4rk/feed-v2/feed.sig \
    --senales /home/m4rk/feed-v2/senales-if.jsonl \
    --senales-rapidas /home/m4rk/feed-v2/senales-rapidas.jsonl \
    --traza /home/m4rk/feed-v2/traza.jsonl \
    --politica if_senal --vigencia-segundos 60 --refresco-segundos 20 --seguir
EOF
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI<CLAVE-PUBLICA-DEDICADA-QUE-GENERARA-EL-BASTION> cf-bastion-d5' > /tmp/pub.pub
# ---------------- espejo bastión
G=/home/gadmin; mkdir -p $G/.ssh $G/cf-b/herramientas; chmod 700 $G/.ssh
for f in d5_episodio.py compuerta_b.py orquestar_b.py; do cp /herramientas/$f $G/cf-b/herramientas/; done
# ---------------- ejecución
A=$(snap)
{
echo "################ SENSOR1 (m4rk) — instalar, seco, CON --con-sudo (muestra los comandos de sudo)"
CF_HOME=$S CF_PAQUETE=$PQ CF_PUBKEY=/tmp/pub.pub CF_FROM=10.10.10.30 CF_SIN_SYSTEMD=1 CF_EXECSTART_FILE=/tmp/execstart bash $PQ/cf_d5_sensor1.sh instalar --con-sudo --reiniciar; echo "rc=$?"
echo; echo "################ SENSOR1 — instalar, seco, SIN --con-sudo (lo que se deja para Mark)"
CF_HOME=$S CF_PAQUETE=$PQ CF_PUBKEY=/tmp/pub.pub CF_FROM=10.10.10.30 CF_SIN_SYSTEMD=1 CF_EXECSTART_FILE=/tmp/execstart bash $PQ/cf_d5_sensor1.sh instalar; echo "rc=$?"
echo; echo "################ SENSOR1 — revertir, seco"
CF_HOME=$S CF_PAQUETE=$PQ CF_SIN_SYSTEMD=1 bash $PQ/cf_d5_sensor1.sh revertir; echo "rc=$?"
echo; echo "################ SENSOR1 — aceptar (solo lectura; sin instalar debe FALLAR en lo no instalado)"
CF_HOME=$S CF_PAQUETE=$PQ CF_SIN_SYSTEMD=1 bash $PQ/cf_d5_sensor1.sh aceptar; echo "rc=$?"
echo; echo "################ BASTIÓN (gadmin) — clave, seco"
CF_HOME=$G CF_PAQUETE=$PQ bash $PQ/cf_d5_bastion.sh clave; echo "rc=$?"
echo; echo "################ BASTIÓN — instalar, seco (CF_HOSTKEY = marcador; en la instalación real es la pública del Sensor1 comprobada por huella)"
CF_HOME=$G CF_PAQUETE=$PQ CF_HOSTKEY="ssh-ed25519 <CLAVE-PUBLICA-DEL-HUESPED-SENSOR1>" bash $PQ/cf_d5_bastion.sh instalar; echo "rc=$?"
echo; echo "################ BASTIÓN — revertir, seco"
CF_HOME=$G CF_PAQUETE=$PQ bash $PQ/cf_d5_bastion.sh revertir; echo "rc=$?"
for par in "kali /home/adminatacante" "clientes /home/adminclientes" "srvdmz /home/adminsrvdmz"; do set -- $par
  echo; echo "################ $1 — instrumentación, instalar y revertir, seco"
  CF_HOME=$2 CF_PAQUETE=$PQ bash $PQ/cf_d5_instrumentacion.sh $1 instalar; echo "rc=$?"
  CF_HOME=$2 CF_PAQUETE=$PQ bash $PQ/cf_d5_instrumentacion.sh $1 revertir; echo "rc=$?"
done
} > $OUT/salida-modo-seco.txt 2>&1
B=$(snap)
echo "espejo antes : $A" | tee -a $OUT/salida-modo-seco.txt
echo "espejo despues: $B" | tee -a $OUT/salida-modo-seco.txt
[ "$A" = "$B" ] && echo "RESULTADO: el modo seco NO cambió el espejo (ni /home de ningún host simulado)" | tee -a $OUT/salida-modo-seco.txt || echo "RESULTADO: EL MODO SECO CAMBIÓ EL ESPEJO" | tee -a $OUT/salida-modo-seco.txt
ls -la /home/adminatacante /home/adminclientes /home/adminsrvdmz 2>&1 | head -3 | tee -a $OUT/salida-modo-seco.txt
