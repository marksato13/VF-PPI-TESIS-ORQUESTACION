# BLOQUE=sensor1_r2  (P0 r2, puntos 5a, 5b, 6, 7, 9, 11 y 13, solo lectura) en Sensor1.
#   argumentos: NOMBRE_DIR PAQUETE SUMAS_ESPERADAS FRANJA_INI FRANJA_FIN
# «comprobar» NUNCA se ejecuta con una versión que pueda escribir caché:
#   - si ecarga/sensor1_muestreadores.sh del paquete ES la 2026-11-06.3 publicada (4ed43856…), se ejecuta tal cual;
#   - si es la 2026-11-06.2 de 902991e (25fb732d…), se DERIVA en memoria la .3 con las mismas tres sustituciones del
#     commit del producto (VERSION, -B en la consulta de VERSION y en obs_pcap --en-seco), se exige que el texto derivado
#     tenga EXACTAMENTE el sha de la .3 publicada y se ejecuta ese texto con $0 = ruta del guion del paquete (así E y P
#     se resuelven igual). No se escribe ni se despliega ningún fichero;
#   - con cualquier otro sha, no se ejecuta (ERROR).
# Además se compara el inventario completo del paquete (tipo, modo, tamaño, mtime y ruta) antes y después.
set -u -o pipefail
B=sensor1_r2; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
[ $# = 5 ] || { echo "uso: NOMBRE PAQUETE SUMAS FRANJA_INI FRANJA_FIN"; E=2; fin; }
D=$HOME/cf-e4/$1; P=$HOME/cf-e4/paquete-$2; SUMAS=$3; FI=$4; FF=$5
S=$P/deploy/etapa4/ecarga/sensor1_muestreadores.sh
V2=25fb732ddc15bc83f1f1a79e6e9ccb7ca0cd867a2dfd48270a26dd9ba03c915b
V3=4ed4385674e9f731c7d50f12b132d86a0a3625355df24ebaf4fa9fa0c8342b6e
FIN_EPOCH=1794197760; FIN_ISO=2026-11-09T04:16:00Z
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
  for i in P13.sumas P13.hashes P13.inventario X.mecanismo_sin_escritura P11 P11.retencion P6.home P6.mem P7 X.dir_no_creado X.paquete_sin_cambios; do
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
    an=$(LC_ALL=C comm -13 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre") | tr '\n' ' '); au=$(LC_ALL=C comm -23 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre") | tr '\n' ' ')
    n=$(grep -c . <<<"$pre")
    [ -z "${an// /}${au// /}" ] && req P13.inventario CUMPLE "$n ficheros = manifiesto" || req P13.inventario NO_CUMPLE "presentes $n; añadidos: ${an:-ninguno}; ausentes: ${au:-ninguno}"
  fi
  snap() { (cd "$P" && find . -printf '%y %m %s %T@ %p\n' | LC_ALL=C sort); }
  a0=$(snap); r0=$?
  # ---- mecanismo sin escritura
  v=$(sha256sum < "$S" | cut -c1-64); r=$?; txt=""
  if [ $r != 0 ]; then req X.mecanismo_sin_escritura ERROR "no se lee $S"
  elif [ "$v" = "$V3" ]; then txt=$(cat "$S") && req X.mecanismo_sin_escritura CUMPLE "sensor1_muestreadores.sh 2026-11-06.3 publicado ($V3)" || req X.mecanismo_sin_escritura ERROR "cat $S"
  elif [ "$v" = "$V2" ]; then
    txt=$(sed -e '2s/VERSION 2026-11-06\.2\./VERSION 2026-11-06.3./' -e '31s/python3 -I -c /python3 -I -B -c /' -e '66s/python3 -I "\$P/python3 -I -B "$P/' "$S"); r=$?
    d=$(printf '%s\n' "$txt" | sha256sum | cut -c1-64)
    if [ $r = 0 ] && [ "$d" = "$V3" ]; then req X.mecanismo_sin_escritura CUMPLE "derivada en memoria la 2026-11-06.3 ($V3) desde la .2 del paquete; nada escrito"
    else req X.mecanismo_sin_escritura ERROR "el texto derivado tiene sha ${d:-?} (rc $r), no el de la .3: no se ejecuta"; txt=""; fi
  else req X.mecanismo_sin_escritura ERROR "sensor1_muestreadores.sh $v desconocido: no se ejecuta"; fi
  # ---- 6, 7, 11
  if [ -z "$txt" ]; then
    for i in P11 P11.retencion P6.home P6.mem P7 X.dir_no_creado; do req $i ERROR "comprobar no ejecutado (mecanismo)"; done
  elif [ -e "$D" ]; then
    for i in P11 P11.retencion P6.home P6.mem P7 X.dir_no_creado; do req $i ERROR "ya existe $D: comprobar no ejecutado"; done
  else
    echo "######## sensor1_muestreadores.sh comprobar $D $FIN_EPOCH $FIN_ISO ($(date -u +%FT%TZ))"
    out=$(bash -c "$txt" "$S" comprobar "$D" "$FIN_EPOCH" "$FIN_ISO" < /dev/null 2>&1); r=$?
    printf '%s\n' "$out" | sed 's/^/| /'; info "rc_comprobar=$r"
    case $r in 0) req P11 CUMPLE "comprobar rc 0";; 1) req P11 NO_CUMPLE "comprobar rc 1: $(grep '^FALLO' <<<"$out" | tr '\n' ';' | cut -c1-300)";; *) req P11 ERROR "comprobar rc $r";; esac
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
