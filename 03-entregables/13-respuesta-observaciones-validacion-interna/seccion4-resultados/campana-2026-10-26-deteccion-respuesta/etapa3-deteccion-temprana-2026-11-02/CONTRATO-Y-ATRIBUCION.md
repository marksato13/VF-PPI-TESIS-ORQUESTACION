# Contrato de `flow_duration_mean_30s` y atribución a entidades excluidas

## 1. flow_duration_mean_30s: entrenamiento frente a operación

**Definición** (extractor congelado, igual en los dos lados): duración media de los flujos de la entidad con actividad en los últimos 30 s, medida desde el primer paquete del flujo **visible en la entrada**.

**Horizonte.** En el entrenamiento, la entrada era el PCAP completo de cada campaña, de unos 15–20 min, así que un flujo largo podía medir hasta ~1 000 s. En operación, el motor usa `[A − 230 s, A]`: un flujo que empezó antes aparece con unos 220–230 s.

**Distribución medida.** Entrenamiento: `particionado-limpio.csv` de Sensor1, leído en solo lectura con `scripts/etapa3/distribucion_flow_duration.py`, ventanas con paquetes. Operación: replay completo del 3B.

| | Entrenamiento (train, n = 57 119) | Operación (3B, n = 9 607) |
|---|---|---|
| p50 | 0,07 s | 1,51 s |
| p90 | 3,9 s | 220,0 s |
| p95 | 67,6 s | 220,2 s |
| p99 | 547 s | 226 s |
| máximo | 1 028 s | 230 s |
| > 180 s | 3,4 % | — |
| > 230 s | 2,8 % | 0 % (imposible) |
| ≥ 200 s | — | **20,2 %** (1 940 ventanas) |

Las ventanas operativas ≥ 200 s son de hosts de infraestructura con conexiones largas: 10.10.50.52 (534), 10.10.50.51 (522), DC2 (450), 10.10.40.10 (396), DC1 (10). La Kali tiene 6.

**Efecto en los scores** (`scripts/etapa3/sensibilidad_flow_duration.py`). En esas 1 940 ventanas se sustituye el valor recortado por lo que podría haber medido un horizonte largo; el valor real es **desconocido**. Luego se recalcula el score con el modelo desplegado.

| Sustituto | Δ score medio | PERMIT → ALERT legítimos α 0,05 / 0,03 / 0,01 | Atacante |
|---|---|---|---|
| 300 s | −0,006 | 4 / 0 / 0 | sin cambios (6 ya en ALERT) |
| 600 s | −0,031 | 188 / 9 / 0 | sin cambios |
| 900 s | −0,041 | 312 / 65 / 1 | sin cambios |

Coincide con lo medido en la Etapa 2: alinear el horizonte a 900 s añadía 54 PERMIT → ALERT legítimos y multiplicaba la memoria por 4.

**Diagnóstico.** La diferencia de contrato es real y está en el **horizonte**, no en la definición. Su efecto va en la dirección de **menos** alarmas sobre los legítimos y no cambia ninguna decisión sobre el atacante del 3B.

**Alternativas evaluadas:**

| Alternativa | Coste | Efecto | Recomendación |
|---|---|---|---|
| A. Mantener 230 s (vigente) | ninguno | contrato distinto, documentado; no empeora legítimos ni atacante en el 3B | **para la candidata** |
| B. Horizonte 900 s en operación | memoria ×4, latencia | +54 a +312 falsas alarmas legítimas (α 0,05) | no |
| C. Recortar la característica en el entrenamiento a 230 s y reentrenar | reentrenar y recalibrar los 3 α | alinea el contrato; efecto desconocido | **propuesta**, no ejecutada |
| D. Sustituir por `flow.age` de EVE | cambia la definición y la fuente | no comparable con el entrenamiento | no (lo prohíbe el encargo) |

**Propuesta C** (artefactos separados, sin ejecutar):

1. Volver a extraer el dataset limpio con el extractor y `--history-seconds 230` por ventana (el mismo horizonte por ancla que el motor). Salida: `particionado-limpio-h230.csv`, sin sobrescribir el vigente.
2. Reentrenar el IF con la misma semilla, hiperparámetros y partición, en un artefacto nuevo `if_limpio_2026_11_h230.joblib` con su manifiesto.
3. Calibrar los umbrales α 0,05 / 0,03 / 0,01 sobre la validación.
4. Comparar con el vigente sobre los 25 episodios, el control y el tráfico confundible. No usar los ataques de desarrollo como confirmación independiente.

No se reentrena sin aprobación.

## 2. Los 8 casos con paquetes atribuidos a entidades excluidas

Origen: `DIAGNOSTICO-14-VENTANAS.md` de la Etapa 2 (casos 1 y 8–14). Herramienta: `scripts/etapa3/flujos_excluidos.py`. Lista los flujos entre la entidad y las IP excluidas, con tramas en (A − 60, A], y el inicio de cada flujo en el archivo.

| Caso | Entidad | A | Flujos con excluidos en (A − 60, A] | Inicio del flujo |
|---|---|---|---|---|
| 1 | 10.10.50.52 | 09:24:40 | TCP 57005 → 10.10.60.10:1514 (agente Wazuh), 16 + 12 tramas | hace 1 795 s |
| 8 | 10.10.10.21 | 09:28:30 | TCP 39061 → 10.10.60.10:1514 (Wazuh); NTP servido a 10.10.60.40 | hace 2 030 s; 22 s |
| 9 | 10.10.10.21 | 09:34:30 | Wazuh | hace 2 390 s |
| 10 | 10.10.10.21 | 09:36:00 | Wazuh; Kerberos (88) y LDAP (389) servidos a 10.10.60.41 | hace 2 480 s; 59 s y 514 s |
| 11 | 10.10.10.21 | 09:41:00 | Wazuh | hace 2 780 s |
| 12 | 10.10.10.21 | 09:46:00 | Wazuh; NTP servido a 10.10.60.40 | hace 3 080 s; 33 s |
| 13 | 10.10.10.21 | 09:56:30 | Wazuh | hace 3 710 s |
| 14 | 10.10.10.21 | 10:02:30 | Wazuh | hace 4 070 s |

**Conclusión.** Es **gestión real**, no actividad de servicio de usuarios ni del atacante:

- La conexión persistente del agente Wazuh de la entidad a su colector (10.10.60.10, excluido) empezó mucho antes del horizonte de 230 s. Sin su primer paquete, la atribución congelada asigna el flujo al otro extremo. Es el mismo efecto de horizonte que en §1.
- Los servicios del DC a hosts de gestión excluidos (Kerberos, LDAP, NTP) los inicia el cliente excluido y se le atribuyen a él por diseño, igual que a cualquier cliente.

**Qué se pierde.** Los latidos del agente Wazuh de DC2 y de 10.10.50.52 no se evalúan en esas ventanas. **Qué no se hace.** No se quitan exclusiones ni se evalúa toda la red.

**Posible mejora (no aplicada; cambiaría la atribución del IF).** En flujos cuyo primer paquete cae fuera del horizonte, desempatar por puerto: el extremo con el puerto efímero es el cliente. Requiere la misma revisión de contrato que la propuesta C.
