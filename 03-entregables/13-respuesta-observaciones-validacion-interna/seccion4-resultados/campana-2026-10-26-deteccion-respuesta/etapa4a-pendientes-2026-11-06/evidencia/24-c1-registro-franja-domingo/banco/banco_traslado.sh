#!/usr/bin/env bash
# [CONTENEDOR sin red] Banco de instalar_bastion_host.sh, con un HOME temporal. No hay transporte: ni scp ni ssh.
#   banco_traslado.sh INSTALAR TGZ PAQUETE_ECARGA COMMIT7 SUMAS TGZSHA
set -u
I=$1; T=$2; PQ=$3; C=$4; S=$5; G=$6
fallos=0; casos=0
caso() {  # caso NOMBRE RC_ESPERADO ESTADO_ESPERADO -- ARGS
  local n=$1 er=$2 ee=$3; shift 4
  local o r; o=$(bash "$I" "$@" 2>&1); r=$?
  casos=$((casos + 1))
  if [ "$r" = "$er" ] && grep -q "ESTADO_FINAL=$ee rc=$er" <<<"$o"; then echo "OK    $n: rc=$r $ee"
  else echo "FALLO $n: rc=$r, se esperaba $er $ee"; printf '%s\n' "$o" | sed 's/^/      /'; fallos=$((fallos + 1)); fi
}
export HOME=$(mktemp -d)
mkdir -p "$HOME/cf-e4/paquete-902991e/deploy/etapa4"
cp -r "$PQ" "$HOME/cf-e4/paquete-902991e/deploy/etapa4/ecarga"
H0=$(cd "$HOME/cf-e4/paquete-902991e" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum)
F=/tmp/cf-e4-ecarga-bastion-$C.tgz
D=$HOME/cf-e4/ecarga-bastion-$C

caso "uso sin argumentos" 2 USO --
caso "verificar sin instalar" 5 NO_VERIFICA -- verificar "$C" "$S"
caso "tgz ausente" 4 TGZ_DISTINTO -- instalar "$C" "$S" "$G"
head -c 100 /dev/zero > "$F"
caso "tgz distinto" 4 TGZ_DISTINTO -- instalar "$C" "$S" "$G"
cp "$T" "$F"
caso "SHA256SUMS esperado distinto" 5 NO_VERIFICA -- instalar "$C" "$(printf 0%.0s {1..64})" "$G"
[ ! -e "$D" ] && echo "OK    sin carpeta tras no verificar" || { echo "FALLO quedó carpeta"; fallos=$((fallos + 1)); }
caso "instalación" 0 VERIFICADO -- instalar "$C" "$S" "$G"
[ ! -e "$F" ] && echo "OK    tgz retirado de /tmp" || { echo "FALLO tgz sigue en /tmp"; fallos=$((fallos + 1)); }
caso "verificar instalado" 0 VERIFICADO -- verificar "$C" "$S"
cp "$T" "$F"
caso "segunda instalación" 3 CARPETA_EXISTENTE -- instalar "$C" "$S" "$G"
rm -f "$F"
[ "$(cd "$HOME/cf-e4/paquete-902991e" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum)" = "$H0" ] \
  && echo "OK    paquete-902991e intacto" || { echo "FALLO el paquete cambió"; fallos=$((fallos + 1)); }
chmod u+w "$D" "$D/muestreo_bastion.sh"
echo "# alterado" >> "$D/muestreo_bastion.sh"
caso "fichero alterado" 5 NO_VERIFICA -- verificar "$C" "$S"
sed -i '$d' "$D/muestreo_bastion.sh"
touch "$D/extra"
caso "fichero de más" 5 NO_VERIFICA -- verificar "$C" "$S"
rm -f "$D/extra"
chmod u+w "$HOME/cf-e4/paquete-902991e/deploy/etapa4/ecarga/guardia.py"
echo "# otro" >> "$HOME/cf-e4/paquete-902991e/deploy/etapa4/ecarga/guardia.py"
caso "guardia distinta del paquete" 5 NO_VERIFICA -- verificar "$C" "$S"
echo "casos=$casos fallos=$fallos"
exit $((fallos > 0))
