"""Pruebas del generador instrumentado (11-nov-2026). Comprueban que la ÚNICA diferencia con el generador firmado de la corrida es el comando de la inundación,
que sin `instrumentacion` o sin id de episodio el comando es EXACTAMENTE el original y que el plan de 25 episodios (orden, fechas relativas, comandos) no cambia."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
ORIG = AQUI.parent / "generador"
CFG_ORIG = AQUI.parent.parent / "etapa4-preparacion-2026-11-02" / "escenarios-4c.json"
CFG_I = AQUI / "escenarios-4c-i.json"


def cargar(nombre, carpeta):
    sys.path.insert(0, str(carpeta))
    try:
        for m in ("esquema_campana",):
            sys.modules.pop(m, None)
        spec = importlib.util.spec_from_file_location(nombre, carpeta / "esquema_campana.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(carpeta))


ESQ_O, ESQ_I = cargar("esq_o", ORIG), cargar("esq_i", AQUI)
CO, CI = json.loads(CFG_ORIG.read_text(encoding="utf-8")), json.loads(CFG_I.read_text(encoding="utf-8"))


class T(unittest.TestCase):
    def test_configs_validan(self):
        self.assertEqual(ESQ_O.validar(CO), [])
        self.assertEqual(ESQ_I.validar(CI), [])

    def test_config_solo_difiere_en_la_inundacion(self):
        a, b = copy.deepcopy(CO), copy.deepcopy(CI)
        b.pop("_nota_instrumentacion")
        for s in b["escenarios"]:
            if s["id"] == "inundacion_http":
                s["params"].pop("instrumentacion"); s["params"].pop("registro_dir")
        self.assertEqual(a, b)

    def test_comandos_identicos_salvo_inundacion_con_id(self):
        for s_o, s_i in zip(CO["escenarios"], CI["escenarios"]):
            for ep in (None, "%s-r1" % s_o["id"]):
                co, ci = ESQ_O.comando_de(CO, s_o), ESQ_I.comando_de(CI, s_i, ep)
                if s_o["id"] == "inundacion_http" and ep:
                    self.assertNotEqual(co, ci)
                else:
                    self.assertEqual(co, ci, (s_o["id"], ep))

    def test_inundacion_sin_ep_id_es_el_original(self):
        s = [x for x in CI["escenarios"] if x["id"] == "inundacion_http"][0]
        so = [x for x in CO["escenarios"] if x["id"] == "inundacion_http"][0]
        self.assertEqual(ESQ_I.comando_de(CI, s), ESQ_O.comando_de(CO, so))

    def test_inundacion_instrumentada_misma_duracion_url_lazos_y_maxtime(self):
        s = [x for x in CI["escenarios"] if x["id"] == "inundacion_http"][0]
        c = ESQ_I.comando_de(CI, s, "inundacion_http-r3")
        self.assertEqual(c, ["env", "CF_MAXTIME=2", "bash", "/home/adminatacante/cf-b/instrumentacion/inundacion_instrumentada.sh",
                             "/home/adminatacante/cf-e4-4c/intentos/intentos-inundacion_http-r3.tsv", "http://10.10.30.10/", "90", "8"])

    def test_validacion_rechaza_rutas_relativas(self):
        c = copy.deepcopy(CI)
        for s in c["escenarios"]:
            if s["id"] == "inundacion_http":
                s["params"]["registro_dir"] = "relativa"
        self.assertTrue(any("registro_dir" in e for e in ESQ_I.validar(c)))

    def test_plan_de_25_episodios_identico_salvo_la_inundacion(self):
        def plan(carpeta, cfg):
            with tempfile.TemporaryDirectory() as d:
                r = subprocess.run([sys.executable, "-B", str(carpeta / "generar_campana_b.py"), "--config", str(cfg), "--salida-dir", d],
                                   capture_output=True, text=True, cwd=d)
                self.assertEqual(r.returncode, 0, r.stderr[-400:])
                marcas = [json.loads(l) for l in (Path(d) / "marcas.jsonl").read_text(encoding="utf-8").splitlines()]
                return [(m["episodio_id"], m["comando"]) for m in marcas if m.get("evento") == "inicio"]
        po, pi = plan(ORIG, CFG_ORIG), plan(AQUI, CFG_I)
        self.assertEqual(len(po), 25)
        self.assertEqual([e for e, _ in po], [e for e, _ in pi])          # mismo orden (misma semilla)
        n_dif = 0
        for (e, co), (_, ci) in zip(po, pi):
            if e.startswith("inundacion_http"):
                n_dif += 1
                self.assertEqual(ci[:3], ["env", "CF_MAXTIME=2", "bash"])
                self.assertTrue(ci[4].endswith("/intentos-%s.tsv" % e))
            else:
                self.assertEqual(co, ci, e)
        self.assertEqual(n_dif, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
