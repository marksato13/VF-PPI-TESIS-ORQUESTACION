#!/usr/bin/env bash
# [CLIENTES adminclientes] Lectura (sin sudo, sin cambios): perfiles de tráfico en marcha, sus argumentos, unidades,
# timers y cron; si alguno lleva la etiqueta piloto-con-dns o una campaña.
set -u
echo "## l2 $(hostname) $(whoami) $(date -u +%FT%T.%3NZ)"
echo "== procesos de los perfiles (argumentos completos)"
ps -eo pid,ppid,user,lstart,args --sort=start_time | grep -E 'perfil|generador|cyberflow|trafico|piloto|campaign|campana|curl|python' | grep -v -E 'grep -E|l2_clientes' | cut -c1-300 | head -40
echo "== unidades y timers relacionados"
systemctl list-units --all --no-pager --plain '*perfil*' '*cyberflow*' '*trafico*' 'cf-*' 2>&1 | head -30
systemctl list-timers --all --no-pager 2>&1 | grep -E 'perfil|cyberflow|trafico|cf-|NEXT' | head
echo "== cron"
crontab -l 2>&1 | grep -v '^#' | sed 's/^/  user: /'
echo "== menciones de piloto-con-dns en el home (sin datos binarios)"
grep -rIl -e 'piloto-con-dns' "$HOME" --exclude-dir=.cache 2>/dev/null | head | sed 's/^/  /'
echo "== ficheros escritos en las últimas 24 h en el home (20 más recientes)"
find "$HOME" -type f -mmin -1440 -not -path '*/.cache/*' -printf '%TY-%Tm-%TdT%TH:%TM %s %p\n' 2>/dev/null | sort -r | head -20 | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
