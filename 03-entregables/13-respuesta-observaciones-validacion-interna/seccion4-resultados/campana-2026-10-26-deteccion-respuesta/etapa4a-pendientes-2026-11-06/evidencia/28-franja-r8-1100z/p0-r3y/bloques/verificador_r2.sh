# BLOQUE=verificador_r2  (P0 r2, punto 1, solo lectura): verificador del host desde ~/cf-e4/paquete-902991e
# (bytes idénticos a a1cea5e). rc del verificador: 0 -> CUMPLE, 1 -> NO_CUMPLE (con fallos), otro -> ERROR.
set -u
B=verificador_r2; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
H=${1:-}; P=$HOME/cf-e4/paquete-902991e/deploy/etapa4; X=()
case "$H" in
  bastion) f=$P/bastion/verificar_bastion.sh;;
  sensor1) f=$P/sensor1/verificar_sensor1.sh;;
  srvdmz)  f=$P/srvdmz/verificar_srvdmz.sh; R=/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z
           [ -d "$R" ] || { req P1.srvdmz ERROR "falta el respaldo $R"; fin; }; X=("$R");;
  *) echo "uso: host"; E=2; fin;;
esac
info "== $H $(hostname 2>&1) $(date -u +%FT%TZ)"
[ -r "$f" ] || { req "P1.$H" ERROR "no legible $f"; fin; }
info "$(sha256sum "$f" 2>&1)"
echo "-------- salida del verificador"
if [ "$H" = srvdmz ]; then CON_SUDO=1 bash "$f" "${X[@]}" < /dev/null; rc=$?; else bash "$f" < /dev/null; rc=$?; fi
echo "-------- fin de la salida del verificador"
case $rc in
  0) req "P1.$H" CUMPLE "verificador rc 0";;
  1) req "P1.$H" NO_CUMPLE "verificador rc 1 (con fallos)";;
  *) req "P1.$H" ERROR "verificador rc $rc";;
esac
fin
