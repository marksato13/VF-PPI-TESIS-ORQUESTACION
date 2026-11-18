set -u
echo "##### clientes $(hostname) $(date -u +%FT%TZ)"
echo "--- unidades"; for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "cyberflow-lab-$s $(systemctl is-active cyberflow-lab-$s) NR=$(systemctl show -p NRestarts --value cyberflow-lab-$s) PID=$(systemctl show -p MainPID --value cyberflow-lab-$s)"; done; echo "target $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
echo "--- procesos por perfil (debe ser exactamente 1 cada uno)"; for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "$s: clientes_lab=$(pgrep -fc "clientes_lab.py --perfil $s ") envoltorio=$(pgrep -fc "clientes_factor1.*--perfil $s ")"; done
echo "total clientes_lab.py: $(pgrep -fc 'clientes_lab.py')  envoltorios factor1: $(pgrep -fc 'clientes_factor1')"
echo "--- 4c en clientes"; ls ~/cf-e4/4c; ls ~/cf-e4/4c/pids ~/cf-e4/4c/perfiles 2>&1 | head -3
echo "--- hashes"; sha256sum ~/laboratorio/clientes_lab.py | cut -c1-8; sha256sum ~/cf-e4/4c/clientes_factor1.py ~/cf-3b-20261101T0721Z/clientes_factor1.py ~/cf-b/instrumentacion/clientes_factor1_tx.py | cut -c1-16,65-
echo "--- sudo -n systemctl cyberflow-lab.target permitido"; sudo -n -l 2>&1 | grep -E 'cyberflow-lab|NOPASSWD' | head -3
echo "--- conexiones salientes 10.10.20.2x"; ss -tn 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '10\.10\.20\.2[0-9]' | sort | uniq -c
echo "--- diff wrapper original vs tx (solo registra)"; diff <(grep -v '^#' ~/cf-3b-20261101T0721Z/clientes_factor1.py) <(grep -v '^#' ~/cf-b/instrumentacion/clientes_factor1_tx.py) | head -12 | cut -c1-140; echo "(fin diff)"; wc -l ~/cf-3b-20261101T0721Z/clientes_factor1.py
