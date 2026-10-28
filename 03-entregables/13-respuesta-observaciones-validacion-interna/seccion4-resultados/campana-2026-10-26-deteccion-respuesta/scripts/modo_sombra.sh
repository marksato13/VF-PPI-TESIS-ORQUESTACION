#!/usr/bin/env bash
# Pone el enforcement en SOMBRA para la campaña A, VERIFICABLE y con FALLO SEGURO.
#   [srv-dmz adminsrvdmz] -> lo ejecutas tú (NOPASSWD ALL) — o yo, al autorizar A. NO se ejecuta en la revisión.
# Por defecto SIMULA (imprime el plan, sale 0). Con --ejecutar aplica y ABORTA (exit!=0) si falla cualquier paso:
# guardar estado, detener el agente, enmascararlo, consultar nft o verificar restricciones. Una consulta nft
# fallida NUNCA se interpreta como 'set vacío'. No edita la unidad (la restauración no puede duplicar argumentos).
# Requiere --motor-verificado: confirma que en el sensor ppi-motor NO corre con --enforce (vía directa del motor).
#
# Inyectable para pruebas: SUDO, SYSTEMCTL, NFT, ESTADO_BASE (por defecto sudo/systemctl/nft//opt/cf-sombra-estado).
set -uo pipefail
SUDO="${SUDO-sudo}"; SYSTEMCTL="${SYSTEMCTL-systemctl}"; NFT="${NFT-nft}"
BASE="${ESTADO_BASE-/opt/cf-sombra-estado}"
EJECUTAR=0; MOTOR_OK=0
for arg in "$@"; do
  [ "$arg" = "--ejecutar" ] && EJECUTAR=1
  [ "$arg" = "--motor-verificado" ] && MOTOR_OK=1
done
TS=$(date -u +%Y%m%d-%H%M%S); EST="$BASE/$TS"
die(){ echo "FALLO SEGURO: $*" >&2; exit 1; }

echo "=== MODO SOMBRA ($([ $EJECUTAR -eq 1 ] && echo EJECUTAR || echo SIMULACION)) estado->$EST"
if [ $EJECUTAR -eq 0 ]; then
  cat <<PLAN
Plan (se aplica con --ejecutar --motor-verificado):
  1. guardar estado real (timer/servicio del agente, unidad, volcado de nft) en $EST
  2. detener ppi-enforce-agent.timer y .service
  3. deshabilitar el timer y enmascarar el servicio (si su unidad está en /etc no se puede: basta el timer)
  4. vaciar los sets cyberflow_bloqueados y cyberflow_limitados
  5. verificar: agente y timer inactivos, timer deshabilitado (y servicio enmascarado si se pudo),
     nft consultable y SIN elements, motor sin --enforce
Nada se aplica en modo simulación.
PLAN
  exit 0
fi

[ $MOTOR_OK -eq 1 ] || die "falta --motor-verificado (confirma en el SENSOR: systemctl cat ppi-motor | grep -- --enforce  => vacío)"

echo "--- 1) guardar estado original (si falla, abortar: no seguir a ciegas)"
$SUDO mkdir -p "$EST" || die "no se pudo crear $EST"
# is-active/is-enabled salen !=0 para inactive/disabled/masked: es un ESTADO válido, no un fallo (con pipefail
# abortaba si el timer ya estaba inactivo). Fallo = no obtener ningún valor.
guardar(){ v=$($SUDO $SYSTEMCTL "$1" "$2" 2>/dev/null || true); [ -n "$v" ] || die "no se pudo leer $1 de $2"
           echo "$v" | $SUDO tee "$EST/$3" >/dev/null || die "no se pudo guardar $3"; }
guardar is-active  ppi-enforce-agent.timer   agent-timer.active
guardar is-enabled ppi-enforce-agent.timer   agent-timer.enabled
$SUDO $NFT list table inet cyberflow                 | $SUDO tee "$EST/nft-antes.txt"        >/dev/null || die "no se pudo volcar nft (no se asume nada)"
guardar is-enabled ppi-enforce-agent.service agent-service.enabled
$SUDO cp /etc/systemd/system/ppi-enforce-agent.service "$EST/" 2>/dev/null || echo "  (aviso: no se copió la unidad; no es crítico porque no se edita)"
# estado del feed y de la escalada (para tratarlos en la restauración; NO se editan los históricos)
FEED="${FEED_DIR-/home/m4rk/feed}"
$SUDO cp "$FEED/estado.json" "$EST/escalada-estado.json" 2>/dev/null && echo "  escalada guardada" || echo "  (aviso: no se halló $FEED/estado.json; escalada DESCONOCIDA)"
$SUDO ls -la "$FEED" 2>/dev/null | $SUDO tee "$EST/feed-ls.txt" >/dev/null || true

echo "--- 2) detener el agente (lo que aplica medidas)"
$SUDO $SYSTEMCTL stop ppi-enforce-agent.timer ppi-enforce-agent.service || die "no se pudo detener el agente"
echo "--- 3) impedir la reactivación: deshabilitar el timer (siempre) y enmascarar el servicio si se puede"
$SUDO $SYSTEMCTL disable ppi-enforce-agent.timer || die "no se pudo deshabilitar el timer"
# 'mask' falla si la unidad del servicio es un fichero en /etc/systemd/system (no puede crear allí el enlace a
# /dev/null). Entonces la garantía es el timer detenido+deshabilitado (el servicio es static: solo lo lanza el timer).
if $SUDO $SYSTEMCTL mask ppi-enforce-agent.service; then MEC="servicio-enmascarado+timer-deshabilitado"
else MEC="timer-deshabilitado"; echo "  aviso: no se pudo enmascarar el servicio; la sombra se garantiza con el timer detenido y deshabilitado"; fi
echo "$MEC" | $SUDO tee "$EST/mecanismo" >/dev/null || die "no se pudo registrar el mecanismo"
echo "--- 4) vaciar restricciones residuales"
$SUDO $NFT flush set inet cyberflow cyberflow_bloqueados || die "no se pudo vaciar bloqueados"
$SUDO $NFT flush set inet cyberflow cyberflow_limitados  || die "no se pudo vaciar limitados"

echo "--- 5) verificar (consulta fallida != set vacío)"
act=$($SUDO $SYSTEMCTL is-active ppi-enforce-agent.service 2>/dev/null || true)
[ "$act" = "active" ] && die "el agente sigue activo"
tac=$($SUDO $SYSTEMCTL is-active ppi-enforce-agent.timer 2>/dev/null || true)
[ "$tac" = "active" ] && die "el timer del agente sigue activo"
ten=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.timer 2>/dev/null || true)
[ "$ten" = "disabled" ] || die "el timer no quedó deshabilitado (is-enabled=$ten)"
msk=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service 2>/dev/null || true)
if [ "$MEC" = "servicio-enmascarado+timer-deshabilitado" ]; then
  [ "$msk" = "masked" ] || die "el agente no quedó enmascarado (is-enabled=$msk)"
fi
for set in cyberflow_bloqueados cyberflow_limitados; do
  out=$($SUDO $NFT list set inet cyberflow $set 2>/dev/null); rc=$?
  [ $rc -ne 0 ] && die "no se pudo consultar $set (NO se asume vacío)"
  echo "$out" | grep -q 'elements' && die "quedan elementos en $set"
done
echo "OK sombra verificada (agente y timer detenidos, mecanismo=$MEC, sets vacíos, motor sin --enforce confirmado)."
echo "$TS" | $SUDO tee "$BASE/ultimo" >/dev/null || die "no se pudo registrar el último estado"
echo "Restaurar tras A: restaurar_enforcement.sh --ejecutar"
