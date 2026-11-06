# Bloque P0 punto 1 (solo lectura): verificador del host desde ~/cf-e4/paquete-902991e (bytes idénticos a a1cea5e).
H=${1:-?}; P=~/cf-e4/paquete-902991e/deploy/etapa4
echo "== $H $(hostname) $(date -u +%FT%TZ)"
case "$H" in
  bastion) sha256sum "$P/bastion/verificar_bastion.sh"; bash "$P/bastion/verificar_bastion.sh" < /dev/null; rc=$?;;
  sensor1) sha256sum "$P/sensor1/verificar_sensor1.sh"; bash "$P/sensor1/verificar_sensor1.sh" < /dev/null; rc=$?;;
  srvdmz)  R=/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z
           [ -d "$R" ] || { echo "FALTA el respaldo $R"; exit 2; }
           sha256sum "$P/srvdmz/verificar_srvdmz.sh"; CON_SUDO=1 bash "$P/srvdmz/verificar_srvdmz.sh" "$R" < /dev/null; rc=$?;;
  *) echo "host desconocido"; exit 2;;
esac
echo "rc_verificador=$rc"
exit $rc
