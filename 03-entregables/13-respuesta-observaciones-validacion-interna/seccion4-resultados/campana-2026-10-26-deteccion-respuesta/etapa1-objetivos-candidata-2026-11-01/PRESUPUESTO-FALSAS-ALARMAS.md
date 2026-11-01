# Presupuesto de falsas alarmas y daño colateral

**Datos de referencia:** el control normal del 3B. Va de 07:32 a 08:05 UTC del 1-nov (33 min), con 2644 ventanas decididas, 22 entidades y cobertura 1,0, y no hubo ataques.

**Simulación:** la misma de `herramientas/presupuesto_e2e.py`, con el código desplegado del publicador y de la escalada. Las restricciones se simulan como si el agente hubiera estado activo, siguiendo sus reglas: un set nft que nunca acorta y un LIMIT que no degrada un BLOCK.

Estos registros son **material de desarrollo**. Las cifras siguientes son referencias para dimensionar, **no** la prueba de la candidata.

---

## 1. Cuatro medidas, siempre separadas

| # | Medida | Unidad | Quién la produce | En sombra |
|---|---|---|---|---|
| M1 | **Señales sobre tráfico normal** | ventanas con veredicto / ventanas decididas, por componente (IF, cada heurístico); e **incidentes de señal**: ventanas de la misma entidad separadas ≤ 120 s | motor | se mide |
| M2 | **Propuestas LIMIT/BLOCK** del publicador | entradas del feed por entidad (sin NUNCA_BLOQUEAR, porque el publicador nunca las emite) | publicador | se mide (el publicador corre en sombra) |
| M3 | **Restricciones aplicadas** a entidades legítimas | incidentes de restricción (intervalos fusionados), segundos y fracción del control restringidos, BLOCK | agente (t_apl en el host) | **estimado** (simulación) |
| M4 | **Fallos de transacciones legítimas** de control | transacciones de los perfiles de clientes con error o timeout atribuible a una restricción | clientes + agente | **no aplica** |

**El DNS 10.10.10.20 sigue en el denominador de M1.** Está en NUNCA_BLOQUEAR, de modo que no aparece en M2 ni en M3, pero sus señales cuentan. Una excepción de bloqueo no borra una señal (decisión del 3A).

**Ventana repetida frente a incidente:**

- Una entidad con 171 ventanas alertadas seguidas constituye **un** incidente de señal.
- Una entidad con 7 alertas aisladas constituye **siete**.
- Por eso las dos cifras se publican juntas. Bajar el α reduce las ventanas, pero **puede aumentar** los incidentes, porque fragmenta las rachas (véase IF 0,01 frente a 0,03 en la tabla).

---

## 2. Referencia del control 3B (33 min)

Tabla completa por entidad en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) §4.

| Configuración | Umbral IF | M1: ventanas con veredicto | M1: de ellas IF / dns_entropy / http_abuse | M1: incidentes de señal (sin NUNCA_BLOQUEAR) | M3: entidades restringidas / 22 | M3: incidentes de restricción (por hora) | M3: entidades restringidas > 50 % del tiempo | BLOCK a legítimos |
|---|---|---|---|---|---|---|---|---|
| desplegado | −0,56940 | 467 (17,7 %) | 396 / 88 / 4 | 26 (23) | 9 | 15 (27,3/h) | 5 | 0 |
| α = 0,05 | −0,56946 | 466 (17,6 %) | 395 / 88 / 4 | 26 (23) | 9 | 15 (27,3/h) | 5 | 0 |
| α = 0,03 | −0,58985 | 336 (12,7 %) | 254 / 88 / 4 | 15 (11) | 7 | 11 (20,0/h) | 4 | 0 |
| α = 0,01 | −0,62239 | 171 (6,5 %) | 83 / 88 / 4 | 18 (14) | 3 | 7 (12,7/h) | 3 | 0 |

**Observaciones:**

1. **Los tres α siguen siendo candidatos y no se elige ninguno aquí.** El α desplegado equivale en la práctica a 0,05 (−0,56940 frente a −0,56946; 396 frente a 395 ventanas).
2. **α no corrige los heurísticos.** Las 88 señales `dns_entropy` caen todas sobre el resolvedor 10.10.10.20 y las 4 de `http_abuse` sobre 10.10.20.26. Son idénticas con los tres α. Su corrección es de la **Etapa 3**.
3. **Amplificación de la escalada.**
   - Cada señal del IF genera un LIMIT de 300 s.
   - Con α = 0,01, 10.10.20.24 tiene solo 9 ventanas alertadas (≈ 4,5 % de sus ventanas), pero pasa **80 %** del control restringida.
   - Por eso el presupuesto se expresa **en restricciones aplicadas y en tiempo restringido**, no solo como tasa de ventanas.
4. **Ningún BLOCK a entidades legítimas en el control** (0 en 33 min). Con cero eventos, la cota superior al 95 % (regla de tres) es 3/0,55 h = **5,5 BLOCK/h**. Es demasiado alta para afirmar nada: el control era corto.
5. **El feed real** que el publicador dejó al final del 3B (10:36:30) proponía LIMIT a cinco clientes legítimos: 10.10.20.21, .22, .24, .26 y 10.10.50.52. El simulador lo reproduce exactamente (`pruebas/`).

---

## 3. Presupuesto propuesto

Todo es **provisional (decisión D6)**: falta la información operativa que lo fijaría, en particular el impacto real de un LIMIT de 100 pps sobre un cliente legítimo (M4).

| Id | Límite | Unidad | Justificación | Evidencia mínima | Estado |
|---|---|---|---|---|---|
| P1 | **0 BLOCK** a entidades legítimas | por campaña | Un BLOCK corta el servicio a un usuario legítimo durante ≥ 300 s y escala hasta 3600 s; no hay un coste aceptable | 0 BLOCK en un control de **≥ T horas**. La cota de 95 % es 3/T por hora: con T = 6 h, ≤ 0,5/h | provisional (T, D6) |
| P2 | ≤ **1 incidente de restricción** (LIMIT) por entidad legítima y jornada de 8 h | incidentes / (entidad·8 h) | Un LIMIT dura 300 s. Un incidente por jornada limita el tiempo restringido a ≈ 1 % y permite revisar cada caso a mano. | Exposición E entidades × T h. Con 0 incidentes, la cota superior es 3·8/(E·T) por entidad·8 h. Con E = 10 legítimas, se necesitan **T ≥ 2,4 h** de control sin incidentes para demostrar ≤ 1. | provisional (D6) |
| P3 | Fracción del tiempo restringido ≤ **1 %** por entidad legítima | s restringidos / s de control | consecuencia de P2 | se mide en el mismo control | provisional |
| P4 | **0 fallos** de transacciones legítimas atribuibles a una restricción | transacciones | Medida directa del daño. Un fallo de la línea base (sin agente) no cuenta. | Comparar con un control sin agente de la misma duración; atribuir cada fallo a una entrada nft vigente | provisional |
| P5 | M1 se **publica** por componente y α, con la cota de Clopper-Pearson y los incidentes; **no es un criterio de aprobación por sí mismo** | ventanas e incidentes | Una señal sin acción no daña. Lo que daña es M3 o M4. M1 sirve para comparar detectores (campaña A). | — | definido |

Cifras del control 3B que se toman como **referencia**, no como límites:

- IF a 14,94 / 9,61 / 3,14 % de las ventanas;
- HEUR 3,48 %;
- HIB 17,62 / 12,71 / 6,47 %.

### 3.1 Compatibilidad del estado actual con el presupuesto

**Ninguna configuración actual lo cumple.** Incluso con α = 0,01, la simulación da 7 incidentes de restricción en 33 min (12,7/h) y 3 entidades restringidas más del 80 % del control. P2 permite ~1 por entidad y 8 h.

Opciones a decidir (D3); ninguna se implementa en esta etapa:

- (a) El IF **solo señala** y la respuesta queda en manos de los heurísticos, cuya tasa en el control fue de 0 BLOCK y de LIMIT solo sobre el DNS (excluido) y sobre 10.10.20.26.
- (b) LIMIT por **persistencia** del IF: k de n ventanas, con k y n fijados antes de medir.
- (c) LIMIT más corto que 300 s.

Cualquiera de ellas es un cambio de producto: se prueba offline en la Etapa 3 y en sombra en la Etapa 4, con **tráfico normal nuevo**.

---

## 4. Qué falta para medir M3 y M4 de verdad

1. **Agente activo** en un control normal sin ataques, con contadores nft (D7).
   - Si la candidata mantiene el LIMIT del IF, ese control **degradará a clientes legítimos**. Es la razón principal para decidir D3 antes de activar nada.
2. **Transacciones de control instrumentadas.** Los perfiles de clientes deben registrar cada transacción con su resultado y su hora. Hoy generan tráfico, pero el éxito por transacción no se recoge de forma sistemática.
3. **Línea base sin agente** de la misma duración, para separar los fallos propios del entorno.
