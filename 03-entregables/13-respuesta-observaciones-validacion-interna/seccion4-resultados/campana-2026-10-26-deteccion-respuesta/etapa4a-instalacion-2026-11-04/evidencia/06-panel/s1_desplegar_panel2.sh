set -u
# [Sensor1 m4rk] Despliegue del panel e0dc71d (rama panel/cadena-v2-20261104). Respaldo primero; nada se borra.
E=~/cyberflow/scripts/engine; N=~/cf-e4/panel-a27889d; PY=~/cyberflow/.venv/bin/python
SELLO=$(date -u +%Y%m%dT%H%M%SZ); B=~/respaldos-etapa4/panel-$SELLO
parar() { echo "PARADA: $*"; exit 1; }
cd $N && sha256sum -c SHA256SUMS >/dev/null || parar "paquete del panel no verifica"
[ "$(sha256sum < $E/dashboard.py | cut -d' ' -f1)" = 457af3738029dffad9673a67d60e967bdc5ffe47b2082a0fb5eb294ae79d227b ] || parar "el panel instalado no es e0dc71d (457af373)"
mkdir -p $B
cp -p $E/cadena_v2.py $B/cadena_v2.py || parar "falta cadena_v2.py instalado"
cp -p $E/dashboard.py $B/dashboard.py
systemctl cat ppi-dashboard > $B/ppi-dashboard.service.txt
systemctl show ppi-dashboard -p MainPID -p ActiveEnterTimestamp -p NRestarts > $B/estado-previo.txt
printf 'panel previo: e0dc71d sha 457af373… (antes de él: ca66db5 a5186d2e…, en panel-20261104T033157Z)\npanel nuevo: a27889d (panel/cadena-v2-20261104)\nrespaldo: %s\n' "$SELLO" > $B/LEEME.txt
(cd $B && sha256sum dashboard.py cadena_v2.py ppi-dashboard.service.txt estado-previo.txt LEEME.txt > SHA256SUMS && sha256sum -c SHA256SUMS >/dev/null) || parar "respaldo no verifica"
echo "respaldo OK: $B"
# compilación en copia aparte antes de tocar nada
T=$(mktemp -d); cp $N/dashboard.py $N/cadena_v2.py $T/
$PY -m py_compile $T/dashboard.py $T/cadena_v2.py || parar "no compila"
(cd $T && $PY -I -c 'import sys; sys.path.insert(0,"."); import dashboard; print("importa; _CADENA_V2 al importar:", dashboard._CADENA_V2)') || parar "no importa"
# instalar
cp $N/cadena_v2.py $E/cadena_v2.py && cp $N/dashboard.py $E/dashboard.py
sha256sum $E/dashboard.py $E/cadena_v2.py
sudo -n systemctl restart ppi-dashboard; sleep 6
echo "ppi-dashboard: $(systemctl is-active ppi-dashboard) NRestarts=$(systemctl show ppi-dashboard -p NRestarts --value) PID=$(systemctl show ppi-dashboard -p MainPID --value)"
journalctl --no-pager -u ppi-dashboard --since "-20s" -o cat | grep -E 'panel:|Traceback|Error' | head
ss -ltn | grep -q '10.10.60.11:8788' && echo "escucha en 10.10.60.11:8788" || echo "NO escucha en 8788"
