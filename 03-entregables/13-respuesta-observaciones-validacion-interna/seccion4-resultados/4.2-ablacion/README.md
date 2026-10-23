# 4.2 — Ablación: qué es válido aquí

- **`ablacion_sensor.py` → `Tabla8-ablacion-sensor.md` / `matriz-episodios-sensor.csv` / `metadata-ablacion-sensor.json`**
  — **VÁLIDO.** Modelo limpio + heurísticos vigentes sobre datos del **sensor** (65 421
  benignas + 181 ventanas Kali). Valida FPR IF 4,53 %. Salvedad: las 181 son la ráfaga de
  contaminación (no la batería 3×3); no incluye DGA.

- **`ablacion_limpio.py` → `Tabla8-ablacion-limpio.*`** — **NO VÁLIDO como resultado.**
  Evalúa el modelo del sensor sobre el set de **laboratorio (simulado)**: da FPR ≈ 90 % por el
  artefacto sim→real. Se conserva solo para **demostrar** por qué no se debe mezclar el dataset
  de laboratorio con el modelo desplegado.

- La batería fiel de 9 episodios (3 DNS / 3 flood / 3 escaneo) con el modelo limpio **requiere
  re-correr** (los datos por ventana y los PCAP originales no se conservaron). Ver
  `..\00-inventario\INVENTARIO-Y-FACTIBILIDAD.md`.
</content>
