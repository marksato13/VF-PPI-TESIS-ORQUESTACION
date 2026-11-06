set -u
# [CLIENTES adminclientes] SOLO LECTURAS: qué generadores legítimos existen y si están en marcha (no arranca nada).
date -u +%FT%TZ
systemctl list-units --all --no-pager --plain 2>/dev/null | grep -iE 'perfil|legit|generador|trafico|cf-|ppi' | head -30
echo "== timers"; systemctl list-timers --all --no-pager 2>/dev/null | grep -iE 'perfil|legit|generador|trafico|cf-|ppi' | head -20
echo "== procesos"; ps -eo pid=,lstart=,args= | grep -iE 'perfil|legit|generador|trafico' | grep -v grep | cut -c1-220 | head -20
echo "== home"; ls -la ~ | head -40
ls ~/*/ 2>/dev/null | head -60
