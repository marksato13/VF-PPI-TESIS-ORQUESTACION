#!/usr/bin/env bash
# [LAPTOP Git Bash] Comprobación POST-COPIA r3 del paquete 902991e en bastión, Sensor1 y srv-dmz. SOLO LECTURA.
#   bash comprobar_post_copia_r3.sh SALIDA_NUEVA
# r3: envía post_copia_host_r3.sh (LC_ALL=C coherente y comm --check-order). Las escrituras del resumen se comprueban
#     (sin tee): si alguna falla, rc 4. El resto es idéntico a la r2, que se conserva.
# Transporte: el guion del host viaja en base64 DENTRO del argumento de ssh (no por stdin ni por una tubería de
# PowerShell, que añade \r\n al final). El host decodifica, imprime el sha256 de los bytes recibidos y ejecuta esos
# mismos bytes. El portátil exige que ese sha256 sea el del fichero local, que no tiene ningún CR.
# Por host guarda <h>.stdout, <h>.stderr y <h>.rc en SALIDA (que debe NO existir: nunca se sobrescribe).
# Códigos: 0 los 3 CONFORME · 2 precondición (uso, SALIDA existente, CR en el guion, herramientas) · 4 algún host no
#          conforme (se listan). Estados por host: CONFORME, NO_CONFORME, ERROR_LECTURA, SSH_FALLIDO,
#          TRANSPORTE_DISTINTO, SIN_RESULTADO, INCOHERENTE.
set -u -o pipefail
VERSION_DRIVER="comprobar_post_copia r3 2026-11-06.2"
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
G="$AQUI/post_copia_host_r3.sh"
EV=0
w() { printf '%s\n' "$*"; printf '%s\n' "$*" >> "$S/resumen.txt" || { EV=1; echo "ERROR_EVIDENCIA resumen.txt" >&2; }; }
K="${CF_CLAVE:-$HOME/.ssh/id_ed25519}"
B=gadmin@10.10.10.30
O="-o BatchMode=yes -o ConnectTimeout=10"
S="${1:-}"
fallar() { echo "PRECONDICION: $1" >&2; echo "RESULTADO_GLOBAL rc=2 PRECONDICION"; exit 2; }
[ -n "$S" ] || fallar "uso: comprobar_post_copia_r3.sh SALIDA_NUEVA"
[ -e "$S" ] && fallar "$S ya existe (no se sobrescribe evidencia)"
for t in ssh base64 sha256sum tr wc; do command -v "$t" > /dev/null || fallar "falta $t"; done
[ -f "$G" ] && [ -r "$G" ] || fallar "no se lee $G"
cr=$(tr -cd '\r' < "$G" | wc -c) || fallar "no se pudieron contar los CR de $G"
[ "$cr" -eq 0 ] 2>/dev/null || fallar "$G contiene ${cr:-?} CR: solo se envía con finales LF"
LOCAL=$(sha256sum < "$G" | cut -c1-64) && [ ${#LOCAL} = 64 ] || fallar "sha256 de $G"
B64=$(base64 -w0 < "$G") && [ -n "$B64" ] || fallar "base64 de $G"
mkdir -p "$S" || fallar "no se crea $S"
{ echo "$VERSION_DRIVER"; echo "inicio $(date -u +%FT%TZ)"; echo "guion $(basename "$G") sha256 $LOCAL bytes $(wc -c < "$G") CR 0"; } > "$S/resumen.txt" \
  || fallar "no se escribe $S/resumen.txt"

orden() {  # orden HOST -> orden remota que imprime el sha de lo recibido y ejecuta esos bytes
  printf 'set -o pipefail; printf %%s %s | base64 -d | sha256sum && printf %%s %s | base64 -d | N=%s bash -s' "$B64" "$B64" "$1"
}
ok=0; malos=""
for h in bastion sensor1 srvdmz; do
  case $h in
    bastion) ssh $O -i "$K" "$B" "$(orden bastion)" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    sensor1) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"$(orden sensor1)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    srvdmz) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \"$(orden srvdmz)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
  esac
  echo "$rc" > "$S/$h.rc"
  recibido=$(head -1 "$S/$h.stdout" | cut -c1-64)
  ultima=$(grep '^RESULTADO ' "$S/$h.stdout" | tail -1)
  ultima_linea=$(tail -1 "$S/$h.stdout")
  rcr=$(printf '%s' "$ultima" | sed -nE 's/^RESULTADO [^ ]+ rc=([0-9]+) .*/\1/p')
  est=$(printf '%s' "$ultima" | sed -nE 's/.* estado=([A-Z_]+).*/\1/p')
  if [ "$rc" = 255 ]; then e=SSH_FALLIDO
  elif [ "$recibido" != "$LOCAL" ]; then e=TRANSPORTE_DISTINTO
  elif [ -z "$ultima" ] || [ "$ultima" != "$ultima_linea" ]; then e=SIN_RESULTADO
  elif ! printf '%s' "$ultima" | grep -q "^RESULTADO $h "; then e=INCOHERENTE
  elif [ "$rcr" != "$rc" ]; then e=INCOHERENTE
  elif [ "$rc" = 0 ] && [ "$est" = CONFORME ]; then e=CONFORME
  elif [ "$rc" = 0 ]; then e=INCOHERENTE
  else e=${est:-INCOHERENTE}; fi
  [ "$e" = CONFORME ] && ok=$((ok + 1)) || malos="$malos $h"
  w "HOST $h rc=$rc estado=$e recibido=${recibido:-ninguno} $(printf '%s' "$ultima" | sed -nE 's/.*(ok=[0-9]+\/[0-9]+).*/\1/p')"
done
printf 'fin %s\n' "$(date -u +%FT%TZ)" >> "$S/resumen.txt" || EV=1
if [ "$EV" != 0 ]; then g="RESULTADO_GLOBAL rc=4 EVIDENCIA_INCOMPLETA ($ok/3 conformes, pero no se pudo escribir todo resumen.txt)"; rg=4
elif [ "$ok" = 3 ]; then g="RESULTADO_GLOBAL rc=0 CONFORME 3/3 (bastion, sensor1, srvdmz)"; rg=0
else g="RESULTADO_GLOBAL rc=4 NO_CONFORME $ok/3; sin conformidad en:$malos"; rg=4; fi
w "$g"
[ "$EV" = 0 ] || rg=4
exit $rg
