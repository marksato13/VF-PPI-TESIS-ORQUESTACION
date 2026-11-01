# Presupuesto de falsas alarmas y daño colateral (versión 2)

**Referencia:** el control normal del 3B. Va de 07:32 a 08:05 UTC (33 min), con 2644 ventanas decididas, 22 entidades y cobertura 1,0, sin ataques.

**Simulación:** `herramientas/presupuesto_e2e.py` v2, con el código desplegado del publicador y de la escalada. Las restricciones son **hipotéticas**: se simulan sobre tráfico registrado en sombra, ninguna se aplicó y no se modela cómo habrían cambiado el tráfico de los clientes.

Estas cifras sirven para **desarrollo y dimensionado**; no son la prueba de la candidata.

Decisiones relacionadas: [D3 y D6](DECISIONES.md).

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

## 3. Presupuesto operativo propuesto ([D6](DECISIONES.md): pendiente esencial)

| Id | Límite | Unidad | Justificación | Cómo se mide |
|---|---|---|---|---|
| P1 | **0 BLOCK** a entidades legítimas | por campaña y control | Un BLOCK corta el servicio ≥ 300 s y escala hasta 3600 s | M3 (BLOCK) en la campaña B y en el control normal nuevo |
| P2 | ≤ **1 intervalo de restricción** por entidad legítima y jornada de 8 h | intervalos / (entidad · 8 h) | Cada intervalo exige revisión humana; uno por jornada es asumible | M3 (intervalos) |
| P3 | ≤ **1 %** del tiempo restringido por entidad legítima, **medido directamente** sobre la unión de intervalos con renovaciones | s restringidos / s de control | Independiente de P2: un solo intervalo renovado puede durar horas | M3 (segundos) |
| P4 | **0 fallos** de transacciones legítimas atribuibles a una restricción | transacciones | Medida directa del daño | M4, frente a una línea base sin agente de la misma duración |
| P5 | Las señales M1 se publican por componente y α, con incidentes y su intervalo de Clopper-Pearson; **no** son criterio de aprobación por sí mismas | ventanas, incidentes | Una señal sin acción no daña; sirve para comparar detectores (campaña A) | M1 |

**Control normal nuevo:** ≥ 2 h, con los perfiles de clientes y sin ataques.

- Con unas 10 entidades legítimas son ~20 entidad·hora.
- Si hay 0 intervalos, la regla de tres da una cota de 3/20 por entidad·hora (≈ 1,2 por entidad·8 h). Es una **descripción de la incertidumbre**, no una garantía.

**Estado actual frente al presupuesto (hipotético, 33 min):**

- La política actual no cumple P2 ni P3 con ningún α.
- `if_senal` cumple P1 y P2, pero **no P3**: 10.10.20.26 queda restringida el 21,9 % del tiempo por `http_abuse`. La corrección es de la Etapa 3: umbral o perfil de `http_abuse` y separación del abuso.

## 4. Qué falta para medir M3 y M4 de verdad

1. Agente instrumentado ([D7](DECISIONES.md)) y activo **solo** cuando se autorice la campaña B; antes, en un control sin ataques si Mark lo autoriza.
2. Transacciones de control registradas una a una, con resultado y hora.
3. Línea base sin agente de la misma duración.
