set -u
echo "##### srv-dmz $(date -u +%FT%TZ) $(id -un)"
echo "--- estado previo"; systemctl is-active ppi-brute-lab ppi-enforce-agent-v2-dmz | paste -sd' '
echo "--- arrancar ppi-brute-lab (sudo -n; NOPASSWD ALL de adminsrvdmz)"; sudo -n systemctl start ppi-brute-lab; echo "rc=$?"; sleep 2
echo "ppi-brute-lab: $(systemctl is-active ppi-brute-lab)/$(systemctl is-enabled ppi-brute-lab)"; ss -tln | grep -E ':(80|18081)\b' | head -3
echo "--- muestreador de sets (instrumentación)"
[ -e ~/cf-b/set-lecturas.jsonl ] && { mv ~/cf-b/set-lecturas.jsonl ~/cf-b/set-lecturas.anterior-$(date -u +%Y%m%dT%H%M%SZ).jsonl; echo "(apartado un set-lecturas.jsonl anterior)"; }
bash ~/cf-b/paquete-despliegue/cf_d5_instrumentacion.sh srvdmz iniciar --aplicar; echo "rc=$?"; sleep 6
echo "PID $(cat ~/cf-b/muestreador.pid) vivo=$(kill -0 $(cat ~/cf-b/muestreador.pid) 2>/dev/null && echo si || echo NO); líneas=$(wc -l < ~/cf-b/set-lecturas.jsonl)"; tail -2 ~/cf-b/set-lecturas.jsonl | cut -c1-200
