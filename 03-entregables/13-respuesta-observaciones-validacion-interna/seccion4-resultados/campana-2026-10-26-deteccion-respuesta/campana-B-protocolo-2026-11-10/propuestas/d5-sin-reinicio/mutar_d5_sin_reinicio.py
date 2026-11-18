#!/usr/bin/env python3
"""Mutaciones de la propuesta D5 sin reinicio (hacer_publicador_d5.py y d5_control.py): cada una debe hacer fallar alguna prueba del banco."""
import pathlib
import shutil
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent
MUT = [
    ("hacer_publicador_d5.py", "    except OSError as ex:\n        print(\"d5: no se pudo escribir", "    except ZeroDivisionError as ex:\n        print(\"d5: no se pudo escribir"),
    ("hacer_publicador_d5.py", "elif resp[\"id\"] in _D5_IDS:", "elif False:"),
    ("hacer_publicador_d5.py", "            _D5_IDS.add(resp[\"id\"])\n", "            pass\n"),
    ("hacer_publicador_d5.py", "elif not origen_permitido or ctl.get(\"origen\") != origen_permitido:", "elif not origen_permitido:"),
    ("hacer_publicador_d5.py", "                del estado[\"escalada\"][k]\n", "                pass\n"),
    ("hacer_publicador_d5.py", "                del estado[\"vigentes\"][k]\n", "                pass\n"),
    ("hacer_publicador_d5.py", "if k.split(\"|\", 1)[0] == o]", "if k.startswith(o[:-1])]"),
    ("hacer_publicador_d5.py", "d5_resp[\"secuencia\"] = obj[\"secuencia\"]", "d5_resp[\"secuencia\"] = 0"),
    ("hacer_publicador_d5.py", "toca = (not a.seguir or nuevos or d5_forzar or ultima_pub is None", "toca = (not a.seguir or nuevos or ultima_pub is None"),
    ("hacer_publicador_d5.py", "if not d5_resp[\"ok\"]:", "if False:"),
    ("d5_control.py", "        os.unlink(control)                                             # nadie", "        pass                                             # nadie"),
    ("d5_control.py", "    if os.path.exists(control):\n        return {\"ok\": False, \"estado\": \"pendiente_previa\"", "    if False:\n        return {\"ok\": False, \"estado\": \"pendiente_previa\""),
    ("d5_control.py", "return a if isinstance(a, dict) and a.get(\"id\") == id_ else None", "return a if isinstance(a, dict) else None"),
    ("d5_control.py", "    os.replace(tmp, control)\n", "    os.replace(tmp, control)\n    return {\"ok\": True, \"estado\": \"acuse\", \"rc\": 0, \"quitado\": {}, \"secuencia\": 1, \"duplicada\": False}\n"),
    # v3: auditoría del publicador y adaptador (reconciliación, sin id nuevo)
    ("hacer_publicador_d5.py", "    except OSError as ex:\n        print(\"d5: no se pudo escribir el acuse", "    except ZeroDivisionError as ex:\n        print(\"d5: no se pudo escribir el acuse"),
    ("hacer_publicador_d5.py", "{\"evento\": \"publicado\", \"id\"","{\"evento\": \"xpublicado\", \"id\""),
    ("hacer_publicador_d5.py", "{\"evento\": \"consumido\", \"t\"", "{\"evento\": \"xconsumido\", \"t\""),
    ("hacer_publicador_d5.py", "{\"evento\": \"ack_fallido\"", "{\"evento\": \"xack\""),
    ("adaptador_banco.py", "    elif retiro_del_cliente:", "    elif False:"),
    ("adaptador_banco.py", "    elif cons and pub:", "    elif False:"),
    ("adaptador_banco.py", "    elif cons and not cons[-1].get(\"ok\"):", "    elif False:"),
    ("adaptador_banco.py", "\"determinada\": d[\"determinada\"],", "\"determinada\": True,"),
    ("adaptador_banco.py", "\"incierto\": not d[\"determinada\"]", "\"incierto\": False"),
    ("adaptador_banco.py", "    while os.path.exists(ruta):", "    while False:"),
    ("adaptador_banco.py", "if x.get(\"id\") == id_] if auditoria", "if True] if auditoria"),
    ("adaptador_banco.py", "    if r[\"estado\"] == \"pendiente_previa\":", "    if False:"),
    ("adaptador_banco.py", "        ev = _guardar_evidencia(", "        cli.solicitar_reset(self.control, origen, 0.1, ahora=self.ahora, dormir=self.dormir, sondeo=self.sondeo)   # reintento\n        ev = _guardar_evidencia("),
]


def main():
    vivos = []
    for i, (f, a, b) in enumerate(MUT):
        src = (AQUI / f).read_text(encoding="utf-8")
        if src.count(a) < 1:
            print(f"M{i:02d} NO APLICA ({f}): {a[:60]!r}")
            vivos.append(i)
            continue
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for g in AQUI.glob("*.py"):
                shutil.copy(g, t / g.name)
            (t / f).write_text(src.replace(a, b, 1), encoding="utf-8")
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t)],
                                capture_output=True, cwd=t, env={**__import__("os").environ, "CF_PRODUCTO": __import__("os").environ.get("CF_PRODUCTO", "/producto-etapa3")}).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {f}: {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())
