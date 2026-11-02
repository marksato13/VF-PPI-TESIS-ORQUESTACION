#!/usr/bin/env bash
# [SENSOR1 m4rk] Lectura (sin sudo, sin cambios): contexto de piloto-con-dns en cyberflow.toml, argumentos completos del
# acumulador y del aprendizaje, últimas líneas del acumulador, y la serie COMPLETA de descartes de Suricata en
# stats.log agregada por hora y por minuto de la hora (para preparar el diagnóstico de la 4A, sin atribuir causa).
set -u
C=$HOME/cyberflow
echo "## l3 $(hostname) $(date -u +%FT%T.%3NZ)"
echo "== cyberflow.toml: líneas que mencionan piloto-con-dns, con 3 de contexto"
grep -n -B3 -A3 'piloto-con-dns' $C/configs/cyberflow.toml | sed 's/^/  /'
echo "== unidades: acumulador y aprendizaje completos"
systemctl cat cyberflow-acumular.service cyberflow-aprendizaje.service 2>/dev/null | grep -v '^#' | sed 's/^/  /'
echo "== acumular.log: últimas 8 líneas"
tail -n 8 $C/logs/acumular.log | cut -c1-300 | sed 's/^/  /'
echo "== aprendizaje: última entrada del registro (¿despliega algo?)"
tail -n 1 $C/artifacts/aprendizaje/registro.jsonl | cut -c1-600 | sed 's/^/  /'
echo "== Suricata stats.log: primera fecha, incrementos de kernel_drops por hora y por minuto de la hora"
head -5 /var/log/suricata/stats.log | grep -m1 '^Date' | sed 's/^/  primera: /'
awk '/^Date:/{split($4,t,":"); h=t[1]; m=t[2]; d=$2} /capture.kernel_drops/{v=$NF; if (n++ && v>p) {inc=v-p; ph[d" "h]+=inc; pm[m]+=inc; ev++; tot+=inc} p=v}
     END{print "  eventos con incremento:", ev, " descartes:", tot;
         print "  -- por hora (fecha hora: descartes)"; for (k in ph) print "  ", k":", ph[k] | "sort";
         close("sort");
         print "  -- por minuto de la hora (mm: descartes)"; for (k in pm) print "  ", k":", pm[k] | "sort"}' /var/log/suricata/stats.log
echo "== kernel_packets al principio y al final del fichero (proporción de descartes)"
awk '/capture.kernel_packets/{if (!a) a=$NF; b=$NF} /capture.kernel_drops/{if (!c) c=$NF; e=$NF} END{printf "  paquetes %d -> %d, descartes %d -> %d, proporción del tramo %.5f%%\n", a, b, c, e, (b>a)?100*(e-c)/(b-a):0}' /var/log/suricata/stats.log
echo "## fin $(date -u +%FT%T.%3NZ)"
