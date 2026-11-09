DEST=$HOME/cf-e4/archivo-sensor1
S="ssh -n -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
norm() { awk -F'\t' 'BEGIN{OFS="\t"} { if ($1=="d") $3="-"; print }' | LC_ALL=C sort -t'	' -k5; }
for D in 4c-x3-cancelada-20261109T1350Z 4c-x3b-cancelada-20261109T1625Z; do
  $S "cd ~/cf-e4/$D && find . -printf '%y\t%m\t%s\t%Ts\t%P\n'" | norm > "$DEST/$D.inventario2-sensor1.tsv"
  ( cd "$DEST/$D" && find . -printf '%y\t%m\t%s\t%Ts\t%P\n' | norm > "$DEST/$D.inventario2-bastion.tsv" )
  A=$(wc -l < "$DEST/$D.inventario2-sensor1.tsv"); B=$(wc -l < "$DEST/$D.inventario2-bastion.tsv")
  F=$(awk -F'\t' '$1=="f"' "$DEST/$D.inventario2-bastion.tsv" | wc -l); DD=$(awk -F'\t' '$1=="d"' "$DEST/$D.inventario2-bastion.tsv" | wc -l); L=$(awk -F'\t' '$1=="l"' "$DEST/$D.inventario2-bastion.tsv" | wc -l)
  if cmp -s "$DEST/$D.inventario2-sensor1.tsv" "$DEST/$D.inventario2-bastion.tsv"; then R=IGUAL; else R=DISTINTO; fi
  echo "$D: inventario (tipo, modo, tamaño [dirs excluidos], mtime en s, ruta) sensor=$A bastión=$B → $R | ficheros=$F directorios=$DD enlaces=$L"
  [ "$R" = DISTINTO ] && diff "$DEST/$D.inventario2-sensor1.tsv" "$DEST/$D.inventario2-bastion.tsv" | head -6
done
echo "tamaños exactos de las copias:"; for D in 4c-x3-cancelada-20261109T1350Z 4c-x3b-cancelada-20261109T1625Z; do echo "  $DEST/$D  $(find $DEST/$D -type f -printf '%s\n' | awk '{s+=$1} END{print s}') bytes en ficheros; du $(du -sb --apparent-size $DEST/$D | cut -f1) B aparentes / $(du -s --block-size=1 $DEST/$D | cut -f1) B en disco"; done
