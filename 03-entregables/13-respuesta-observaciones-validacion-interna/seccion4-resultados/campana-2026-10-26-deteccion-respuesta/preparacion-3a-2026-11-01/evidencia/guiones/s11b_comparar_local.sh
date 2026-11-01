#!/usr/bin/env bash
# PASO3A s11b — LOCAL, solo lectura: compara los blobs desplegados (out_s11_sensor_codigo.txt, git hash-object en el
# Sensor1) con los blobs de los commits en el clon local del repositorio del producto. El Sensor1 no es un clon git:
# por eso en out_s11 la columna blob_24f8a80 sale vacía y el texto "(DISTINTO)" de esa salida NO es una comparación.
set -u
OUT="$1"; REPO="$2"
cd "$REPO" || exit 1
echo "## s11b $(date -u +%FT%T.%3NZ) clon=$(basename "$REPO")"
echo "  24f8a80 -> $(git rev-parse --verify 24f8a80^{commit}) $(git log -1 --format='%ci %s' 24f8a80)"
echo "  f57ca00 -> $(git rev-parse --verify f57ca00^{commit} 2>&1) $(git log -1 --format='%ci %s' f57ca00 2>&1)"
echo "  6d92ff3 -> $(git rev-parse --verify 6d92ff3^{commit} 2>&1) tags: $(git tag --points-at 6d92ff3 2>&1 | tr '\n' ' ')"
grep -oE '^  [^ ]+ sha256=[0-9a-f]* blob_desplegado=[0-9a-f]*' "$OUT" | while read -r f s b; do
  b=${b#blob_desplegado=}; [ -z "$b" ] && continue
  c=$(git rev-parse "24f8a80:$f" 2>/dev/null); a=$(git rev-parse "f57ca00:$f" 2>/dev/null); t=$(git rev-parse "6d92ff3:$f" 2>/dev/null)
  r="DISTINTO"; [ "$b" = "$c" ] && r="IGUAL_24f8a80"
  [ "$r" = DISTINTO ] && [ "$b" = "$a" ] && r="IGUAL_f57ca00"
  [ "$b" = "$t" ] && r="$r+IGUAL_6d92ff3"
  if [ "$r" = DISTINTO ] && [ -n "$c" ]; then
    n=$(git show "24f8a80:$f" | git hash-object --stdin); d=$(git show "24f8a80:$f" | sed 's/$/\r/' | git hash-object --stdin)
    [ "$b" = "$d" ] && r="IGUAL_24f8a80_con_CRLF (blob LF $n)"
  fi
  echo "  $f desplegado=$b 24f8a80=$c f57ca00=$a 6d92ff3=$t -> $r"
done
echo "## fin"
