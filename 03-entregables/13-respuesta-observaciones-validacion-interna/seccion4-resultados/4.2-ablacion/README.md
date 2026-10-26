# 4.2 — Ablación: qué es válido aquí

- **`aporte-componentes-2026-10-26/`** — **VIGENTE.** Contiene:
  - El antecedente 6/9 · 7/9 · 9/9, verificado y reproducido 9/9. Era del modelo contaminado.
  - Los mismos 9 episodios del 5-oct re-procesados desde sus PCAP con el IF limpio (α 0,05 y 0,03), los heurísticos
    vigentes y el híbrido.
  - La Tabla 8 y las métricas por ventana sobre la población de la Tabla 7.

  Ver `NOTA-APORTE-COMPONENTES.md`.

- **`ablacion_sensor.py` → `Tabla8-ablacion-sensor.md` / `matriz-episodios-sensor.csv` / `metadata-ablacion-sensor.json`**
  — **Válido como apoyo.** Usa el modelo limpio y los heurísticos sobre 65 421 ventanas benignas y 181 ventanas Kali
  del sensor. Salvedad: esas 181 ventanas son la ráfaga de contaminación, no la batería 3×3.

- **`ablacion_limpio.py` → `Tabla8-ablacion-limpio.*`** — **No es válido como resultado.** Evalúa el modelo del sensor
  sobre el set de laboratorio (simulado) y da una FPR de ≈ 90 % por el artefacto sim→real. Se conserva solo para
  demostrar por qué no se mezclan los dos conjuntos.

- Corrección del 26-oct: el inventario del 23-oct decía que los PCAP de la batería no se habían conservado. Sí se
  conservaron, en Sensor1 `~/piloto/`.
