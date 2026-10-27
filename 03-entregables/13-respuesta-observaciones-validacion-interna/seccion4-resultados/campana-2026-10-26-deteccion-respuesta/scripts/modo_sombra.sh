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
  2. detener ppi-enforce-agent.timer y .service ; 3. enmascarar el servicio
  4. vaciar los sets cyberflow_bloqueados y cyberflow_limitados
  5. verificar: agente inactivo+enmascarado, nft consultable y SIN elements, motor sin --enforce
Nada se aplica en modo simulación.
PLAN
  exit 0
fi

[ $MOTOR_OK -eq 1 ] || die "falta --motor-verificado (confirma en el SENSOR: systemctl cat ppi-motor | grep -- --enforce  => vacío)"

echo "--- 1) guardar estado original (si falla, abortar: no seguir a ciegas)"
$SUDO mkdir -p "$EST" || die "no se pudo crear $EST"
$SUDO $SYSTEMCTL is-active ppi-enforce-agent.timer   | $SUDO tee "$EST/agent-timer.active"  >/dev/null || die "no se pudo guardar estado (active)"
$SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.timer  | $SUDO tee "$EST/agent-timer.enabled" >/dev/null || die "no se pudo guardar estado (enabled)"
$SUDO $NFT list table inet cyberflow                 | $SUDO tee "$EST/nft-antes.txt"        >/dev/null || die "no se pudo volcar nft (no se asume nada)"
$SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service | $SUDO tee "$EST/agent-service.enabled" >/dev/null || die "no se pudo guardar estado (service enabled/masked)"
$SUDO cp /etc/systemd/system/ppi-enforce-agent.service "$EST/" 2>/dev/null || echo "  (aviso: no se copió la unidad; no es crítico porque no se edita)"
# estado del feed y de la escalada (para tratarlos en la restauración; NO se editan los históricos)
FEED="${FEED_DIR-/home/m4rk/feed}"
$SUDO cp "$FEED/estado.json" "$EST/escalada-estado.json" 2>/dev/null && echo "  escalada guardada" || echo "  (aviso: no se halló $FEED/estado.json; escalada DESCONOCIDA)"
$SUDO ls -la "$FEED" 2>/dev/null | $SUDO tee "$EST/feed-ls.txt" >/dev/null || true

echo "--- 2) detener el agente (lo que aplica medidas)"
$SUDO $SYSTEMCTL stop ppi-enforce-agent.timer ppi-enforce-agent.service || die "no se pudo detener el agente"
echo "--- 3) enmascarar el servicio (que ningún timer lo reactive)"
$SUDO $SYSTEMCTL mask ppi-enforce-agent.service || die "no se pudo enmascarar el agente"
echo "--- 4) vaciar restricciones residuales"
$SUDO $NFT flush set inet cyberflow cyberflow_bloqueados || die "no se pudo vaciar bloqueados"
$SUDO $NFT flush set inet cyberflow cyberflow_limitados  || die "no se pudo vaciar limitados"

echo "--- 5) verificar (consulta fallida != set vacío)"
act=$($SUDO $SYSTEMCTL is-active ppi-enforce-agent.service 2>/dev/null || true)
[ "$act" = "active" ] && die "el agente sigue activo"
msk=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service 2>/dev/null || true)
[ "$msk" = "masked" ] || die "el agente no quedó enmascarado (is-enabled=$msk)"
for set in cyberflow_bloqueados cyberflow_limitados; do
  out=$($SUDO $NFT list set inet cyberflow $set 2>/dev/null); rc=$?
  [ $rc -ne 0 ] && die "no se pudo consultar $set (NO se asume vacío)"
  echo "$out" | grep -q 'elements' && die "quedan elementos en $set"
done
echo "OK sombra verificada (agente detenido+enmascarado, sets vacíos, motor sin --enforce confirmado)."
echo "$TS" | $SUDO tee "$BASE/ultimo" >/dev/null || die "no se pudo registrar el último estado"
echo "Restaurar tras A: restaurar_enforcement.sh --ejecutar"
