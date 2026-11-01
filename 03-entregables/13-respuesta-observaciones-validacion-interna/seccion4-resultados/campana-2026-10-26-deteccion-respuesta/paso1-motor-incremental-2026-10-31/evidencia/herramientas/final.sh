#!/bin/bash
# Resultado final: progreso, pruebas, rc, recursos, analisis completo, tablas y empaquetado de la evidencia.
cd ~/cf-p1
cat progreso.txt
echo "== pruebas 24f8a80 (sensor)"; grep -E "^(Ran|OK|FAILED|FAIL:|ERROR:)|^rc=" pruebas-9b4cf2b.txt
cut -c1-16,65- huellas-9b4cf2b.txt
for d in r1-ref-perfil r3-cand r4-cand-reinicio-9b4cf2b r5-cand-reinicio-tiempos; do
  echo "== $d $(cat $d/inicio.txt) -> $(cat $d/fin.txt) $(cat $d/rc.txt)"
  grep -E "Elapsed|Maximum res" $d/stderr.txt
  grep -c -E "Traceback" $d/stderr.txt
done
bash herramientas/empaquetar.sh
python3 herramientas/tablas_p1.py entrega/resumen.json > entrega/RESULTADOS.md
cat entrega/analisis.stdout | cut -c1-250
