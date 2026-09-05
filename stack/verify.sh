#!/usr/bin/env bash
# Verifica lo que quedo realmente instalado y funcionando. Sin root.
# No dice "instalado": ejecuta cada cosa y mira si responde.
. "$(dirname "$0")/install/comun.sh"
set +e
cd "$(dirname "$0")/.."

ok=0; no=0
comprueba(){ # nombre  comando...
  local n="$1"; shift
  if "$@" >/dev/null 2>&1; then printf "  \033[32m✓\033[0m %s\n" "$n"; ok=$((ok+1))
  else printf "  \033[31m✗\033[0m %s\n" "$n"; no=$((no+1)); fi
}

paso "Nucleo (sin dependencias externas)"
comprueba "ppi-trace indexa"    ./stack/bin/ppi-trace ingest
comprueba "ppi-trace verifica"  ./stack/bin/ppi-trace check
comprueba "ppi-secrets escanea" ./stack/bin/ppi-secrets --todo

paso "Cadena documental"
comprueba "pandoc"   pandoc --version
comprueba "graphviz" dot -V
# pdflatex NO basta: se atraganta con tau, nu, alpha y las flechas que estos
# documentos usan constantemente, y falla con un error de LaTeX ilegible.
# Lo que hay que comprobar es el motor Unicode y un PDF de verdad.
comprueba "motor Unicode (lualatex o xelatex)" \
  bash -c 'command -v lualatex >/dev/null || command -v xelatex >/dev/null'
comprueba "PDF real con simbolos griegos" ./stack/bin/ppi-prueba-pdf

paso "Contenedores"
comprueba "docker"          docker --version
comprueba "compose v2"      docker compose version
comprueba "docker sin sudo" docker info

paso "Copias"
comprueba "restic" restic version
comprueba "age"    age --version

printf "\n  %s funcionando · %s no\n" "$ok" "$no"
[ "$no" -gt 0 ] && echo "  Lo que falta se instala con:  sudo stack/install.sh"
exit 0
