# Propuesta para el Hallazgo 2 (ventanas del episodio anterior) — DECISIÓN EXPLÍCITA de Mark (no implementada)

## Hallazgo (§43)
En 3 de 10 ejecuciones de la puerta D5 (#4, #7, #9) el primer intento falló porque el motor emitió una **decisión nueva sobre la Kali** 0,4–5,1 s después de la limpieza, sobre una ventana de 60 s que todavía incluía la cola del episodio recién terminado: `dns_entropy` (DC1) tras E3 y E5, `http_abuse` (srv-dmz) tras E6; esta última sí fue aplicada por el agente y retirada por el reintento. Es independiente del reinicio. Con la integración actual (bloqueo sin reintento, §45.6) ese mismo patrón **bloquea** la puerta y exige reanudación manual: sin resolverlo, sería frecuente (3 de 7 puertas con episodio previo en B2; las dos de DNS y la última de inundación).

## Datos que acotan la solución (trazas de B2, `revision-evidencia-b2\evidencia-local\`)
- Las tres decisiones tardías se registraron a **fin + 43 s, + 50,6 s y + 44,2 s** del episodio anterior (el máximo observado: fin + 50,6 s). La ventana de 60 s de la heurística se cierra a **fin + 60 s**.
- La puerta corre a **fin + 15 s** (`--espera-fin`, por omisión 15,0 en `compuerta_b.py puerta`) y dura ≈ 35–90 s; el hueco entre el fin de un episodio y el inicio del siguiente fue de **210 s** (330 s tras un DNS), así que hay holgura.

## Opción A (recomendada): esperar al cierre de la ventana antes de la ÚNICA solicitud
Ejecutar la puerta a **fin + 75 s** (= cierre de la ventana de 60 s + 15 s de margen): `compuerta_b.py puerta --espera-fin 75`. **Sin cambios de código**: el parámetro ya existe.
- *No ignora señales vigentes:* cualquier decisión sobre la Kali emitida durante la ventana se registra y se limpia/retira como hoy (el agente la aplica, D5 la retira con `retirar_origen`, ambos quedan en la traza y en `puertas-D5.jsonl`); simplemente no llega después de la solicitud.
- *No genera solicitudes repetidas:* hay **una** solicitud por puerta; si falla, bloqueo y reanudación manual (sin cambio).
- *Coste:* ninguno en la cadencia: 75 s + ≈ 35–90 s de puerta < 210 s de hueco mínimo. Margen mínimo ≈ 45 s. En un DNS con 330 s, holgado.
- *Riesgo:* una decisión aún más tardía (> fin + 75 s) volvería a bloquear (el máximo observado fue 50,6 s). Una regla aplicada por el agente entre el fin y la puerta se retira en la propia puerta (`nft_antes → retirar → nft_despues`), como en #9.
- *Comprobación de aceptación:* con el arnés de integración (`arnes_integracion.py`, escenarios `base` y `puerta_lenta`) y `espera_fin` escalado a 75 s, 0 violaciones I1–I3 y 0 puertas bloqueadas con decisiones tardías sintéticas a fin + 50 s. **Ejecutada en banco (11-nov), ver abajo.**

## Opción B: puerta en dos fases (pre-limpieza informativa + limpieza definitiva)
Una primera lectura a fin + 15 s que no solicita nada, solo registra las entradas/decisiones nuevas sobre la Kali, y la solicitud a fin + 60 s + margen cuando no haya decisiones nuevas durante N s. Más código y pruebas (≈ 3 h) para el mismo efecto que A; solo aporta una traza más rica.

## Opción C (no recomendada): reintento automático
Reintentar la puerta en 60 s (lo que se hizo en B2). **Descartada:** repite la solicitud, contradice la regla acordada.

## Decisión que se pide
Elegir A (recomendada), B o aceptar el bloqueo manual tal cual. Con A basta cambiar el argumento de arranque de la puerta en el guion de lanzamiento (`g01b_lanzar_bateria_b.sh`); se prueba en banco y se documenta antes de ordenar la corrida.

## Prueba en banco de la opción A (11-nov; `propuestas\d5-sin-reinicio\test_espera_puerta.py`, 3 pruebas pasan; `evidencia-transporte\pruebas-espera-75.txt`)
Mismo mecanismo real (`compuerta_b.paso_puerta` con `espera_fin`, la puerta integrada y el publicador como proceso), **tiempo a escala 1/60** (15 s → 0,25 s; 50,6 s → 0,84 s; 75 s → 1,25 s): prueba la lógica de la espera, **no** las duraciones reales.
| Caso | Resultado |
|---|---|
| Puerta a fin + 15 s, decisión tardía a fin + 50,6 s (patrón B2 #7) | **falla y queda bloqueada** (1 solicitud) |
| Puerta a fin + 75 s, misma decisión | **pasa** (1 solicitud): la decisión se vio (2 publicaciones nuevas sobre la Kali en la traza) y la limpieza la quitó del estado vigente; no se ignora |
| Puerta a fin + 75 s, decisión a fin + 85 s | **falla y queda bloqueada**: es el límite |
## Límites ante decisiones demoradas
- Cualquier decisión sobre la Kali **posterior a fin + 75 s** (o que llegue durante la comprobación del agente, ≈ 25 s más) vuelve a bloquear la puerta; el máximo observado en B2 fue fin + 50,6 s, pero B2 tiene solo 3 casos. El bloqueo es seguro (sin solicitudes repetidas) y se resuelve con reanudación manual.
- El margen real contra el hueco de 210 s: 75 s + ≈ 35–90 s de puerta; si la puerta real (con SSH) dura más, el margen mínimo (≈ 45 s) se reduce. Se mide en el ensayo de aceptación.
- No cubre decisiones del motor que no pasan por el publicador ni retardos del propio motor mayores que la ventana de 60 s.