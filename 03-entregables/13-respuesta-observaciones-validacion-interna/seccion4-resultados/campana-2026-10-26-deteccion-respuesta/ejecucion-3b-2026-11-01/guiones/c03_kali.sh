#!/usr/bin/env bash
# PASO3B c03 — Kali (solo lectura + directorio nuevo): hashes del generador y escenarios, ausencia de otra campaña.
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$B"
echo "## c03 $(hostname) $(date -u +%FT%T.%3NZ) -> $B"
sha256sum ~/cf-campana-A/scripts/generar_campana.py ~/cf-campana-A/scripts/esquema_campana.py ~/cf-campana-A/escenarios/escenarios.json | tee "$B/sha256-generador.txt" | sed 's/^/  /'
cat > "$B/sha256-esperado.txt" <<EOF
c586d813472d5853ae43fe512b5a53d22654699ace10894e43f57b3ddc4b171b  $HOME/cf-campana-A/scripts/generar_campana.py
e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144  $HOME/cf-campana-A/scripts/esquema_campana.py
67798012cbd306e9c06ebccf5ec293c7d9db12951d93119f739c3f86a83c64ec  $HOME/cf-campana-A/escenarios/escenarios.json
EOF
sha256sum -c "$B/sha256-esperado.txt" | sed 's/^/  /'
echo "  procesos de carga: $(ps -eo comm= | grep -cE '^(curl|nmap|dig|hping3)$')  generadores: $(pgrep -fc 'generar_campana|kali_episodio_tecnico')"
echo "  directorios previos: $(ls -d $HOME/cf-* | grep -v "$B" | tr '\n' ' ')"
echo "  herramientas: $(command -v nmap curl dig openssl python3 tmux screen setsid | tr '\n' ' ')"
echo "  ip: $(ip -4 -o addr | awk '{print $2, $4}' | tr '\n' ' ')"
df -h $HOME | tail -1 | sed 's/^/  disco /'
echo "## fin $(date -u +%FT%T.%3NZ)"
