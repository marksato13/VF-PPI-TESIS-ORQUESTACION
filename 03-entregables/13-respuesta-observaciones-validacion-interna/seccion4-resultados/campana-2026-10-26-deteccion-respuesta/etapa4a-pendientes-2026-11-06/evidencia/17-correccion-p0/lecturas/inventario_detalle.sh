# [SENSOR1 m4rk] Detalle de SOLO LECTURA de los ficheros de ~/cf-e4/paquete-902991e que no están en su manifiesto:
# fecha, tamaño, propietario, cabecera del .pyc (magic, flags, mtime y tamaño del fuente) y comparación con el fuente.
# No ejecuta Python ni importa nada: solo find, stat, od y sha256sum.
P=~/cf-e4/paquete-902991e
echo "== $(hostname) $(id -un) $(date -u +%FT%TZ)"
esp=$(sed -E 's/^[0-9a-f]{64}  //' "$P/SHA256SUMS" | LC_ALL=C sort) || { echo "ERROR leyendo SHA256SUMS"; exit 3; }
pre=$(cd "$P" && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort) || { echo "ERROR find"; exit 3; }
echo "manifiesto=$(printf '%s\n' "$esp" | grep -c .) presentes=$(printf '%s\n' "$pre" | grep -c .)"
echo "-- ausentes (LC_ALL=C comm):"; LC_ALL=C comm -23 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre") | grep . || echo "(ninguno)"
echo "-- añadidos (LC_ALL=C comm):"; anad=$(LC_ALL=C comm -13 <(printf '%s\n' "$esp") <(printf '%s\n' "$pre") | grep .); echo "${anad:-(ninguno)}"
echo "-- directorios no presentes en el manifiesto:"
(cd "$P" && find . -type d -name __pycache__ -printf '%p  %TY-%Tm-%TdT%TH:%TM:%TS  %u\n')
for f in $anad; do
  a="$P/${f#./}"
  echo "## $f"
  stat -c 'tamaño=%s B  modo=%A  propietario=%U  modificado=%y  cambiado=%z  nacido=%w' "$a"
  sha256sum "$a"
  echo "cabecera (16 bytes, little-endian): $(od -An -tx1 -N16 "$a")"
  echo "magic=$(od -An -tu2 -N2 "$a" | tr -d ' ')  flags=$(od -An -tu4 -j4 -N4 "$a" | tr -d ' ')  mtime_fuente=$(od -An -tu4 -j8 -N4 "$a" | tr -d ' ')  tamaño_fuente=$(od -An -tu4 -j12 -N4 "$a" | tr -d ' ')"
  case "$f" in */__pycache__/*.pyc)
    s="$(dirname "$(dirname "$a")")/$(basename "$a" | sed -E 's/\.cpython-[0-9]+\.pyc$/.py/')"
    echo "fuente: $s  mtime=$(stat -c %Y "$s")  tamaño=$(stat -c %s "$s")  sha256=$(sha256sum < "$s" | cut -c1-16)…"
    echo "nombres del fuente dentro del .pyc: $(grep -a -o 'evaluar_ecarga[a-z_.]*' "$a" | sort -u | head -5 | tr '\n' ' ')";;
  esac
done
echo "-- python3 del sistema: $(python3 -V 2>&1)  (cpython-312 = 3.12)"
echo "-- otros __pycache__ bajo ~/cf-e4/paquete-* (histórico, solo listado):"
find ~/cf-e4 -maxdepth 6 -path '*/paquete-*/*' -name '*.pyc' -printf '%TY-%Tm-%TdT%TH:%TM  %p\n' 2>/dev/null | sort
exit 0
