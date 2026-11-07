#!/usr/bin/env bash
# [LAPTOP Git Bash] Banco de comprobar_p12_host.sh con ficheros simulados (texto), sin red y sin procesos.
# Ningún caso arranca nada: se escriben solo las marcas que dejaría el arranque, en un directorio temporal.
set -u
G="$(cd "$(dirname "$0")/../herramientas" && pwd)/comprobar_p12_host.sh"
W=$(mktemp -d); f=0
trap 'rm -rf "$W"' EXIT
mk() {  # mk NOMBRE FIN_EPOCH RC CONFIRMADO(si/no) VIVOS EVENTOS_ISO|- S14_LINEA|-
  local d="$W/$1"; mkdir -p "$d/sensor1"
  { for i in $(seq 1 "$5"); do echo "vivo   10$i muestreador$i"; done
    [ "$4" = si ] && echo "ARRANQUE_CONFIRMADO: 4 muestreadores vivos"
    [ "$2" = - ] || echo "FIN_ARRANCAR epoch=$2 rc=$3"; } > "$d/arrancar-muestreadores.txt"
  [ "$6" = - ] || echo "$6 arrancados (fin 1794197760 = 2026-11-09T04:16:00Z)" > "$d/sensor1/eventos.log"
  [ "$7" = - ] || printf '%s\n{"t":1}\n' "$7" > "$d/sensor1/s14.jsonl"
  echo "$d"
}
chk() {  # chk DESCRIPCION RC_ESPERADO ESTADO DIR
  local o r; o=$(bash "$G" "$4" 2>&1); r=$?
  if [ "$r" = "$2" ] && grep -q "^REQ P12 $3 " <<<"$o" && [ "$(tail -1 <<<"$o")" = "FIN_P12 rc=$r" ]; then echo "PASA  $1 (rc $r, $3)"
  else echo "FALLA $1 (rc $r)"; printf '%s\n' "$o" | sed 's/^/      /'; f=$((f+1)); fi
}
S='{"inicio": 1794192601.25, "version": "2026-11-06.1", "hasta": 1794197760}'
chk "arranque a las 02:50Z, confirmado: CUMPLE"            0 CUMPLE    "$(mk ok 1794192605 0 si 4 2026-11-09T02:50:01Z "$S")"
chk "límite exacto 02:55:00Z en la confirmación: NO_CUMPLE" 1 NO_CUMPLE "$(mk exacto 1794192900 0 si 4 2026-11-09T02:54:56Z '{"inicio": 1794192896.0}')"
chk "arrancados tarde (02:56Z): NO_CUMPLE"                  1 NO_CUMPLE "$(mk tarde 1794192964 0 si 4 2026-11-09T02:56:00Z '{"inicio": 1794192960.5}')"
chk "arrancar rc 3 (uno no quedó vivo): NO_CUMPLE"          1 NO_CUMPLE "$(mk rc3 1794192605 3 no 3 2026-11-09T02:50:01Z "$S")"
chk "arrancar rc 2 (DIR ya usado): NO_CUMPLE"               1 NO_CUMPLE "$(mk rc2 1794192601 2 no 0 - -)"
chk "sin transcripción: ERROR"                              3 ERROR     "$W/no-existe"
chk "transcripción sin FIN_ARRANCAR: ERROR"                 3 ERROR     "$(mk sinfin - 0 si 4 2026-11-09T02:50:01Z "$S")"
d=$(mk dosfin 1794192605 0 si 4 2026-11-09T02:50:01Z "$S"); echo "FIN_ARRANCAR epoch=1794192606 rc=0" >> "$d/arrancar-muestreadores.txt"
chk "dos líneas FIN_ARRANCAR: ERROR"                        3 ERROR     "$d"
chk "rc 0 sin ARRANQUE_CONFIRMADO: ERROR (incoherente)"     3 ERROR     "$(mk incoh 1794192605 0 no 4 2026-11-09T02:50:01Z "$S")"
chk "rc 0 con 3 vivos: ERROR (incoherente)"                 3 ERROR     "$(mk tresvivos 1794192605 0 si 3 2026-11-09T02:50:01Z "$S")"
chk "sin eventos.log: ERROR"                                3 ERROR     "$(mk sineventos 1794192605 0 si 4 - "$S")"
chk "s14.jsonl sin «inicio»: ERROR"                         3 ERROR     "$(mk sininicio 1794192605 0 si 4 2026-11-09T02:50:01Z '{"t": 1794192602.0}')"
chk "sin s14.jsonl: ERROR"                                  3 ERROR     "$(mk sins14 1794192605 0 si 4 2026-11-09T02:50:01Z -)"
chk "marca de arranque posterior a la confirmación: ERROR"  3 ERROR     "$(mk orden 1794192605 0 si 4 2026-11-09T02:51:00Z "$S")"
d=$(mk ilegible 1794192605 0 si 4 2026-11-09T02:50:01Z "$S"); chmod 000 "$d/sensor1/eventos.log"
if [ -r "$d/sensor1/eventos.log" ]; then echo "OMITIDA eventos.log sin permiso de lectura (este usuario lo sigue leyendo: root o Windows)"
else chk "eventos.log ilegible: ERROR" 3 ERROR "$d"; fi
echo "RESULTADO_BANCO_P12 fallos=$f guion_sha=$(sha256sum < "$G" | cut -c1-64)"; exit $((f > 0))
