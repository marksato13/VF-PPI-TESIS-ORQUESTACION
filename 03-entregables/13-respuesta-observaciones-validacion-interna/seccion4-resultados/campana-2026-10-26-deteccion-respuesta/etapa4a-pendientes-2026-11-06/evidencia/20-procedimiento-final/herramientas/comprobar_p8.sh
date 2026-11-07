#!/usr/bin/env bash
# [LAPTOP Git Bash] P8 de E-carga v2 (PROTOCOLO-CARGA-v2 r4 §3.5, punto 8): «ventana fijada en epoch y publicada, con su
# commit, ANTES de T_g». Comprobación DOCUMENTAL y de SOLO LECTURA (git fetch + API de GitHub, nada se escribe en el
# repositorio ni en los hosts). VERSION 2026-11-07.1
#   comprobar_p8.sh SALIDA_NUEVA
# Evidencia que exige, toda a la vez:
#   1. el commit que publicó la franja (8f17273, protocolo v2 r1) y el de la revisión vigente r4 (034d57d) están en
#      origin/main;
#   2. la tabla de §3.2 (filas «| …» entre «### 3.2» y «### 3.3») de PROTOCOLO-CARGA-v2.md en origin/main es idéntica
#      byte a byte a la publicada en 8f17273, y contiene T_g 1794193200 y la ventana 1794194100–1794197700;
#   3. el registro de pushes de GitHub (API /activity) fecha la llegada a main de 8f17273 y de 034d57d ANTES de T_g;
#   4. origin/main declara «Revisión vigente: r4».
# rc: 0 CUMPLE · 1 NO_CUMPLE (franja cambiada, no publicada o publicada después de T_g) · 3 ERROR (no se pudo leer; nunca
# se aprueba) · 2 uso.
set -u -o pipefail
export LC_ALL=C
S="${1:?uso: comprobar_p8.sh SALIDA_NUEVA}"; [ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
D="${CF_DOCS:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio}"
REPO=marksato13/VF-PPI-TESIS-ORQUESTACION
F=03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06/PROTOCOLO-CARGA-v2.md
C_FRANJA=8f17273b51ea72d94c394ef740b2dc9456690f45; C_R4=034d57d
TG=1794193200
mkdir "$S" || exit 2
exec > >(tee "$S/p8.txt") 2>&1
fin() { echo "REQ P8 $1 $2"; echo "FIN_P8 rc=$3"; echo "$3" > "$S/rc"; exit "$3"; }
echo "INFO p8 $(date -u +%FT%TZ) epoch $(date -u +%s); T_g $TG ($(date -u -d @$TG +%FT%TZ))"
git -C "$D" fetch -q origin || fin ERROR "git fetch falló" 3
M=$(git -C "$D" rev-parse origin/main) || fin ERROR "no se pudo leer origin/main" 3
C_R4=$(git -C "$D" rev-parse "$C_R4^{commit}") || fin ERROR "no existe $C_R4" 3
echo "INFO origin/main $M"
for c in $C_FRANJA $C_R4; do
  git -C "$D" merge-base --is-ancestor "$c" "$M"; r=$?
  case $r in 0) echo "INFO $c está en origin/main ($(git -C "$D" show -s --format='%ci, «%s»' "$c"))";;
             1) fin NO_CUMPLE "$c no está en origin/main" 1;; *) fin ERROR "merge-base rc $r" 3;; esac
done
tabla() { git -C "$D" show "$1:$F" | sed -n '/^### 3.2/,/^### 3.3/p' | grep -E '^\| '; }
t0=$(tabla $C_FRANJA) && t1=$(tabla "$M") || fin ERROR "no se pudo leer la tabla de §3.2" 3
h0=$(printf '%s\n' "$t0" | sha256sum | cut -c1-64); h1=$(printf '%s\n' "$t1" | sha256sum | cut -c1-64)
echo "INFO tabla §3.2 en 8f17273 sha256 $h0"; echo "INFO tabla §3.2 en origin/main sha256 $h1"
printf '%s\n' "$t1" | sed 's/^/TABLA /'
[ "$h0" = "$h1" ] || fin NO_CUMPLE "la tabla de §3.2 cambió desde 8f17273: la franja publicada no es la misma" 1
grep -q '1794193200' <<<"$t1" && grep -q '1794194100–1794197700' <<<"$t1" || fin NO_CUMPLE "la tabla no contiene T_g 1794193200 y la ventana 1794194100–1794197700" 1
git -C "$D" show "$M:$F" | grep -q '^\*\*Revisión vigente: r4' || fin NO_CUMPLE "origin/main no declara la revisión vigente r4" 1
A=$(gh api "repos/$REPO/activity?per_page=100&time_period=month&ref=refs/heads/main" \
      --jq '.[] | [.after, .timestamp, .activity_type, .before] | @tsv' 2>&1) || fin ERROR "API de GitHub /activity: $(head -1 <<<"$A")" 3
for c in $C_FRANJA $C_R4; do
  l=$(awk -v c="$c" -F'\t' '$1==c' <<<"$A" | head -1)
  [ -n "$l" ] || fin ERROR "sin registro de push de $c en /activity (no se puede fechar su publicación)" 3
  ts=$(cut -f2 <<<"$l"); te=$(date -u -d "$ts" +%s) || fin ERROR "fecha ilegible $ts" 3
  echo "INFO push a main de ${c:0:7}: $ts (epoch $te, $(cut -f3 <<<"$l") desde $(cut -f4 <<<"$l" | cut -c1-7))"
  [ "$te" -lt "$TG" ] || fin NO_CUMPLE "${c:0:7} llegó a main en $ts, no antes de T_g" 1
  eval "T_${c:0:7}=$ts"
done
fin CUMPLE "franja publicada en ${C_FRANJA:0:7} (push $T_8f17273) y sin cambios hasta origin/main ${M:0:7}; protocolo vigente r4 (${C_R4:0:7}, push $(eval echo \$T_${C_R4:0:7})); tabla §3.2 sha256 $h1; T_g $(date -u -d @$TG +%FT%TZ)" 0
