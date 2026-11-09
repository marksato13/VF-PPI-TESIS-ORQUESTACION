set -u
S="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
DEST=$HOME/cf-e4/archivo-sensor1
mkdir -p "$DEST"
for D in 4c-x3-cancelada-20261109T1350Z 4c-x3b-cancelada-20261109T1625Z; do
  echo "## $D $(date -u +%T)Z"
  [ -e "$DEST/$D" ] && { echo "PARAR: ya existe $DEST/$D"; continue; }
  $S "tar -C ~/cf-e4 -cf - $D" | tar -C "$DEST" -xf - || { echo "FALLO copia $D"; continue; }
  echo "   copiado $(date -u +%T)Z; inventario y sha256 en el sensor..."
  $S "cd ~/cf-e4/$D && find . -printf '%y %m %s %T@ %P\n' | awk '{ split(\$4,a,\".\"); printf \"%s %s %s %s %s\n\", \$1,\$2,\$3,a[1],substr(\$0, index(\$0,\$5)) }' | LC_ALL=C sort -k5 > /tmp/inv-sensor-$D.txt; find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > /tmp/sha-sensor-$D.txt; wc -l < /tmp/inv-sensor-$D.txt; wc -l < /tmp/sha-sensor-$D.txt"
  $S "cat /tmp/inv-sensor-$D.txt" > "$DEST/$D.inventario-sensor1.txt"
  $S "cat /tmp/sha-sensor-$D.txt"  > "$DEST/$D.sha256-sensor1.txt"
  ( cd "$DEST/$D" && find . -printf '%y %m %s %T@ %P\n' | awk '{ split($4,a,"."); printf "%s %s %s %s %s\n", $1,$2,$3,a[1],substr($0, index($0,$5)) }' | LC_ALL=C sort -k5 > "$DEST/$D.inventario-bastion.txt"
    find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$DEST/$D.sha256-bastion.txt" )
  $S "rm -f /tmp/inv-sensor-$D.txt /tmp/sha-sensor-$D.txt"
  if cmp -s "$DEST/$D.inventario-sensor1.txt" "$DEST/$D.inventario-bastion.txt"; then echo "   inventario (tipo, modo, tamaño, mtime en s, ruta): IGUAL ($(wc -l < "$DEST/$D.inventario-bastion.txt") entradas)"; else echo "   inventario DISTINTO:"; diff "$DEST/$D.inventario-sensor1.txt" "$DEST/$D.inventario-bastion.txt" | head -10; fi
  if cmp -s "$DEST/$D.sha256-sensor1.txt" "$DEST/$D.sha256-bastion.txt"; then echo "   sha256 de todos los ficheros: IGUAL ($(wc -l < "$DEST/$D.sha256-bastion.txt") ficheros)"; else echo "   sha256 DISTINTO:"; diff "$DEST/$D.sha256-sensor1.txt" "$DEST/$D.sha256-bastion.txt" | head -10; fi
  echo "   bytes (suma de ficheros) bastión: $(find "$DEST/$D" -type f -printf '%s\n' | awk '{s+=$1} END{print s}')  | du: $(du -sh "$DEST/$D" | cut -f1)  | ruta: $DEST/$D"
  echo "   sha256 del listado de sha256 (sensor|bastión): $(sha256sum < "$DEST/$D.sha256-sensor1.txt" | cut -c1-16) | $(sha256sum < "$DEST/$D.sha256-bastion.txt" | cut -c1-16)"
done
echo "== espacio"; df -h "$HOME" | tail -1 | awk '{print "bastión libres " $4 " (usado " $5 ")"}'
ssh -n -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'df -B1 / | tail -1 | awk "{print \"sensor1 libres bytes: \" \$4}"'
echo "## fin $(date -u +%T)Z"
