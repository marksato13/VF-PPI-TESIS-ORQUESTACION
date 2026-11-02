#!/usr/bin/env bash
# [KALI adminatacante] ETAPA4 c03 — solo lectura + directorio nuevo ~/cf-e4-4c: hashes del generador, del esquema,
# de escenarios.json (3B) y de escenarios-4c.json (semilla 20261102), y ausencia de otra campaña en marcha.
# escenarios-4c.json debe haberse copiado antes a ~/cf-campana-A/escenarios/ (PROTOCOLO-4C §4.1).
# Resultado esperado: cuatro "OK" de sha256sum -c, 0 procesos de carga y 0 generadores. Parada: cualquier FAILED.
set -u
B=$HOME/cf-e4-4c
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$B"
echo "## c03-e4 $(hostname) $(date -u +%FT%T.%3NZ) -> $B"
cat > "$B/sha256-esperado.txt" <<EOF
c586d813472d5853ae43fe512b5a53d22654699ace10894e43f57b3ddc4b171b  $HOME/cf-campana-A/scripts/generar_campana.py
e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144  $HOME/cf-campana-A/scripts/esquema_campana.py
67798012cbd306e9c06ebccf5ec293c7d9db12951d93119f739c3f86a83c64ec  $HOME/cf-campana-A/escenarios/escenarios.json
73c0b204d1e6f8844f23d6ec3c8c30732b5084f2fea3df96d26a2c2a7927aacd  $HOME/cf-campana-A/escenarios/escenarios-4c.json
EOF
sha256sum -c "$B/sha256-esperado.txt" | sed 's/^/  /'
echo "  procesos de carga: $(ps -eo comm= | grep -cE '^(curl|nmap|dig|hping3|hydra)$')  generadores: $(pgrep -fc 'generar_campana|kali_episodio_tecnico')"
echo "  herramientas: $(command -v nmap curl dig openssl python3 setsid | tr '\n' ' ')"
echo "  nmap: $(nmap --version 2>/dev/null | head -1)"
echo "  ip: $(ip -4 -o addr | awk '{print $2, $4}' | tr '\n' ' ')"
df -h "$HOME" | tail -1 | sed 's/^/  disco /'
timedatectl show -p NTPSynchronized | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
