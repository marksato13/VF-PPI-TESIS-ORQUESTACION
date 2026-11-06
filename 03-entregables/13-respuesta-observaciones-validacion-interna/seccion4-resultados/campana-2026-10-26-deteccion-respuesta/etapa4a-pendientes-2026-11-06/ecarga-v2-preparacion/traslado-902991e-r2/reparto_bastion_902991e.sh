# reparto_bastion_902991e.sh — revisión r2 (traslado 2026-11-07.1). Sustituye al bloque REMOTO (heredoc) de
# evidencia/13-correccion-s14/paquete_902991e.sh. Se ejecuta EN EL BASTIÓN con `bash -s`, lanzado por
# paquete_902991e.sh. Entorno: RUN, TGZ, SUMAS. Espera en /tmp del bastión cf-e4-stage-902991e.$RUN.tgz y
# cf-e4-op_host-902991e.$RUN.sh. Copia el tgz a Sensor1 y srv-dmz, ejecuta op_host en los tres hosts y conserva el
# código REAL de cada uno. SOLO copia y verifica.
#
# Salida: una línea por host, exactamente "RESULTADO <host> rc=<n> estado=<ESTADO>", para bastion, sensor1 y srvdmz.
# Códigos por host: los de op_host (0, 2–11) y además
#   30 SCP_FALLIDO (bastión -> host)   31 FICHEROS_AUSENTES_EN_BASTION   32 TGZ_DISTINTO_EN_BASTION
#   96 USO_REPARTO   97 INCOHERENTE (rc y ESTADO_FINAL no coinciden)   98 SIN_ESTADO_FINAL   255 SSH_FALLIDO
# rc del guion: 0 solo si los tres hosts terminaron con rc 0 y estado VERIFICADO o YA_VERIFICADO; si no, 1.
set -u -o pipefail
C=902991e
RUN=${RUN:-}; TGZ=${TGZ:-}; SUMAS=${SUMAS:-}
declare -A RC EST
TW=""
fijar() { RC[$1]=$2; EST[$1]=$3; printf 'reparto: %s %s rc=%s %s\n' "$1" "$4" "$2" "$3"; }
todos() { local h; for h in bastion sensor1 srvdmz; do fijar "$h" "$1" "$2" "$3"; done; }
salir() {
  local h ok=1
  for h in bastion sensor1 srvdmz; do
    printf 'RESULTADO %s rc=%s estado=%s\n' "$h" "${RC[$h]:-98}" "${EST[$h]:-SIN_RESULTADO}"
    case "${RC[$h]:-98}:${EST[$h]:-}" in 0:VERIFICADO|0:YA_VERIFICADO) ;; *) ok=0;; esac
  done
  [ $ok -eq 1 ] && exit 0
  exit 1
}
limpiar() {
  local r
  if [ -n "$STG" ]; then
    rm -f -- "$STG" "$OPH"; r=$?
    printf 'reparto: bastion limpieza-tmp rc=%s %s\n' $r "$([ $r -eq 0 ] && echo eliminados || echo NO-ELIMINADOS)"
  fi
  if [ -n "$TW" ]; then rm -rf -- "$TW" || printf 'reparto: bastion limpieza-temporal rc=%s NO-ELIMINADO %s\n' $? "$TW"; fi
  return 0
}
ejecutar() {   # ejecutar <host> <rc de ssh/bash> <fichero de salida>: interpreta el código REAL y ESTADO_FINAL
  local h=$1 r=$2 out=$3 l est erc
  cat -- "$out"
  l=$(grep -E "^$h: ESTADO_FINAL=[A-Z0-9_]+ rc=[0-9]+\$" "$out" | tail -1)
  est=$(printf '%s' "$l" | sed -E 's/^.*ESTADO_FINAL=([A-Z0-9_]+) rc=([0-9]+)$/\1/')
  erc=$(printf '%s' "$l" | sed -E 's/^.*ESTADO_FINAL=([A-Z0-9_]+) rc=([0-9]+)$/\2/')
  if [ "$r" -eq 255 ]; then fijar "$h" 255 SSH_FALLIDO op_host
  elif [ -z "$l" ]; then fijar "$h" "$([ "$r" -eq 0 ] && echo 98 || echo "$r")" SIN_ESTADO_FINAL op_host
  elif [ "$erc" != "$r" ]; then fijar "$h" 97 INCOHERENTE "op_host(rc=$r,final=$erc)"
  else fijar "$h" "$r" "$est" op_host
  fi
}

if ! [[ "$RUN" =~ ^[0-9]{8}T[0-9]{6}Z-[0-9]+$ ]] || ! [[ "$TGZ" =~ ^[0-9a-f]{64}$ ]] || ! [[ "$SUMAS" =~ ^[0-9a-f]{64}$ ]]; then
  STG=""; OPH=""; todos 96 USO_REPARTO entorno; salir
fi
STG="/tmp/cf-e4-stage-$C.$RUN.tgz"
OPH="/tmp/cf-e4-op_host-$C.$RUN.sh"
TW=$(mktemp -d -t cf-e4-reparto.XXXXXX) || { TW=""; todos 96 USO_REPARTO mktemp; limpiar; salir; }
if [ ! -f "$STG" ] || [ ! -f "$OPH" ]; then todos 31 FICHEROS_AUSENTES_EN_BASTION recepcion; limpiar; salir; fi
x=$(sha256sum -- "$STG" | cut -c1-64)
if [ "$x" != "$TGZ" ]; then todos 32 TGZ_DISTINTO_EN_BASTION "recepcion(${x:-ilegible})"; limpiar; salir; fi
printf 'reparto: bastion recepcion rc=0 tgz=%s\n' "$TGZ"

O="-o BatchMode=yes -o ConnectTimeout=10"
for d in 'sensor1 m4rk@10.10.60.11 cyberflow-to-sensor' 'srvdmz adminsrvdmz@10.10.30.10 cyberflow-to-srv'; do
  set -- $d; h=$1; u=$2; k="$HOME/.ssh/$3"
  scp -q $O -i "$k" "$STG" "$u:$STG" < /dev/null; r=$?
  if [ $r -ne 0 ]; then
    fijar "$h" 30 SCP_FALLIDO "scp-paquete(rc=$r)"
    ssh $O -i "$k" "$u" "rm -f -- $STG" < /dev/null; r=$?          # retirar un tgz parcial; nunca oculta el fallo
    printf 'reparto: %s limpieza-tgz-parcial rc=%s\n' "$h" $r
    continue
  fi
  printf 'reparto: %s scp-paquete rc=0\n' "$h"
  ssh $O -i "$k" "$u" "N=$h RUN=$RUN TGZ=$TGZ SUMAS=$SUMAS bash -s" < "$OPH" > "$TW/$h.out" 2>&1; r=$?
  ejecutar "$h" $r "$TW/$h.out"
done
N=bastion RUN=$RUN TGZ=$TGZ SUMAS=$SUMAS bash "$OPH" < /dev/null > "$TW/bastion.out" 2>&1; r=$?
ejecutar bastion $r "$TW/bastion.out"
limpiar
salir
