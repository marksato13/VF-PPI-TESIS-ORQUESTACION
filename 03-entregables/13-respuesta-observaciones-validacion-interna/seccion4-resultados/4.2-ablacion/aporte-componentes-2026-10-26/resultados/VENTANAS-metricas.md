# Metricas por ventana (poblacion de la Tabla 7)

## Principal (IF con la regla de la Tabla 7; heuristicos en todas las ventanas)

| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 54 | 2955 | 62466 | 30 | 0.0179 | 0.6429 | 0.0349 | 4.52 % |
| IF_0.03 | 54 | 1723 | 63698 | 30 | 0.0304 | 0.6429 | 0.0580 | 2.63 % |
| HEUR | 47 | 472 | 64949 | 37 | 0.0906 | 0.5595 | 0.1559 | 0.72 % |
| HIB_0.05 | 54 | 3417 | 62004 | 30 | 0.0156 | 0.6429 | 0.0304 | 5.22 % |
| HIB_0.03 | 54 | 2192 | 63229 | 30 | 0.0240 | 0.6429 | 0.0464 | 3.35 % |

## Operativa del motor (no elegibles sin evaluar; sin paquetes en 10 s el IF no se puntua)

| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 54 | 2831 | 62590 | 30 | 0.0187 | 0.6429 | 0.0364 | 4.33 % |
| IF_0.03 | 54 | 1689 | 63732 | 30 | 0.0310 | 0.6429 | 0.0591 | 2.58 % |
| HEUR | 47 | 472 | 64949 | 37 | 0.0906 | 0.5595 | 0.1559 | 0.72 % |
| HIB_0.05 | 54 | 3294 | 62127 | 30 | 0.0161 | 0.6429 | 0.0315 | 5.04 % |
| HIB_0.03 | 54 | 2158 | 63263 | 30 | 0.0244 | 0.6429 | 0.0470 | 3.30 % |

## Sensibilidad: sin las 74 ventanas normales inciertas de 10.10.20.30 (65 431)

| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 54 | 2955 | 62392 | 30 | 0.0179 | 0.6429 | 0.0349 | 4.52 % |
| IF_0.03 | 54 | 1723 | 63624 | 30 | 0.0304 | 0.6429 | 0.0580 | 2.64 % |
| HEUR | 47 | 472 | 64875 | 37 | 0.0906 | 0.5595 | 0.1559 | 0.72 % |
| HIB_0.05 | 54 | 3417 | 61930 | 30 | 0.0156 | 0.6429 | 0.0304 | 5.23 % |
| HIB_0.03 | 54 | 2192 | 63155 | 30 | 0.0240 | 0.6429 | 0.0464 | 3.35 % |

## Auditoria

```json
{
 "n_oro": 65421,
 "n_ataques": 84,
 "n_total": 65505,
 "claves_unicas": 65505,
 "duplicados": 0,
 "solape_oro_ataques": 0,
 "kali_en_oro": 74,
 "claves_iguales_tabla7": true,
 "etiquetas_iguales_tabla7": true,
 "max_abs_dif_score_vs_tabla7": 1.1102230246251565e-16,
 "predicciones_cubren_todas": true,
 "sin_paquetes_10s": {
  "oro": 45558,
  "ataques": 0
 },
 "no_elegibles": {
  "oro": 0,
  "ataques": 0
 }
}
```

Falsas alarmas dentro de las 74 ventanas inciertas: {"IF_0.05": 0, "IF_0.03": 0, "HEUR": 0, "HIB_0.05": 0, "HIB_0.03": 0}

Heuristicos disparados: {"oro": {"dns_entropy": 471, "http_abuse": 1}, "ataques": {"port_scan": 20, "http_abuse": 27}}

Solape en ataques alfa 0.05: {"ambos": 47, "solo_IF": 7, "solo_heur": 0, "ninguno": 30} · en falsas alarmas: {"ambos": 10, "solo_IF": 2945, "solo_heur": 462}
Solape en ataques alfa 0.03: {"ambos": 47, "solo_IF": 7, "solo_heur": 0, "ninguno": 30} · en falsas alarmas: {"ambos": 3, "solo_IF": 1720, "solo_heur": 469}
