#!/bin/bash
# Empaqueta la evidencia del paso 1 en ~/cf-p1/entrega (para el repo de documentacion) y escribe su manifiesto.
# No borra nada de ~/cf-p1: las corridas completas se conservan alli.
set -eu
P=~/cf-p1; E=$P/entrega
rm -rf $E; mkdir -p $E/corridas $E/herramientas
cd $P
python3 herramientas/analizar_p1.py --base . --marcas herramientas/marcas.jsonl --salida $E/resumen.json > $E/analisis.stdout
for d in r0-perfil-ref r1-ref-perfil r2-cand-verif r3-cand r4-ref-reinicio r4-cand-reinicio r4-cand-reinicio-9b4cf2b r5-cand-reinicio-tiempos; do
  [ -d $d ] || continue
  o=$E/corridas/$d; mkdir -p $o
  for f in inicio.txt fin.txt rc.txt stdout.txt huellas.txt; do [ -f $d/$f ] && cp $d/$f $o/; done
  [ -f $d/stderr.txt ] && cp $d/stderr.txt $o/stderr-y-time-v.txt   # incluye /usr/bin/time -v (RSS maximo, CPU)
  [ -f $d/motor_decision.log ] && gzip -9c $d/motor_decision.log > $o/motor_decision.log.gz
  [ -f $d/ciclos-arnes.jsonl ] && gzip -9c $d/ciclos-arnes.jsonl > $o/ciclos-arnes.jsonl.gz
  [ -f $d/_state/ciclos.jsonl ] && gzip -9c $d/_state/ciclos.jsonl > $o/ciclos-motor.jsonl.gz
  [ -f $d/verificacion.jsonl ] && gzip -9c $d/verificacion.jsonl > $o/verificacion.jsonl.gz
done
cp herramientas/replay_motor.py herramientas/analizar_p1.py herramientas/corridas.sh herramientas/fase_c.sh \
   herramientas/r0_perfil_ref.sh herramientas/marcas.jsonl args-motor.txt $E/herramientas/ 2>/dev/null || true
cp huellas.txt $E/huellas-4552d83.txt; cp huellas-9b4cf2b.txt $E/ 2>/dev/null || true
cp pruebas-9b4cf2b.txt $E/pruebas-unittest-24f8a80-sensor.txt 2>/dev/null || true
cp progreso.txt corridas.out $E/ 2>/dev/null || true
sha256sum ~/cf-campana-A-20261029/fuentes/eve.json > $E/huellas-entradas.txt
(cd ~/cf-campana-A-20261029/archivo-pcap && ls live-*.pcap | wc -l && cat live-*.pcap | sha256sum) >> $E/huellas-entradas.txt
du -sh $P $E
(cd $E && find . -type f ! -name MANIFIESTO.sha256 | sort | xargs sha256sum > MANIFIESTO.sha256)
wc -l $E/MANIFIESTO.sha256
