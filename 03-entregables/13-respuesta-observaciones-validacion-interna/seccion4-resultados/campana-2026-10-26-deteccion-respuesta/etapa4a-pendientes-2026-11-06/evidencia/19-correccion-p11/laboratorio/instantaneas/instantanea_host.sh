#!/usr/bin/env bash
# [HOST] Instantánea de SOLO LECTURA del paquete 902991e: estructura completa (tipo, modo, tamaño, mtime con ns,
# propietario, ruta; también directorios) y sha256 de cada fichero regular. No escribe nada.
# Salida: secciones ESTRUCTURA y SHA256, y al final «INSTANTANEA <host> rc=<n> estructura=<sha> contenidos=<sha> ficheros=<n>».
set -u -o pipefail
export LC_ALL=C
N=${N:-?}
P="$HOME/cf-e4/paquete-902991e"
[ -d "$P" ] && [ ! -L "$P" ] || { echo "INSTANTANEA $N rc=3 sin paquete $P"; exit 3; }
e=$(find "$P" -printf '%y %m %s %T@ %u %p\n' | sort) || { echo "INSTANTANEA $N rc=3 find falló"; exit 3; }
s=$(cd "$P" && find . -type f -print0 | sort -z | xargs -0 sha256sum) || { echo "INSTANTANEA $N rc=3 sha256sum falló"; exit 3; }
echo "INFO $N $(id -un) $(hostname) $(date -u +%FT%TZ)"
echo "== ESTRUCTURA"; printf '%s\n' "$e"
echo "== SHA256"; printf '%s\n' "$s"
he=$(printf '%s\n' "$e" | sha256sum | cut -c1-64); hs=$(printf '%s\n' "$s" | sha256sum | cut -c1-64)
nf=$(printf '%s\n' "$s" | grep -c .)
echo "INSTANTANEA $N rc=0 estructura=$he contenidos=$hs ficheros=$nf sumas=$(sha256sum < "$P/SHA256SUMS" | cut -c1-64)"
exit 0
