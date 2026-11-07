#!/usr/bin/env bash
# [banco sin red] Lanzadores de la fase A con reloj, ssh y herramientas simulados. No se conecta a ningún host.
#   banco_lanzadores.sh CARPETA_DE_LOS_LANZADORES
L=${1:?}; T=$(mktemp -d); f=0
E24=evidencia/24-c1-registro-franja-domingo; E25=evidencia/25-franja-r6-20h
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
cat > "$T/bin/sleep" <<'FIN'
#!/usr/bin/env bash
exit 0
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
  rotacion) mkdir -p "\$2"; echo "\$1" > "\$2/modo"; [ "\$1" = rotacion ] && exit \${RC_A0B:-0}; exit \${RC_A7B:-0};;
  traslado) echo "bastion: ESTADO_FINAL=VERIFICADO rc=0";;
  p0) mkdir -p "\$2"; exit \${RC_A6:-0};;
  p8|previa|postcopia|forzar) mkdir -p "\${@: -1}"; [ "$2" = postcopia ] && exit \${RC_A3:-0};;
esac
exit 0
FIN
}
monta() {
  RR="$T/r$1"; TRAZA="$RR/traza"; W="$RR/copia"; mkdir -p "$RR/evidencia/14-ecarga-ejecucion"; : > "$TRAZA"
  export CF_R="$RR" CF_W="$W"
  echo T1 > "$RR/evidencia/14-ecarga-ejecucion/T1-referencias.txt"
  herr $E25/herramientas/00_referencias.sh referencias; herr $E25/herramientas/comprobar_rotacion.sh rotacion
  herr $E25/herramientas/comprobar_p8_r6.sh p8; herr $E24/herramientas/comprobar_p8_r5.sh p8
  herr evidencia/19-correccion-p11/laboratorio/previa.sh previa; herr evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh postcopia
  herr $E24/traslado/trasladar_bastion.sh traslado; herr $E24/variante/comprobar_forzar.sh forzar
  herr evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh tomar
  herr $E25/p0-r3w/p0_r3.sh p0; herr $E24/p0-r3v/p0_r3.sh p0
  EJ="$RR/evidencia/14-ecarga-ejecucion"
}
hora() { echo "$1" > "$RELOJ"; }
tiene() { grep -q "^$1 " "$TRAZA"; }

monta 1; hora 1794096299; bash "$L/lanzar_a1.sh" r6 >/dev/null; [ $? = 2 ] && [ ! -e "$EJ/A0.txt" ] && ok "A1 r6 antes de 19:05: no empieza" || no "A1 r6 temprano"
monta 2; hora 1794096300; RC_A0B=1 bash "$L/lanzar_a1.sh" r6 > "$T/o"; r=$?
[ $r = 10 ] && ! tiene referencias && ! tiene previa && [ ! -e "$EJ/A1-lanzador.ok" ] && ok "A0b rc 1: rc 10, ningún paso posterior" || no "A0b rc 1: r=$r"
RC_A0B=3 bash "$L/lanzar_a1.sh" r6 >/dev/null; [ $? = 1 ] && ok "segundo intento sobre un A0.txt existente: se niega" || no "reintento"
monta 3; hora 1794096300; RC_A0B=3 bash "$L/lanzar_a1.sh" r6 >/dev/null; [ $? = 10 ] && ok "A0b error de transporte: rc 10" || no "A0b rc 3"
h0=$(sha256sum < "$EJ/A0.txt"); hb=$(sha256sum < "$EJ/A0b-rotacion/modo")
bash "$L/lanzar_a2.sh" r6 >/dev/null; [ $? = 2 ] && ok "A2 antes del P0: no empieza" || no "A2 temprano"
hora 1794097800; bash "$L/lanzar_a2.sh" r6 >/dev/null; [ $? = 1 ] && ! tiene p0 && ok "A2 sin A0–A5 conformes: se niega" || no "A2 sin A1"
hora 1794098000; bash "$L/rearmar_r5.sh" "A0b no cumple" > "$T/o"; r=$?
D="$EJ/intento-r6-20h"
[ $r = 0 ] && [ ! -e "$EJ/A0.txt" ] && [ "$(sha256sum < "$D/A0.txt")" = "$h0" ] && [ "$(sha256sum < "$D/A0b-rotacion/modo")" = "$hb" ] && [ -e "$EJ/T1-referencias.txt" ] && grep -q 'A0b no cumple' "$D/MOTIVO.txt" \
  && ok "rearme: intento r6 apartado con los mismos hashes; T1 no se mueve" || no "rearme r=$r"
hora 1794103500; bash "$L/lanzar_a1.sh" r5 > "$T/o"; r=$?
[ $r = 0 ] && [ "$(sha256sum < "$D/A0.txt")" = "$h0" ] && [ -e "$EJ/A0.txt" ] && ! grep -q 'rotacion rotacion' <(tail -n 12 "$TRAZA") && ok "A1 r5 tras el rearme: rc 0, evidencia r6 intacta" || { no "A1 r5 r=$r"; cat "$T/o"; }
hora 1794105000; bash "$L/lanzar_a2.sh" r5 >/dev/null; r=$?; [ $r = 0 ] && [ -e "$EJ/A8.txt" ] && [ ! -e "$EJ/A7b-aprendizaje" ] && ok "A2 r5 tras el rearme: rc 0, sin A7b" || no "A2 r5 r=$r"

monta 4; hora 1794096300; bash "$L/lanzar_a1.sh" r6 >/dev/null; [ $? = 0 ] && ok "A1 r6 completo" || no "A1 r6"
hora 1794097800; PASO=5 bash "$L/lanzar_a2.sh" r6 > "$T/o"; r=$?
e=$(sed -n 's/^rotacion \([0-9]*\) aprendizaje.*/\1/p' "$TRAZA")
[ $r = 0 ] && [ -n "$e" ] && [ "$e" -ge 1794098100 ] && [ "$(sed -n 's/^p0 \([0-9]*\) .*/\1/p' "$TRAZA")" -lt 1794098100 ] && ok "A7b lanzado en $e, no antes de 1794098100, tras el P0" || { no "A7b r=$r e=$e"; cat "$T/o"; }

monta 5; hora 1794096300; bash "$L/lanzar_a1.sh" r6 >/dev/null; hora 1794097800; RC_A6=5 bash "$L/lanzar_a2.sh" r6 >/dev/null; r=$?
[ $r = 1 ] && ! tiene rotacion\ 1794098 && [ ! -e "$EJ/A8.txt" ] && [ "$(cat "$EJ/A6-p0-r3-inmediato.rc-driver")" = 5 ] && ok "P0 rc 5: se detiene antes de A7b" || no "P0 r=$r"
monta 6; hora 1794096300; bash "$L/lanzar_a1.sh" r6 >/dev/null; hora 1794097800; RC_A7B=1 PASO=5 bash "$L/lanzar_a2.sh" r6 >/dev/null; r=$?
[ $r = 1 ] && [ ! -e "$EJ/A8.txt" ] && ok "A7b rc 1: se detiene antes de A8" || no "A7b r=$r"
monta 7; hora 1794096300; RC_A3=1 bash "$L/lanzar_a1.sh" r6 >/dev/null; r=$?
[ $r = 1 ] && ! tiene traslado && [ ! -e "$EJ/A1-lanzador.ok" ] && ok "A3 rc 1: se detiene antes de A3b" || no "A3 r=$r"
monta 8; hora 1794096300; bash "$L/lanzar_a1.sh" r6 >/dev/null; hora 1794099000; bash "$L/lanzar_a2.sh" r6 >/dev/null; [ $? = 1 ] && ! tiene p0 && ok "A2 a las 19:50: se niega" || no "A2 tarde"
hora 1794097800; PASO=5 SSH_RESP=OCUPADA bash "$L/lanzar_a2.sh" r6 >/dev/null; [ $? = 1 ] && ! grep -q 'A8 CONFORME' "$EJ/A8.txt" && ok "A8 ocupada: rc 1" || no "A8"
hora 1794097800; PASO=5 SSH_RC=255 bash "$L/lanzar_a2.sh" r6 >/dev/null; r=$?
[ $r = 1 ] && grep -q 'ssh_rc=255 salida=LIBRE' "$EJ/A8.txt" && ! grep -q 'A8 CONFORME' "$EJ/A8.txt" && ok "A8 con ssh rc 255 aunque imprima LIBRE: rc 1 y rc registrado" || no "A8 ssh rc r=$r"
monta 10; hora 1794096300; bash "$L/lanzar_a1.sh" r6 >/dev/null; hora 1794097800; PASO=5 bash "$L/lanzar_a2.sh" r6 >/dev/null; r=$?
[ $r = 0 ] && [ "$(grep -c 'ssh_rc=0 salida=LIBRE' "$EJ/A8.txt")" = 2 ] && grep -q 'A8 CONFORME' "$EJ/A8.txt" && ok "A8 conforme: dos ssh rc 0 y LIBRE registrados" || no "A8 conforme r=$r"
monta 9; hora 1794096300; RC_A0B=1 bash "$L/lanzar_a1.sh" r6 >/dev/null; touch "$EJ/B3-p12"; hora 1794098000; bash "$L/rearmar_r5.sh" x >/dev/null; [ $? = 1 ] && [ -e "$EJ/A0.txt" ] && ok "rearme con fase B: se niega y no mueve nada" || no "rearme B"
rm "$EJ/B3-p12"; hora 1794098000; SSH_RESP=OCUPADA bash "$L/rearmar_r5.sh" x >/dev/null; [ $? = 1 ] && [ -e "$EJ/A0.txt" ] && ok "rearme con carpeta r6 en los hosts: se niega" || no "rearme X"
hora 1794103500; bash "$L/rearmar_r5.sh" x >/dev/null; [ $? = 1 ] && [ -e "$EJ/A0.txt" ] && ok "rearme a la hora de la r5: se niega" || no "rearme tarde"
echo "FALLOS=$f"; exit "$f"
