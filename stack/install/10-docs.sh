#!/usr/bin/env bash
# Cadena documental: de Markdown a PDF listo para la revista.
# Es lo unico del stack con fecha limite real: el articulo va a IJIES.
. "$(dirname "$0")/comun.sh"
exige_root
paso "Pandoc, LaTeX y Graphviz"
apt-get update -qq
apt_faltantes pandoc graphviz \
  texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
  texlive-lang-spanish lmodern
verde "Cadena documental lista."
echo "  prueba:  stack/bin/ppi-doc <archivo.md>"
