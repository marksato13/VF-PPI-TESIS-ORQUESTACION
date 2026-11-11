import importlib.util, pathlib, re, sys, unittest

AQUI = pathlib.Path(__file__).parent
SRC = (AQUI / "e1_por_destino.py").read_text(encoding="utf-8")


def cargar(src):
    ns = {}
    exec(compile(src, "e1", "exec"), ns)
    return ns["e1_por_destino"]


F = cargar(SRC)


class T(unittest.TestCase):
    def test_verificado(self):
        r = F([105.0, 110.0], 100, 200, 90, 150, "verificado")
        self.assertEqual((r["resultado"], r["paquetes_en_ventana_y_episodio"], r["paquetes_previos_al_inicio_en_ventana"]), ("verificado", 2, 0))

    def test_sin_paquetes_dentro_indeterminado(self):
        self.assertEqual(F([50.0, 160.0], 100, 200, 90, 150, "verificado")["resultado"], "indeterminado")

    def test_solo_paquetes_previos(self):
        r = F([95.0], 100, 200, 90, 150, "verificado")
        self.assertEqual((r["resultado"], r["paquetes_previos_al_inicio_en_ventana"]), ("indeterminado", 1))

    def test_senal_fallida_prevalece(self):
        self.assertEqual(F([120.0], 100, 200, 90, 150, "fallido")["resultado"], "fallido")

    def test_senal_indeterminada(self):
        self.assertEqual(F([120.0], 100, 200, 90, 150, "indeterminado")["resultado"], "indeterminado")

    def test_limites_inclusivos(self):
        self.assertEqual(F([100.0], 100, 200, 100, 100, "verificado")["paquetes_en_ventana_y_episodio"], 1)
        self.assertEqual(F([150.0], 100, 200, 90, 150, "verificado")["paquetes_en_ventana_y_episodio"], 1)

    def test_ventana_fuera_del_episodio(self):
        self.assertEqual(F([120.0], 100, 200, 300, 400, "verificado")["resultado"], "indeterminado")

    def test_ventana_no_corta_fin(self):
        self.assertEqual(F([250.0], 100, 200, 90, 300, "verificado")["resultado"], "indeterminado")


def mutantes():
    return [
        ("dentro > 0 -> True", SRC.replace("dentro > 0", "True")),
        ("ignora resultado_senal", SRC.replace('resultado_senal == "verificado" and dentro > 0', "dentro > 0")),
        ("a = ev_ini (ignora inicio)", SRC.replace("a, b = max(t_inicio, ev_ini), min(t_fin, ev_fin)", "a, b = ev_ini, min(t_fin, ev_fin)")),
        ("b = ev_fin (ignora fin)", SRC.replace("a, b = max(t_inicio, ev_ini), min(t_fin, ev_fin)", "a, b = max(t_inicio, ev_ini), ev_fin")),
        ("fallido -> indeterminado", SRC.replace('if resultado_senal == "fallido":\n        res = "fallido"', 'if False:\n        res = "fallido"')),
    ]


class Mut(unittest.TestCase):
    def test_mutantes_muertos(self):
        vivos = []
        for nombre, src in mutantes():
            assert src != SRC, nombre
            f = cargar(src)
            global F
            orig = F
            F = f
            try:
                r = unittest.TextTestRunner(stream=open("nul" if sys.platform == "win32" else "/dev/null", "w"), verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
            finally:
                F = orig
            if r.wasSuccessful():
                vivos.append(nombre)
        self.assertEqual(vivos, [], "mutantes vivos")


if __name__ == "__main__":
    unittest.main(verbosity=2)
