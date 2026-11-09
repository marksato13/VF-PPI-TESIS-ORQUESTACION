VGD=$HOME/cf-e4/vigia-20261106
B=$HOME/cf-e4/4c-cancelada-20261109T1058Z
echo "## prueba final del vigía desplegado $(date -u +%FT%TZ)"
echo "== 1) hashes (esperado 2fe00200e755fd02 / 274b4d613357be60)"; sha256sum $VGD/vigia_4c.py $VGD/salud_captura.py | cut -c1-16
echo "== 2) el vigía importa la salud_captura de su directorio y pasa el EVE al clasificador"
grep -nE "^import salud_captura|^from salud_captura|import salud_captura as|importlib|sc = " $VGD/vigia_4c.py | head -5
grep -nE "suricata_eve=se|medida_suricata_eve\(sc.leer_eve_stats" $VGD/vigia_4c.py
python3 -I - <<PY
import sys; sys.path.insert(0, "$VGD")
import vigia_4c as v, salud_captura as s
print("   vigia", v.VERSION, "| salud_captura", s.VERSION, "|", s.__file__)
PY
echo "== 3) eve filtrado SIN eventos stats (para provocar medida faltante)"
grep -v '"event_type":"stats"' /var/log/suricata/eve.json > $HOME/.eve_sin_stats.json; ls -l $HOME/.eve_sin_stats.json | awk '{print "   bytes",$5}'
cat > $HOME/.pv.py <<'PY'
import datetime as dt, json, subprocess, sys
vig, B, eve, modo = sys.argv[1:5]
ep = lambda h: dt.datetime.fromisoformat(f"2026-11-09T{h}+00:00").timestamp()
EP = [("inundacion_http-r4", "09:37:50", "09:39:20"), ("fuerza_bruta_http-r4", "09:42:50", "09:44:20"), ("dns_inusual-r1", "09:47:50", "09:49:20"),
      ("fuerza_bruta_http-r3", "09:52:50", "09:54:20"), ("dns_inusual-r3", "09:57:50", "09:59:20"), ("inundacion_http-r3", "10:02:50", "10:04:20")]
if modo == "fuera": EP = [("sin_muestras-0800", "08:00:00", "08:01:30")]
pedidos = []
for n, a, b in EP: pedidos += ["--clasificar", f"{n}:{ep(a):.3f}:{ep(b):.3f}"]
c = ["python3", "-I", vig, "sensor", "--archivador", f"{B}/archivo-pcap", "--muestras", f"{B}/salud/muestras.jsonl", "--lista-blanca", "10.10.10.20,10.10.30.10",
     "--origen", "10.10.20.30", "--journalctl", "sudo -n journalctl --no-pager", "--eve-cursor", "-1", "--eve", eve] + pedidos
r = subprocess.run(c, capture_output=True, text=True)
try: j = json.loads(r.stdout)
except Exception: print("ERROR", (r.stderr or r.stdout)[:300]); sys.exit(1)
cl = j.get("clases", {})
for n, v in cl.items(): print(f"   {n:22} {v.get('clase')}  motivos={v.get('motivos') or v.get('motivo')} suricata={v.get('suricata')}")
json.dump(cl, open(sys.argv[5], "w"))
PY
echo "== 4) los seis intervalos de la corrida cancelada, EVE real"
python3 -I $HOME/.pv.py $VGD/vigia_4c.py $B /var/log/suricata/eve.json seis $HOME/.cl_real.json
echo "== 5) mismos seis intervalos, EVE SIN medida de Suricata (debe dar C3)"
python3 -I $HOME/.pv.py $VGD/vigia_4c.py $B $HOME/.eve_sin_stats.json seis $HOME/.cl_sinstats.json
echo "== 6) intervalo fuera de las muestras de salud (debe dar C3), EVE real"
python3 -I $HOME/.pv.py $VGD/vigia_4c.py $B /var/log/suricata/eve.json fuera $HOME/.cl_fuera.json
echo "== 7) X1 con el decidir() del vigía desplegado y las clases reales obtenidas"
python3 -I - <<PY
import sys, json, os; sys.path.insert(0, "$VGD")
import vigia_4c as vg
H = os.path.expanduser("~")
def corre(nombre, cl, orden):
    st = vg.estado_inicial(25); st["orden_fin"] = list(orden)
    o = {"sensor": {"ok": True, "unidades": {}, "tcpdump": {"ok": True, "lecturas": []}, "anillo": {"ok": True, "salto_max_s": 5.0}, "archivador": {"ok": True, "lineas_fallo": 0, "perdidos": 0}, "eve": {"ok": True, "fuera": []}}, "clases": cl}
    _, x = vg.condiciones(st, o, 1.0, dict(vg.CRIT))
    print(f"   {nombre}: X1 = {'SÍ -> ' + x[0][:70] if any(i.startswith('X1') for i in x) else 'no'}")
real = json.load(open(f"{H}/.cl_real.json")); sin = json.load(open(f"{H}/.cl_sinstats.json"))
corre("6 episodios con EVE real (C0)", real, real)
corre("6 episodios con EVE sin stats (C3)", sin, sin)
PY
rm -f $HOME/.eve_sin_stats.json $HOME/.pv.py $HOME/.cl_real.json $HOME/.cl_sinstats.json $HOME/.cl_fuera.json
echo "## fin (temporales propios borrados)"
