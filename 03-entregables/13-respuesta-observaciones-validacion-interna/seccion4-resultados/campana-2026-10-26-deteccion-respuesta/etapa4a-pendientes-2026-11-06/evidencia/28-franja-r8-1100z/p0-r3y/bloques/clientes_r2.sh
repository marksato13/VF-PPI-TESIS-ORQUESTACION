# BLOQUE=clientes_r2  (P0 r2, puntos 4, 5a y 10, solo lectura) ejecutado en el bastión contra clientes (10.10.20.20).
# generadores.sh de paquete-902991e: configuracion, estado, comprobar-parado y permisos (ninguna arranca ni para nada).
# Códigos de generadores.sh: 0 consulta completa y conforme; 4 leído pero NO conforme; 2/3/5 o 255 (ssh) -> ERROR.
set -u -o pipefail
B=clientes_r2; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
G=$HOME/cf-e4/paquete-902991e/deploy/etapa4/ecarga/generadores.sh
G_SHA=0badeac51ccf2339122412a7607b01176b22f97413e927134bb11ab208a3f662
GEN_SHA=ae5134a778e66d90f5c3fbcd47323e328f3422cf4ba8d5197649f402c1d4cdc3
CLI=(ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$HOME/.ssh/cyberflow-to-clientes" adminclientes@10.10.20.20)
mapa() {  # mapa ID RC DESCRIPCION
  case $2 in 0) req "$1" CUMPLE "$3 rc 0";; 4) req "$1" NO_CUMPLE "$3 rc 4 (leído, no conforme)";; *) req "$1" ERROR "$3 rc $2";; esac
}
if ! [ -r "$G" ]; then
  req X.generadores_sh ERROR "no legible $G"
  for i in P10 P4.parado X.estado_generadores X.permisos; do req $i ERROR "sin generadores.sh"; done
else
  s=$(sha256sum < "$G" | cut -c1-64); r=$?
  if [ $r != 0 ]; then req X.generadores_sh ERROR "sha256sum rc $r"
  elif [ "$s" = "$G_SHA" ]; then req X.generadores_sh CUMPLE "generadores.sh $s ($(grep -m1 '^VERSION=' "$G"))"
  else req X.generadores_sh NO_CUMPLE "generadores.sh $s distinto de $G_SHA"; fi
  for o in configuracion estado comprobar-parado permisos; do
    echo "######## generadores.sh $o"
    "${CLI[@]}" "bash -s $o" < "$G"; r=$?
    info "rc_$o=$r"
    case $o in
      configuracion)    mapa P10 $r "generadores.sh configuracion";;
      estado)           [ $r = 0 ] && req X.estado_generadores CUMPLE "estado leído (rc 0)" || req X.estado_generadores ERROR "generadores.sh estado rc $r";;
      comprobar-parado) mapa P4.parado $r "generadores.sh comprobar-parado";;
      permisos)         mapa X.permisos $r "generadores.sh permisos";;
    esac
  done
fi
echo "######## clientes: generador, zona y reloj"
l=$("${CLI[@]}" 'echo "EPOCH $(date -u +%s)"; s=$(sha256sum < "$HOME/laboratorio/clientes_lab.py") || exit 3; echo "GEN ${s:0:64}"; timedatectl show -p Timezone -p NTPSynchronized || exit 3' < /dev/null); r=$?
printf '%s\n' "$l" | sed 's/^/INFO clientes /'
if [ $r != 0 ]; then
  for i in P4.generador P5a.clientes X.sincronizado.clientes; do req $i ERROR "lecturas en clientes rc $r"; done
else
  g=$(sed -n 's/^GEN //p' <<<"$l"); z=$(sed -n 's/^Timezone=//p' <<<"$l"); n=$(sed -n 's/^NTPSynchronized=//p' <<<"$l")
  case "$g" in "") req P4.generador ERROR "sin hash del generador";; "$GEN_SHA") req P4.generador CUMPLE "clientes_lab.py $g";;
               *) req P4.generador NO_CUMPLE "clientes_lab.py $g distinto de $GEN_SHA";; esac
  case "$z" in "") req P5a.clientes ERROR "sin Timezone";; Etc/UTC|UTC) req P5a.clientes CUMPLE "Timezone=$z";; *) req P5a.clientes NO_CUMPLE "Timezone=$z";; esac
  case "$n" in yes) req X.sincronizado.clientes CUMPLE "NTPSynchronized=yes";; no) req X.sincronizado.clientes NO_CUMPLE "NTPSynchronized=no";;
               *) req X.sincronizado.clientes ERROR "sin NTPSynchronized";; esac
fi
fin
