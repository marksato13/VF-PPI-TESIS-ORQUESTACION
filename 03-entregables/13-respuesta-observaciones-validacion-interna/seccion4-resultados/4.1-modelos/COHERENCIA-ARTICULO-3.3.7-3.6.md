# Cross-check de coherencia: 4.1 ejecutado vs artículo (3.3.7 y 3.6)

Contrastado contra `Articulo-IJIES-espanol-subrayado_actualizado_MARK.docx` (secciones extraídas).

## Lo que el artículo describe y SÍ coincide con lo ejecutado (v2)

- **3.3.7 "Evaluación y congelado":** "mantiene fijos el escalador, el IF y el umbral calibrado";
  "65 421 observaciones de prueba normal para los falsos positivos"; "ROC-AUC utilizando el negativo
  de su puntuación de normalidad"; "manifiesto registra parámetros, versiones de bibliotecas y SHA-256";
  "distingue la detección por ventana de la cobertura por episodio". → **Exactamente lo ejecutado en v2**
  (Pipeline congelado, 65 421 test, anomalía = −score_samples, run-manifest con hashes+versiones, ventana
  vs episodio declarados).
- **3.6 / Tabla 5:** FPR del IF (65 421), Detección del IF por familia (TPR, ROC-AUC), comparación por
  componentes (9 episodios), Suricata (9 + Nikto), fuerza bruta (1), aplicación de respuestas. → Coincide
  con el diseño de 4.1/4.2/4.3/4.4. Las ecuaciones t0/t1/t2 de 3.6 coinciden con 4.4.

**Conclusión:** la metodología descrita en 3.3.7/3.6 es coherente con la evaluación 4.1 ejecutada; no hay
que reescribirla retrospectivamente.

## Cambios que DEBEN declararse / corregir en el artículo

1. **OCSVM → Isolation Forest (crítico):** el **resumen** y las **palabras clave** todavía listan
   *"One-Class SVM"* como modelo/keyword, pero el detector desplegado y evaluado es **Isolation Forest
   limpio** (`if_limpio_2026_10`). 3.3.7 ya dice "el IF", pero **abstract, keywords e introducción/
   contribuciones** deben reflejar el IF (dejando el OCSVM como antecedente comparado, Tabla 7). Es el
   cambio metodológico de F5; propagarlo para no contradecir el cuerpo.
2. **Etiqueta de familia = PROXY observable, no ground-truth.** 3.6 dice "ataques identificados por
   familia". En 4.1 la familia se asignó con el **criterio observable de nota M** (HTTP/DNS por contadores),
   no por un etiquetado por-ataque verificado. Declararlo así en el texto (es una aproximación honesta).
3. **Nikto:** 3.6/Tabla 5 anuncia un control Nikto en la comparación con Suricata; la campaña ejecutada
   (4.3) **aún no incluyó Nikto** → o se ejecuta o se ajusta la Tabla 5. (Esto es 4.3, no 4.1.)
4. **Evaluación reutilizada:** 3.3.7 no dice que el conjunto 84+65 421 ya se usó para elegir modelo
   (14-oct). Para no sobre-afirmar, conviene una frase de que la comparación es de **transferencia** y que
   este conjunto no es un test ciego independiente del limpio.

## No confundir (coherente con el esquema de afirmaciones)
IF solo (4.1) ≠ híbrido (4.2); resultado actual ≠ histórico; ventana ≠ episodio; FPR offline ≠ impacto
operativo; desempeño en esta red ≠ generalización a otra red.
</content>
