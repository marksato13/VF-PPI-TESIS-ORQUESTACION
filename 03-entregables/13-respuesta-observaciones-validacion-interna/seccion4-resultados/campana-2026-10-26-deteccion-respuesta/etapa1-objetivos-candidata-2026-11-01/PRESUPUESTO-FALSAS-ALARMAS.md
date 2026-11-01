# Presupuesto de falsas respuestas y daño colateral (versión 3)

**Referencia:** el control normal del 3B. Va de 07:32 a 08:05 UTC (33 min), con 2644 ventanas decididas, 22 entidades y cobertura 1,0, sin ataques.

**Simulación:** `herramientas/presupuesto_e2e.py` v2, con el código desplegado del publicador y de la escalada. Las restricciones son **hipotéticas**: se simulan sobre tráfico registrado en sombra, ninguna se aplicó y no se modela cómo habrían cambiado el tráfico de los clientes.

Estas cifras sirven para **desarrollo y dimensionado**; no son la prueba de la candidata.

Decisiones relacionadas: [D3 y D6](DECISIONES.md). D3 adopta `if_senal`; P1 y P4 son objetivos operativos aceptados; P2 y P3 son una propuesta técnica pendiente de confirmar.

## 1. Medidas (siempre separadas) y unidades

| # | Medida | Unidad | En sombra |
|---|---|---|---|
| M1 | **Señales sobre tráfico normal**, por componente (IF a cada α, cada heurístico) | ventanas con señal / ventanas decididas; e **incidentes de señal** (ventanas de la misma entidad separadas ≤ 120 s) | medida |
| M2 | **Propuestas** del publicador (LIMIT/BLOCK) | entradas del feed por entidad (sin NUNCA_BLOQUEAR) | medida (el publicador corre en sombra) |
| M3 | **Restricciones sobre entidades legítimas** | intervalos de restricción por entidad; **segundos restringidos medidos sobre la unión de intervalos, incluidas las renovaciones**; BLOCK | **hipotética** (simulada) |
| M4 | **Transacciones legítimas** de control fallidas por una restricción | transacciones | **no aplica** |

- **El DNS 10.10.10.20 sigue en el denominador de M1**, aunque nunca se restrinja (está en NUNCA_BLOQUEAR).
- **El tiempo restringido no se deduce del número de intervalos.** Cada nueva señal **renueva** la caducidad (300 s para LIMIT), de modo que un único intervalo puede durar todo el control: 10.10.20.22 tuvo 1 intervalo con 198 renovaciones y quedó restringida el 99,7 % del tiempo.

## 2. Referencia del control 3B por política y α

Tabla completa en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) §3.

| Política · umbral | M1/M2: ventanas con veredicto | Incidentes de señal (sin NUNCA) | M3: entidades con restricción hipotética | Intervalos | Renovaciones | Entidades > 50 % del control | BLOCK |
|---|---|---|---|---|---|---|---|
| actual · desplegado (≈ α 0,05) | 467 (17,7 %) | 23 | 9 | 15 | 734 | 5 | 0 |
| actual · α 0,03 | 336 (12,7 %) | 11 | 7 | 11 | 558 | 4 | 0 |
| actual · α 0,01 | 171 (6,5 %) | 14 | 3 | 7 | 355 | 3 | 0 |
| persist_2 · desplegado | 360 (13,6 %) | 8 | 4 | 6 | 506 | 3 | 0 |
| persist_3 · desplegado | 304 (11,5 %) | 11 | 3 | 5 | 458 | 3 | 0 |
| persist_3 · α 0,01 | 105 (4,0 %) | 7 | 2 | 5 | 111 | 1 | 0 |
| **if_senal** | 92 (3,5 %): 88 `dns_entropy` sobre el DNS y 4 `http_abuse` | 1 | **1** (10.10.20.26, 21,9 %) | 1 | 14 | 0 | 0 |

**Observaciones:**

1. Las señales M1 **del IF** no dependen de la política: con el α desplegado son 396 ventanas (14,9 %), con α 0,03, 254 (9,6 %) y con α 0,01, 83 (3,1 %). La política solo decide si esas señales **restringen**.
2. **Los tres α siguen siendo candidatos** para la comparación de detectores en sombra. Elegir α no corrige los heurísticos: las 88 señales `dns_entropy` sobre el resolvedor y las 4 de `http_abuse` sobre 10.10.20.26 son iguales con cualquier α (Etapa 3).
3. Bajar α o exigir persistencia reduce las entidades afectadas, pero no protege a 10.10.20.22, .24 y .26, cuyo comportamiento es anómalo **de forma persistente** para el modelo.
4. En 33 min no hubo **ningún BLOCK** a entidades legítimas. Con cero eventos, la regla de tres da una cota de 5,5/h: con un control tan corto no se puede afirmar nada fuerte.
5. Las «3–9 entidades» son **entidades del control normal con restricciones hipotéticas**, no episodios de ataque ni restricciones aplicadas.
6. **Excepción de respuesta ≠ exclusión de población.** El resolvedor 10.10.10.20 está en NUNCA_BLOQUEAR: no se le aplica ninguna restricción **como origen**. Pero **sigue en el denominador** de las señales (M1): sus 88 señales `dns_entropy` cuentan como señales sobre tráfico legítimo y se corrigen en la Etapa 3 (atribución al cliente). Lo mismo vale para cualquier otra entidad protegida.
7. **Una tasa de señales baja no prueba ausencia de daño.** El daño se mide con M3 (restricciones) y M4 (transacciones), no con M1.

## 3. Presupuesto de falsas respuestas ([D6](DECISIONES.md))

| Id | Límite | Estado | Unidad | Cómo se mide |
|---|---|---|---|---|
| P1 | **0 BLOCK** a entidades legítimas (en srv-dmz y, con D1, DNS-DENEGAR en DC1, que cuenta como bloqueo del servicio) | **objetivo operativo aceptado** | BLOCK por campaña y control | M3 |
| P4 | **0 fallos de transacciones legítimas** atribuibles a una restricción | **objetivo operativo aceptado** | transacciones | M4 frente a la línea base |
| P2 | ≤ **1 intervalo** de LIMIT por entidad legítima y **jornada de 8 h** | **propuesta técnica de ingeniería**, pendiente de confirmar antes de congelar | intervalos / (entidad · 8 h) | M3 (intervalos) |
| P3 | ≤ **1 %** del tiempo de observación restringido por entidad legítima | **propuesta técnica de ingeniería**, pendiente de confirmar antes de congelar | s restringidos / s observados | M3 (segundos, unión de intervalos) |
| P5 | Señales M1 publicadas por componente y α, con incidentes; **no** son criterio de aprobación | práctica de publicación | ventanas, incidentes | M1 |

**Sobre los valores de P2 y P3:**

- Son una propuesta de ingeniería para este laboratorio: un intervalo que exige revisión humana por jornada se considera asumible, y un 1 % del tiempo es del orden de 5 minutos por jornada. **No** son umbrales científicos universales.
- P2 y P3 son **independientes**: un único intervalo renovado puede durar todo el control (10.10.20.22: 1 intervalo, 198 renovaciones, 99,7 %). Cumplir P2 no implica cumplir P3.
- Si el usuario prefiere otros valores, cambian antes de congelar, no después de ver los resultados.

## 4. Cómo se medirá (control normal nuevo y campaña B)

| Magnitud | Definición operativa | Fuente |
|---|---|---|
| **Intervalo de restricción** | Unión de los periodos en que el origen está en un set, desde la aplicación (t_apl) hasta la caducidad o la retirada. Una renovación (nueva señal que amplía `hasta`) **no** crea un intervalo nuevo, pero se cuenta aparte. | registro del agente (D7) + relectura del set |
| **Renovaciones** | número de ampliaciones de `hasta` dentro de un intervalo | feed y registro del agente |
| **Duración y exposición por entidad** | segundos restringidos (unión de intervalos) / segundos de observación de esa entidad; LIMIT y BLOCK por separado | registro del agente |
| **Propuestas** | entradas del feed por entidad (M2) | feed |
| **Aplicaciones** | elementos realmente cargados en srv-dmz o DC1 (M3 real) | agente instrumentado |
| **Transacciones afectadas** | transacciones de control con resultado y hora; un fallo es **atribuible** si ocurre con la entidad restringida y el mismo tipo de fallo no aparece en la línea base | clientes de control |
| **Fallos de la línea base** | mismas transacciones, misma duración, **sin agente**: es el ruido de fondo del laboratorio | control sin agente |
| **Por componente y α** | M1 por IF (α 0,05, 0,03 y 0,01) y por heurístico; M2 y M3 por regla que originó la restricción | motor y feed |

**Lo que permite concluir un control de 2 h:** permite medir lo ocurrido **durante esas 2 h**. **No** demuestra por sí solo que una entidad cumpla P2 en una jornada de 8 h. Con unas 10 entidades legítimas son ~20 entidad·hora. Si hay 0 intervalos, la regla de tres da una cota de 3/20 por entidad·hora (≈ 1,2 por entidad·8 h), que **no** es inferior a 1. Se publica como descripción de la incertidumbre, no como cumplimiento.

**Recomendación concreta:** para poder **afirmar** P2 por jornada, el control normal de la candidata debería durar al menos **una jornada de 8 h** (mismo perfil de clientes, sin ataques). Si solo se hacen 2 h, P2 se declara «sin violación observada en 2 h», sin extrapolar a 8 h. P3 sí se mide directamente sobre el tiempo observado.

**Estado actual frente al presupuesto (hipotético, 33 min, control 3B):**

- La política desplegada (IF → LIMIT) no cumple P2 ni P3 con ningún α.
- `if_senal` cumple P1 y P2, y **no** P3: 10.10.20.26 queda restringida el 21,9 % del tiempo por `http_abuse`. La corrección pertenece a la Etapa 3.
- Ninguna de estas cifras es una aplicación real ni una validación independiente.

## 5. Qué falta para medir M3 y M4 de verdad

1. Agentes instrumentados (D7) en srv-dmz y DC1, activos **solo** cuando se autorice: primero en un control sin ataques y después en la campaña B.
2. Transacciones de control registradas una a una, con resultado y hora, incluidas consultas DNS a DC1.
3. Una línea base sin agente de la misma duración.
