#!/usr/bin/env bash
# Restaura el enforcement en APLICAR tras la campaña A, al estado EXACTO previo, con FALLO SEGURO.
#   [srv-dmz adminsrvdmz] -> lo ejecutas tú — o yo. NO se ejecuta en la revisión.
# Por defecto SIMULA; con --ejecutar aplica. ABORTA (exit!=0) si falta el respaldo o la restauración queda a
# medias. NO usa valores por defecto que arranquen servicios cuando falta el respaldo. No edita la unidad.
#
# Antes de reactivar el agente trata las restricciones y el estado de escalada para no aplicar decisiones
# residuales de la campaña A: vacía los sets y AVISA de revisar estado.json (escalada) manualmente.
# Inyectable para pruebas: SUDO, SYSTEMCTL, NFT, ESTADO_BASE.
set -uo pipefail
SUDO="${SUDO-sudo}"; SYSTEMCTL="${SYSTEMCTL-systemctl}"; NFT="${NFT-nft}"
BASE="${ESTADO_BASE-/opt/cf-sombra-estado}"
EJECUTAR=0; [ "${1:-}" = "--ejecutar" ] && EJECUTAR=1
die(){ echo "FALLO: $*" >&2; exit 1; }

TS=$(cat "$BASE/ultimo" 2>/dev/null || true)
EST="$BASE/$TS"
echo "=== RESTAURAR ($([ $EJECUTAR -eq 1 ] && echo EJECUTAR || echo SIMULACION)) desde $EST"
if [ $EJECUTAR -eq 0 ]; then
  echo "Plan: vaciar sets residuales, revisar estado.json (escalada), desenmascarar y reactivar el agente SEGÚN"
  echo "el respaldo $EST (sin valores por defecto). Se aplica con --ejecutar."
  exit 0
fi

[ -n "$TS" ] && [ -d "$EST" ] || die "no hay respaldo del estado ($BASE/ultimo / $EST): no se restaura a ciegas"
[ -f "$EST/agent-timer.active" ] && [ -f "$EST/agent-timer.enabled" ] || die "respaldo incompleto: faltan ficheros de estado"
ac=$(cat "$EST/agent-timer.active"); en=$(cat "$EST/agent-timer.enabled")

echo "--- 0) evitar decisiones residuales de la campaña A antes de reactivar"
$SUDO $NFT flush set inet cyberflow cyberflow_bloqueados || die "no se pudo vaciar bloqueados antes de reactivar"
$SUDO $NFT flush set inet cyberflow cyberflow_limitados  || die "no se pudo vaciar limitados antes de reactivar"
echo "   AVISO: revisar /home/*/feed/estado.json (contador de escalada) antes de que el agente vuelva a actuar."

echo "--- 1) desenmascarar"
$SUDO $SYSTEMCTL unmask ppi-enforce-agent.service || die "no se pudo desenmascarar"
echo "--- 2) reactivar SEGÚN el respaldo ($ac/$en)"
if [ "$en" = "enabled" ]; then $SUDO $SYSTEMCTL enable ppi-enforce-agent.timer || die "no se pudo habilitar"; fi
if [ "$ac" = "active" ]; then $SUDO $SYSTEMCTL start ppi-enforce-agent.timer || die "no se pudo iniciar el timer"; fi

echo "--- 3) verificar restauración (no anunciar completo si es parcial)"
msk=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service 2>/dev/null || true)
[ "$msk" = "masked" ] && die "el servicio sigue enmascarado"
if [ "$ac" = "active" ]; then
  t=$($SUDO $SYSTEMCTL is-active ppi-enforce-agent.timer 2>/dev/null || true)
  [ "$t" = "active" ] || die "el timer no quedó activo como estaba"
fi
echo "OK enforcement restaurado al estado previo ($ac/$en). Comprobar: journalctl -u ppi-enforce-agent -n 20"
