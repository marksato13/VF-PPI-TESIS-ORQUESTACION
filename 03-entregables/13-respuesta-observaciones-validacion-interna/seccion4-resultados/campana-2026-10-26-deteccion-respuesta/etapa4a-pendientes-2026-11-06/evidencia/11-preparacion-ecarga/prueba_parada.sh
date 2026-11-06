set -u
# [BASTIÓN gadmin] Prueba del CAMINO DE PARADA de los generadores con los generadores YA PARADOS (target inactivo):
# muestreo_bastion.sh en modo real con PARADA_EPOCH inmediata -> generadores.sh parar por ssh -> sudo -n systemctl stop
# sobre un target inactivo (no cambia nada). NO arranca nada. Carpeta rotulada seco.
G=cf-e4/ecarga-v2-guiones-c7f24510
D=~/cf-e4/ecarga-v2-seco-$(date -u +%Y%m%dT%H%M%SZ)/bastion-prueba-parada
CLI="ssh -n -o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
echo "-- antes"; $CLI "bash ~/$G/generadores.sh estado"
F=$(( $(date +%s) + 20 )); PA=$(date +%s)
bash ~/$G/muestreo_bastion.sh "$D" $F $PA real > /dev/null 2>&1; echo "muestreo_bastion (real, parada inmediata) rc=$?"
echo "-- eventos"; cat "$D/eventos.log"
echo "-- después"; $CLI "bash ~/$G/generadores.sh estado"
echo "fin $(date -u +%FT%TZ)"
