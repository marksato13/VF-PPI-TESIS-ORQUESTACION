# Se ejecuta en CADA host (bash -s) con C, ESPERADO, ECARGA y N en el entorno. Los ficheros llegan antes a /tmp/cf-e4-stage-*.
# Solo copia y verifica. No sobrescribe nada: si ~/cf-e4/paquete-$C o su tgz ya existen, sale con rc 3 sin tocar nada.
# Junto a las copias sustituidas de los guiones (si existen) deja un aviso; su contenido no se toca.
set -u
cd ~ || exit 2
mkdir -p cf-e4
if [ -e cf-e4/paquete-$C ] || [ -e cf-e4/paquete-$C.tgz ]; then echo "$N: YA EXISTE ~/cf-e4/paquete-$C: no se sobrescribe"; exit 3; fi
mv /tmp/cf-e4-stage-$C.tgz cf-e4/paquete-$C.tgz
cd cf-e4 && tar -xzf paquete-$C.tgz && cd paquete-$C || exit 2
sha256sum -c --strict --quiet SHA256SUMS && echo "$N: SHA256SUMS verifica ($(wc -l < SHA256SUMS) ficheros)"
echo "$N: SHA256SUMS interno $(sha256sum < SHA256SUMS | cut -c1-64)"
EV=$(sha256sum < deploy/etapa4/sensor1/evaluar_ecarga.py | cut -c1-64)
[ "$EV" = "$ESPERADO" ] && echo "$N: evaluar_ecarga.py = publicado ($EV)" || echo "$N: EVALUADOR DISTINTO ($EV)"
(cd deploy/etapa4/ecarga && sha256sum -c --strict --quiet SHA256SUMS && echo "$N: deploy/etapa4/ecarga/SHA256SUMS verifica")
E=$(sha256sum < deploy/etapa4/ecarga/SHA256SUMS | cut -c1-64)
[ "$E" = "$ECARGA" ] && echo "$N: ecarga/SHA256SUMS = publicado ($E)" || echo "$N: ecarga/SHA256SUMS DISTINTO ($E)"
grep -m1 '^VERSION=' deploy/etapa4/ecarga/generadores.sh | sed "s|^|$N: generadores.sh |"
cd ~/cf-e4
for v in ecarga-v2-guiones-c7f24510 ecarga-v2-evaluacion-e83f4be6; do
  [ -d "$v" ] || continue
  if [ -e "$v.SUSTITUIDO.txt" ]; then echo "$N: aviso de $v ya presente"
  else printf '%s\n' "$v SUSTITUIDO por ~/cf-e4/paquete-$C/deploy/etapa4/ecarga (PREPARACION-ECARGA-v2-r2)." \
       "No usar: generadores.sh daba rc 0 tras un start fallido y derivar_pcap aprobaba observaciones incompletas." > "$v.SUSTITUIDO.txt" \
       && echo "$N: aviso creado junto a $v (su contenido no se toca)"; fi
  (cd "$v" && sha256sum -c --strict --quiet SHA256SUMS && echo "$N: $v intacto (su SHA256SUMS verifica)")
done
ls -1 ~/cf-e4 | sed "s|^|$N: cf-e4/|"
