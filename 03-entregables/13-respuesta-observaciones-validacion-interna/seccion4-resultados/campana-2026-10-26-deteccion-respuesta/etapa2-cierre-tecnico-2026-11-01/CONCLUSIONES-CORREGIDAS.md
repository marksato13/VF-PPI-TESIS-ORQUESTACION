# Conclusiones corregidas (punto 9 del cierre técnico)

Este documento corrige varias afirmaciones de la entrega `etapa2-candidata-2026-11-01`. Esa entrega se conserva como antecedente y no se reescribe. Cada fila cita la frase anterior y su versión corregida, y la sección 3 resume cómo se usa el vocabulario en todo el cierre.

## 1. Afirmaciones que se corrigen

| # | Antes (entrega 2026-11-01) | Corregido | Por qué |
|---|---|---|---|
| C1 | «Con capturas por ficheros no se puede cortar [el escaneo breve] mientras dura, ni siquiera con 5 s y una regla temprana» (README, PRESUPUESTO §2) | En **la candidata actual**, y para **el episodio `escaneo_breve-r5`**, la primera decisión llegó después del fin del escaneo. La cadena es: ficheros de 5 s cerrados, ventanas de 10 s, relé por SSH y agente en el destino. Desglose de los 5 escaneos breves (`VALIDACION-3B-25-EPISODIOS.md`, §4): en los 5, la primera señal `port_scan` llega después del fin, entre +0,2 s y +8,2 s en el reloj del replay, y esa es la conclusión para esta candidata y esos 5 episodios. **No** queda demostrado que cualquier diseño por ficheros sea inviable: la sección 2 da alternativas con su presupuesto. | Se generalizó a partir de un solo episodio y de una sola configuración. |
| C2 | «Exigiría inspección en línea (por ejemplo, Suricata IPS…), lo que cambia la arquitectura» | El IPS **no** es obligatorio. Es una de varias alternativas (sección 2) y ninguna está medida todavía. | Se presentó una alternativa como si fuera la única. |
| C3 | «El PCAP (contenido del modelo, L3/L4) está completo» porque tcpdump informó 0 descartes (DIAGNOSTICO-DESCARTES-SURICATA) | tcpdump informó **0 descartes en su propio socket** (contador acumulado del proceso). Ese contador **no mide** pérdidas anteriores: puerto SPAN, conmutador virtual o NIC. Lo correcto es decir que el PCAP no perdió paquetes **en tcpdump**. Su completitud respecto del tráfico real **no está demostrada**. | Se confundía la ausencia de descartes en un punto con la completitud de toda la cadena. |
| C4 | «primer_efecto» al primer paquete contado por la regla del LIMIT | Ahora se separan cuatro hechos: **regla aplicada y confirmada** (el elemento con su id en nft); **coincidencias** (el contador del elemento, que es tráfico que coincide, **no** mitigación); **descartes por origen** (el set `descartes_limite`, que solo crece cuando se supera el límite); y **efecto medido** (respuestas y tasa en el cliente o en el servidor). Ensayo C8 en el banco: con 3 consultas/s, 12 coincidencias y 0 descartes; por encima del límite, con dos orígenes, 47 coincidencias = 13 descartes + 34 respondidas en cada origen. | Una coincidencia no implica descarte. |
| C5 | Proporciones de alarmas y detecciones del tramo de 25 min (5 episodios) usadas como orientación general | El tramo se mantiene como tramo. Las cifras de los 25 episodios salen del replay completo del 3B (`VALIDACION-3B-25-EPISODIOS.md`) y no se extrapolan del tramo. | 5 episodios en 25 min de un solo día no representan los 25. |
| C6 | «Decisión D-N, pendiente de Mark» y propuesta de 90/minuto con ráfaga 10 (PRESUPUESTO §3) | No se pide ningún número sin evidencia. El LIMIT de DNS a 5/s **no mitiga** el escenario (2,3 consultas/s): queda **pendiente**. El límite se fijará con una medida de tasas legítimas por origen sobre varios días y con la atribución DNS resuelta (R-E2). No se convierte en BLOCK ni se cambia el helper. | El valor de 1,5/s salía de un solo día y su margen era de ×1,5–×1,7. |
| C7 | Umbral de `http_abuse` como decisión del usuario | Igual que C6: no se pide un umbral. Lo que hay es evidencia: 10.10.20.26, un cliente legítimo, supera el umbral durante la fuerza bruta r3. El requisito R-E3.4 (separar HTTP legítimo de abuso) queda para la Etapa 3. | |
| C8 | Diferencias de características entre rotaciones atribuidas a «disponibilidad» y la deriva de `flow_duration_mean_30s` (P-5) | La causa era el **horizonte de entrada**, no la disponibilidad. El motor podaba el anillo desde el paquete más nuevo leído (`newest − 230 s`), así que el inicio, el propietario, el `flow_attempt` y las retransmisiones de cada flujo dependían del momento de la decisión. Corregido con un horizonte fijado por ventana (`[W − 230 s, …]`): r2 (15 s) frente a r3 (5 s) da 0 vectores distintos de 1255 y 0 claves distintas de 1625. Detalle en `DIAGNOSTICO-CARACTERISTICAS-Y-REINICIO.md`. | Diagnóstico incompleto en la entrega anterior. |
| C9 | El reinicio (r7) cambiaba 16 decisiones durante unos 50 s «por pérdida de historial» | La causa exacta es doble: `EveTail` arrancaba al final de `eve.json`, sin historial L7 de 60 s, y el buffer de PCAP se reconstruía con el horizonte del instante del arranque. Ahora el motor reanuda desde la última ventana registrada, relee del anillo y de `eve.json` el horizonte de la siguiente ventana y marca `historial_completo` en cada decisión. | |
| C10 | «`escaneo_breve-r1` hay señal antes del fin (16,4 s)» (INFORME-CAMPANA-3B) | Esa señal es la regla `brute_force` en la ventana de 09:31:00, que termina **antes** de la ráfaga del escaneo (09:31:02,5–09:31:06,8). La dispararon 40 peticiones `curl GET /auth` (401) del mismo origen al puerto 18081, entre 09:30:53 y 09:31:10, en paralelo al escaneo; su procedencia no consta en las marcas. La categoría «oportuna» se mantiene porque no se cambian criterios, pero **el escaneo r1 no se detectó durante el ataque**: su primera señal `port_scan` llega 5,9 s después del fin. | La categoría se leía como detección del escaneo sin mirar qué regla la producía. |
| C11 | (No afirmado antes; se prevé la conclusión fácil.) «La truncación de `flow_duration_mean_30s` a 230 s exige reentrenar» | **No se concluye.** Es una diferencia de contrato real: en el entrenamiento el horizonte llega a unos 15–20 min, el bosque tiene 498 cortes por encima de 230 s y afecta al 19 % de las ventanas con contenido del tramo. Pero alinear el horizonte (900 s) solo añade falsas alarmas sobre entidades legítimas (54 PERMIT → ALERT a α 0,05 en 676 ventanas; ninguna sobre el origen de ensayo), multiplica la memoria por 4 y hace inviable la latencia. La decisión queda para la Etapa 3, con la distribución del dataset de entrenamiento (`DIAGNOSTICO-CARACTERISTICAS-Y-REINICIO.md`, §5.4). | Sin esa medida, «reentrenar» sería una conclusión sin evidencia. |

## 2. Escaneo breve: alternativas y su presupuesto (sin implementar)

**Presupuesto.** En `escaneo_breve-r5` la ráfaga útil duró **unos 5 s** (08:47:40–08:47:44,9; 2016 SYN). Para cortarla *mientras dura*, la suma de estos componentes tiene que caber en esos segundos:

1. espera al cierre de la captura;
2. lectura y decisión;
3. publicación;
4. transporte;
5. aplicación en el destino.

Las cifras medidas (banco, replay) y pendientes están en `resultados/`.

| Alternativa | Qué cambia | Presupuesto estimado hasta aplicar | Coste y riesgos | Estado |
|---|---|---|---|---|
| A1. Candidata actual (5 s + ventanas de 10 s) | — | Rotación (≤ 5 s + 0,5 s de proceso) + ciclo + feed (0,13–0,25 s) + relé (local 0,48 s p50; SSH sin medir) + agente (~0,5 s) | — | Medido en replay: llega después del fin en r5 |
| A2. Rotación de 1–2 s y regla temprana por fichero (R-E1), sin esperar a la ventana de 10 s | Lectura del fichero recién cerrado con un contador por origen y destino de SYN a puertos distintos | ≈ 1–2,5 s + publicación + relé + agente | 5–15 veces más ficheros (inodos, disco, CPU del motor). La regla temprana es heurística y **no** toca el modelo ni el contrato de 28 características | Sin medir. Prueba en replay con `trocear_pcap.py --segundos 1` |
| A3. Lectura del fichero abierto (tail del pcap) | Sin esperar a la rotación | Lectura y decisión en < 1 s | Paquetes a medio escribir, complejidad. Cambia el supuesto de «fichero cerrado» | Sin medir |
| A4. Contador local en el destino (nft `meter`/set dinámico por origen) | La detección del escaneo vive en srv-dmz | < 1 s, sin pasar por el sensor | Lógica de detección repartida, falsos positivos locales y otra superficie en el destino. Cambia la arquitectura | Sin medir |
| A5. Alertas EVE de Suricata (reglas de escaneo) como disparador | El sensor ya escribe EVE casi en tiempo real; hoy corre **sin reglas** | Alerta EVE en ~1 s + publicación + relé + agente | Activar reglas en Sensor1 (CPU, descartes ya observados en 21 intervalos). ET Open está en otra VM | Sin medir |
| A6. IPS en línea (NFQUEUE) | Suricata en el camino del tráfico | Sub-segundo | Punto de fallo en línea, rendimiento y modo IPS incompatible con `tpacket-v3`. **No obligatorio** | Sin medir |

Ninguna se implementa ni se recomienda todavía. La Etapa 3 debe medir al menos A2 y A5 en replay, que son las que no cambian el despliegue, antes de elegir.

## 3. Vocabulario usado en todo el cierre

| Término | Qué es | Dónde se registra |
|---|---|---|
| **Señal** | Decisión del motor con una regla heurística o con una clase IF (α) en una ventana | `motor_decision.log` |
| **Restricción** | Entrada del feed v2 (LIMIT/BLOCK, destino, alcance, hasta) | `feed.json` firmado |
| **Entrega** | La pareja feed/firma llegó al destino | traza del relé, `entregado_en` |
| **Aceptación** | El agente verificó la firma y el contrato | traza del agente, `recepcion`/`aceptado` |
| **Aplicación confirmada** | El elemento con su id está en nft | traza del agente, `confirmacion` |
| **Coincidencia** | Paquetes del origen que coinciden con la regla | contador del elemento |
| **Descarte** | Paquetes descartados por superar el límite (LIMIT) o por bloqueo (BLOCK) | `descartes_limite` / contador de `bloqueados` |
| **Efecto** | Cambio medido en el tráfico (tasa, respuestas, transacciones) | cliente o servidor (ensayo C8) |

En ningún sitio se cuenta una señal como mitigación, ni una coincidencia como descarte.

## 4. Preparado para la Etapa 3 (no implementado)

| Requisito | Qué hay preparado | Qué falta |
|---|---|---|
| R-E1 Detección temprana del escaneo | Presupuesto (sección 2), troceador a N s y comparador | Implementar A2 o A5 en una rama y medir en replay |
| R-E2 Atribución DNS | Evidencia: `dns_entropy` dispara sobre DC1 (10.10.10.20), que reenvía las consultas de los clientes | Atribuir al cliente original (EVE de DC1 o logs de Samba) sin instalar nada en DC1 sin autorización |
| R-E3.1 Sin renovaciones por actividad antigua | Simulación: 115 → 52 entradas (`etapa2-candidata/resultados/renovaciones-*`) | Aplicar en el publicador y probar |
| R-E3.4 Separar HTTP legítimo y abuso | Evidencia: 10.10.20.26 en la fuerza bruta r3 | Criterio con evidencia, sin pedir un número al usuario |
| DNS (LIMIT ineficaz a 5/s) | Instrumentación de coincidencias, descartes y efecto (C8) | Medir tasas legítimas por origen sobre varios días; hasta entonces, **pendiente** |
