#!/usr/bin/env bash
# [LAPTOP Git Bash] Comprobación ANTICIPADA de las precondiciones de P0 (PROTOCOLO-CARGA-v2 r4 §3.5). SOLO LECTURA.
#   bash p0_anticipado.sh SALIDA_NUEVA
# No arranca ni para generadores ni muestreadores, no programa nada, no cambia servicios ni permisos.
# Cada bloque viaja en base64 dentro del argumento de ssh (sin stdin ni tuberías de PowerShell) y se ejecuta con
# «bash -s» en su host; se guardan <bloque>.stdout, .stderr y .rc. Antes de enviarlo se exige que no tenga CR, y el
# host imprime el sha256 de lo que recibió (primera línea), que se compara con el del fichero local.
# NO sustituye al P0 inmediatamente anterior al ensayo (ver el README de la carpeta).
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
BL="$AQUI/bloques"
K="${CF_CLAVE:-$HOME/.ssh/id_ed25519}"; B=gadmin@10.10.10.30; O="-o BatchMode=yes -o ConnectTimeout=10"
S="${1:?uso: p0_anticipado.sh SALIDA_NUEVA}"
[ -e "$S" ] && { echo "PRECONDICION: $S ya existe"; exit 2; }
mkdir -p "$S" || exit 2
declare -A DEST=([bastion]="" [sensor1]="m4rk@10.10.60.11 ~/.ssh/cyberflow-to-sensor" [srvdmz]="adminsrvdmz@10.10.30.10 ~/.ssh/cyberflow-to-srv")
remoto() {  # remoto NOMBRE HOST FICHERO_BLOQUE [ARGS...]
  local n=$1 h=$2 f=$3; shift 3
  local cr; cr=$(tr -cd '\r' < "$f" | wc -c) || { echo "$n ERROR lectura de $f" | tee -a "$S/resumen.txt"; return; }
  [ "$cr" -eq 0 ] || { echo "$n ERROR $f tiene $cr CR: no se envía" | tee -a "$S/resumen.txt"; echo 2 > "$S/$n.rc"; return; }
  local l b r d k; l=$(sha256sum < "$f" | cut -c1-64); b=$(base64 -w0 < "$f")
  r="set -o pipefail; printf %s $b | base64 -d | sha256sum && printf %s $b | base64 -d | bash -s -- $*"
  if [ "$h" = bastion ]; then ssh $O -i "$K" "$B" "$r" < /dev/null > "$S/$n.stdout" 2> "$S/$n.stderr"; rc=$?
  else read -r d k <<<"${DEST[$h]}"; ssh $O -i "$K" "$B" "ssh $O -i $k $d \"$r\"" < /dev/null > "$S/$n.stdout" 2> "$S/$n.stderr"; rc=$?; fi
  echo "$rc" > "$S/$n.rc"
  local rec; rec=$(head -1 "$S/$n.stdout" | cut -c1-64)
  [ "$rec" = "$l" ] && t=igual || t="DISTINTO(${rec:-nada})"
  echo "$n host=$h rc=$rc transporte=$t bloque=$(basename "$f") sha=${l:0:12}" | tee -a "$S/resumen.txt"
}
{ echo "p0_anticipado 2026-11-06.1"; echo "inicio $(date -u +%FT%TZ) portatil_epoch $(date -u +%s)"; } > "$S/resumen.txt"
remoto 00-estado-bastion  bastion "$BL/estado_host.sh" bastion
remoto 00-estado-sensor1  sensor1 "$BL/estado_host.sh" sensor1
remoto 00-estado-srvdmz   srvdmz  "$BL/estado_host.sh" srvdmz
remoto 01-verificar-bastion bastion "$BL/verificador.sh" bastion
remoto 02-verificar-sensor1 sensor1 "$BL/verificador.sh" sensor1
remoto 03-verificar-srvdmz  srvdmz  "$BL/verificador.sh" srvdmz
remoto 04-precheck-s11      bastion "$BL/precheck.sh" p0-anticipado
remoto 05-clientes          bastion "$BL/clientes_desde_bastion.sh"
remoto 06-sensor1-comprobar sensor1 "$BL/sensor1_p0.sh" "p0-anticipado-$(date -u +%Y%m%dT%H%M%SZ)"
echo "fin $(date -u +%FT%TZ) portatil_epoch $(date -u +%s)" >> "$S/resumen.txt"
