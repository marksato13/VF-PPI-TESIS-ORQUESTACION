# Se ejecuta en CADA host (bash -s) con C, ESPERADO, ECARGA y N en el entorno. El tgz llega antes a /tmp/cf-e4-stage-*.
# Solo copia y verifica. No sobrescribe nada: si ~/cf-e4/paquete-$C o su tgz ya existen, sale con rc 3 sin tocar nada.
# Junto a ~/cf-e4/paquete-a12deae (si existe) deja un aviso NO-USAR; el contenido de paquete-a12deae no se toca.
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
grep -m1 '^VERSION' deploy/etapa4/ecarga/evaluar_s14.py | sed "s|^|$N: evaluar_s14.py |"
grep -m1 '^VERSION' deploy/etapa4/ecarga/construir_entrada.py | sed "s|^|$N: construir_entrada.py |"
cd ~/cf-e4
v=paquete-a12deae
if [ -d "$v" ]; then
  if [ -e "$v.NO-USAR.txt" ]; then echo "$N: aviso de $v ya presente"
  else printf '%s\n' "$v SUSTITUIDO por ~/cf-e4/paquete-$C (PROTOCOLO-CARGA-v2 r4, PREPARACION-ECARGA-v2-r3)." \
       "No usar para S14 ni para construir la entrada: evaluar_s14 2026-11-06.1 no contaba el hueco anterior al tramo saturado." > "$v.NO-USAR.txt" \
       && echo "$N: aviso creado junto a $v (su contenido no se toca)"; fi
  (cd "$v" && sha256sum -c --strict --quiet SHA256SUMS && echo "$N: $v intacto (su SHA256SUMS verifica)")
fi
ls -1 ~/cf-e4 | grep -E '^paquete-(a12deae|902991e)' | sed "s|^|$N: cf-e4/|"
