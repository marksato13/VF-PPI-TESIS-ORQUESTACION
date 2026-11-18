"""Simulación (SIN --autorizado: no lanza ningún comando) del plan 7–25. Comprueba que el tramo contiene EXACTAMENTE los 19 episodios pendientes de B3, con sus IDs, orden y
parámetros originales (comando, destino, servicio, timeout), que ninguno de los 6 de B3 reaparece, que el esquema y la config son idénticos a los desplegados y que, sin la opción,
el generador produce el plan completo de 25 como antes. El plan de referencia es el de las marcas REALES de B3 (campana_inicio.orden)."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
B3 = AQUI.parent / "corrida-2026-11-11" / "analisis" / "bastion" / "corrida" / "marcas.jsonl"
if not B3.exists():
    B3 = Path(r"C:\Users\markp\cf-b3\bastion\corrida\marcas.jsonl")
CFG = AQUI / "escenarios-4c-i.json"
GEN_ACTUAL = AQUI.parent / "generador-instrumentado" / "generar_campana_b.py"
HASH_DESPLEGADOS = {"esquema_campana.py": "c51efd6e495232ce", "escenarios-4c-i.json": "b891674ae849d519"}       # los de la Kali (sha256-esperado-i.txt)
NONCE_B3 = "4c-20261111T051928Z-2eb2f728a738"
SEIS_B3 = ["inundacion_http-r4", "fuerza_bruta_http-r4", "dns_inusual-r1", "fuerza_bruta_http-r3", "dns_inusual-r3", "inundacion_http-r3"]


def correr(gen, *extra):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, "-B", str(gen), "--config", str(CFG), "--salida-dir", d, *extra], capture_output=True, text=True, cwd=d)
        marcas = [json.loads(l) for l in (Path(d) / "marcas.jsonl").read_text(encoding="utf-8").splitlines()] if (Path(d) / "marcas.jsonl").exists() else []
        return r, marcas


def plan(marcas):
    ini = [m for m in marcas if m.get("evento") == "campana_inicio"][0]
    ep = {m["episodio_id"]: m for m in marcas if m.get("evento") == "inicio"}
    return ini, ep


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b3 = [json.loads(l) for l in B3.read_text(encoding="utf-8").splitlines()]
        cls.orden_b3 = [m for m in b3 if m["evento"] == "campana_inicio"][0]["orden"]
        cls.inicios_b3 = [m["episodio_id"] for m in b3 if m["evento"] == "inicio"]
        r, m = correr(GEN_ACTUAL)
        assert r.returncode == 0, r.stderr[-300:]
        cls.ini_full, cls.ep_full = plan(m)
        r, m = correr(AQUI / "generar_campana_b.py", "--desde-episodio", "fuerza_bruta_http-r1", "--nonce", "4c-B4-20261111T120000Z-abcdef012345")
        assert r.returncode == 0, r.stderr[-300:]
        cls.ini_t, cls.ep_t = plan(m)
        cls.marcas_t = m

    def test_el_plan_completo_actual_es_el_de_las_marcas_reales_de_b3(self):
        self.assertEqual(len(self.orden_b3), 25)
        self.assertEqual(self.ini_full["orden"], self.orden_b3)                       # misma semilla -> mismo orden
        self.assertEqual(self.inicios_b3, SEIS_B3)
        self.assertEqual(self.orden_b3[:6], SEIS_B3)

    def test_el_tramo_contiene_exactamente_los_19_pendientes_en_orden(self):
        self.assertEqual(self.ini_t["orden"], self.orden_b3[6:])
        self.assertEqual(len(self.ini_t["orden"]), 19)
        self.assertEqual(self.ini_t["orden"][0], "fuerza_bruta_http-r1")               # el episodio 7
        self.assertEqual(len(set(self.ini_t["orden"])), 19)                            # sin duplicados
        self.assertFalse(set(self.ini_t["orden"]) & set(SEIS_B3))                      # ninguno de B3 reaparece
        self.assertEqual(set(self.ini_t["orden"]) | set(SEIS_B3), set(self.orden_b3))   # entre ambos, los 25 sin faltar ni sobrar

    def test_parametros_y_comandos_de_cada_episodio_son_los_originales(self):
        self.assertEqual(sorted(self.ep_t), sorted(self.ini_t["orden"]))
        for e, m in self.ep_t.items():
            o = self.ep_full[e]
            for k in ("comando", "destino", "servicio", "timeout_s", "escenario", "repeticion", "campana"):
                self.assertEqual(m.get(k), o.get(k), (e, k))

    def test_la_marca_de_inicio_registra_el_tramo_y_los_omitidos(self):
        t = self.ini_t["tramo"]
        self.assertEqual(t["omitidos"], SEIS_B3)
        self.assertEqual(t["orden_completo"], self.orden_b3)
        self.assertEqual(t["desde_episodio"], "fuerza_bruta_http-r1")
        self.assertNotIn("tramo", self.ini_full)

    def test_id_de_corrida_nuevo(self):
        self.assertNotEqual(self.ini_t["nonce"], NONCE_B3)
        self.assertTrue(self.ini_t["nonce"].startswith("4c-B4-"))

    def test_sin_la_opcion_el_generador_nuevo_da_el_plan_completo_identico_al_actual(self):
        r, m = correr(AQUI / "generar_campana_b.py")
        ini, ep = plan(m)
        self.assertEqual(ini["orden"], self.ini_full["orden"])
        self.assertEqual({e: x["comando"] for e, x in ep.items()}, {e: x["comando"] for e, x in self.ep_full.items()})

    def test_episodio_inexistente_aborta_sin_lanzar_nada(self):
        r, m = correr(AQUI / "generar_campana_b.py", "--desde-episodio", "no-existe-r9")
        self.assertEqual(r.returncode, 2)
        self.assertFalse([x for x in m if x.get("evento") == "inicio"])

    def test_el_episodio_7_es_el_primero_no_el_6_ni_el_8(self):
        self.assertEqual(self.orden_b3[5], "inundacion_http-r3")                        # el 6.º de B3
        self.assertEqual(self.orden_b3[6], "fuerza_bruta_http-r1")                     # el 7.º
        self.assertEqual(self.orden_b3[24], self.ini_t["orden"][-1])                   # el 25.º es el último del tramo

    def test_esquema_y_config_identicos_a_los_desplegados(self):
        for n, h in HASH_DESPLEGADOS.items():
            self.assertEqual(hashlib.sha256((AQUI / n).read_bytes()).hexdigest()[:16], h, n)

    def test_el_unico_cambio_del_generador_es_la_opcion_desde_episodio(self):
        a = GEN_ACTUAL.read_text(encoding="utf-8").splitlines()
        b = (AQUI / "generar_campana_b.py").read_text(encoding="utf-8").splitlines()
        import difflib
        quitadas = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] == "-" and l[:3] != "---"]
        añadidas = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] == "+" and l[:3] != "+++"]
        self.assertEqual(len(quitadas), 2)                                              # solo las 2 líneas de `jsonl(marcas, …campana_inicio…)` que se reescriben
        self.assertTrue(all("desde" in l or "tramo" in l or "completo" in l or "omitidos" in l or "ini" in l or "jsonl" in l or "return 2" in l or "print" in l or "plan" in l or "}" in l or l.strip() in ("+", "") or "help" in l or "if " in l for l in añadidas), añadidas)


if __name__ == "__main__":
    unittest.main(verbosity=2)
