#!/usr/bin/env bash
# Archiva SIN HUECOS la captura FULL-SPAN del motor para la campana, con los permisos REALES del sensor.
#   [SENSOR m4rk] -> lo ejecuto yo. NO requiere root ni cambios administrativos.
#
# Estrategia (se conserva): ppi-motor-capture ya captura TODA la poblacion del espejo (tcpdump -i ens37, SIN
# filtro de host, ficheros de 15 s). Son del grupo m4rk (dir setgid 2750), asi que los LEO y COPIO sin sudo.
# Este archivador COPIA los ficheros YA CERRADOS a un directorio PROPIO antes de que la poda
# (cyberflow-limpieza, find -mmin +15 -delete) los borre. cf-capturar (host 10.10.20.30) es SOLO-Kali y NO es
# el archivo. EVE y el acumulador son telemetria DERIVADA y NO sustituyen estos paquetes.
#
# Robustez (este fichero):
#   - NO oculta fallos: cada copia fallida/incompleta se registra (fichero, hora, motivo) en archivar.log y
#     marca un ESTADO verificable (ESTADO.txt) + codigo de salida != 0. No termina anunciando exito si hubo
#     perdida.
#   - Copia SOLO ficheros cerrados (excluye el activo y exige edad >= CLOSE_AGE) y VERIFICA integridad (sha256
#     copia == origen) usando temporal + mv atomico. Una copia que falla o queda incompleta NO se considera
#     archivada y se REINTENTA en los siguientes barridos (no se salta en silencio).
#   - Detecta PERDIDA real: un fichero visto-cerrado que desaparece del anillo sin haberse archivado se registra
#     como PERDIDO y pone ESTADO=FALLO.
#   - Prechequeos: herramientas (cp/sha256sum/stat/df/tcpdump), lectura de origen, escritura en destino y espacio
#     libre minimo. Si no se puede garantizar, aborta con ESTADO=FALLO.
#   - Barrido final (al parar) se ejecuta y su resultado queda PERSISTIDO en ESTADO.txt y archivar.log.
#
# Subcomandos:
#   archivar_captura.sh [DST] [INT]        bucle de archivado (por defecto; Ctrl-C/SIGTERM -> barrido final)
#   archivar_captura.sh barrido  <DST>     un unico barrido (precheck+sweep); sale !=0 si hay fallo/perdida
#   archivar_captura.sh inventario <DIR>   inventario: nombre, tamano, primer/ultimo paquete, sha256; solapes/duplicados
#   archivar_captura.sh estado-motor       estadisticas disponibles del proceso REAL ppi-motor-capture
#
# Inyectables para pruebas: RING, CP (comando de copia), MIN_KB, CLOSE_AGE.
set -uo pipefail
RING="${RING:-/var/lib/ppi-motor-capture}"
CP="${CP:-cp}"
MIN_KB="${MIN_KB:-1048576}"     # minimo libre (KiB) para garantizar el archivado (1 GiB)
CLOSE_AGE="${CLOSE_AGE:-16}"    # s: fichero "cerrado" = no es el activo y su mtime tiene >= esta edad
INT_DEFAULT="${INT_DEFAULT:-60}"

now(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
LOGF=""; STATUSF=""; ARCHF=""; SEENF=""; DST=""
# log va a STDERR (y al fichero), NUNCA a stdout: asi no contamina las capturas $(sweep ...).
log(){ local m="$(now) $*"; printf '%s\n' "$m" >&2; [ -n "$LOGF" ] && printf '%s\n' "$m" >> "$LOGF" 2>/dev/null || true; }
have(){ command -v "$1" >/dev/null 2>&1; }
sha(){ sha256sum "$1" 2>/dev/null | awk '{print $1}'; }

precheck(){ # $1=DST ; !=0 si NO se puede garantizar el archivado
  local D="$1" rc=0 t
  for t in sha256sum stat df ls awk; do have "$t" || { log "FALLO precheck: falta herramienta '$t'"; rc=1; }; done
  # tcpdump solo es necesario para 'inventario'/'estado-motor'; no para archivar
  have "$CP" || have "$(echo "$CP" | awk '{print $1}')" || { log "FALLO precheck: comando de copia no disponible ('$CP')"; rc=1; }
  local p="$D/.probe.$$"; if ( : > "$p" ) 2>/dev/null; then rm -f "$p"; else log "FALLO precheck: destino NO escribible ($D)"; rc=1; fi
  if ! ls "$RING"/ >/dev/null 2>&1; then log "FALLO precheck: origen NO legible ($RING)"; rc=1; fi
  local one; one=$(ls -1 "$RING"/live-*.pcap 2>/dev/null | head -1)
  if [ -n "$one" ] && [ ! -r "$one" ]; then log "FALLO precheck: no puedo leer un pcap del origen ($one)"; rc=1; fi
  local avail; avail=$(df -Pk "$D" 2>/dev/null | awk 'NR==2{print $4}')
  if [ "${avail:-0}" -lt "$MIN_KB" ]; then log "FALLO precheck: espacio insuficiente (${avail:-0} KiB < ${MIN_KB} KiB)"; rc=1
  else log "precheck OK: ${avail} KiB libres (>= ${MIN_KB})"; fi
  return $rc
}

archive_one(){ # $1=SRC $2=DST ; 0 ok, 1 fail. Copia verificada (temporal+mv), nunca deja copia parcial como final.
  local src="$1" D="$2" name out tmp hs ht sz cerr
  name=$(basename "$src"); out="$D/$name"; tmp="$D/.tmp.$name.$$"
  hs=$(sha "$src"); [ -z "$hs" ] && { log "FALLO $name: no pude hashear el origen (ilegible?)"; return 1; }
  if [ -f "$out" ]; then
    if [ "$(sha "$out")" = "$hs" ]; then grep -qxF "$name" "$ARCHF" 2>/dev/null || echo "$name" >> "$ARCHF"; return 0; fi
    log "AVISO $name: copia previa NO coincide con el origen -> se recopia"
  fi
  if ! cerr=$($CP "$src" "$tmp" 2>&1 >/dev/null); then log "FALLO $name: copia fallida: ${cerr:-error de cp}"; rm -f "$tmp" 2>/dev/null; return 1; fi
  ht=$(sha "$tmp")
  if [ "$ht" != "$hs" ]; then log "FALLO $name: copia INCOMPLETA/corrupta (sha copia=${ht:-vacio} != origen=$hs)"; rm -f "$tmp" 2>/dev/null; return 1; fi
  if ! mv -f "$tmp" "$out" 2>/dev/null; then log "FALLO $name: no pude mover el temporal al destino"; rm -f "$tmp" 2>/dev/null; return 1; fi
  if [ "$(sha "$out")" != "$hs" ]; then log "FALLO $name: verificacion final distinta tras mover"; return 1; fi
  sz=$(stat -c%s "$out" 2>/dev/null); echo "$name" >> "$ARCHF"; log "OK $name (${sz} bytes) sha=$hs"; return 0
}

sweep(){ # $1=DST ; imprime "<fallos> <perdidos>"
  local D="$1" act f name age fail=0 lost=0 b
  act=$(ls -1t "$RING"/live-*.pcap 2>/dev/null | head -1)
  for f in "$RING"/live-*.pcap; do
    [ -e "$f" ] || continue
    [ "$f" = "$act" ] && continue
    age=$(( $(date +%s) - $(stat -c%Y "$f" 2>/dev/null || echo 0) ))
    [ "$age" -lt "$CLOSE_AGE" ] && continue
    name=$(basename "$f")
    grep -qxF "$name" "$SEENF" 2>/dev/null || echo "$name" >> "$SEENF"
    grep -qxF "$name" "$ARCHF" 2>/dev/null && continue
    archive_one "$f" "$D" || fail=$((fail+1))
  done
  # PERDIDOS: visto-cerrado, no archivado, ya no en el anillo ni en destino
  while IFS= read -r b; do
    [ -z "$b" ] && continue
    grep -qxF "$b" "$ARCHF" 2>/dev/null && continue
    [ -e "$RING/$b" ] && continue
    [ -f "$D/$b" ] && continue
    lost=$((lost+1))
    grep -qF "PERDIDO $b" "$LOGF" 2>/dev/null || log "FALLO $b: PERDIDO (podado del anillo sin archivar)"
  done < "$SEENF"
  echo "$fail $lost"
}

write_status(){ # $1=DST $2=fallos $3=perdidos
  local D="$1" fail="${2:-0}" lost="${3:-0}" seen arch
  seen=$(grep -c . "$SEENF" 2>/dev/null); seen=${seen:-0}; arch=$(grep -c . "$ARCHF" 2>/dev/null); arch=${arch:-0}
  if [ "$lost" -gt 0 ]; then printf 'FALLO: %s perdido(s); %s fallo(s) de copia en el ultimo barrido; vistos=%s archivados=%s  (%s)\n' "$lost" "$fail" "$seen" "$arch" "$(now)" > "$STATUSF"
  elif [ "$fail" -gt 0 ]; then printf 'PENDIENTE: %s fallo(s) de copia en el ultimo barrido (se reintentan); vistos=%s archivados=%s  (%s)\n' "$fail" "$seen" "$arch" "$(now)" > "$STATUSF"
  else printf 'OK: vistos=%s archivados=%s, sin fallos  (%s)\n' "$seen" "$arch" "$(now)" > "$STATUSF"; fi
}

init_dst(){ DST="$1"; mkdir -p "$DST" || { echo "no se pudo crear $DST" >&2; exit 2; }
  LOGF="$DST/archivar.log"; STATUSF="$DST/ESTADO.txt"; ARCHF="$DST/.archivados"; SEENF="$DST/.vistos"
  : >> "$ARCHF"; : >> "$SEENF"; }

fin(){ log "parando: espero ${CLOSE_AGE}s a que cierre el ultimo fichero y hago barrido final"
  sleep "$CLOSE_AGE"; local r f l
  if ! r=$(sweep "$DST"); then log "FALLO: el barrido final no pudo ejecutarse"; echo "FALLO: barrido final no ejecutado ($(now))" > "$STATUSF" 2>/dev/null || true; exit 6; fi
  f=${r% *}; l=${r#* }
  if ! [ "$f" -ge 0 ] 2>/dev/null || ! [ "$l" -ge 0 ] 2>/dev/null; then log "FALLO: resultado de barrido final invalido ('$r')"; echo "FALLO: barrido final invalido ($(now))" > "$STATUSF" 2>/dev/null || true; exit 6; fi
  write_status "$DST" "$f" "$l"
  log "FIN $(cat "$STATUSF" 2>/dev/null)"
  # Codigo de salida = resultado del cierre: 0 SOLO si completo y verificado (sin pendientes ni perdidos).
  [ "$l" -gt 0 ] && exit 4      # archivos perdidos
  [ "$f" -gt 0 ] && exit 5      # copias pendientes/fallidas en el barrido final
  exit 0; }

cmd_archivar(){ init_dst "${1:-$HOME/cf-campana-archivo/campana-$(date -u +%Y%m%d%H%M%S)}"; local INT="${2:-$INT_DEFAULT}"
  log "INICIO archivador DST=$DST RING=$RING intervalo=${INT}s CLOSE_AGE=${CLOSE_AGE}s MIN_KB=${MIN_KB}"
  df -h "$DST" | awk 'NR==2{print "espacio: "$4" libres ("$5") en "$6}'
  if ! precheck "$DST"; then log "ABORTO: precheck fallido -> NO se puede garantizar el archivado"; echo "FALLO: precheck ($(now))" > "$STATUSF"; exit 3; fi
  trap fin INT TERM
  log "archivando... (Ctrl-C para terminar con barrido final)"
  local r f l
  while true; do r=$(sweep "$DST"); f=${r% *}; l=${r#* }; write_status "$DST" "$f" "$l"; sleep "$INT"; done
}

cmd_barrido(){ init_dst "$1"
  if ! precheck "$DST"; then echo "FALLO: precheck ($(now))" > "$STATUSF"; log "barrido: precheck fallido"; cat "$STATUSF"; exit 3; fi
  local r f l; r=$(sweep "$DST"); f=${r% *}; l=${r#* }; write_status "$DST" "$f" "$l"; cat "$STATUSF"
  { [ "${l:-0}" -gt 0 ] && exit 4; }; { [ "${f:-0}" -gt 0 ] && exit 5; }; exit 0
}

cmd_inventario(){ local DIR="$1" n=0 dup=0 ovl=0 rst=0 prev_last="" prev_name="" f name sz first last h key
  echo "# INVENTARIO de $DIR  ($(now))"
  echo "# la continuidad NO se deduce del numero de ficheros; se juzga por marcas de PAQUETE (solape/hueco/reinicio)."
  printf "%-30s %10s  %-20s %-20s %s\n" "fichero" "bytes" "primer_paquete" "ultimo_paquete" "sha256(16)"
  declare -A seenhash
  for f in "$DIR"/live-*.pcap; do
    [ -e "$f" ] || continue; n=$((n+1))
    name=$(basename "$f"); sz=$(stat -c%s "$f" 2>/dev/null)
    first=$(tcpdump -ttnr "$f" 2>/dev/null | head -1 | awk '{print $1}')
    last=$(tcpdump -ttnr "$f" 2>/dev/null | tail -1 | awk '{print $1}')
    h=$(sha "$f")
    printf "%-30s %10s  %-20s %-20s %s\n" "$name" "${sz:-NA}" "${first:-NA}" "${last:-NA}" "${h:0:16}"
    if [ -n "${seenhash[$h]:-}" ]; then dup=$((dup+1)); echo "   DUPLICADO: $name tiene el mismo sha256 que ${seenhash[$h]}"; else seenhash[$h]="$name"; fi
    if [ -n "$prev_last" ] && [ -n "$first" ]; then
      local d; d=$(awk -v a="$prev_last" -v b="$first" 'BEGIN{printf "%.3f", b-a}')
      awk -v d="$d" 'BEGIN{exit !(d < -0.001)}' && { ovl=$((ovl+1)); echo "   SOLAPE: $name empieza ${d}s respecto al fin de $prev_name"; }
      awk -v d="$d" 'BEGIN{exit !(d > 20)}'     && { rst=$((rst+1)); echo "   HUECO/REINICIO: +${d}s entre $prev_name y $name"; }
    fi
    prev_last="$last"; prev_name="$name"
  done
  echo "# ficheros=$n duplicados_sha=$dup solapes=$ovl huecos/reinicios=$rst"
}

cmd_estado_motor(){
  local pid; pid=$(systemctl show ppi-motor-capture -p MainPID --value 2>/dev/null)
  echo "# ppi-motor-capture (proceso REAL) ($(now))"
  echo -n "is-active: "; systemctl is-active ppi-motor-capture 2>/dev/null
  systemctl show ppi-motor-capture -p ActiveEnterTimestamp -p MainPID -p NRestarts -p MemoryCurrent 2>/dev/null | sed 's/^/  /'
  echo "ficheros presentes en el anillo: $(ls -1 "$RING"/live-*.pcap 2>/dev/null | wc -l)"
  echo "descartes de kernel del proceso ACTUAL (PID ${pid:-?}):"
  local dl; dl=$(sudo -n journalctl --no-pager -u ppi-motor-capture 2>/dev/null | grep -iE 'drop|descart|truncat')
  if [ -n "$dl" ] && echo "$dl" | grep -q "tcpdump\[${pid}\]"; then
    echo "$dl" | grep "tcpdump\[${pid}\]" | sed 's/^/  [PID actual] /'
  else
    [ -n "$dl" ] && { echo "  (hay lineas de descarte en el journal, pero de PIDs ANTERIORES -no del $pid-; NO se usan como sustituto:)"; echo "$dl" | tail -3 | sed 's/^/    [historico otro PID] /'; }
    echo "  NO MEDIDOS para el proceso actual: corre con -G (rotacion) sin --print-statistics y no imprime stats en vivo."
    echo "  NO se afirma 0 perdidas. Indicador de continuidad disponible: NRestarts=0 (sin reinicios de captura) +"
    echo "  inventario sin huecos/solapes por marca de paquete (ver 'inventario')."
  fi
}

case "${1:-archivar}" in
  barrido)     shift; cmd_barrido "${1:?uso: barrido <DST>}" ;;
  inventario)  shift; cmd_inventario "${1:?uso: inventario <DIR>}" ;;
  estado-motor) cmd_estado_motor ;;
  archivar)    shift; cmd_archivar "${1:-}" "${2:-}" ;;
  *)           cmd_archivar "${1:-}" "${2:-}" ;;
esac
