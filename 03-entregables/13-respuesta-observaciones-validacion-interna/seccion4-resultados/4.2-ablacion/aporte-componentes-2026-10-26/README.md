# 4.2 — Aporte de los componentes (26-oct-2026)

Datos y evidencias para la sección 4.2. No redacta el artículo, no toca el Word ni el sistema desplegado. Todo es
offline y está en `NOTA-APORTE-COMPONENTES.md`.

## Resumen

**Verificado.** El histórico «IF 6/9 · heurísticos 7/9 · híbrido 9/9» viene de la batería del 5-oct, con 3 episodios
de DNS, 3 de inundación HTTP y 3 de escaneo. Se obtuvo con el modelo **contaminado** `if_recalibrado_2026_09`
(umbral −0,568892) y con los heurísticos `2026-09-30.1` más DNS a 0,45. **No** corresponde al IF actual ni a
α = 0,03. Los PCAP, `eve.json` y `features.csv` **se conservan** en Sensor1 `~/piloto/`. El resultado histórico se
reproduce exactamente en 9/9 episodios.

**Recalculado offline.** Mismos episodios, procesamiento del motor vigente, IF limpio congelado y heurísticos
`2026-10-06.2`:

- IF 6/9 con α 0,05 y con α 0,03 (falla en DNS).
- Heurísticos 9/9.
- Híbrido 9/9.

Ningún episodio lo detecta solo el IF. Los heurísticos actuales se ajustaron a la vista de esta batería, así que su
9/9 no es independiente.

**Por ventana (población de la Tabla 7, 65 505 ventanas):**

| Configuración | Recall | FPR |
|---|---|---|
| IF 0,05 | 0,643 | 4,52 % |
| IF 0,03 | 0,643 | 2,63 % |
| Heurísticos | 0,560 | 0,72 % |
| Híbrido 0,05 | 0,643 | 5,22 % |
| Híbrido 0,03 | 0,643 | 3,35 % |

El híbrido no añade aciertos y suma entre 462 y 469 falsas alarmas. Casi todas son `dns_entropy` sobre 10.10.10.20,
que está en `NUNCA_BLOQUEAR`.

**Falta.**

- Episodios de fuerza bruta HTTP: no hay ninguno.
- N mayor que 3.
- Episodios nuevos para medir los heurísticos de forma independiente.
- Una prueba en vivo con el IF limpio.

Reutilizar estos datos **no** valida de forma independiente la elección de α.

## Archivos

| Archivo | Contenido |
|---|---|
| `config-aporte.json` | Configuración registrada antes de recalcular |
| `evaluar_componentes.py` | Script único y reproducible |
| `antecedente/` | `orq.sh`, `orq_results.csv`, `orq.log`, `brute_tiempos.txt` (bastión); `proc.sh`, `score.py`, `dedup_merge.py` (sensor); heurísticos `2026-09-30.1` |
| `resultados/TABLA8-componentes.{md,csv}` | Tabla 8 |
| `resultados/complementariedad-episodios.csv` | Ambos, solo IF, solo heurísticos y ninguno, por α |
| `resultados/episodios-registro.csv` | Una fila por episodio y configuración: detección, primera señal, latencia, componente, acción y evidencia |
| `resultados/episodios-ventanas.csv.gz` | Todas las ventanas del replay con puntuación y señales |
| `resultados/episodios-metadatos.json` | T0, primer y último paquete, intervalo de atribución y conteos del procesamiento |
| `resultados/episodios-senales-no-atribuibles.csv` | Señales en otras entidades durante los episodios |
| `resultados/reproduccion-original.{csv,json}` | Reproducción del histórico frente a `orq_results.csv` |
| `resultados/contraste-acumulador-vivo.json` | Sensibilidad con las ventanas del acumulador en vivo |
| `resultados/control-base-05oct.json` | Control normal con el mismo procesamiento (no comparable con la Tabla 7) |
| `resultados/VENTANAS-metricas.{md,csv}`, `ventanas-metricas.json` | TP, FP, TN, FN, precisión, recall, F1 y FPR: principal, operativa y sin las 74 ventanas inciertas |
| `resultados/ventanas-predicciones.csv.gz` | Predicción por ventana (65 505) de las cinco configuraciones |
| `resultados/umbrales-verificados.json` | Umbrales recalculados sobre 65 553 ventanas |
| `MANIFIESTO-APORTE.json` | SHA-256 de las entradas externas y de todo lo publicado |

## Reproducir

```
python evaluar_componentes.py --datos DIR todo
```

`DIR` es una copia de solo lectura de Sensor1:

- `~/piloto/`
- `~/cyberflow/scripts/{engine,features}`
- `~/cyberflow/configs/features/multilayer-v2.json`
- Los dos modelos con sus manifiestos.
- `oro.csv` y `ataques-nota-M.csv`.
- `acum-20261005.csv`: filas de `artifacts/linea-base/multilayer-v3.csv` del 5-oct entre las 19:40 y las 20:55 UTC.

Los hashes están en el manifiesto. Los PCAP (unos 150 MB) y `oro.csv` no se publican aquí.
</content>
</invoke>
