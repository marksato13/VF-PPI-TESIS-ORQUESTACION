#!/usr/bin/env bash
# [LAPTOP Git Bash] Paso A1 del procedimiento final de E-carga v2: referencias e integridad. SOLO LECTURA sobre los
# repositorios (git fetch, git archive) y sobre GitHub; no se conecta a ningún host. VERSION 2026-11-07.2
#   00_referencias.sh COPIA_NUEVA
# Extrae a COPIA_NUEVA la carpeta etapa4a-pendientes-2026-11-06 de origin/main TAL COMO ESTÁ PUBLICADA (git archive) y
# comprueba, sobre esa copia, todo lo que se va a ejecutar. Las herramientas del día se lanzan desde esa copia, no desde
# la copia de trabajo, para ejecutar exactamente los bytes publicados.
# Comprueba:
#   docs     origin/main contiene 999bce6 (P11 corregido) y el commit que publicó el procedimiento final; ningún commit
#            posterior a éste toca etapa4a-pendientes (si lo hay: rc 1, revisar antes de seguir);
#            MANIFIESTO.sha256 y los SHA256SUMS de 18, 19 y 20 verifican sobre la copia, y el conjunto = manifiesto;
#   producto origin/recuperacion/etapa4a-pendientes-20261106 = 975e715 exactamente; 902991e es antecesor;
#            ecarga/SHA256SUMS en 902991e = e001352c… (paquete de los hosts) y sensor1_muestreadores.sh en 975e715 =
#            63f74957… (el texto que P0 r3 deriva en memoria);
#   herramientas  imprime el sha256 de cada guion del día, leído de la copia.
# rc: 0 todo coincide · 1 alguna referencia o hash distinto (NO seguir) · 2 uso.
set -u -o pipefail
export LC_ALL=C
W="${1:?uso: 00_referencias.sh COPIA_NUEVA}"; [ ! -e "$W" ] || { echo "ya existe $W"; exit 2; }
D="${CF_DOCS:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio}"
PR="${CF_PRODUCTO:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion}"
B=03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta
P=etapa4a-pendientes-2026-11-06
PROC=$B/$P/ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-FINAL.md
g=0; ok() { echo "OK    $*"; }; no() { echo "FALLO $*"; g=1; }
echo "INFO referencias $(date -u +%FT%TZ)"
git -C "$D" fetch -q origin && git -C "$PR" fetch -q origin || { echo "FALLO git fetch"; exit 1; }
M=$(git -C "$D" rev-parse origin/main); echo "INFO docs origin/main $M"
git -C "$D" merge-base --is-ancestor 999bce698d508cbb51f7ae0a1bcb792367ff165d "$M" && ok "docs contiene 999bce6 (corrección de P11)" || no "docs sin 999bce6"
C=$(git -C "$D" log -1 --format=%H "$M" -- "$PROC")
[ -n "$C" ] && ok "procedimiento final publicado en ${C:0:7} ($(git -C "$D" show -s --format=%ci "$C"))" || no "procedimiento final no publicado en origin/main"
if [ -n "$C" ]; then
  n=$(git -C "$D" log --format='%h %ci %s' "$C..$M" -- "$B/$P")
  [ -z "$n" ] && ok "ningún commit posterior al procedimiento toca $P" || { no "commits posteriores al procedimiento en $P (revisar antes de seguir):"; printf '%s\n' "$n" | sed 's/^/        /'; }
fi
mkdir -p "$W" || exit 2
git -C "$D" archive "$M" "$B/$P" | tar -x -C "$W" || { echo "FALLO git archive"; exit 1; }
cd "$W/$B/$P" || exit 1
sha256sum -c --strict --quiet MANIFIESTO.sha256 && ok "MANIFIESTO.sha256 verifica ($(wc -l < MANIFIESTO.sha256) ficheros, sha $(sha256sum < MANIFIESTO.sha256 | cut -c1-16)…)" || no "MANIFIESTO.sha256"
diff <(find . -type f ! -name MANIFIESTO.sha256 | sed 's|^\./||' | sort) <(sed -E 's/^[0-9a-f]{64}  //' MANIFIESTO.sha256 | sort) > /dev/null \
  && ok "conjunto de ficheros = manifiesto" || no "conjunto de ficheros distinto del manifiesto"
for d in evidencia/18-cache-archivada-postcopia-p0 evidencia/19-correccion-p11 evidencia/20-procedimiento-final; do
  (cd "$d" && sha256sum -c --strict --quiet SHA256SUMS) && ok "$d: SHA256SUMS verifica" || no "$d: SHA256SUMS"
done
echo "INFO herramientas del día (sha256 en la copia publicada):"
for f in evidencia/20-procedimiento-final/herramientas/00_referencias.sh \
         evidencia/20-procedimiento-final/herramientas/comprobar_p8.sh \
         evidencia/20-procedimiento-final/herramientas/comprobar_p12.sh \
         evidencia/20-procedimiento-final/herramientas/comprobar_p12_host.sh \
         evidencia/19-correccion-p11/laboratorio/previa.sh evidencia/19-correccion-p11/laboratorio/previa_host.sh \
         evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh \
         evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/post_copia_host_r3.sh \
         evidencia/19-correccion-p11/p0-r3/p0_r3.sh evidencia/19-correccion-p11/p0-r3/bloques/sensor1_r3.sh \
         evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh evidencia/18-cache-archivada-postcopia-p0/instantaneas/instantanea_host.sh \
         evidencia/06-observacion/obs_p4_post.sh; do
  [ -r "$f" ] && echo "      $(sha256sum < "$f" | cut -c1-64)  $f" || no "falta $f"
done
[ "$(sha256sum < evidencia/19-correccion-p11/p0-r3/bloques/sensor1_r3.sh | cut -c1-64)" = 5ef3372a671d0b41d928823caa6a92d8f109b5c329a56e1719ab5979f4f911cd ] \
  && ok "bloque sensor1_r3.sh = 5ef3372a… (P0 r3)" || no "bloque sensor1_r3.sh distinto"
[ "$(sha256sum < evidencia/06-observacion/obs_p4_post.sh | cut -c1-64)" = 25d8d3697087d9c7c035986ec42d2f4d15e1fc9a6bf5c0e083d55a2a34a6db62 ] \
  && ok "obs_p4_post.sh = 25d8d369… (S7)" || no "obs_p4_post.sh distinto"
cd "$HOME" || exit 1   # 2026-11-07.2: desde la copia, con ruta larga, git.exe no arranca (límite Win32) y daba 4 FALLO falsos
R=$(git -C "$PR" rev-parse origin/recuperacion/etapa4a-pendientes-20261106)
[ "$R" = 975e715808f3ad454055712660414f2e8fd50878 ] && ok "producto rama = 975e715" || no "producto rama = $R (se esperaba 975e715: revisar)"
git -C "$PR" merge-base --is-ancestor 902991ec077c9495a99e1075cb26af35ae980507 "$R" && ok "902991e es antecesor de la rama" || no "902991e no es antecesor"
[ "$(git -C "$PR" show 902991e:deploy/etapa4/ecarga/SHA256SUMS | sha256sum | cut -c1-64)" = e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80 ] \
  && ok "ecarga/SHA256SUMS de 902991e = e001352c… (paquete de los hosts)" || no "ecarga/SHA256SUMS de 902991e distinto"
[ "$(git -C "$PR" show 975e715:deploy/etapa4/ecarga/sensor1_muestreadores.sh | sha256sum | cut -c1-64)" = 63f7495714bf43c750748a1a6aad1e0506d10478b67034e41bd395490c05f823 ] \
  && ok "sensor1_muestreadores.sh de 975e715 = 63f74957… (2026-11-06.4)" || no "sensor1_muestreadores.sh de 975e715 distinto"
echo "COPIA $W/$B/$P"
echo "RESULTADO_REFERENCIAS rc=$g"; exit $g
