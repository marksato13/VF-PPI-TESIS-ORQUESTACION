"""[CONTENEDOR sin red] Diagnóstico del margen de T_g. Ejecuta el arrancar_c1.sh real de 27bcd46 sin muestreador ni ssh y
anota qué motivo de denegación da. Solo importa si es «T_g ya pasó al llegar a C1». No hay generadores ni hosts: la puerta
deniega siempre, antes de emitir ninguna orden."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time

S = "/r/deploy/etapa4/ecarga/arrancar_c1.sh"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40


def tirada(fraccion, margen):
    while abs((time.time() % 1) - fraccion) > 0.004:
        pass
    t_g = int(time.time()) + margen
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "bastion").mkdir(); (d / "manual").mkdir()
    r = subprocess.run(["bash", S, str(d), str(t_g)], capture_output=True, text=True, timeout=30)
    f = d / "manual" / "RESULTADO-C1"
    m = json.loads(f.read_text())["motivo"] if f.exists() else "(sin RESULTADO-C1)"
    shutil.rmtree(d)
    return r.returncode, m


for etiqueta, fr, mg in (("t_g=int(now)+1, fracción .985 (lo que hace la prueba, peor caso)", .985, 1),
                         ("t_g=int(now)+1, fracción .900", .900, 1),
                         ("t_g=int(now)+1, fracción .050 (control)", .050, 1),
                         ("t_g=int(now)+3, fracción .985 (con la corrección)", .985, 3)):
    if mg == 3:
        n = 12
    else:
        n = N
    pasado = 0
    otros = {}
    for _ in range(n):
        rc, m = tirada(fr, mg)
        if "T_g ya pasó" in m:
            pasado += 1
        else:
            otros[m[:60]] = otros.get(m[:60], 0) + 1
    print(f"{etiqueta}: {pasado}/{n} «T_g ya pasó»; otros motivos: {otros}", flush=True)
