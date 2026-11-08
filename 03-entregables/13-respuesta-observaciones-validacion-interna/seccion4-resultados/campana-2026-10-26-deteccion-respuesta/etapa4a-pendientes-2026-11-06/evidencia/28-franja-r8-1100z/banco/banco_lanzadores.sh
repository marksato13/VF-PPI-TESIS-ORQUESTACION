#!/usr/bin/env bash
# [banco sin red] Lanzadores r8 de la fase A con reloj, ssh y herramientas simulados. No se conecta a ningún host.
#   banco_lanzadores.sh CARPETA_DE_LOS_LANZADORES
# Derivado de evidencia/25-franja-r6-20h/banco/banco_lanzadores.sh, con la franja r8 y la exigencia de F3.
L=${1:?}; T=$(mktemp -d); f=0
E24=evidencia/24-c1-registro-franja-domingo; E26=evidencia/28-franja-r8-1100z; EJR=evidencia/27-ecarga-r8-ejecucion
ok() { echo "OK    $*"; }; no() { echo "FALLO $*"; f=$((f + 1)); }
mkdir -p "$T/bin"
cat > "$T/bin/date" <<'FIN'
#!/usr/bin/env bash
if [ "${1:-}" = +%s ]; then e=$(cat "$RELOJ"); echo "$e"; echo $((e + ${PASO:-0})) > "$RELOJ"; else /usr/bin/date "$@"; fi
FIN
cat > "$T/bin/ssh" <<'FIN'
#!/usr/bin/env bash
echo "${SSH_RESP:-LIBRE}"; exit "${SSH_RC:-0}"
FIN
chmod +x "$T"/bin/*
export PATH="$T/bin:$PATH" RELOJ="$T/reloj"
herr() {  # ruta relativa, nombre
  mkdir -p "$(dirname "$RR/$1")"
  cat > "$RR/$1" <<FIN
#!/usr/bin/env bash
echo "$2 \$(cat "\$RELOJ") \$*" >> "$TRAZA"
case "$2" in
  referencias) mkdir -p "\$1"; echo "COPIA $RR";;
  traslado) echo "bastion: ESTADO_FINAL=VERIFICADO rc=0";;
  p0) mkdir -p "\$2"; exit \${RC_A6:-0};;
  p8|previa|postcopia|forzar) mkdir -p "\${@: -1}"; [ "$2" = postcopia ] && exit \${RC_A3:-0};;
esac
exit 0
FIN
}
monta() {  # monta N [sinF3|F3mal]
  RR="$T/r$1"; TRAZA="$RR/traza"; W="$RR/copia"; EJ="$RR/$EJR"; mkdir -p "$EJ" "$RR/evidencia/14-ecarga-ejecucion"; : > "$TRAZA"
  echo r5 > "$RR/evidencia/14-ecarga-ejecucion/A0.txt"
  export CF_R="$RR" CF_W="$W"
  herr $E26/herramientas/00_referencias.sh referencias; herr $E26/herramientas/comprobar_p8_r8.sh p8
  herr evidencia/19-correccion-p11/laboratorio/previa.sh previa; herr evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh postcopia
  herr $E24/traslado/trasladar_bastion.sh traslado; herr $E24/variante/comprobar_forzar.sh forzar
  herr evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh tomar
  herr $E26/p0-r3y/p0_r3.sh p0
  mkdir -p "$EJ/F3-forzar-con"
  case "${2:-}" in
    sinF3) rmdir "$EJ/F3-forzar-con";;
    F3mal) echo "RESULTADO_FORZAR rc=1 guion_sha=x REQ FORZAR.con NO_CUMPLE" > "$EJ/F3-forzar-con/resumen.txt";;
    *) echo "RESULTADO_FORZAR rc=0 guion_sha=x REQ FORZAR.con CUMPLE argv exacto" > "$EJ/F3-forzar-con/resumen.txt";;
  esac
}
hora() { echo "$1" > "$RELOJ"; }
tiene() { grep -q "^$1 " "$TRAZA"; }

monta 1; hora 1794132299; bash "$L/lanzar_a1.sh" r8 >/dev/null; [ $? = 2 ] && [ ! -e "$EJ/A0.txt" ] && ok "A1 r8 antes de las 10:05Z: no empieza" || no "A1 temprano"
bash "$L/lanzar_a1.sh" r5 >/dev/null; [ $? = 2 ] && ok "A1 con otra franja (r5): uso" || no "A1 r5"
monta 2 sinF3; hora 1794132300; bash "$L/lanzar_a1.sh" r8 >/dev/null; r=$?
[ $r = 1 ] && [ ! -e "$EJ/A0.txt" ] && ! tiene referencias && ok "sin F3: rc 1, ni A0 ni A1" || no "sin F3 r=$r"
monta 3 F3mal; hora 1794132300; bash "$L/lanzar_a1.sh" r8 >/dev/null; r=$?
[ $r = 1 ] && [ ! -e "$EJ/A0.txt" ] && ok "F3 NO_CUMPLE: rc 1, no empieza" || no "F3 mal r=$r"
monta 4; hora 1794132300; bash "$L/lanzar_a1.sh" r8 > "$T/o"; r=$?
[ $r = 0 ] && [ "$(cat "$EJ/A1-lanzador.ok")" = r8 ] && [ "$(cat "$RR/evidencia/14-ecarga-ejecucion/A0.txt")" = r5 ] && [ ! -e "$RR/evidencia/14-ecarga-ejecucion/A1-lanzador.ok" ] \
  && ok "A1 r8 completo: escribe en la 27 y no toca la 14" || { no "A1 r8 r=$r"; cat "$T/o"; }
bash "$L/lanzar_a1.sh" r8 >/dev/null; [ $? = 1 ] && ok "segundo intento sobre A0.txt existente: se niega" || no "reintento"
hora 1794133799; bash "$L/lanzar_a2.sh" r8 >/dev/null; [ $? = 2 ] && ! tiene p0 && ok "A2 antes de las 10:30Z: no empieza" || no "A2 temprano"
hora 1794133800; PASO=5 bash "$L/lanzar_a2.sh" r8 > "$T/o"; r=$?
[ $r = 0 ] && [ "$(grep -c 'ssh_rc=0 salida=LIBRE' "$EJ/A8.txt")" = 2 ] && grep -q 'A8 CONFORME' "$EJ/A8.txt" && [ "$(cat "$EJ/A6-p0-r3-inmediato.rc-driver")" = 0 ] \
  && grep -q "^p0 [0-9]* inmediato $EJ/A6-p0-r3-inmediato" "$TRAZA" && ok "A2 r8 completo: P0 r3x inmediato, A7, A8 conforme" || { no "A2 r8 r=$r"; cat "$T/o"; }
monta 5; hora 1794132300; RC_A3=1 bash "$L/lanzar_a1.sh" r8 >/dev/null; r=$?
[ $r = 1 ] && ! tiene traslado && [ ! -e "$EJ/A1-lanzador.ok" ] && ok "A3 rc 1: se detiene antes de A3b" || no "A3 r=$r"
monta 6; hora 1794133800; bash "$L/lanzar_a1.sh" r8 >/dev/null; [ $? = 1 ] && [ ! -e "$EJ/A0.txt" ] && ok "A1 a la hora del P0: se niega" || no "A1 tarde"
monta 7; hora 1794132300; bash "$L/lanzar_a1.sh" r8 >/dev/null; hora 1794133800; RC_A6=5 bash "$L/lanzar_a2.sh" r8 >/dev/null; r=$?
[ $r = 1 ] && [ ! -e "$EJ/A8.txt" ] && [ "$(cat "$EJ/A6-p0-r3-inmediato.rc-driver")" = 5 ] && ok "P0 rc 5: se detiene antes de A7 y A8" || no "P0 r=$r"
monta 8; hora 1794132300; bash "$L/lanzar_a1.sh" r8 >/dev/null; hora 1794135000; bash "$L/lanzar_a2.sh" r8 >/dev/null; [ $? = 1 ] && ! tiene p0 && ok "A2 a las 10:50Z: se niega" || no "A2 tarde"
hora 1794133800; PASO=5 SSH_RESP=OCUPADA bash "$L/lanzar_a2.sh" r8 >/dev/null; [ $? = 1 ] && ! grep -q 'A8 CONFORME' "$EJ/A8.txt" && ok "A8 ocupada: rc 1" || no "A8 ocupada"
monta 9; hora 1794132300; bash "$L/lanzar_a1.sh" r8 >/dev/null; hora 1794133800; PASO=5 SSH_RC=255 bash "$L/lanzar_a2.sh" r8 >/dev/null; r=$?
[ $r = 1 ] && grep -q 'ssh_rc=255 salida=LIBRE' "$EJ/A8.txt" && ! grep -q 'A8 CONFORME' "$EJ/A8.txt" && ok "A8 con ssh rc 255 aunque imprima LIBRE: rc 1 y rc registrado" || no "A8 ssh rc r=$r"
grep -q '20261108T1100Z' "$L/lanzar_a2.sh" && ! grep -q 'T0300Z' "$L/lanzar_a2.sh" && ok "A8 consulta la carpeta ecarga-v2-ejecucion-20261108T1100Z" || no "carpeta X"
echo "FALLOS=$f"; rm -rf "$T"; exit "$f"
