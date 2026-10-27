#!/usr/bin/env bash
# Verifica el FALLO SEGURO de modo_sombra.sh / restaurar_enforcement.sh con comandos SIMULADOS.
# No toca ningún host. Ningún caso de fallo debe anunciar éxito ni salir con código 0.
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
SH="$AQUI/../scripts"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FBIN="$TMP/bin"; mkdir -p "$FBIN"
fallos=0; ok=0

cat > "$FBIN/fsudo"      <<'E'
#!/usr/bin/env bash
exec "$@"
E
cat > "$FBIN/fsudo_deny" <<'E'
#!/usr/bin/env bash
echo "sudo: denegado" >&2; exit 1
E
cat > "$FBIN/fsystemctl" <<'E'
#!/usr/bin/env bash
sub="$1"; shift || true
case "$sub" in
  is-active)  echo "${ACT:-inactive}";;
  is-enabled) echo "${ENA:-enabled}";;
  stop)   [ "${FAIL_STOP:-0}" = 1 ] && exit 1 || exit 0;;
  mask)   [ "${FAIL_MASK:-0}" = 1 ] && exit 1 || exit 0;;
  unmask) [ "${FAIL_UNMASK:-0}" = 1 ] && exit 1 || exit 0;;
  enable|start) [ "${FAIL_START:-0}" = 1 ] && exit 1 || exit 0;;
  *) exit 0;;
esac
E
cat > "$FBIN/fnft" <<'E'
#!/usr/bin/env bash
case "$*" in
  *"list set"*)   [ "${FAIL_NFTQ:-0}" = 1 ] && exit 3;  echo "table inet cyberflow { set s { type ipv4_addr } }";;
  *"list table"*) [ "${FAIL_NFTD:-0}" = 1 ] && exit 3;  echo "table inet cyberflow {}";;
  *flush*)        [ "${FAIL_FLUSH:-0}" = 1 ] && exit 1; exit 0;;
  *) exit 0;;
esac
E
chmod +x "$FBIN"/*

S="SUDO=$FBIN/fsudo SYSTEMCTL=$FBIN/fsystemctl NFT=$FBIN/fnft"
run(){ # descripcion ; espera_exito(0/1) ; env... ; -- comando
  desc="$1"; espera="$2"; shift 2
  out="$(env "$@" bash 2>&1)"; rc=$?
  exito=$(echo "$out" | grep -cE 'OK sombra verificada|OK agente restaurado')
  if [ "$espera" = 1 ]; then
    { [ $rc -eq 0 ] && [ "$exito" -ge 1 ]; } && { echo "OK  $desc"; ok=$((ok+1)); } || { echo "FALLA $desc (rc=$rc exito=$exito)"; fallos=$((fallos+1)); }
  else
    { [ $rc -ne 0 ] && [ "$exito" -eq 0 ]; } && { echo "OK  $desc"; ok=$((ok+1)); } || { echo "FALLA $desc (rc=$rc exito=$exito; anunció éxito en un fallo)"; fallos=$((fallos+1)); }
  fi
}

M(){ echo "bash '$SH/modo_sombra.sh' --ejecutar --motor-verificado"; }
R(){ echo "bash '$SH/restaurar_enforcement.sh' --ejecutar"; }
R2(){ echo "bash '$SH/restaurar_enforcement.sh' --ejecutar --escalada-revisada"; }
mkbackup(){ # dir ts ac en svc
  mkdir -p "$1/$2"; echo "$2" > "$1/ultimo"
  echo "$3" > "$1/$2/agent-timer.active"; echo "$4" > "$1/$2/agent-timer.enabled"
  echo "$5" > "$1/$2/agent-service.enabled"; echo '{}' > "$1/$2/escalada-estado.json"
}

# feliz: sombra OK (agente inactivo, enmascarado, sets sin elements)
run "sombra feliz" 1 ESTADO_BASE="$TMP/e1" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=masked ACT=inactive <<<"$(M)"
# fallos: ninguno debe anunciar éxito
run "sudo denegado"        0 ESTADO_BASE="$TMP/e2" SUDO="$FBIN/fsudo_deny" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" <<<"$(M)"
run "servicio no se detiene" 0 ESTADO_BASE="$TMP/e3" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" FAIL_STOP=1 <<<"$(M)"
run "consulta nft falla"   0 ESTADO_BASE="$TMP/e4" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=masked ACT=inactive FAIL_NFTQ=1 <<<"$(M)"
run "falta --motor-verificado" 0 ESTADO_BASE="$TMP/e5" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" <<<"bash '$SH/modo_sombra.sh' --ejecutar"
# restauración correcta (estado original activo/enabled; escalada revisada)
mkbackup "$TMP/r1" T1 active enabled enabled
run "restaurar correcta" 1 ESTADO_BASE="$TMP/r1" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=enabled ACT=active <<<"$(R2)"
# estado original ENMASCARADO: se restaura a enmascarado (no se reactiva)
mkbackup "$TMP/r2" T1 inactive masked masked
run "restaurar a enmascarado" 1 ESTADO_BASE="$TMP/r2" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=masked ACT=inactive <<<"$(R2)"
# escalada pendiente: sin --escalada-revisada no debe continuar
mkbackup "$TMP/r3" T1 active enabled enabled
run "escalada pendiente (sin confirmar)" 0 ESTADO_BASE="$TMP/r3" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=enabled ACT=active <<<"$(R)"
# error de verificación: timer no queda activo aunque el respaldo decía active
mkbackup "$TMP/r4" T1 active enabled enabled
run "error de verificación" 0 ESTADO_BASE="$TMP/r4" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" ENA=enabled ACT=inactive <<<"$(R2)"
# respaldo ausente e incompleto
run "restaurar sin respaldo" 0 ESTADO_BASE="$TMP/vacio" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" <<<"$(R2)"
mkdir -p "$TMP/e6/XX"; echo XX > "$TMP/e6/ultimo"
run "restaurar respaldo incompleto" 0 ESTADO_BASE="$TMP/e6" SUDO="$FBIN/fsudo" SYSTEMCTL="$FBIN/fsystemctl" NFT="$FBIN/fnft" <<<"$(R2)"

echo "----- sombra: $ok ok, $fallos fallos"
[ $fallos -eq 0 ]
