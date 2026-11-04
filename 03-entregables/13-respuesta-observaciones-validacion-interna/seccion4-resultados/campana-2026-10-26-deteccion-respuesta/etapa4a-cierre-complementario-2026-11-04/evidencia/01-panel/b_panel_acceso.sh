set -u
# [BASTIÓN gadmin] Acceso al panel 93f076e: sin sesión, y POST «Preparar demo» (sin credenciales)
U=https://10.10.60.11:8788
echo "GET /api/status sin sesión: $(curl -sk -o /dev/null -w '%{http_code}' $U/api/status)"
echo "POST /api/demo/preparar: $(curl -sk -o /tmp/prep.out -w '%{http_code}' -X POST -H 'X-CyberFlow: 1' $U/api/demo/preparar) $(cat /tmp/prep.out)"
echo "GET / (login): $(curl -sk -o /dev/null -w '%{http_code}' $U/)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'ls -l --time-style=full-iso ~/feed/peticiones/'
