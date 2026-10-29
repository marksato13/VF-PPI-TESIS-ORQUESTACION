"""Huecos entre ciclos del motor por tramo, a partir de motor_decision.log (solo lectura).

Un ciclo es un grupo de decisiones con logged_at a menos de 0,3 s entre sí; el hueco es la distancia entre
ciclos consecutivos. Sirve para documentar por qué la cobertura (tolerancia 20 s) falló durante la batería.
Uso: python huecos_ciclo_motor.py --motor motor_decision.log --tramo NOMBRE,INI,FIN [...] [--salida f.csv]
"""
import argparse
import csv
import datetime
import json
import sys


def ep(s: str) -> float:
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True)
    ap.add_argument("--tramo", action="append", required=True, help="NOMBRE,INICIO_ISO,FIN_ISO")
    ap.add_argument("--tolerancia", type=float, default=20.0)
    ap.add_argument("--salida")
    a = ap.parse_args()
    t = sorted(json.loads(l)["logged_at"] for l in open(a.motor, encoding="utf-8") if '"event": "decision"' in l)
    filas = []
    for tr in a.tramo:
        nom, ini, fin = tr.split(",")
        x = [v for v in t if ep(ini) <= v <= ep(fin)]
        g = sorted(y - x0 for x0, y in zip(x, x[1:]) if y - x0 > 0.3)
        n = len(g)
        q = (lambda p: round(g[min(n - 1, int(p * n))], 1)) if n else (lambda p: None)
        filas.append({"tramo": nom, "inicio": ini, "fin": fin, "decisiones": len(x), "huecos": n,
                      "p50_s": q(.5), "p90_s": q(.9), "p99_s": q(.99), "max_s": round(g[-1], 1) if n else None,
                      f"mayores_{a.tolerancia:g}s": sum(v > a.tolerancia for v in g)})
    w = csv.DictWriter(open(a.salida, "w", newline="", encoding="utf-8") if a.salida else sys.stdout,
                       fieldnames=list(filas[0]))
    w.writeheader(); w.writerows(filas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
