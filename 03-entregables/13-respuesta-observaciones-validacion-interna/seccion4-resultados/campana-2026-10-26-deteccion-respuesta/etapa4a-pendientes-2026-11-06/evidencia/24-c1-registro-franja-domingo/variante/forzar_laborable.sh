#!/usr/bin/env bash
# [CLIENTES root] Variante temporal y reversible del protocolo E-carga v2 r5. VERSION 2026-11-07.1
# Lo ejecuta Mark con sudo: adminclientes no puede escribir en /etc/systemd/system ni hacer daemon-reload sin contraseña.
#   forzar_laborable.sh aplicar    añade un drop-in a cada una de las seis unidades con la opción existente --forzar-laborable
#   forzar_laborable.sh revertir   retira esos drop-ins y nada más
# No edita las unidades, ni clientes_lab.py, ni arranca o para nada. Con el target activo no hace ningún cambio.
# rc: 0 hecho y comprobado · 1 no conforme: revisar antes de seguir · 2 uso
set -u -o pipefail
RAIZ=${CF_RAIZ:-}                    # solo el banco lo cambia
SC=${CF_SYSTEMCTL:-systemctl}
GEN=/home/adminclientes/laboratorio/clientes_lab.py
GEN_LOCAL=${CF_GEN:-$GEN}
HASH=${CF_HASH:-ae5134a778e66d90f5c3fbcd47323e328f3422cf4ba8d5197649f402c1d4cdc3}
PERFILES="ofimatica:10.10.20.21 navegacion:10.10.20.22 descargas:10.10.20.23 aplicacion:10.10.20.24 ligero:10.10.20.25 erratico:10.10.20.26"
CONF=10-forzar-laborable-r5.conf
ORDEN=${1:-}
dir_de() { printf '%s/etc/systemd/system/cyberflow-lab-%s.service.d' "$RAIZ" "$1"; }
fin() { echo "FORZAR_LABORABLE $ORDEN rc=$1 ${2:-}"; exit "$1"; }

[ "$ORDEN" = aplicar ] || [ "$ORDEN" = revertir ] || { echo "uso: forzar_laborable.sh aplicar|revertir"; exit 2; }
[ -n "$RAIZ" ] || [ "$(id -u)" = 0 ] || fin 1 "hay que ejecutarlo con sudo"
[ "$($SC is-active cyberflow-lab.target 2>/dev/null)" = inactive ] || fin 1 "cyberflow-lab.target no está inactive: no se cambia nada"
for p in $PERFILES; do
  a=$($SC is-active "cyberflow-lab-${p%%:*}.service" 2>/dev/null)
  [ "$a" = inactive ] || [ "$a" = failed ] || fin 1 "${p%%:*} está $a: no se cambia nada"
done
h=$(sha256sum < "$GEN_LOCAL" | cut -c1-64)
[ "$h" = "$HASH" ] || fin 1 "sha256 del generador $h distinto del esperado"

if [ "$ORDEN" = aplicar ]; then
  for p in $PERFILES; do
    d=$(dir_de "${p%%:*}")
    if [ -e "$d" ] && [ -n "$(ls -A "$d")" ]; then fin 1 "$d ya existe y no está vacío: no se cambia nada"; fi
  done
  hechos=""
  for p in $PERFILES; do
    n=${p%%:*}; ip=${p#*:}; d=$(dir_de "$n")
    if mkdir -p "$d" && printf '[Service]\nExecStart=\nExecStart=/usr/bin/python3 %s --perfil %s --origen %s --servidor 10.10.30.10 --dns 10.10.10.20 --forzar-laborable\n' \
         "$GEN" "$n" "$ip" > "$d/$CONF.tmp" && chmod 0644 "$d/$CONF.tmp" && mv -f "$d/$CONF.tmp" "$d/$CONF"; then
      hechos="$hechos $d"
    else
      for x in $hechos "$d"; do rm -f "$x/$CONF" "$x/$CONF.tmp"; rmdir "$x" 2>/dev/null; done
      fin 1 "no se pudo escribir $d: retirados los drop-ins de esta pasada"
    fi
  done
else
  for p in $PERFILES; do
    d=$(dir_de "${p%%:*}")
    rm -f "$d/$CONF" "$d/$CONF.tmp"
    [ ! -d "$d" ] || rmdir "$d" 2>/dev/null || fin 1 "$d contiene otros ficheros: no se tocan"
  done
fi
$SC daemon-reload || fin 1 "daemon-reload falló: revisar el estado de las unidades"
fin 0 "seis unidades; comprobar ahora con comprobar_forzar.sh"
