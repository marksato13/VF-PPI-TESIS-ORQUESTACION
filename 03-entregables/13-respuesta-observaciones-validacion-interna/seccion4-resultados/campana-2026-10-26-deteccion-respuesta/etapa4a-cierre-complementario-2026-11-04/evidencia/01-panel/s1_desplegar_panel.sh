set -u
# [Sensor1 m4rk] Despliegue del panel 93f076e (rama panel/cadena-v2-20261104). Respaldo primero; nada se borra.
E=~/cyberflow/scripts/engine; N=~/cf-e4/panel-93f076e; PY=~/cyberflow/.venv/bin/python
SELLO=$(date -u +%Y%m%dT%H%M%SZ); B=~/respaldos-etapa4/panel-$SELLO
parar() { echo "PARADA: $*"; exit 1; }
cd $N && sha256sum -c SHA256SUMS >/dev/null || parar "paquete del panel no verifica"
[ "$(sha256sum < $E/dashboard.py | cut -d' ' -f1)" = 16e7f43019ae29c69210a8c311f0f01d532ccfa65b5858ef6db0a02a67dfb274 ] || parar "el panel instalado no es a27889d (16e7f430)"
[ "$(sha256sum < $E/cadena_v2.py | cut -d' ' -f1)" = 8dbaa3773b3fe815efc74f94bb580cf19957b50cdb52cbe348dfa1491d624869 ] || parar "cadena_v2.py instalado no es a27889d (8dbaa377)"
mkdir -p $B
cp -p $E/cadena_v2.py $B/cadena_v2.py; cp -p $E/dashboard.py $B/dashboard.py
systemctl cat ppi-dashboard > $B/ppi-dashboard.service.txt
systemctl show ppi-dashboard -p MainPID -p ActiveEnterTimestamp -p NRestarts -p ExecStart > $B/estado-previo.txt
printf 'panel previo: a27889d (dashboard 16e7f430…, cadena_v2 8dbaa377…)\npanel nuevo: 93f076e (panel/cadena-v2-20261104)\nrespaldo: %s\n' "$SELLO" > $B/LEEME.txt
(cd $B && sha256sum dashboard.py cadena_v2.py ppi-dashboard.service.txt estado-previo.txt LEEME.txt > SHA256SUMS && sha256sum -c SHA256SUMS >/dev/null) || parar "respaldo no verifica"
echo "respaldo OK: $B"
T=$(mktemp -d); cp $N/dashboard.py $N/cadena_v2.py $T/
$PY -m py_compile $T/dashboard.py $T/cadena_v2.py || parar "no compila"
(cd $T && $PY -I -c 'import sys; sys.path.insert(0,"."); import dashboard, cadena_v2; print("importa; HUECO", cadena_v2.HUECO_TRAZA_S, "FRESCA", cadena_v2.TRAZA_FRESCA_S)') || parar "no importa"
cp $N/cadena_v2.py $E/cadena_v2.py && cp $N/dashboard.py $E/dashboard.py
sha256sum $E/dashboard.py $E/cadena_v2.py
sudo -n systemctl restart ppi-dashboard; sleep 8
echo "ppi-dashboard: $(systemctl is-active ppi-dashboard) NRestarts=$(systemctl show ppi-dashboard -p NRestarts --value) PID=$(systemctl show ppi-dashboard -p MainPID --value)"
journalctl --no-pager -u ppi-dashboard --since "-25s" -o cat | grep -E 'panel:|Traceback|Error' | head
ss -ltn | grep -q '10.10.60.11:8788' && echo "escucha en 10.10.60.11:8788" || echo "NO escucha en 8788"
