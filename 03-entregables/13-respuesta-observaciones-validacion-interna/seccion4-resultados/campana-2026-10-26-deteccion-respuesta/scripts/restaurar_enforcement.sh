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
EJECUTAR=0; ESCALADA_OK=0
for arg in "$@"; do
  [ "$arg" = "--ejecutar" ] && EJECUTAR=1
  [ "$arg" = "--escalada-revisada" ] && ESCALADA_OK=1
done
die(){ echo "FALLO: $*" >&2; exit 1; }

TS=$(cat "$BASE/ultimo" 2>/dev/null || true)
EST="$BASE/$TS"
echo "=== RESTAURAR ($([ $EJECUTAR -eq 1 ] && echo EJECUTAR || echo SIMULACION)) desde $EST"
if [ $EJECUTAR -eq 0 ]; then
  cat <<PLAN
Plan (se aplica con --ejecutar --escalada-revisada):
  0. comprobar respaldo completo; vaciar sets residuales de la campaña A
  1. exigir confirmación explícita de que se revisó la escalada (feed/estado.json); un aviso NO basta
  2. desenmascarar y reactivar el agente SEGÚN el estado guardado (sin defaults que arranquen servicios)
  3. verificar; NO se anuncia "restauración exacta" (los sets vaciados son limpieza experimental no recuperable)
PLAN
  exit 0
fi

# respaldo completo o abortar
[ -n "$TS" ] && [ -d "$EST" ] || die "no hay respaldo del estado ($BASE/ultimo / $EST): no se restaura a ciegas"
for f in agent-timer.active agent-timer.enabled agent-service.enabled; do
  [ -f "$EST/$f" ] || die "respaldo incompleto: falta $f (no se restaura con valores por defecto)"
done
ac=$(cat "$EST/agent-timer.active"); en=$(cat "$EST/agent-timer.enabled"); svc=$(cat "$EST/agent-service.enabled")

echo "--- 0) evitar decisiones residuales de A: vaciar sets antes de reactivar"
$SUDO $NFT flush set inet cyberflow cyberflow_bloqueados || die "no se pudo vaciar bloqueados antes de reactivar"
$SUDO $NFT flush set inet cyberflow cyberflow_limitados  || die "no se pudo vaciar limitados antes de reactivar"

echo "--- 1) escalada y feed: comprobación EXPLÍCITA (un aviso no permite continuar)"
if [ -f "$EST/escalada-estado.json" ]; then
  echo "   escalada guardada en $EST/escalada-estado.json (contadores previos a A)."
else
  echo "   escalada DESCONOCIDA (no se guardó estado.json)."
fi
[ $ESCALADA_OK -eq 1 ] || die "falta --escalada-revisada: revisa el feed y el contador de escalada (que el agente no aplique decisiones residuales de A) y vuelve a lanzar con --escalada-revisada"

echo "--- 2) reactivar SEGÚN el respaldo (timer activo=$ac enabled=$en ; service=$svc)"
if [ "$svc" = "masked" ]; then
  echo "   el servicio estaba ENMASCARADO antes de A: se deja enmascarado (no se reactiva)."
else
  $SUDO $SYSTEMCTL unmask ppi-enforce-agent.service || die "no se pudo desenmascarar"
  if [ "$en" = "enabled" ]; then $SUDO $SYSTEMCTL enable ppi-enforce-agent.timer || die "no se pudo habilitar"; fi
  if [ "$en" = "disabled" ]; then $SUDO $SYSTEMCTL disable ppi-enforce-agent.timer || die "no se pudo deshabilitar"; fi
  if [ "$ac" = "active" ]; then $SUDO $SYSTEMCTL start ppi-enforce-agent.timer || die "no se pudo iniciar el timer"; fi
fi

echo "--- 3) verificar (no anunciar completo si es parcial)"
if [ "$svc" = "masked" ]; then
  m=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service 2>/dev/null || true)
  [ "$m" = "masked" ] || die "el servicio no quedó como estaba (enmascarado)"
else
  m=$($SUDO $SYSTEMCTL is-enabled ppi-enforce-agent.service 2>/dev/null || true)
  [ "$m" = "masked" ] && die "el servicio sigue enmascarado"
  if [ "$ac" = "active" ]; then
    t=$($SUDO $SYSTEMCTL is-active ppi-enforce-agent.timer 2>/dev/null || true)
    [ "$t" = "active" ] || die "el timer no quedó activo como estaba"
  fi
fi
echo "OK agente restaurado al estado previo (timer=$ac/$en, service=$svc). NO es 'restauración exacta': los sets de"
echo "nftables se vaciaron (limpieza experimental de A, no recuperable). Comprobar: journalctl -u ppi-enforce-agent -n 20"
