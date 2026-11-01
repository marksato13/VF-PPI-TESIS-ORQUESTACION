#!/usr/bin/env bash
# PASO3A s07 — desde el bastion. Kali: plan efectivo SIN trafico (generar_campana.py sin --autorizado) en un directorio
# separado. Clientes: mecanismo del envoltorio de factor 1,0 comprobado SIN arrancarlo (hash + import con main guard).
set -u
echo "## s07 $(date -u +%FT%T.%3NZ)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 '
set -u; D=$HOME/cf-paso3a-plan-sin-trafico-20261101T0523Z; mkdir -p $D
echo "  kali antes: carga=$(ps -eo comm= | grep -cE "^(curl|nmap|dig|hping3)$")"
sha256sum ~/cf-campana-A/scripts/generar_campana.py ~/cf-campana-A/scripts/esquema_campana.py ~/cf-campana-A/escenarios/escenarios.json | sed "s/^/  /"
cd ~/cf-campana-A/scripts && python3 generar_campana.py --config ~/cf-campana-A/escenarios/escenarios.json --salida-dir $D/corrida > $D/simulacion.stdout 2> $D/simulacion.stderr; echo "  rc=$?"
tail -15 $D/simulacion.stdout | sed "s/^/  | /"; tail -3 $D/simulacion.stderr | sed "s/^/  ! /"
echo "  ficheros:"; find $D -type f | sed "s/^/   /"
echo "  kali despues: carga=$(ps -eo comm= | grep -cE "^(curl|nmap|dig|hping3)$")"
python3 - $D/corrida <<PY
import json, sys, glob, collections
from pathlib import Path
d = Path(sys.argv[1])
for f in sorted(d.rglob("*.json*")):
    print("   ", f.name, f.stat().st_size)
m = [json.loads(l) for f in d.rglob("marcas*.jsonl") for l in open(f) if l.strip()]
c = collections.Counter((x.get("evento"), x.get("estado")) for x in m)
print("   marcas:", dict(c))
ini = [x for x in m if x.get("evento") == "inicio"]
print("   episodios:", len(ini), dict(collections.Counter(x.get("escenario") for x in ini)))
PY
'
echo "## clientes: mecanismo factor 1,0 (sin arrancar)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 '
sha256sum ~/cf-paso2-20261101T0254Z/clientes_factor1.py ~/laboratorio/clientes_lab.py | sed "s/^/  /"
grep -n "def factor_horario\|factor_horario(\|__name__" ~/laboratorio/clientes_lab.py | sed "s/^/  /"
python3 -c "
import sys, datetime; sys.path.insert(0, \"/home/adminclientes/laboratorio\")
import clientes_lab as c
o = c.factor_horario(datetime.datetime.now())
c.factor_horario = lambda ahora, forzar_laborable=False: 1.0
print(\"  import sin efectos (main no se ejecuta); original ahora=%.3f; parcheado=%.1f\" % (o, c.factor_horario(datetime.datetime.now())))
"
echo "  envoltorios vivos: $(ps -eo args= | grep -c "[c]lientes_factor1.py")  target=$(systemctl is-active cyberflow-lab.target)"'
echo "## fin"
