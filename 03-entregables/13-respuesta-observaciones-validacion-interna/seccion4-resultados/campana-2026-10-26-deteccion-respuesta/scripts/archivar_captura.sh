#!/usr/bin/env bash
# Archiva SIN HUECOS la captura FULL-SPAN del motor para la campana, con los permisos REALES del sensor.
#   [SENSOR m4rk] -> lo ejecuto yo. NO requiere root ni cambios administrativos.
#
# Fundamento: ppi-motor-capture ya captura TODA la poblacion del espejo (tcpdump -i ens37, SIN filtro de host,
# ficheros de 15 s con marca de tiempo, -s 0). Esos ficheros son del grupo m4rk (dir setgid 2750), asi que los
# puedo LEER y COPIAR sin privilegios. El unico motivo por el que el anillo "recicla" es la poda
# cyberflow-limpieza (find -mmin +15 -delete, cada 5 min). Este archivador COPIA los ficheros ya CERRADOS del
# anillo a un directorio PROPIO antes de que la poda los borre -> archivo durable, completo y gapless.
#
# A diferencia de cf-capturar (host 10.10.20.30, SOLO Kali), este archivo conserva el control normal de toda la
# red ademas del trafico de ensayo. EVE y el acumulador son telemetria DERIVADA y NO sustituyen estos paquetes.
#
# Garantias:
#   - SIN sobrescritura: nombres live-YYYYmmddHHMMSS.pcap unicos (15 s) + cp --update=none (no re-copia ni pisa).
#   - Copia byte-identica: se EXCLUYE el fichero ACTIVO (en escritura); se copia en el siguiente barrido ya cerrado.
#   - Gapless: barrido cada INTERVALO_S (por defecto 60 s) << retencion del anillo (15 min), con amplio margen.
#
# Uso: archivar_captura.sh [DIR_ARCHIVO] [INTERVALO_S]
#   Arrancar ANTES del control-normal de la campana y dejar correr durante historia previa, episodios y
#   periodo posterior. Parar (Ctrl-C / SIGTERM) tras el ultimo posterior: hace un barrido final.
set -uo pipefail
RING=/var/lib/ppi-motor-capture
DST="${1:-$HOME/cf-campana-archivo/campana-$(date -u +%Y%m%d%H%M%S)}"
INT="${2:-60}"
mkdir -p "$DST" || { echo "no se pudo crear $DST" >&2; exit 1; }
echo "archivo: $DST"
echo "fuente : $RING (ens37, FULL-SPAN, sin filtro de host) ; barrido cada ${INT}s ; poda del anillo: -mmin +15"
df -h "$DST" | awk 'NR==2{print "espacio: "$4" libres ("$5" usado) en "$6}'
sweep(){
  local act; act=$(ls -1t "$RING"/live-*.pcap 2>/dev/null | head -1)   # fichero ACTIVO (en escritura): excluir
  local f
  for f in "$RING"/live-*.pcap; do
    [ -e "$f" ] || continue
    [ "$f" = "$act" ] && continue
    cp --update=none "$f" "$DST/" 2>/dev/null
  done
}
fin(){
  echo "parando: espero 16 s a que cierre el ultimo fichero y hago barrido final..."
  sleep 16; sweep
  local n; n=$(ls -1 "$DST"/live-*.pcap 2>/dev/null | wc -l)
  echo "FIN: $n ficheros archivados, $(du -sh "$DST" 2>/dev/null | cut -f1) en $DST"
  exit 0
}
trap fin INT TERM
echo "archivando... (Ctrl-C para terminar con barrido final)"
while true; do sweep; sleep "$INT"; done
