#!/usr/bin/env bash
# [LAPTOP Git Bash] Paso A1 del procedimiento final de E-carga v2: referencias e integridad. SOLO LECTURA sobre los
# repositorios (git fetch, git archive) y sobre GitHub; no se conecta a ningún host. VERSION 2026-11-07.4
#   00_referencias.sh COPIA_NUEVA
# Extrae a COPIA_NUEVA la carpeta etapa4a-pendientes-2026-11-06 de origin/main TAL COMO ESTÁ PUBLICADA (git archive) y
# comprueba, sobre esa copia, todo lo que se va a ejecutar. Las herramientas del día se lanzan desde esa copia, no desde
# la copia de trabajo, para ejecutar exactamente los bytes publicados.
# Comprueba:
#   docs     origin/main contiene 55f560a y el commit que publicó el procedimiento final; ningún commit
#            posterior a éste toca etapa4a-pendientes (si lo hay: rc 1, revisar antes de seguir);
#            MANIFIESTO.sha256 y los SHA256SUMS de 18, 19, 20, 21, 22 y 23 verifican sobre la copia, y el conjunto = manifiesto;
#   producto origin/recuperacion/etapa4a-pendientes-20261106 = ea3f356 exactamente; f24c922 y 902991e son antecesores;
#            deploy/ es idéntico en f24c922 y en ea3f356 (después de f24c922 solo cambian pruebas): el traslado usa los bytes de f24c922;
#            ecarga/SHA256SUMS en 902991e = e001352c… (paquete de los hosts) y sensor1_muestreadores.sh en f24c922 =
#            63f74957… (el texto que P0 r3 deriva en memoria); ecarga/SHA256SUMS en f24c922 = 4a402311…;
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
git -C "$D" merge-base --is-ancestor 55f560a9ea86f1af2d7db014e665c2d3734f8460 "$M" && ok "docs contiene 55f560a" || no "docs sin 55f560a"
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
for d in evidencia/18-cache-archivada-postcopia-p0 evidencia/19-correccion-p11 evidencia/20-procedimiento-final evidencia/21-correccion-guardia-parada-s7 evidencia/22-banco-temporizacion-8x-pendiente evidencia/23-correccion-c1-tg-estabilidad-banco; do
  (cd "$d" && sha256sum -c --strict --quiet SHA256SUMS) && ok "$d: SHA256SUMS verifica" || no "$d: SHA256SUMS"
done
echo "INFO herramientas del día (sha256 en la copia publicada):"
for f in evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh \
         evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/instalar_bastion_host.sh \
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
[ "$R" = ea3f3561cac20021cfcefed338600e7c938e93a6 ] && ok "producto rama = ea3f356" || no "producto rama = $R (se esperaba ea3f356: revisar)"
git -C "$PR" merge-base --is-ancestor f24c9221dc99b6f716a27d5ce55f9ea0dfa795cc "$R" && ok "f24c922 es antecesor de la rama" || no "f24c922 no es antecesor"
git -C "$PR" diff --quiet f24c9221dc99b6f716a27d5ce55f9ea0dfa795cc "$R" -- deploy && ok "deploy/ idéntico a f24c922" || no "deploy/ cambió desde f24c922"
git -C "$PR" merge-base --is-ancestor 902991ec077c9495a99e1075cb26af35ae980507 "$R" && ok "902991e es antecesor de la rama" || no "902991e no es antecesor"
[ "$(git -C "$PR" show 902991e:deploy/etapa4/ecarga/SHA256SUMS | sha256sum | cut -c1-64)" = e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80 ] \
  && ok "ecarga/SHA256SUMS de 902991e = e001352c… (paquete de los hosts)" || no "ecarga/SHA256SUMS de 902991e distinto"
[ "$(git -C "$PR" show f24c922:deploy/etapa4/ecarga/sensor1_muestreadores.sh | sha256sum | cut -c1-64)" = 63f7495714bf43c750748a1a6aad1e0506d10478b67034e41bd395490c05f823 ] \
  && ok "sensor1_muestreadores.sh de f24c922 = 63f74957… (2026-11-06.4)" || no "sensor1_muestreadores.sh de f24c922 distinto"
[ "$(git -C "$PR" show f24c922:deploy/etapa4/ecarga/SHA256SUMS | sha256sum | cut -c1-64)" = 4a402311145b6b5d4cca7edc3623b7294da52a0fd3c6d1a28a910868b80ac089 ] \
  && ok "ecarga/SHA256SUMS de f24c922 = 4a402311…" || no "ecarga/SHA256SUMS de f24c922 distinto"
echo "COPIA $W/$B/$P"
echo "RESULTADO_REFERENCIAS rc=$g"; exit $g
