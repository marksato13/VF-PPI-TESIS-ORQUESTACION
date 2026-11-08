# BLOQUE=precheck_r2  (P0 r2, puntos 2 y 3 + cadena v2/v1; S11) en el bastión. precheck.sh viaja SIN CAMBIOS
# (b3127edd…) en base64 como primer argumento; aquí se comprueba su sha, se ejecuta y se EVALÚA su salida.
# precheck.sh no propaga errores (su rc es el de su última orden y un sudo fallido produce el sha de la cadena vacía,
# que es justo el ruleset esperado de srv-dmz). Por eso aquí:
#   - su stderr se captura aparte (prefijo «STDERR| »): cualquier línea en stderr es ERROR (el P0 del 06-nov no tuvo ninguna);
#   - cada sección (SENSOR1, BASTION, SRV-DMZ) debe tener su línea de referencia; si falta, sus REQ son ERROR;
#   - un valor esperado ausente con la sección completa es NO_CUMPLE.
set -u -o pipefail
B=precheck_r2; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
PC_SHA=b3127eddb28978c38295a425f8e672d7476d9ab4e5a779c656e19e3d65f980b8
[ $# -ge 2 ] || { echo "uso: B64_PRECHECK ETIQUETA"; E=2; fin; }
s=$(printf %s "$1" | base64 -d | sha256sum | cut -c1-64); r=$?
if [ $r != 0 ] || [ "$s" != "$PC_SHA" ]; then
  req X.precheck_identico ERROR "precheck recibido sha=${s:-?} rc=$r (esperado $PC_SHA): no se ejecuta"; fin
fi
req X.precheck_identico CUMPLE "precheck.sh $PC_SHA"
out=$(printf %s "$1" | base64 -d | bash -s -- "$2" 2> >(sed 's/^/STDERR| /')); r=$?
printf '%s\n' "$out" | sed 's/^/| /'
[ $r = 0 ] && req X.precheck_rc CUMPLE "rc 0" || req X.precheck_rc ERROR "precheck rc $r"
e=$(grep -c '^STDERR| ' <<<"$out")
[ "$e" = 0 ] && req X.precheck_stderr CUMPLE "stderr vacío" || req X.precheck_stderr ERROR "$e línea(s) en stderr: $(grep -m2 '^STDERR| ' <<<"$out" | tr '\n' ' ' | cut -c1-200)"
s1=$(awk '$0=="## SENSOR1"{f=1;next} $0=="## BASTION"{f=0} f' <<<"$out")
ba=$(awk '$0=="## BASTION"{f=1;next} $0=="## SRV-DMZ"{f=0} f' <<<"$out")
sd=$(awk 'f; $0=="## SRV-DMZ"{f=1}' <<<"$out")
grep -q '^ppi-motor pid=[0-9]' <<<"$s1" && c1=si || c1=no
grep -q '^ppi-relay-eventos ' <<<"$ba" && cb=si || cb=no
grep -q '^ppi-enforce-agent-v2-dmz ' <<<"$sd" && grep -q '^tablas: \[' <<<"$sd" && cd=si || cd=no
ev() {  # ev ID SECCION_COMPLETA TEXTO_SECCION REGEX DESCRIPCION
  if [ "$2" != si ]; then req "$1" ERROR "sección sin su línea de referencia (ssh o lectura fallida): no se evalúa $5"
  elif grep -qE "$4" <<<"$3"; then req "$1" CUMPLE "$5"
  else req "$1" NO_CUMPLE "no aparece: $5"; fi
}
ev P2.modelo     $c1 "$s1" '^df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60  /.*\.joblib$' "modelo df547da0…"
ev P2.manifiesto $c1 "$s1" '^b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7  /.*\.json$' "manifiesto b3ad6805…"
ev P2.esquema    $c1 "$s1" '^e032a1a28650d438ae707c93b3045801770b3a069b4395426077af3bbd2b0e33  /.*multilayer-v2\.json$' "esquema e032a1a2…"
ev P2.ec78ca5    $c1 "$s1" '^ec78ca5 SHA256SUMS OK$' "ec78ca5 SHA256SUMS OK"
ev P2.suricata   $c1 "$s1" '^0962ce68b565c237ded37313f578e1a1b05229206741e76f7d3a2daaa6e694d0  /etc/suricata/suricata\.yaml$' "suricata.yaml 0962ce68…"
ev P3.ruleset.sensor1 $c1 "$s1" '^24c320e3e953857317c08beb04e34f34c6f132bb6cccd0f1b4c7ab98b621a21e  ruleset-sensor1-normalizado$' "ruleset Sensor1 24c320e3…"
ev P3.procesos.precheck $c1 "$s1" '^procesos con --enforce/--aplicar: 0$' "0 procesos con --enforce/--aplicar en Sensor1"
if [ $c1 = si ]; then
  m=""; for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 suricata ppi-publicar-feed-v2; do
    grep -qE "^$u pid=[0-9]+ NRestarts=[0-9]+ active$" <<<"$s1" || m="$m $u"; done
  [ -z "$m" ] && req X.cadena_v2.sensor1 CUMPLE "motor, captura, vía rápida, suricata y feed v2 active" || req X.cadena_v2.sensor1 NO_CUMPLE "no active:$m"
else req X.cadena_v2.sensor1 ERROR "sección SENSOR1 sin su línea de referencia"; fi
if [ $c1 = si ]; then
  grep -qE '^v1 ppi-publicar-feed\.timer disabled/inactive$' <<<"$s1" && grep -qE '^v1 ppi-publicar-feed [a-z-]+/inactive$' <<<"$s1" \
    && req X.v1.sensor1 CUMPLE "ppi-publicar-feed.timer disabled/inactive y servicio inactive" || req X.v1.sensor1 NO_CUMPLE "cadena v1 no desactivada en Sensor1"
else req X.v1.sensor1 ERROR "sección SENSOR1 sin su línea de referencia"; fi
ev X.relay_v2   $cb "$ba" '^ppi-relay-eventos enabled/active pid=[0-9]+ NRestarts=[0-9]+$' "relé v2 enabled/active"
ev X.v1.bastion $cb "$ba" '^ppi-relay-feed\.timer disabled/inactive ' "ppi-relay-feed.timer disabled/inactive"
ev X.agente_v2  $cd "$sd" '^ppi-enforce-agent-v2-dmz enabled/active pid=[0-9]+ NRestarts=[0-9]+$' "agente v2 enabled/active"
ev X.v1.srvdmz  $cd "$sd" '^ppi-enforce-agent\.timer disabled/inactive ' "ppi-enforce-agent.timer disabled/inactive"
ev P3.tablas.srvdmz  $cd "$sd" '^tablas: \[\]$' "srv-dmz sin tablas nft"
ev P3.ruleset.srvdmz $cd "$sd" '^e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  ruleset-srvdmz$' "ruleset srv-dmz e3b0c442… (vacío; vale solo con stderr vacío)"
ev X.eventos_aplicacion $cd "$sd" '^eventos aplicacion: 0$' "0 eventos de aplicación en la traza del agente"
fin
