# Ficha para el cambio del artículo: OCSVM → Isolation Forest recalibrado

**Para:** compañero de artículo (IJIES). **De:** reconciliación con el sistema desplegado.
**Regla de oro:** no se renombra el modelo y se dejan los números. **Cada cifra de OCSVM
se sustituye por la del IF con su denominador y su evidencia.** Las de OCSVM que no tengan
equivalente medido en IF **se retiran o se marcan "a medir"**, no se reutilizan.

## 1. Qué cambia y por qué (el relato honesto)

OCSVM (`ocsvm_scaled`) fue el modelo del **laboratorio** (versión anterior). Al llevarlo a
la red real **no transfirió**: FPR **92,4 %**. Se **recalibró un Isolation Forest** con
tráfico normal de esa red → FPR **4,45 %**, y **ese es el modelo desplegado y en operación**
(`if_recalibrado_2026_09`). El argumento del paper **no** es "IF ganó un concurso", sino:
*OCSVM fue el mejor en el banco pero no transfirió; recalibramos un IF en la red objetivo y
es el que opera.* Más sólido y más honesto.

## 2. Tabla de reemplazo (dónde dice OCSVM → qué poner)

| En el artículo | Cifra OCSVM (quitar) | Cifra IF recalibrado (poner) + denominador | Evidencia | Estado |
|---|---|---|---|---|
| Modelo / detector | One-Class SVM | **Isolation Forest recalibrado** (`if_recalibrado_2026_09`), Pipeline escalador+IF | FICHA-TECNICA §2 | listo |
| Hiperparámetro de contaminación | `nu = 0,05` | percentil **`alpha = 0,05`** en validación | nota L | listo |
| Umbral | `1,8126` (decision OCSVM) | **`score_samples < −0,568892`** (= `decision_function < −0,068892`) | FICHA §2 | listo |
| Detección global | 88,8 % (143/161) | **69 % global = 54/78** ventanas Kali | nota M | listo |
| Detección por familia | — / implícito | **HTTP 27/27 (100 %)**, escaneo **27/43 (63 %)**, DNS **0/8 (0 %)** | nota M | listo |
| FPR laboratorio | 4,71 % (13/276) | **4,45 % sobre test normal retenido (65 421 ventanas)**; baja desde 92,4 % tras recalibrar | nota L, `ensayo-if-v2.json` | listo |
| FPR operación | 25,81 % / 22,97 % | **No reutilizar** (eran de OCSVM/F6). El FPR del **sistema completo** (con heurísticos+enforcement) se mide **aparte** | — | a medir |
| Cobertura del sistema | — | **Stack híbrido 9/9** por episodio (modelo solo 6/9, heurísticos 7/9). **No** atribuir 9/9 al modelo | 31-ABLACION, 32-RESUMEN | listo |
| Comparación con IDS de firmas | — | CyberFlow 9/9 vs **Suricata (ET Open) 0/9** en esa batería, **bajo ese ruleset** | 25-BATERIA, 32 | listo |
| Tiempo de respuesta | mediana **8,0 s** (n=8) | **No trasladable** (era bloqueo local F6). Enforcement distribuido: detección ~2–40 s, hasta BLOCK ~1–2,5 min (cadencia minutely) | evidencias de tiempos | a medir/precisar |
| ROC-AUC | 0,9741 | **No existe medido para IF** en el mismo marco → retirar o medir | — | a medir |
| Ablación | multicapa 66,5 %→88,8 % (features) | distinta: **ablación del stack** 6/9·7/9·9/9 | 31-ABLACION | sustituir el sentido |
| Significancia (McNemar+Holm) | 6 comparaciones OCSVM | **No aplica a IF** sin re-correr | — | a medir o retirar |
| Variables | 28 (y a veces 31) | modelo consume **28 (contrato v2)**; extractor v3 emite **31** (+capa 2, fuera del scoring); 27 de 28 observables | FICHA §3 | listo |
| Dataset de recalibración | 1.373 normal + 179 anómalas (lab) | recalibración IF sobre **337 980 ventanas** Sensor1 (train 204 148 / val 65 633 / test 65 421) | nota L | listo |
| Disponibilidad | — | **cero caídas en 58 corridas, 55 verificadas** (no "siempre") | F6 | listo (se mantiene) |

## 3. Qué NO cambiar

- **Las citas de OCSVM en "Related Works"/Marco teórico** (refs de literatura): se quedan;
  describen el estado del arte, no tu modelo.
- El **abstract, keywords, método y resultados** sí pasan a Isolation Forest recalibrado.

## 4. Si quieres afirmar que el IF "gana" (condición)

Hace falta una **comparación justa**: mismo conjunto retenido para todos los candidatos y
criterio de selección fijado **antes** de ver el test (pre-registrado). Sin eso, se declara
como lo que es —el modelo que **transfiere** a la red objetivo—, no como ganador de un
ranking. La promoción histórica de OCSVM se hizo tras ver el test (sesgo declarado): no
repetir ese patrón con IF.

## 5. Fuentes (todo verificable)

- `CYBERFLOW/producto-as-deployed/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md` (verdad del despliegue)
- `.../docs/dataset/MODEL_CARD_IF_RECALIBRADO.md` · `.../docs/RECONCILIACION-MANIFIESTO-MOTOR.md`
- `02-metodologia/trazabilidad/afirmaciones-cientificas.md` (bloque B = claims del IF, con estado)
- `04-evidencias/cyberflow/`: `L` (recalibración/FPR), `M` (detección Kali), `N` (BLOCK banco), `O` (LIMIT vivo)
- `02-metodologia/comparacion-cyberflow-suricata/`: `31-ABLACION-RESULTADO.md`, `32-RESUMEN-RESULTADOS.md`
