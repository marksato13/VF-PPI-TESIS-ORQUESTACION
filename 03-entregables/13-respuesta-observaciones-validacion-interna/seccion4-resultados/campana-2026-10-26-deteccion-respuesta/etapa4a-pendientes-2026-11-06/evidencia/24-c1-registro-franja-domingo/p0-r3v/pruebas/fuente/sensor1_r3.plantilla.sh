# BLOQUE=sensor1_r3  (P0 r3, puntos 5a, 5b, 6, 7, 9, 11 y 13, solo lectura) en Sensor1.
#   argumentos: NOMBRE_DIR PAQUETE SUMAS_ESPERADAS FRANJA_INI FRANJA_FIN
# Sustituye a ../../../17-correccion-p0/p0-r2/bloques/sensor1_r2.sh (se conserva). Cambio: «comprobar» se ejecuta con
# sensor1_muestreadores.sh 2026-11-06.4 (producto @@COMMIT_PRODUCTO@@), que identifica los muestreadores por el argv de
# /proc/<pid>/cmdline y no por texto (la .3 usaba «pgrep -af» y, ejecutada como «bash -c "$txt"», coincidía consigo misma:
# P11 NO_CUMPLE falso en el P0 r2 del 06-nov 23:24Z). Nuevo requisito P11.muestreadores: CUMPLE (ausencia confirmada),
# NO_CUMPLE (presencia) o ERROR (estado desconocido); P11 sigue siendo el rc de «comprobar».
# «comprobar» NUNCA se ejecuta con una versión que pueda escribir caché ni con texto no publicado:
#   - si ecarga/sensor1_muestreadores.sh del paquete ES la .4 publicada (V4), se ejecuta tal cual;
#   - si es la .3 (V3) o la .2 de 902991e (V2), se DERIVA en memoria la .4: .2 -> .3 con las tres sustituciones del
#     commit 20dabe2 (sha exigido V3) y .3 -> .4 sustituyendo las líneas 2, 22-25 y 63-64 por el texto publicado en
#     @@COMMIT_PRODUCTO@@ (sha exigido V4); se ejecuta ese texto con $0 = ruta del guion del paquete. Nada se escribe;
#   - con cualquier otro sha, o si algún texto derivado no tiene exactamente el sha exigido, no se ejecuta (ERROR).
# Además se compara el inventario completo del paquete (tipo, modo, tamaño, mtime y ruta) antes y después.
set -u -o pipefail
B=sensor1_r3; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
[ $# = 5 ] || { echo "uso: NOMBRE PAQUETE SUMAS FRANJA_INI FRANJA_FIN"; E=2; fin; }
D=$HOME/cf-e4/$1; P=$HOME/cf-e4/paquete-$2; SUMAS=$3; FI=$4; FF=$5
S=$P/deploy/etapa4/ecarga/sensor1_muestreadores.sh
V2=25fb732ddc15bc83f1f1a79e6e9ccb7ca0cd867a2dfd48270a26dd9ba03c915b
V3=4ed4385674e9f731c7d50f12b132d86a0a3625355df24ebaf4fa9fa0c8342b6e
V4=@@V4@@
FIN_EPOCH=1794111360; FIN_ISO=2026-11-08T04:16:00Z
# Texto publicado de la .4 que sustituye a las líneas 22-25 (procesos con pgrep) y 63-64 (su uso) de la .3.
BLOQUE_A=$(cat <<'FIN_TEXTO_PUBLICADO_A'
@@BLOQUE_A@@
FIN_TEXTO_PUBLICADO_A
)
BLOQUE_B=$(cat <<'FIN_TEXTO_PUBLICADO_B'
@@BLOQUE_B@@
FIN_TEXTO_PUBLICADO_B
)
sha_txt() { printf '%s\n' "$1" | sha256sum | cut -c1-64; }
de3a4() {  # texto de la .3 -> texto de la .4 (por stdout)
  local t=$1
  printf '%s\n' "$t" | sed -n '1p'
  printf '%s\n' "$t" | sed -n '2p' | sed 's/VERSION 2026-11-06\.3\./VERSION 2026-11-06.4./'
  printf '%s\n' "$t" | sed -n '3,21p'
  printf '%s\n' "$BLOQUE_A"
  printf '%s\n' "$t" | sed -n '26,62p'
  printf '%s\n' "$BLOQUE_B"
  printf '%s\n' "$t" | sed -n '65,$p'
}
# ---- 5b y 5a
ep=$(date -u +%s); r=$?
if [ $r != 0 ] || ! [[ $ep =~ ^[0-9]+$ ]]; then req P5b ERROR "date rc $r"
elif [ "$ep" -lt "$FI" ]; then req P5b NO_EVALUABLE "ahora $ep ($(date -u -d "@$ep" +%FT%TZ)) es anterior a la franja [$FI,$FF]: solo evaluable en el P0 inmediato"
elif [ "$ep" -le "$FF" ]; then req P5b CUMPLE "ahora $ep dentro de la franja [$FI,$FF]"
else req P5b NO_CUMPLE "ahora $ep posterior a la franja [$FI,$FF]"; fi
z=$(timedatectl show -p Timezone --value 2>&1); r=$?
case "$r:$z" in 0:Etc/UTC|0:UTC) req P5a.sensor1 CUMPLE "Timezone=$z";; 0:*) req P5a.sensor1 NO_CUMPLE "Timezone=$z";; *) req P5a.sensor1 ERROR "timedatectl rc $r";; esac
# ---- 13: el paquete es el esperado, con inventario exacto
if ! [ -d "$P" ] || ! [ -r "$P/SHA256SUMS" ]; then
  for i in P13.sumas P13.hashes P13.inventario X.mecanismo_sin_escritura P11 P11.muestreadores P11.retencion P6.home P6.mem P7 X.dir_no_creado X.paquete_sin_cambios; do
    req $i ERROR "no existe o no se lee $P/SHA256SUMS"; done
else
  s=$(sha256sum < "$P/SHA256SUMS" | cut -c1-64); r=$?
  [ $r != 0 ] && req P13.sumas ERROR "sha256sum rc $r" || { [ "$s" = "$SUMAS" ] && req P13.sumas CUMPLE "SHA256SUMS $s" || req P13.sumas NO_CUMPLE "SHA256SUMS $s distinto de $SUMAS"; }
  (cd "$P" && sha256sum -c --strict --quiet SHA256SUMS < /dev/null) 2>&1 | head -5 | sed 's/^/INFO sha256sum -c /'; r=${PIPESTATUS[0]}
  case $r in 0) req P13.hashes CUMPLE "sha256sum -c --strict rc 0";; 1) req P13.hashes NO_CUMPLE "sha256sum -c rc 1";; *) req P13.hashes ERROR "sha256sum -c rc $r";; esac
  esp=$(sed -E 's/^[0-9a-f]{64}  //' "$P/SHA256SUMS" | LC_ALL=C sort); r1=$?
  pre=$(cd "$P" && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort); r2=$?
  if [ $r1 != 0 ] || [ $r2 != 0 ]; then req P13.inventario ERROR "lectura del inventario rc $r1/$r2"
  else
    an=$(LC_ALL=C comm --check-order -13 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre")); c1=$?
    au=$(LC_ALL=C comm --check-order -23 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre")); c2=$?
    n=$(grep -c . <<<"$pre")
    if [ $c1 != 0 ] || [ $c2 != 0 ]; then req P13.inventario ERROR "comm rc $c1/$c2"
    elif [ -z "$an$au" ]; then req P13.inventario CUMPLE "$n ficheros = manifiesto"
    else req P13.inventario NO_CUMPLE "presentes $n; añadidos: $(tr '\n' ' ' <<<"${an:-ninguno}"); ausentes: $(tr '\n' ' ' <<<"${au:-ninguno}")"; fi
  fi
  snap() { (cd "$P" && find . -printf '%y %m %s %T@ %p\n' | LC_ALL=C sort); }
  a0=$(snap); r0=$?
  # ---- mecanismo sin escritura
  v=$(sha256sum < "$S" | cut -c1-64); r=$?; txt=""
  if [ $r != 0 ]; then req X.mecanismo_sin_escritura ERROR "no se lee $S"
  elif [ "$v" = "$V4" ]; then txt=$(cat "$S") && req X.mecanismo_sin_escritura CUMPLE "sensor1_muestreadores.sh 2026-11-06.4 publicado ($V4)" || req X.mecanismo_sin_escritura ERROR "cat $S"
  elif [ "$v" = "$V3" ] || [ "$v" = "$V2" ]; then
    if [ "$v" = "$V2" ]; then
      t3=$(sed -e '2s/VERSION 2026-11-06\.2\./VERSION 2026-11-06.3./' -e '31s/python3 -I -c /python3 -I -B -c /' -e '66s/python3 -I "\$P/python3 -I -B "$P/' "$S"); r=$?; de="la .2"
    else t3=$(cat "$S"); r=$?; de="la .3"; fi
    d3=$(sha_txt "$t3")
    if [ $r != 0 ] || [ "$d3" != "$V3" ]; then req X.mecanismo_sin_escritura ERROR "la .3 derivada desde $de tiene sha ${d3:-?} (rc $r), no $V3: no se ejecuta"
    else
      t4=$(de3a4 "$t3"); r=$?; d4=$(sha_txt "$t4")
      if [ $r = 0 ] && [ "$d4" = "$V4" ]; then txt=$t4; req X.mecanismo_sin_escritura CUMPLE "derivada en memoria la 2026-11-06.4 ($V4) desde $de del paquete (paso .3 $V3); nada escrito"
      else req X.mecanismo_sin_escritura ERROR "la .4 derivada tiene sha ${d4:-?} (rc $r), no la publicada $V4: no se ejecuta"; fi
    fi
  else req X.mecanismo_sin_escritura ERROR "sensor1_muestreadores.sh $v desconocido: no se ejecuta"; fi
  # ---- 6, 7, 11
  if [ -z "$txt" ]; then
    for i in P11 P11.muestreadores P11.retencion P6.home P6.mem P7 X.dir_no_creado; do req $i ERROR "comprobar no ejecutado (mecanismo)"; done
  elif [ -e "$D" ]; then
    for i in P11 P11.muestreadores P11.retencion P6.home P6.mem P7 X.dir_no_creado; do req $i ERROR "ya existe $D: comprobar no ejecutado"; done
  else
    echo "######## sensor1_muestreadores.sh comprobar $D $FIN_EPOCH $FIN_ISO ($(date -u +%FT%TZ))"
    out=$(bash -c "$txt" "$S" comprobar "$D" "$FIN_EPOCH" "$FIN_ISO" < /dev/null 2>&1); r=$?
    printf '%s\n' "$out" | sed 's/^/| /'; info "rc_comprobar=$r"
    case $r in 0) req P11 CUMPLE "comprobar rc 0";; 1) req P11 NO_CUMPLE "comprobar rc 1: $(grep '^FALLO' <<<"$out" | tr '\n' ';' | cut -c1-300)";; *) req P11 ERROR "comprobar rc $r";; esac
    nm=$(grep -cE '^(OK    ningún muestreador en marcha|FALLO ya hay muestreadores en marcha|FALLO estado de los muestreadores DESCONOCIDO)' <<<"$out")
    if [ "$nm" != 1 ]; then req P11.muestreadores ERROR "comprobar dio $nm veredictos de muestreadores (se exige 1)"
    elif grep -q '^OK    ningún muestreador en marcha' <<<"$out"; then req P11.muestreadores CUMPLE "$(grep -m1 '^OK    ningún muestreador' <<<"$out" | cut -c7-200)"
    elif grep -q '^FALLO ya hay muestreadores en marcha' <<<"$out"; then req P11.muestreadores NO_CUMPLE "$(grep -m1 '^FALLO ya hay muestreadores' <<<"$out" | cut -c7-300)"
    else req P11.muestreadores ERROR "$(grep -m1 '^FALLO estado de los muestreadores' <<<"$out" | cut -c7-300)"; fi
    lin() {  # lin ID REGEX_OK REGEX_FALLO DESCRIPCION
      if grep -qE "$2" <<<"$out"; then req "$1" CUMPLE "$(grep -m1 -E "$2" <<<"$out" | cut -c7-200)"
      elif grep -qE "$3" <<<"$out"; then req "$1" NO_CUMPLE "$(grep -m1 -E "$3" <<<"$out" | cut -c7-200)"
      else req "$1" ERROR "comprobar no informó de $4"; fi
    }
    lin P11.retencion '^OK    retención del anillo' '^FALLO (retención del anillo|no se pudo medir la retención)' "la retención (medida SIN carga)"
    lin P6.home '^OK    /home libre' '^FALLO /home libre' "/home libre"
    lin P6.mem '^OK    MemAvailable' '^FALLO MemAvailable' "MemAvailable"
    if grep -q '^OK    obs_pcap --en-seco rc 0$' <<<"$out" && grep -q '^OK    obs_pcap en seco no creó salida$' <<<"$out"; then req P7 CUMPLE "obs_pcap --en-seco rc 0 y sin salida"
    elif grep -qE '^FALLO obs_pcap' <<<"$out"; then req P7 NO_CUMPLE "$(grep -m1 '^FALLO obs_pcap' <<<"$out")"
    else req P7 ERROR "comprobar no informó de obs_pcap --en-seco"; fi
    { [ -e "$D" ] || [ -e "$D-seco-obs_pcap" ]; } && req X.dir_no_creado NO_CUMPLE "comprobar creó $D o $D-seco-obs_pcap" || req X.dir_no_creado CUMPLE "no creó $D ni salida en seco"
  fi
  a1=$(snap); r1=$?
  if [ $r0 != 0 ] || [ $r1 != 0 ] || [ -z "$a0" ]; then req X.paquete_sin_cambios ERROR "inventario del paquete rc $r0/$r1"
  elif [ "$a0" = "$a1" ]; then req X.paquete_sin_cambios CUMPLE "inventario (tipo, modo, tamaño, mtime, ruta) idéntico antes y después: $(grep -c . <<<"$a1") entradas"
  else req X.paquete_sin_cambios NO_CUMPLE "el paquete cambió: $(diff <(printf '%s\n' "$a0") <(printf '%s\n' "$a1") | grep '^[<>]' | head -5 | tr '\n' ';')"; fi
fi
# ---- 9: paquete-ae2900e (evaluador del veredicto)
A=$HOME/cf-e4/paquete-ae2900e
(cd "$A" && sha256sum -c --strict --quiet SHA256SUMS < /dev/null) 2>&1 | head -3 | sed 's/^/INFO ae2900e /'; r=${PIPESTATUS[0]}
ev=$(sha256sum < "$A/deploy/etapa4/sensor1/evaluar_ecarga.py" | cut -c1-64); r2=$?
vv=$(grep -m1 '^VERSION' "$A/deploy/etapa4/sensor1/evaluar_ecarga.py" | cut -c1-40); r3=$?
if [ $r -gt 1 ] || [ $r2 != 0 ] || [ $r3 -gt 1 ]; then req P9 ERROR "lecturas de paquete-ae2900e rc $r/$r2/$r3"
elif [ $r = 0 ] && [ "$ev" = 53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f ] && [[ $vv == *2026-11-06.4* ]]; then req P9 CUMPLE "SHA256SUMS OK, evaluador 53e9f7bd…, $vv"
else req P9 NO_CUMPLE "sha256sum -c rc $r, evaluador $ev, $vv"; fi
# ---- informativo
info "eve: $(ls -l --time-style=+%FT%T /var/log/suricata/eve.json 2>&1)"
info "anillo: $(ls -1 /var/lib/ppi-motor-capture 2>/dev/null | wc -l) ficheros; primero $(ls -1 /var/lib/ppi-motor-capture 2>/dev/null | head -1); ahora $(date -u +%Y%m%d%H%M%S)"
fin
