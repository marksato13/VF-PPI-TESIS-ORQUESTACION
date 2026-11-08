#!/usr/bin/env bash
# [LAPTOP Git Bash] P0 r3 de E-carga v2 (PROTOCOLO-CARGA-v2 r4 §3.5). SOLO LECTURA. VERSION 2026-11-07.r3x
#   bash p0_r3.sh anticipado|inmediato SALIDA_NUEVA [--paquete ID --sumas SHA256]
# r3: sustituye a ../../17-correccion-p0/p0-r2/p0_r2.sh (se conserva). ÚNICO cambio: el bloque de Sensor1 es
#     sensor1_r3.sh, que ejecuta «comprobar» con sensor1_muestreadores.sh 2026-11-06.4 (muestreadores identificados
#     por argv, no con pgrep) y emite el nuevo REQ P11.muestreadores (CUMPLE / NO_CUMPLE / ERROR si es desconocido).
#     Los demás bloques son copias byte a byte de los de la r2.
# Sustituye a ../16-postcopia-p0/p0/p0_anticipado.sh (que se conserva): aquel guardaba el rc de cada bloque pero
# terminaba SIEMPRE con rc 0, aunque fallaran los 9 ssh.
#
# Qué hace. Envía 9 bloques de solo lectura (base64 dentro del argumento de ssh; el host devuelve primero el sha256 de
# lo recibido). Cada bloque imprime líneas «REQ <id> <CUMPLE|NO_CUMPLE|NO_EVALUABLE|ERROR> <detalle>» y termina con
# «FIN_BLOQUE <nombre> rc=<n>» y exit n (0 = todas sus lecturas hechas; 3 = alguna lectura falló).
#
# Un bloque está «ejecutado sin errores» SOLO si: ssh rc 0; transporte igual; FIN_BLOQUE es la última línea y su rc
# coincide con el de ssh; están todos los REQ esperados, una vez cada uno; y ninguno es ERROR. Si no, se guarda el motivo
# y sus REQ quedan SIN_VERIFICAR (no cuentan como cumplidos).
#
# Categorías (se informan por separado):
#   anticipable  todo lo que se puede comprobar antes del día del ensayo (1, 2, 3, 4, 5a, 5c, 6, 7, 9, 10, 11, 13, X.*)
#   momento      5b (date -u dentro de la franja): solo es evaluable en el P0 inmediato; en modo inmediato es obligatorio
#   documental   8 (ventana publicada antes de T_g): no la comprueba esta herramienta
#   ejecucion    12 (muestreadores arrancados antes de T_g-300 s): ocurre DESPUÉS de P0, en la ejecución
#
# rc global:
#   0  los 9 bloques sin errores Y todas las anticipables CUMPLE (y, en modo inmediato, también 5b)
#   2  uso o precondición local (no se conecta)
#   4  algún bloque falló o quedó sin verificar (manda sobre 5: la evaluación de requisitos no es completa)
#   5  bloques sin errores, pero alguna precondición NO_CUMPLE o NO_EVALUABLE
# rc 0 de los bloques NUNCA sustituye a la evaluación de los requisitos: son dos resúmenes distintos.
set -u -o pipefail
VERSION=2026-11-07.r3x
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
BL="$AQUI/bloques"
K="${CF_CLAVE:-$HOME/.ssh/id_ed25519}"; B=gadmin@10.10.10.30; O="-o BatchMode=yes -o ConnectTimeout=10"
MODO="${1:-}"; S="${2:-}"
case "$MODO" in anticipado|inmediato) ;; *) echo "uso: p0_r3.sh anticipado|inmediato SALIDA_NUEVA [--paquete ID --sumas SHA256]"; exit 2;; esac
[ -n "$S" ] || { echo "uso: falta SALIDA_NUEVA"; exit 2; }
shift 2
PAQ=902991e; SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c
while [ $# -gt 0 ]; do
  case "$1" in --paquete) PAQ=${2:?}; shift 2;; --sumas) SUMAS=${2:?}; shift 2;; *) echo "uso: argumento $1"; exit 2;; esac
done
[[ $PAQ =~ ^[0-9a-f]{7,40}$ ]] && [[ $SUMAS =~ ^[0-9a-f]{64}$ ]] || { echo "PRECONDICION: --paquete/--sumas no válidos"; exit 2; }
# Constantes del protocolo r7 §2 (NO se cambian aquí): franja de P0, 6 h 30 min después que la r5, y su comprobación del día.
FRANJA_INI=1794128400; FRANJA_FIN=1794137400
[ -e "$S" ] && { echo "PRECONDICION: $S ya existe (no se sobrescribe)"; exit 2; }
for f in estado_r2.sh verificador_r2.sh precheck_r2.sh precheck.sh clientes_r2.sh sensor1_r3.sh; do
  [ -r "$BL/$f" ] || { echo "PRECONDICION: falta $BL/$f"; exit 2; }
done
for h in ssh base64 sha256sum date awk; do command -v $h > /dev/null || { echo "PRECONDICION: falta $h"; exit 2; }; done
mkdir -p "$S" || { echo "PRECONDICION: no se pudo crear $S"; exit 2; }

declare -A DEST=([bastion]="" [sensor1]="m4rk@10.10.60.11 ~/.ssh/cyberflow-to-sensor" [srvdmz]="adminsrvdmz@10.10.30.10 ~/.ssh/cyberflow-to-srv")
# REQ esperados por bloque (si falta alguno, el bloque queda SIN VERIFICAR)
declare -A ESPERADOS
ESPERADOS[00-estado-bastion]="X.sincronizado.bastion P3.procesos.bastion"
ESPERADOS[00-estado-sensor1]="X.sincronizado.sensor1 P3.procesos.sensor1"
ESPERADOS[00-estado-srvdmz]="X.sincronizado.srvdmz P3.procesos.srvdmz"
ESPERADOS[01-verificar-bastion]="P1.bastion"
ESPERADOS[02-verificar-sensor1]="P1.sensor1"
ESPERADOS[03-verificar-srvdmz]="P1.srvdmz"
ESPERADOS[04-precheck-s11]="X.precheck_identico X.precheck_rc X.precheck_stderr P2.modelo P2.manifiesto P2.esquema P2.ec78ca5 P2.suricata P3.ruleset.sensor1 P3.procesos.precheck X.cadena_v2.sensor1 X.v1.sensor1 X.relay_v2 X.v1.bastion X.agente_v2 X.v1.srvdmz P3.tablas.srvdmz P3.ruleset.srvdmz X.eventos_aplicacion"
ESPERADOS[05-clientes]="X.generadores_sh P10 P4.parado X.estado_generadores X.permisos P4.generador P5a.clientes X.sincronizado.clientes"
ESPERADOS[06-sensor1]="P5b P5a.sensor1 P13.sumas P13.hashes P13.inventario X.mecanismo_sin_escritura P11 P11.muestreadores P11.retencion P6.home P6.mem P7 X.dir_no_creado X.paquete_sin_cambios P9"
ORDEN=(00-estado-bastion 00-estado-sensor1 00-estado-srvdmz 01-verificar-bastion 02-verificar-sensor1 03-verificar-srvdmz 04-precheck-s11 05-clientes 06-sensor1)

EV=0            # 1 si no se pudo escribir alguna evidencia: el resultado no puede ser 0
w() { printf '%s\n' "$*"; printf '%s\n' "$*" >> "$S/resumen.txt" || { EV=1; echo "ERROR_EVIDENCIA no se pudo escribir resumen.txt" >&2; }; }
guarda() { printf '%s\n' "$2" > "$S/$1" || { EV=1; echo "ERROR_EVIDENCIA no se pudo escribir $1" >&2; }; }
categoria() { case "$1" in P5b) echo momento;; P8) echo documental;; P12) echo ejecucion;; *) echo anticipable;; esac; }

declare -A EST_BLOQUE MOT_BLOQUE REQ_EST REQ_DET REQ_BLOQUE
BLOQUES_OK=0

remoto() {  # remoto NOMBRE HOST FICHERO_BLOQUE [ARGS...]
  local n=$1 h=$2 f=$3; shift 3
  local cr l b r d k rc out ultima frc id st det linea faltan dup=""
  EST_BLOQUE[$n]=ERROR
  if ! cr=$(tr -cd '\r' < "$f" | wc -c); then MOT_BLOQUE[$n]="ERROR_LECTURA_LOCAL no se pudo leer $f"; guarda "$n.rc" "-"; return; fi
  if [ "$cr" -ne 0 ]; then MOT_BLOQUE[$n]="CR_EN_BLOQUE $f tiene $cr CR: no se envía"; guarda "$n.rc" "-"; return; fi
  l=$(sha256sum < "$f" | cut -c1-64) && b=$(base64 -w0 < "$f") || { MOT_BLOQUE[$n]="ERROR_LECTURA_LOCAL sha/base64 de $f"; return; }
  r="set -o pipefail; printf %s $b | base64 -d | sha256sum && printf %s $b | base64 -d | bash -s -- $*"
  if [ "$h" = bastion ]; then ssh $O -i "$K" "$B" "$r" < /dev/null > "$S/$n.stdout" 2> "$S/$n.stderr"; rc=$?
  else read -r d k <<<"${DEST[$h]}"; ssh $O -i "$K" "$B" "ssh $O -i $k $d \"$r\"" < /dev/null > "$S/$n.stdout" 2> "$S/$n.stderr"; rc=$?; fi
  guarda "$n.rc" "$rc"
  if ! out=$(cat "$S/$n.stdout"); then MOT_BLOQUE[$n]="ERROR_LECTURA_LOCAL no se pudo leer $n.stdout"
  elif [ "$rc" = 255 ]; then MOT_BLOQUE[$n]="SSH_FALLIDO rc 255 ($(tail -1 "$S/$n.stderr" 2>/dev/null | cut -c1-160))"
  elif [ -z "$out" ]; then MOT_BLOQUE[$n]="SIN_SALIDA rc $rc"
  elif [ "$(head -1 <<<"$out")" != "$l  -" ]; then MOT_BLOQUE[$n]="TRANSPORTE_DISTINTO recibido=$(head -1 <<<"$out" | cut -c1-64) local=$l"
  else
    ultima=$(grep -v '^[[:space:]]*$' <<<"$out" | tail -1)
    if ! [[ $ultima =~ ^FIN_BLOQUE\ ([^ ]+)\ rc=([0-9]+)$ ]]; then MOT_BLOQUE[$n]="INCOMPLETO sin FIN_BLOQUE al final (rc ssh $rc)"
    else
      frc=${BASH_REMATCH[2]}
      if [ "$frc" != "$rc" ]; then MOT_BLOQUE[$n]="INCOHERENTE FIN_BLOQUE rc=$frc y ssh rc=$rc"
      else
        faltan=""
        for id in ${ESPERADOS[$n]}; do
          c=$(grep -cE "^REQ ${id//./\\.} (CUMPLE|NO_CUMPLE|NO_EVALUABLE|ERROR)( |$)" <<<"$out")   # mal formada = falta
          [ "$c" = 1 ] || { [ "$c" = 0 ] && faltan="$faltan $id" || dup="$dup $id"; }
        done
        if [ -n "$faltan" ]; then MOT_BLOQUE[$n]="FALTAN_REQ$faltan"
        elif [ -n "$dup" ]; then MOT_BLOQUE[$n]="REQ_DUPLICADO$dup"
        elif grep -q '^REQ [^ ]* ERROR' <<<"$out"; then MOT_BLOQUE[$n]="ERROR_EN_BLOQUE rc $rc: $(grep '^REQ [^ ]* ERROR' <<<"$out" | cut -d' ' -f2 | tr '\n' ' ')"
        elif [ "$rc" != 0 ]; then MOT_BLOQUE[$n]="RC_NO_CERO rc $rc sin REQ ERROR"
        else EST_BLOQUE[$n]=OK; MOT_BLOQUE[$n]="sin errores"; BLOQUES_OK=$((BLOQUES_OK+1)); fi
      fi
    fi
  fi
  for id in ${ESPERADOS[$n]}; do
    REQ_BLOQUE[$id]=$n
    linea=$(grep -m1 "^REQ ${id//./\\.} " <<<"${out:-}")
    st=$(cut -d' ' -f3 <<<"$linea"); det=$(cut -d' ' -f4- <<<"$linea")
    if [ "${EST_BLOQUE[$n]}" = OK ]; then REQ_EST[$id]=$st; REQ_DET[$id]=$det
    else
      case "$st" in ERROR) REQ_EST[$id]=ERROR; REQ_DET[$id]=$det;;
                   *) REQ_EST[$id]=SIN_VERIFICAR; REQ_DET[$id]="bloque $n: ${MOT_BLOQUE[$n]}${st:+ (el bloque decía $st)}";; esac
    fi
  done
  guarda "$n.motivo" "${EST_BLOQUE[$n]} ${MOT_BLOQUE[$n]}"
  w "BLOQUE $n host=$h rc=$rc estado=${EST_BLOQUE[$n]} motivo=${MOT_BLOQUE[$n]} bloque=$(basename "$f") sha=${l:0:12}"
}

TS=$(date -u +%Y%m%dT%H%M%SZ)
{ printf 'p0_r3 %s modo=%s paquete=%s sumas=%s\n' "$VERSION" "$MODO" "$PAQ" "$SUMAS"
  printf 'inicio %s portatil_epoch %s franja=[%s,%s]\n' "$(date -u +%FT%TZ)" "$(date -u +%s)" "$FRANJA_INI" "$FRANJA_FIN"; } > "$S/resumen.txt" \
  || { echo "PRECONDICION: no se pudo escribir $S/resumen.txt"; exit 2; }
B64PC=$(base64 -w0 < "$BL/precheck.sh") || { echo "PRECONDICION: no se pudo leer precheck.sh"; exit 2; }
remoto 00-estado-bastion  bastion "$BL/estado_r2.sh" bastion
remoto 00-estado-sensor1  sensor1 "$BL/estado_r2.sh" sensor1
remoto 00-estado-srvdmz   srvdmz  "$BL/estado_r2.sh" srvdmz
remoto 01-verificar-bastion bastion "$BL/verificador_r2.sh" bastion
remoto 02-verificar-sensor1 sensor1 "$BL/verificador_r2.sh" sensor1
remoto 03-verificar-srvdmz  srvdmz  "$BL/verificador_r2.sh" srvdmz
remoto 04-precheck-s11      bastion "$BL/precheck_r2.sh" "$B64PC" "p0-$MODO"
remoto 05-clientes          bastion "$BL/clientes_r2.sh"
remoto 06-sensor1           sensor1 "$BL/sensor1_r3.sh" "p0-$MODO-$TS" "$PAQ" "$SUMAS" "$FRANJA_INI" "$FRANJA_FIN"

# Requisitos que no lee ningún host
dia=$(date -u -d "@$FRANJA_INI" +%u 2>/dev/null)
case "$dia" in 7) REQ_EST[P5c]=CUMPLE; REQ_DET[P5c]="domingo UTC (ISO 7), franja del protocolo r7; el factor de laborable lo comprueba comprobar_forzar.sh con (F2)";;
               [1-6]) REQ_EST[P5c]=NO_CUMPLE; REQ_DET[P5c]="la franja r7 debe caer en domingo UTC y empieza en ISO $dia";;
               *) REQ_EST[P5c]=ERROR; REQ_DET[P5c]="no se pudo calcular el día de $FRANJA_INI";; esac
REQ_EST[P8]=NO_EVALUABLE; REQ_DET[P8]="documental: la ventana está publicada en el protocolo r4 §3.2; esta herramienta no lo comprueba"
REQ_EST[P12]=NO_EVALUABLE; REQ_DET[P12]="se cumple en la ejecución (arranque de los muestreadores antes de T_g-300 s), después de P0"

w "== DETALLE DE PRECONDICIONES (categoría estado id: detalle)"
ANT_C=0; ANT_MAL=""; OTROS=""
for id in $(printf '%s\n' "${!REQ_EST[@]}" | LC_ALL=C sort -V); do
  cat=$(categoria "$id"); st=${REQ_EST[$id]}
  w "REQ $cat $st $id: ${REQ_DET[$id]}"
  if [ "$cat" = anticipable ]; then [ "$st" = CUMPLE ] && ANT_C=$((ANT_C+1)) || ANT_MAL="$ANT_MAL $id=$st"
  else OTROS="$OTROS $id=$st"; fi
done
NANT=$(for id in "${!REQ_EST[@]}"; do categoria "$id"; done | grep -c '^anticipable$')
w "== RESUMEN"
w "BLOQUES $BLOQUES_OK/${#ORDEN[@]} ejecutados sin errores"
for n in "${ORDEN[@]}"; do [ "${EST_BLOQUE[$n]:-ERROR}" = OK ] || w "   bloque con error: $n -> ${MOT_BLOQUE[$n]:-sin ejecutar}"; done
w "PRECONDICIONES anticipables: $ANT_C/$NANT CUMPLE${ANT_MAL:+; no cumplidas o sin verificar:$ANT_MAL}"
w "PRECONDICIONES de momento, documentales y de ejecución:$OTROS"
rc=0; ver=""
if [ $BLOQUES_OK -ne ${#ORDEN[@]} ]; then rc=4; ver="NO VERIFICADO: $(( ${#ORDEN[@]} - BLOQUES_OK )) bloque(s) con error; las precondiciones no se pueden dar por evaluadas"
elif [ -n "$ANT_MAL" ]; then rc=5; ver="PRECONDICIONES NO CONFORMES:$ANT_MAL"
elif [ "$MODO" = inmediato ] && [ "${REQ_EST[P5b]}" != CUMPLE ]; then rc=5; ver="P0 INMEDIATO NO CONFORME: P5b=${REQ_EST[P5b]} (${REQ_DET[P5b]})"
elif [ "$MODO" = inmediato ]; then ver="P0 INMEDIATO CONFORME (P8 documental y P12 de la ejecución quedan fuera de esta herramienta)"
else ver="PRECONDICIONES ANTICIPABLES CONFORMES. NO sustituye al P0 inmediato: P5b=${REQ_EST[P5b]}"; fi
printf 'fin %s portatil_epoch %s\n' "$(date -u +%FT%TZ)" "$(date -u +%s)" >> "$S/resumen.txt" || EV=1
if [ $EV != 0 ]; then rc=4; ver="NO VERIFICADO: no se pudo escribir toda la evidencia ($ver)"; fi
w "RESULTADO_GLOBAL rc=$rc modo=$MODO $ver"
if [ $EV != 0 ] && [ $rc = 0 ]; then echo "RESULTADO_GLOBAL rc=4: la última escritura de evidencia falló" >&2; exit 4; fi
exit $rc
