# Cambios respecto a `c1de49d` (Etapa 1, versión 3)

La versión 2 (`c1de49d474dc86a36ce20e852ad04cced9897ad9`) y la 1 (`2482a40`) se conservan en Git. Los datos del 3B y su revisión no se tocan.

**Camino aceptado por el usuario (1-nov-2026):**

- responder mientras el ataque sigue activo;
- 25 episodios por campaña, 5 por escenario;
- conservar las 28 características del IF, sin las 3 de L2;
- DC1 como objetivo DNS, con respuesta aplicable allí, limitada al DNS y al origen;
- el IF como detector, sin que una alerta aislada restrinja;
- priorizar el tráfico legítimo y medir las falsas **respuestas**, no solo las señales.

| # | Encargo | Corrección o resultado | Evidencia |
|---|---|---|---|
| 1 | HEAD y fuentes vigentes | Doc `c1de49d`; código main `7b275b8` y candidata `24f8a80` (sin cambios). Lecturas en vivo de solo lectura del sensor, de DC1 y del bastión. | REFERENCIAS.md |
| 2 | Contrato de características | **28 = L3 9 + L4 8 + L7 11** (17 PCAP + 11 EVE). Esquema ampliado de **31** = las 28 + 3 de L2. Coinciden en el mismo orden el esquema, el manifiesto desplegado, el extractor y `n_features_in_ = 28` del joblib del sensor. «12 L7» corregido en todos los documentos vigentes. Sin cambios en el modelo, el escalador, los umbrales ni el vector. | CONTRATO-CARACTERISTICAS.md; `herramientas/contrato_caracteristicas.py`; `contrato/`; pruebas, bloque 7 |
| 3 | D1, viabilidad en DC1 | **DC1 es Samba 4.22.10 sobre Debian 13** con DNS interno, no Windows: la política DNS y el Firewall de Windows **no son aplicables**. Se recomienda nftables en DC1 (UDP/TCP 53 + origen, set con `timeout`, DNS-DENEGAR y DNS-LIMITAR por origen). Punto de aplicación resuelto; compatibilidad concreta pendiente; despliegue no autorizado. | D1-VIABILIDAD-DC1.md; `d1-dc1/` |
| 4 | D3 consolidada | `if_senal` **adoptada**. Se documenta qué cambia en el publicador; α 0,05/0,03/0,01 conservados sin elegir. Tres resultados separados por episodio (IF / heurístico previsto / respuesta) y consecuencias declaradas. | DECISIONES §D3; TABLAS-E2E §5; JSON `tres_resultados_d3`; pruebas, bloque 6 |
| 5 | D6 consolidado | P1 (0 BLOCK) y P4 (0 transacciones fallidas) **aceptados**. P2 y P3 (≤ 1 intervalo por 8 h; ≤ 1 % del tiempo) como **propuesta técnica pendiente**, independientes entre sí. Se definen la medición (unión de intervalos, renovaciones, exposición, línea base, por componente y α) y el límite de un control de 2 h. Excepción de respuesta ≠ exclusión de población. | PRESUPUESTO-FALSAS-ALARMAS §2–§5 |
| 6 | Matriz única | D1–D8 en tres planos (alcance o diseño / compatibilidad pendiente / autorización futura). D2 y D4 no se vuelven a preguntar. | DECISIONES.md |
| 7 | Coherencia | README, OBJETIVOS (E1 con tres resultados, punto de aplicación DC1, regla de equivalencia), MATRIZ (DNS en DC1), PRESUPUESTO-TEMPORAL, DISENO-VALIDACION y REFERENCIAS actualizados. Poblaciones: 25 ejecutados en el 3B / 15 admitidos / control hipotético / futuras campañas A y B. | todos los .md |
| 8 | Etapa 2 | Lista ordenada de 9 trabajos offline con entregable, dependencias y criterio de terminado. D1 solo bloquea los puntos 7–8. | DISENO-VALIDACION.md |
| 9 | Verificación | Simulador v3 y tablas v3 regenerados; **43** comprobaciones OK y 0 fallos (antes 31); manifiesto rehecho. | `pruebas/`; MANIFIESTO.sha256 |

## Cambios de herramientas

| Herramienta | Cambio | Prueba nueva |
|---|---|---|
| `presupuesto_e2e.py` v3 | `primera_alerta_if()` (anomalía del IF por umbral, sin política); guarda los episodios de `if_senal`; salida `tres_resultados_d3`. **Ninguna cifra anterior cambia.** | umbrales sintéticos; un α menor no adelanta; sostenido-r3; DNS r2–r4 sin IF; ningún «modelo:» en if_senal |
| `tablas_e2e.py` v3 | §5: tres resultados por episodio y resumen por escenario | — |
| `contrato_caracteristicas.py` (nuevo) | conteo por capa y fuente; esquema = manifiesto = extractor; 28 frente a 31; metadatos ≠ características | conteo, ampliado y detección de una capa alterada |

## Hallazgos nuevos que se publican

- En **dns_inusual r2–r4**, el IF no alertó con ningún α; solo `dns_entropy` detectó.
- En el **escaneo breve**, la anomalía del IF también llega tarde (1/5 antes del fin, por la misma ventana que `brute_force` en r1).
- Ningún episodio del 3B dependió **solo** del IF: con `if_senal` hay acción heurística en los 25. En escaneo_sostenido-r3 esa acción viene de una regla equivocada.
- La lista NUNCA_BLOQUEAR desplegada **no incluye a DC2 (10.10.10.21)**. Hay que añadirlo en la candidata antes de cualquier agente en DC1.
- El LIMIT de srv-dmz usa un **cubo de 100/s compartido** por todas las IPs limitadas, no uno por IP. Se declara; en DC1 se propone un límite por origen.
