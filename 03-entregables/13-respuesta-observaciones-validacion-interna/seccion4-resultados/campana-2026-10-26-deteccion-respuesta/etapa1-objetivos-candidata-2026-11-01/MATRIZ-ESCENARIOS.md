# Matriz por escenario (versión 3)

**Fuentes:**

- `escenarios/escenarios.json` y `FICHAS-ESCENARIOS.md` (configuración congelada de la campaña);
- `heuristicos.py` VERSION 2026-10-06.2 (motor `24f8a80`);
- [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) (simulación v3; §5 separa IF, heurístico previsto y respuesta).

**Decisiones:** [DECISIONES.md](DECISIONES.md). **Criterios E1–E5:** [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) §3.

**Reglas comunes:**

- 5 episodios por escenario y campaña ([D4](DECISIONES.md)). Origen: Kali 10.10.20.30.
- No se usan la IP del generador, los horarios ni los identificadores del episodio para **producir** una detección; solo sirven para atribuirla *a posteriori*.
- El escaneo breve **no se prolonga**.
- Las cifras «3B» son de la **simulación sobre sombra** con la política actual (IF → LIMIT) y el α desplegado.
  - «Antes\*» significa antes del fin **bajo supuestos** (escenarios favorable y alto; demoras de activación y de efecto desconocidas).
  - «Det. posterior» significa que t_det **medido** es posterior a `t_fin_eval`.
  - Describen el 3B; no prueban la candidata.

| Elemento | Escaneo sostenido | Escaneo breve | Fuerza bruta HTTP | Inundación HTTP | DNS inusual |
|---|---|---|---|---|---|
| **Comportamiento y duración** | `nmap -sT 1-65535 -T4 --max-rate 1500 --max-retries 0` a 10.10.30.10. Natural, 65,5–66,3 s (3B). | `nmap -sT 1-1000 -T4` a 10.10.30.10. Natural, 17,6–18,0 s (3B). **No se prolonga.** | Bucle de 90 s de autenticaciones fallidas contra :18081/auth; `control:control123 → 200` como verificación | 8 bucles de `curl --max-time 2` a :80 durante 90 s (~160 intentos/s en r1) | `dig` con nombres aleatorios `*.lab-ppi` a 10.10.10.20 cada 0,4 s durante 90 s; el comodín responde, sin NXDOMAIN |
| **t_fin_eval** ([D8](DECISIONES.md)) | min(t_inicio + D_ref, observado); D_ref 3B = 65,52 s | ídem; D_ref 3B = 17,59 s | min(t_inicio + 90 s, observado) | ídem | ídem |
| **Evidencia de atribución** | SYN del origen al destino en el SPAN dentro de la ventana y de [inicio, fin] | ídem | Peticiones HTTP del origen a :18081 en el EVE con 401/403. Requiere C0: en C1 no se afirma ausencia. | Peticiones HTTP del origen a :80 en el EVE y el SPAN | Consultas `dns` del origen a 10.10.10.20 en el EVE; C1 limita |
| **Regla prevista (E1)** | `port_scan` → BLOCK | `port_scan` → BLOCK, que debe decidir **con evidencia parcial** y antes del fin | `brute_force` → BLOCK (≥ 5 req/60 s y ≥ 80 % de 401/403) | `http_abuse` → LIMIT (≥ 100 req/60 s, fallos < 0,8). El IF, como señal ([D3](DECISIONES.md)). | `dns_entropy` sobre el **cliente** (≥ 20 consultas/60 s y ratio de nombres únicos ≥ 0,45) |
| **Respuesta prevista y condiciones** | BLOCK del origen en srv-dmz. Requiere agente activo (campaña B) y limpieza previa ([D5](DECISIONES.md)). | ídem | ídem | LIMIT del origen en srv-dmz (`limit rate over 100/second drop`) | **En DC1** (Samba sobre Debian), con nftables limitado a UDP/TCP 53 y al origen: DNS-LIMITAR por origen (N por fijar) o DNS-DENEGAR ([D1](D1-VIABILIDAD-DC1.md); punto de aplicación resuelto, comprobaciones técnicas pendientes) |
| **Evidencia de aplicación (E2)** | Agente instrumentado: hora y retorno del commit, lote y lectura del set ([D7](DECISIONES.md)) | ídem | ídem | ídem | Agente de DC1: hora y retorno del commit nft, relectura del set `inet cyberflow_dns` y contadores (D1, D7) |
| **Evidencia de efecto (E3)** | Desaparecen los SYN-ACK/RST del destino al origen en el SPAN **mientras siguen los SYN** del origen; contadores nft | ídem | Cesan las respuestas HTTP de :18081 al origen mientras siguen sus peticiones | Tasa de respuestas HTTP del destino al origen en bloques de 1 s, frente a los 10 s previos a t_apl, mientras siguen las peticiones. Umbral del efecto: **provisional, se fija con D3** (propuesta: reducción ≥ 50 %). | Las consultas del origen a `@10.10.10.20` dejan de recibir respuesta (DNS-DENEGAR) o su tasa de respuestas cae según N (DNS-LIMITAR) mientras siguen enviándose; contadores nft |
| **Tráfico legítimo a preservar (E4)** | Transacciones de control a srv-dmz (HTTP :80 y :18081 de los clientes 10.10.20.21–26); SSH de gestión desde el bastión (en NUNCA_BLOQUEAR) | ídem | Inicios de sesión legítimos en :18081 | HTTP :80 de los clientes | Resolución DNS de todos los clientes en DC1; servicios AD de DC1 (88, 389, 445…) intactos; replicación con DC2 (10.10.10.21, en NUNCA_BLOQUEAR en la candidata) |
| **Caducidad o retirada (E5)** | Caducidad del set o retirada verificada antes del siguiente episodio | ídem | ídem | ídem | Retirada de la política o regla verificada |
| **Criterio por episodio** | Cumple si se cumplen E1–E5 (en A, solo E1 y el registro de E4). Fallo si alguno falla; indeterminado si la incertidumbre impide ordenar frente a t_fin_eval. | ídem | ídem | ídem | ídem, con D1 resuelta. Mientras no lo esté, en B **solo E1 y E4 son evaluables** y la familia se publica como «respuesta no evaluable: falta el punto de aplicación». No se elige en silencio quedarse solo con la detección. |
| **3B, regla prevista (medido / bajo supuestos)** | t_det 22,0–74,3 s; antes\* 4/5. En r3, `port_scan` llega a los 74,3 s (det. posterior), después de un IF a 22,0 s y de un `brute_force` mal atribuido. | t_det 26,2–39,5 s; **det. posterior 5/5**. En r1, la primera señal es `brute_force` a 16,4 s, que no valida `port_scan`. | t_det 18,4–25,1 s; antes\* 5/5 | `http_abuse` t_det 24,2–29,3 s, en la misma ventana que el IF; antes\* 5/5; **efecto desconocido**. Solo 1/5 admitidos. | t_det 17,2–25,9 s; antes\* 5/5 (detección); sin punto de aplicación |
| **Trabajo que lo condiciona** | D5, D7, activación (B) | Etapas 2 **y** 3 (PRESUPUESTO-TEMPORAL §4) | D5, D7; descartes de Suricata | D3; descartes (Etapa 2); separar abuso de escaneo (Etapa 3) | D1; atribución DNS al cliente (Etapa 3) |

## Errores de atribución observados en el 3B (casos para las pruebas de regresión de la Etapa 3)

| Episodio | Señal | Problema |
|---|---|---|
| escaneo_breve-r1 | `brute_force` «5 req HTTP» a 16,4 s | Un escaneo `-sT` de 1–1000 activa la regla de fuerza bruta: hay que verificar qué peticiones HTTP la originaron |
| escaneo_sostenido-r3 | `brute_force` «16 req HTTP» a 22,0 s | ídem |
| inundacion_http-r1…r5 | `port_scan` → BLOCK a los 112–117 s (después del fin) | El abuso HTTP se mezcla con el escaneo |
| control normal | `dns_entropy` 88 veces sobre 10.10.10.20 | El resolvedor reenvía las consultas: la regla atribuye al resolvedor en vez de al cliente |
| control normal | `http_abuse` 4 veces sobre 10.10.20.26 | Un cliente legítimo supera el umbral de volumen |
