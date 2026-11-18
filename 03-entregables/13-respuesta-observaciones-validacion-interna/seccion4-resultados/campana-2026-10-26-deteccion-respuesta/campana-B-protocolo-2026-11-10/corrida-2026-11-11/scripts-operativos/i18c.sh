echo "$(date -u +%FT%TZ)"
V=~/cf-e4/4c/vigilancia.log
echo "vigilancia líneas: $(wc -l < $V)"; grep -c -E 'motor=active.*enforce=0.*cap=active/NR=0 via=active sur=active' $V; grep -v -E 'motor=active NR=0 enforce=0' $V | head -3
python3 - <<'PY'
import re,os
m=0;n=0
for l in open(os.path.expanduser("~/cf-e4/4c/vigilancia.log")):
    if "04:45" > l[11:16] and l[:10]=="2026-11-11" and False: pass
    g=re.search(r"dur=\[([^\]]*)\]",l)
    if g and "2026-11-11T04:4" <= l[:16] or (g and l[:13]>="2026-11-11T05" and l[:16]<="2026-11-11T05:15"):
        v=[float(x) for x in g.group(1).split(",") if x.strip()]; n+=1; m=max(m,max(v))
print("líneas en ventana",n,"ciclo máx %.2f s"%m)
PY
echo "--- canal simulado"; tail -2 ~/cf-e4/4c/canal-simulado.out; ps -eo args | grep -c '[k]20_canal'
echo "--- relojes p10b"; bash ~/cf-e4/p10b_relojes.sh 2>&1 | tail -8
echo "--- verificar_bastion"; bash ~/cf-e4/paquete-a1cea5e/deploy/etapa4/bastion/verificar_bastion.sh 2>&1 | tail -4
echo "--- verificar_srvdmz CON_SUDO"; ssh -n -o BatchMode=yes srvdmz 'ls -d /var/lib/cyberflow/reversion-B/* | tail -3; ls ~/respaldos-etapa4 2>/dev/null | tail -3' 2>&1
