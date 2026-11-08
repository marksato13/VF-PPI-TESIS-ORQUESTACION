#!/usr/bin/env bash
# [LAPTOP Git Bash] P8 de E-carga v2 con la franja r8: ventana fijada en epoch y publicada, con su commit, ANTES de T_g.
# Comprobación DOCUMENTAL y de SOLO LECTURA (git fetch + API de GitHub). VERSION 2026-11-07.1
#   comprobar_p8_r8.sh SALIDA_NUEVA
# Exige, a la vez:
#   1. el commit que publicó la r8, el de la r5 (antecedente ejecutado) y el de la r4 están en origin/main;
#   2. la tabla de la sección «## 2. Franja» de PROTOCOLO-CARGA-v2-r8.md en origin/main es idéntica a la del commit que la
#      publicó, y contiene T_g 1794135600 y la ventana 1794136500–1794140100;
#   3. las tablas de la r4 (sha256 d450f44d…) y de la r5 siguen siendo las publicadas: quedan como antecedente;
#   4. el registro de pushes de GitHub fecha la llegada a main de la r8 ANTES de T_g.
# La aprobación de Mark es una orden del chat: esta herramienta no la comprueba ni la sustituye.
# rc: 0 CUMPLE · 1 NO_CUMPLE · 3 ERROR, nunca se aprueba · 2 uso.
set -u -o pipefail
export LC_ALL=C
S="${1:?uso: comprobar_p8_r8.sh SALIDA_NUEVA}"; [ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
D="${CF_DOCS:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio}"
REPO=marksato13/VF-PPI-TESIS-ORQUESTACION
B=03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06
F4=$B/PROTOCOLO-CARGA-v2.md; F5=$B/PROTOCOLO-CARGA-v2-r8.md; F5R=$B/PROTOCOLO-CARGA-v2-r5.md
C_R5=3f204553d8b057e3279c81ddbb3a116816767001; C_R4=034d57d; C_RES=70b945bd3fd3b07c5bfb379e4928e2b291186ef2
TG=1794135600; TABLA_R4=d450f44d1720eab6a1a02e6c27e52337cd26e70ee4a64c2dc66ed99f4cc40460
mkdir "$S" || exit 2
exec > >(tee "$S/p8.txt") 2>&1
fin() { echo "REQ P8 $1 $2"; echo "FIN_P8 rc=$3"; echo "$3" > "$S/rc"; exit "$3"; }
echo "INFO p8 r8 $(date -u +%FT%TZ) epoch $(date -u +%s); T_g $TG ($(date -u -d @$TG +%FT%TZ))"
git -C "$D" fetch -q origin || fin ERROR "git fetch falló" 3
M=$(git -C "$D" rev-parse origin/main) || fin ERROR "no se pudo leer origin/main" 3
C_R4=$(git -C "$D" rev-parse "$C_R4^{commit}") || fin ERROR "no existe $C_R4" 3
echo "INFO origin/main $M"
for c in $C_R4 $C_RES $C_R5; do
  git -C "$D" merge-base --is-ancestor "$c" "$M"; r=$?
  case $r in 0) echo "INFO $c está en origin/main ($(git -C "$D" show -s --format='%ci, «%s»' "$c"))";;
             1) fin NO_CUMPLE "$c no está en origin/main" 1;; *) fin ERROR "merge-base rc $r" 3;; esac
done
tabla5() { git -C "$D" show "$1:$F5" | sed -n '/^## 2\. Franja/,/^## 3\./p' | grep -E '^\| '; }
tablar() { git -C "$D" show "$1:$F5R" | sed -n '/^## 2\. Franja/,/^## 3\./p' | grep -E '^\| '; }
tabla4() { git -C "$D" show "$1:$F4" | sed -n '/^### 3.2/,/^### 3.3/p' | grep -E '^\| '; }
t0=$(tabla5 $C_R5) && t1=$(tabla5 "$M") && t4=$(tabla4 "$M") || fin ERROR "no se pudieron leer las tablas" 3
h0=$(printf '%s\n' "$t0" | sha256sum | cut -c1-64); h1=$(printf '%s\n' "$t1" | sha256sum | cut -c1-64); h4=$(printf '%s\n' "$t4" | sha256sum | cut -c1-64)
echo "INFO tabla r8 en ${C_R5:0:7} sha256 $h0"; echo "INFO tabla r8 en origin/main sha256 $h1"; echo "INFO tabla r4 en origin/main sha256 $h4"
printf '%s\n' "$t1" | sed 's/^/TABLA /'
[ "$h0" = "$h1" ] || fin NO_CUMPLE "la tabla de la r8 cambió desde ${C_R5:0:7}" 1
[ "$h4" = "$TABLA_R4" ] || fin NO_CUMPLE "la tabla §3.2 de la r4 ya no es la publicada" 1
[ "$(tablar $C_RES)" = "$(tablar "$M")" ] || fin NO_CUMPLE "la tabla de la r5 ya no es la publicada" 1
grep -q '1794135600' <<<"$t1" && grep -q '1794136500–1794140100' <<<"$t1" || fin NO_CUMPLE "la tabla no contiene T_g 1794135600 y la ventana 1794136500–1794140100" 1
A=$(gh api "repos/$REPO/activity?per_page=100&time_period=month&ref=refs/heads/main" \
      --jq '.[] | [.after, .timestamp, .activity_type, .before] | @tsv' 2>&1) || fin ERROR "API de GitHub /activity: $(head -1 <<<"$A")" 3
l=$(awk -v c="$C_R5" -F'\t' '$1==c' <<<"$A" | head -1)
[ -n "$l" ] || fin ERROR "sin registro de push de $C_R5 en /activity (no se puede fechar su publicación)" 3
ts=$(cut -f2 <<<"$l"); te=$(date -u -d "$ts" +%s) || fin ERROR "fecha ilegible $ts" 3
echo "INFO push a main de ${C_R5:0:7}: $ts (epoch $te, $(cut -f3 <<<"$l") desde $(cut -f4 <<<"$l" | cut -c1-7))"
[ "$te" -lt "$TG" ] || fin NO_CUMPLE "${C_R5:0:7} llegó a main en $ts, no antes de T_g" 1
fin CUMPLE "franja r8 publicada en ${C_R5:0:7} (push $ts) y sin cambios hasta origin/main ${M:0:7}; tabla sha256 $h1; T_g $(date -u -d @$TG +%FT%TZ)" 0
