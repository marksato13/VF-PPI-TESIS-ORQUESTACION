#!/usr/bin/env bash
# Banco de analisis_db3.py (PROPUESTA) con el motor y el inventario REALES del 3B y salud/EVE sintéticos (como banco_4b_completo.sh).
# Montajes: /e (enmienda), /herr (herramientas planas con analisis_db3.py y limites_db3.py), /d3b, /out.
set -u
OUT=${OUT:-/out}; mkdir -p "$OUT"; export HERR=/herr D3B=/d3b AQUI=/e/tests; fallo=0
ok() { if eval "$2"; then echo "OK    $1"; else echo "FALLO $1"; fallo=1; fi; }
for esc in limpio eventos; do
  export HOME=/tmp/h-$esc; mkdir -p "$HOME"; python3 /e/tests/generar_entorno_4b.py "$HOME" "$esc" p1 > /dev/null || exit 2
  B=$HOME/cf-e4/4b
  python3 /herr/analisis_db3.py --motor $B/copias/motor_decision.log --inventario $B/replay/motor_decision.log --config /herr/config-campana-4c.json \
    --desde 2026-11-01T07:32:00Z --hasta 2026-11-01T08:05:00Z --salud-captura /herr/salud_captura.py \
    --incrementos <(python3 /herr/salud_captura.py intervalos $B/salud/muestras.jsonl /dev/stdout) --tcpdump-anillo $B/salud/tcpdump-anillo.log \
    --suricata-eve $B/copias/eve-segmento.json --ahora 1795000000 --min-c0-horas 0.2 --salida "$OUT/db3-$esc.json" > "$OUT/db3-$esc.stdout" 2> "$OUT/db3-$esc.err"
  echo "rc=$? $esc: $(cat $OUT/db3-$esc.stdout)"
done
python3 - <<'PY'
import json, sys
sys.path.insert(0, "/herr")
import limites_db3 as db
L = json.load(open("/out/db3-limpio.json")); E = json.load(open("/out/db3-eventos.json"))
fallos = 0
def ok(c, m):
    global fallos
    print(("OK    " if c else "FALLO ") + m); fallos += 0 if c else 1
ok(L["poblacion_seleccion"] == [f"10.10.20.{n}" for n in range(21, 27)], "población de selección = los seis perfiles")
for al in ("0.05", "0.03", "0.01"):
    sel = L["alfas"][al]["seleccion"]
    ok(all(e["ventanas_faltantes"] == 0 for e in sel.values()), f"limpio α {al}: ninguna ventana faltante en las entidades de selección")
    ok(all(e["L1_avisos_por_hora"]["minimo"] == e["L1_avisos_por_hora"]["observado"] == e["L1_avisos_por_hora"]["maximo"] for e in sel.values()),
       f"limpio α {al}: sin faltantes las cotas de L1 coinciden con lo observado")
    ok(all(e["L2_fraccion_en_alerta"]["minimo"] == e["L2_fraccion_en_alerta"]["observado"] == e["L2_fraccion_en_alerta"]["maximo"] for e in sel.values()),
       f"limpio α {al}: sin faltantes las cotas de L2 coinciden con lo observado")
    ok(all(e["horas_c0"] < 2 for e in sel.values()), f"limpio α {al}: con 33 min de control ninguna entidad llega a 2 h C0")
# con eventos hay faltantes, y las cotas se abren
ab = E["alfas"]["0.05"]["seleccion"]
ok(any(e["ventanas_faltantes"] > 0 for e in ab.values()), "eventos: hay ventanas faltantes en las entidades de selección (C1/C3 y ausentes)")
ok(all(e["L2_fraccion_en_alerta"]["minimo"] <= e["L2_fraccion_en_alerta"]["observado"] <= e["L2_fraccion_en_alerta"]["maximo"] for e in ab.values() if e["ventanas_c0_decididas"]),
   "eventos: mínimo ≤ observado ≤ máximo en L2")
ok(all(e["L1_avisos_por_hora"]["minimo"] <= e["L1_avisos_por_hora"]["observado"] <= e["L1_avisos_por_hora"]["maximo"] for e in ab.values()),
   "eventos: mínimo ≤ observado ≤ máximo en L1")
# regla: el verdicto de un α concluyente exige que todas las entidades cumplan
vf = E["alfas"]["0.05"]["veredicto_alfa"]
ok(vf["elegible"] == all(d == "cumple" for d in vf["entidades"].values()), "la elegibilidad de un α = todas las entidades de selección «cumple»")
# las no seleccionadas se reportan aparte
ok(all(ip not in E["alfas"]["0.05"]["reportadas_aparte"] for ip in L["poblacion_seleccion"]), "los perfiles no se repiten en «reportadas aparte»")
print("RESULTADO:", "todas las comprobaciones OK" if not fallos else f"HAY {fallos} FALLOS")
sys.exit(1 if fallos else 0)
PY
exit $?
