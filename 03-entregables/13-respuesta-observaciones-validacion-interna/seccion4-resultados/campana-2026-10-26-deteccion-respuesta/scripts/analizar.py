#!/usr/bin/env python3
"""Análisis de la campaña A (esqueleto; se completa cuando existan los datos).

Entradas (de la campaña, aún no generadas):
  marcas.jsonl              registro del generador en la Kali (episodio_id, inicio/fin pared+monotónico, comando, código)
  motor_decision.log        decisiones EMITIDAS en vivo, con su hora de escritura (= hora de emisión)
  features/scores por ventana del motor, o replay del PCAP continuo con el procesamiento vigente

Produce:
  - categorías D/P/N/NE por episodio y configuración (IF 0,05, IF 0,03, HEUR, HIB 0,05, HIB 0,03)
  - emitidas (del log) vs derivadas (recomputadas sobre las ventanas observadas)
  - Tabla 8 por familia; control normal; falsas alarmas con denominador común

Reutiliza, SIN copiarla, la lógica ya revisada de:
  ../../4.2-ablacion/aporte-componentes-r2-2026-10-26/evaluar_r2.py
  (clase Entorno, senales(), categoria(), paso_umbrales, metricas).

NO ejecuta nada de la campaña; es el analizador posterior. Se versiona ahora para fijar el método antes de los datos.
"""
from __future__ import annotations
import sys
from pathlib import Path

R2 = (Path(__file__).resolve().parents[1].parent
      / "4.2-ablacion" / "aporte-componentes-r2-2026-10-26")


def main() -> int:
    print("Esqueleto de análisis de la campaña A.")
    print("Método fijado en config-campana.json (criterios D/P/N/NE, emitidas vs derivadas).")
    print(f"Lógica reutilizable en: {R2/'evaluar_r2.py'} (existe: {(R2/'evaluar_r2.py').exists()})")
    print("Pendiente: conectar marcas.jsonl + motor_decision.log + ventanas cuando exista la campaña.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
