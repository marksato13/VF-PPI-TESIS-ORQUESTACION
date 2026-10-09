# Ficha para el cambio del artículo: OCSVM → Isolation Forest recalibrado

**Para:** compañero de artículo (IJIES). **De:** reconciliación con el sistema desplegado.
**Regla de oro:** no se renombra el modelo y se dejan los números. **Cada cifra del OCSVM se
sustituye por la del IF con su denominador y su evidencia.** Las del OCSVM sin equivalente
medido en IF **se retiran, se marcan «a medir» o se presentan explícitamente como
históricas de F6**; nunca se reutilizan como si fueran del IF.

## 1. Qué cambia y por qué (el relato honesto)

El OCSVM (`ocsvm_scaled`) fue el modelo del **laboratorio** (versión anterior). Llevado sin
recalibrar a la red real, sus primeras decisiones fueron **92,4 %** de ALERT sin ataques
(casi todo interfaces del cortafuegos emitiendo CARP). Se **recalibró un Isolation Forest**
con tráfico normal de esa red, que da **4,45 %** sobre test normal retenido, y **ese es el
modelo desplegado** (`if_recalibrado_2026_09`).

**Cómo contarlo sin sobreafirmar:** «el OCSVM fue el mejor en el banco pero no transfirió;
recalibramos un IF en la red objetivo y es el que opera». **No** escribir que «la
recalibración redujo el FPR de 92,4 % a 4,45 %»: entre ambas mediciones cambiaron el
**modelo**, los **datos** y el **alcance** (se excluyó el plano de control y se deduplicó el
espejo), así que la comparación **no aísla** el efecto de recalibrar. Si se quiere esa
atribución, hay que puntuar ambos modelos sobre el mismo conjunto retenido.

## 2. Tabla de reemplazo (dónde dice OCSVM → qué poner)

| En el artículo | Cifra OCSVM (quitar) | Cifra IF recalibrado (poner) + denominador | Evidencia | Estado |
|---|---|---|---|---|
| Modelo / detector | One-Class SVM | **Isolation Forest recalibrado** (`if_recalibrado_2026_09`), Pipeline escalador + IF | ficha técnica §2 | listo |
| Contaminación | `nu = 0,05` | percentil **`alpha = 0,05`** sobre validación | nota L | listo |
| Umbral | `1,8126` | **`score_samples < −0,568892`** (= `decision_function < −0,068892`) | ficha técnica §2 | listo; la equivalencia sobre el artefacto vivo, pendiente de publicar |
| Detección global | 88,8 % (143/161) | **69 % = 54/78** ventanas Kali | nota M | listo |
| Detección por familia | — | **HTTP 27/27**, escaneo **27/43**, DNS **0/8** (ensayo DNS contra un host que no era el resolver) | nota M | listo |
| FPR | 4,71 % (13/276) | **4,45 % sobre test normal retenido (65 421 ventanas)**. No presentarlo como «bajada desde 92,4 %» (ver §1) | nota L | listo |
| FPR en operación | 25,81 % / 22,97 % | **No reutilizar**: son del OCSVM en F6. El FPR del **sistema completo** se mide aparte | — | a medir |
| Cobertura del sistema | — | **Stack híbrido 9/9** por episodio (modelo solo 6/9, heurísticos 7/9). No atribuir 9/9 al modelo | 31, 32 | listo |
| Comparación con IDS de firmas | — | 9/9 vs **Suricata (ET Open) 0/9** en esa batería, **bajo ese ruleset** | 25, 32 | listo |
| Tiempo de respuesta | mediana 8,0 s (n = 8) | **No trasladable** (era bloqueo local en F6). Distribuido: acción dominada por timers de un minuto; medir de punta a punta | — | a medir |
| ROC-AUC | 0,9741 | **No medido para el IF** en el mismo marco → retirar o medir | — | a medir |
| Ablación | multicapa 66,5 % → 88,8 % (variables) | otra cosa: **ablación del stack** 6/9 · 7/9 · 9/9 | 31 | cambiar el sentido |
| Significancia (McNemar + Holm) | 6 comparaciones del OCSVM | **No aplica al IF** sin volver a correrla | — | a medir o retirar |
| Variables | 28 (a veces 31) | el modelo consume **28** (contrato v2); el extractor v3 emite **31** (+ capa 2, fuera del scoring); 27 de 28 observables | ficha técnica §3 | listo |
| Datos de calibración | 1.373 normal + 179 anómalas (laboratorio) | IF recalibrado sobre **337 980 ventanas** de Sensor1 (train 204 148 / val 65 633 / test 65 421) | nota L | listo |
| Disponibilidad | «cero caídas en 58 corridas, 55 verificadas» | **Solo de F6** (OCSVM, sensor en línea). Puede conservarse **explícitamente asociada a F6**; **no** demuestra la disponibilidad del despliegue con IF | 02-resultados-f6 | histórico |

## 3. Qué NO cambiar

- **Las citas de OCSVM en «Related Works» / marco teórico**: describen el estado del arte,
  no el modelo del artículo.
- El **abstract, keywords, método y resultados** sí pasan a Isolation Forest recalibrado.

## 4. Selección del modelo (cómo describirla)

La selección legítima se hace **con validación y un criterio fijado antes de mirar el
test**; el **test se reserva** para una única evaluación final. La promoción histórica del
OCSVM se hizo **tras ver el test** (sesgo de selección declarado): no repetir ese patrón ni
presentar la elección del IF como preregistrada. Si se quiere afirmar que el IF «gana», hace
falta una comparación justa —mismo conjunto retenido para todos los candidatos y criterio
preregistrado—; si no, se presenta como lo que es: el modelo que **transfiere** a la red
objetivo.

## 5. Fuentes (todo verificable)

- Producto, fijado a `main@01b6f3f`:
  [ficha técnica](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md) ·
  [model card del IF](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/dataset/MODEL_CARD_IF_RECALIBRADO.md) ·
  [reconciliación](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/RECONCILIACION-MANIFIESTO-MOTOR.md).
- [`afirmaciones-cientificas.md`](afirmaciones-cientificas.md) (bloque B = afirmaciones del IF, con estado).
- `04-evidencias/cyberflow/`: [L](../../04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md) (recalibración y FPR), [M](../../04-evidencias/cyberflow/M-deteccion-kali-sensor1-2026-09-30.md) (detección Kali), [N](../../04-evidencias/cyberflow/N-e2e-enforcement-2026-09-30.md) (BLOCK en banco), [O](../../04-evidencias/cyberflow/O-enforcement-vivo-campana-ataque-2026-10-01.md) (LIMIT en vivo).
- `02-metodologia/comparacion-cyberflow-suricata/`: [31 — ablación](../comparacion-cyberflow-suricata/31-ABLACION-RESULTADO.md), [32 — resumen](../comparacion-cyberflow-suricata/32-RESUMEN-RESULTADOS.md).
- Histórico de F6 y del OCSVM: [`../historico-laboratorio/`](../historico-laboratorio/README.md).
