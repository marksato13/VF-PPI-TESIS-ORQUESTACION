# Se ejecuta en CADA host (bash -s) con C, ESPERADO y N en el entorno. Los ficheros llegan antes a /tmp/cf-e4-stage-*.
# No sobrescribe nada: si ~/cf-e4/paquete-$C o su tgz ya existen, sale con rc 3 sin tocar nada.
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
python3 -I - <<'PY'
import importlib.util as u, os
s = u.spec_from_file_location("e", "deploy/etapa4/sensor1/evaluar_ecarga.py")
m = u.module_from_spec(s); s.loader.exec_module(m)
print(os.environ["N"] + ": VERSION importada", m.VERSION)
PY
cd ~/cf-e4
if [ -d paquete-f6dc685 ]; then
  if [ -e paquete-f6dc685.NO-USAR-PARA-VEREDICTO.txt ]; then echo "$N: aviso ya presente"
  else mv /tmp/cf-e4-stage-aviso.txt paquete-f6dc685.NO-USAR-PARA-VEREDICTO.txt && echo "$N: aviso creado junto a paquete-f6dc685 (su contenido no se toca)"; fi
  (cd paquete-f6dc685 && sha256sum -c --strict --quiet SHA256SUMS && echo "$N: paquete-f6dc685 intacto (su SHA256SUMS verifica)")
fi
rm -f /tmp/cf-e4-stage-aviso.txt
ls -1 ~/cf-e4 | sed "s|^|$N: cf-e4/|"
