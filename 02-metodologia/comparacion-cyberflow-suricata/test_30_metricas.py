"""Pruebas de 30-metricas.py con fixtures sintéticos (sin ficheros ni red)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

RUTA = Path(__file__).with_name("30-metricas.py")
_spec = importlib.util.spec_from_file_location("metricas30", RUTA)
assert _spec and _spec.loader
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


EPISODIOS = [
    {"id": "A", "familia": "scan", "t_inicio": 1000, "t_fin": 1100, "entidad_ip": "x"},
    {"id": "B", "familia": "flood", "t_inicio": 2000, "t_fin": 2100, "entidad_ip": "x"},
    {"id": "C", "familia": "dns", "t_inicio": 3000, "t_fin": 3100, "entidad_ip": "x"},
    {"id": "D", "familia": "scan", "t_inicio": 4000, "t_fin": 4100, "entidad_ip": "x"},
]
# A,B,C detectados dentro de ventana; D no. (A a los 10 s, B a los 50 s, C a los 99 s)
DETECCIONES = {"A": [1010], "B": [2050], "C": [3099], "D": []}


class MetricasTests(unittest.TestCase):
    def test_metricas_deteccion_valores_conocidos(self):
        r = m.metricas_deteccion(EPISODIOS, DETECCIONES,
                                 ventanas_benignas_total=100,
                                 ventanas_benignas_con_deteccion=10)
        self.assertEqual((r["TP"], r["FP"], r["FN"], r["TN"]), (3, 10, 1, 90))
        self.assertAlmostEqual(r["TPR_recall"], 0.75)
        self.assertAlmostEqual(r["FPR"], 0.10)
        self.assertAlmostEqual(r["precision"], round(3 / 13, 4))
        self.assertAlmostEqual(r["exactitud"], round(93 / 104, 4))
        # F1 = 2*P*R/(P+R)
        p, rec = 3 / 13, 0.75
        self.assertAlmostEqual(r["F1"], round(2 * p * rec / (p + rec), 4))

    def test_fpr_cero_sin_falsos(self):
        r = m.metricas_deteccion(EPISODIOS, DETECCIONES, 527, 0)
        self.assertEqual(r["FP"], 0)
        self.assertAlmostEqual(r["FPR"], 0.0)
        self.assertAlmostEqual(r["precision"], 1.0)  # TP/(TP+0)

    def test_latencia(self):
        lat = m.latencia_por_episodio(EPISODIOS, DETECCIONES)
        self.assertAlmostEqual(lat["por_episodio"]["A"], 10.0)
        self.assertAlmostEqual(lat["por_episodio"]["B"], 50.0)
        self.assertAlmostEqual(lat["por_episodio"]["C"], 99.0)
        self.assertIsNone(lat["por_episodio"]["D"])
        self.assertAlmostEqual(lat["resumen"]["mediana_s"], 50.0)
        self.assertEqual(lat["resumen"]["n_con_latencia"], 3)

    def test_deteccion_fuera_de_ventana_no_cuenta(self):
        # una detección tardía, fuera de [t_inicio,t_fin], no debe contar
        r = m.metricas_deteccion(
            [{"id": "A", "t_inicio": 1000, "t_fin": 1100}],
            {"A": [1200]}, 10, 0)
        self.assertEqual((r["TP"], r["FN"]), (0, 1))

    def test_ablacion_modelo_2de3_heuristico_3de3(self):
        por_ep = [
            {"id": "A", "detected_by_model": True, "detected_by_heuristic": True},
            {"id": "B", "detected_by_model": True, "detected_by_heuristic": True},
            {"id": "C", "detected_by_model": False, "detected_by_heuristic": True},
        ]
        ab = m.ablacion(por_ep)
        self.assertEqual(ab["modelo"]["detectados"], 2)
        self.assertAlmostEqual(ab["modelo"]["fraccion"], round(2 / 3, 4))
        self.assertEqual(ab["heuristicos"]["detectados"], 3)
        self.assertAlmostEqual(ab["heuristicos"]["fraccion"], 1.0)
        self.assertEqual(ab["combinado"]["detectados"], 3)

    def test_informe_integra_todo(self):
        rep = m.informe({
            "episodios": EPISODIOS, "detecciones": DETECCIONES,
            "benignas": {"total": 100, "con_deteccion": 10},
            "ablacion": [{"id": "A", "detected_by_model": True,
                          "detected_by_heuristic": False}],
        })
        self.assertEqual(rep["n_episodios"], 4)
        self.assertEqual(rep["cobertura"]["detectados"], 3)
        self.assertIn("ablacion", rep)


if __name__ == "__main__":
    unittest.main()
