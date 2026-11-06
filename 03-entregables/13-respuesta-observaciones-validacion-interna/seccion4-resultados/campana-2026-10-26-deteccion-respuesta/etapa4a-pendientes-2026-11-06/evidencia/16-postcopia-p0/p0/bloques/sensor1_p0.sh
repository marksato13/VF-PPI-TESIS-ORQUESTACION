# Bloque P0 puntos 5, 6, 7, 9, 11 y 13 (solo lectura) en Sensor1. «comprobar» NO crea DIR (solo exige que esté libre)
# ni salida de obs_pcap en seco; su padre (~/cf-e4) ya existe. No se arranca ningún muestreador.
D=~/cf-e4/${1:?nombre}
P=~/cf-e4/paquete-902991e
max=0
echo "######## sensor1_muestreadores.sh comprobar $D 1794197760 2026-11-09T04:16:00Z  ($(date -u +%FT%TZ))"
[ -e "$D" ] && { echo "ABORTA: ya existe $D"; exit 2; }
sha256sum "$P/deploy/etapa4/ecarga/sensor1_muestreadores.sh"
bash "$P/deploy/etapa4/ecarga/sensor1_muestreadores.sh" comprobar "$D" 1794197760 2026-11-09T04:16:00Z < /dev/null; r=$?
echo "rc_comprobar=$r"; max=$r
[ -e "$D" ] && echo "AVISO: comprobar creó $D" || echo "comprobar no creó $D"
[ -e "$D-seco-obs_pcap" ] && echo "AVISO: obs_pcap en seco creó salida" || echo "obs_pcap en seco sin salida"
echo "######## punto 9: paquete-ae2900e"
(cd ~/cf-e4/paquete-ae2900e && sha256sum -c --strict --quiet SHA256SUMS 2>&1 | head -5); r=${PIPESTATUS[0]}
echo "rc_ae2900e_sha256sums=$r"; [ $r -gt $max ] && max=$r
sha256sum ~/cf-e4/paquete-ae2900e/deploy/etapa4/sensor1/evaluar_ecarga.py
grep -m1 '^VERSION' ~/cf-e4/paquete-ae2900e/deploy/etapa4/sensor1/evaluar_ecarga.py
echo "######## punto 5: zona"
echo "timezone=$(cat /etc/timezone 2>&1) TZ_env=${TZ:-} date=$(date +%Z)"
echo "######## EVE y anillo (lectura directa)"
ls -l --time-style=+%FT%T /var/log/suricata/eve.json 2>&1
u=$(tail -c 400000 /var/log/suricata/eve.json 2>/dev/null | grep -E '"event_type": ?"stats"' | tail -1 | cut -c1-60); echo "último stats EVE: ${u:-NINGUNO en los últimos 400 kB}"
a=/var/lib/ppi-motor-capture; echo "anillo: $(ls -1 $a 2>&1 | wc -l) ficheros; primero $(ls -1 $a | head -1); último $(ls -1 $a | tail -1); ahora $(date -u +%Y%m%d%H%M%S)"
echo "######## journal (lectura)"
journalctl --no-pager -u suricata -n 2 2>&1 | cut -c1-200; echo "rc_journal=${PIPESTATUS[0]}"
exit $max
