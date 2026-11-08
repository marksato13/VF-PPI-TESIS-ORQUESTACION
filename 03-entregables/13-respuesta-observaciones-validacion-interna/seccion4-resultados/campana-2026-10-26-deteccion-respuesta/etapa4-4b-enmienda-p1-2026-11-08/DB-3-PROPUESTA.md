# DB-3 · límites de falsas alertas del IF por α, ventanas faltantes y población (PROPUESTA para revisión)

**Estado: propuesta. Nada de esto está aprobado, publicado ni usado.** Se fija antes de ver ningún resultado de la 4B ni de la 4C. Referencia ejecutable de las cotas: `scripts/limites_db3.py` (9 pruebas).
No cambia el α desplegado, el modelo ni el umbral. B no usa nada de esto: sus respuestas dependen solo de los heurísticos (D3).

## 1. Qué se cuenta

- **Unidad: el aviso.** Racha de ventanas con ALERT del IF (para un α) sobre la misma entidad. Dos ALERT forman el mismo aviso si entre ellas hay **menos de 60 s**.
- **Tiempo:** solo tramos C0 continuos de la 4B. Los tramos no se suman para llegar a 8 h. C1 y C2 se publican aparte y no deciden.
- **Herramienta:** M1a de `control_4b.py` (mismo `score_samples`, tres cortes). La agrupación en avisos y las cotas son un paso de análisis aparte que se publicaría con su hash.

## 2. Población: quién decide α y quién solo se informa

| Grupo | IP | Papel |
|---|---|---|
| **Selección de α** | Los **seis perfiles legítimos**: 10.10.20.21 a .26 | Deciden si un α es elegible |
| Se reporta aparte, con las mismas métricas | **Kali** (10.10.20.30, solo con el canal simulado de k20) | No decide; cualquier aviso suyo es falso (no hay ataques) |
| Se reporta aparte | **DC1** (10.10.10.20, resolvedor) | No decide |
| Se reporta aparte | **Las demás IP** con ventanas (srv-dmz, bastión, infraestructura…) | No decide |

Motivo: los seis perfiles son la carga legítima que el laboratorio genera y que el IF verá en la campaña; Kali, DC1 y el resto no son generadores controlados. Se publican todas, sin excluir ninguna de la población del control (`exclusiones_poblacion` sigue vacía).
Una entidad de selección con **menos de 2 h C0** observadas no puede cumplir de forma concluyente: queda `no_concluyente`.

## 3. Los límites: propuestas operativas

Son valores de trabajo, **no derivados de datos ni de un criterio estadístico**. Se justifican por lo que un operador puede revisar y por analogía con P2 y P3 (que no se afirman aquí).

| Límite | Valor propuesto | Motivo operativo |
|---|---|---|
| **L1 · avisos** | ≤ 1 aviso por entidad y hora de control | Con 6 entidades, a lo sumo ~6 avisos por hora en el panel: revisable. Es 8 veces el límite de P2 (≤ 1 intervalo de LIMIT por entidad y jornada de 8 h) porque una señal del IF no corta tráfico; el factor 8 es una elección, no un cálculo |
| **L2 · tiempo en alerta** | ≤ 10 % de las ventanas decididas de la entidad en ALERT | Una entidad que pasa más de una décima parte del tiempo marcada deja de servir para priorizar. Es 10 veces P3 (≤ 1 % del tiempo restringido), también por elección |

Se exige **por entidad** (no en conjunto), porque una sola entidad ruidosa ya inutiliza la señal.
**Declaración:** en el control de 33 min del 3B (datos de desarrollo) el IF marcó el 14,9 %, 9,6 % y 3,1 % de 2 644 ventanas (α 0,05/0,03/0,01). Se conoce y no se usó para ajustar L1 ni L2.

## 4. Ventanas faltantes: cotas, no ALERT

**Qué es una ventana faltante** (de una entidad, en el periodo del control): no evaluada, ausente del inventario, o decidida pero fuera de la población principal (C1, C2 o C3, incluidos los `datos_faltantes` de Suricata). Su estado frente al IF **se desconoce**: no es ALERT ni PERMIT.

**Por qué no se marcan como ALERT.** Marcarlas todas ALERT es el peor caso solo para el tiempo en alerta (L2). Para los avisos (L1) puede **unir** dos avisos separados y dar *menos* avisos: favorece al α. Ejemplo probado en `test_marcar_faltantes_como_alert_une_avisos`: dos ALERT a 70 s son 2 avisos; con la franja intermedia faltante marcada ALERT son 1.

**Tratamiento propuesto**, para cada entidad y α:

| Medida | Mínimo | Observado | Máximo |
|---|---|---|---|
| **L1** avisos por hora (horas = ventanas requeridas × 10 s) | Las faltantes ALERT **solo cuando unen** avisos conocidos (se cuentan únicamente avisos con alguna ALERT conocida) | Solo las ALERT conocidas; las faltantes no unen | Observado + los avisos nuevos que cabrían en faltantes a ≥ 60 s de toda ALERT conocida y entre sí (empaquetado voraz) |
| **L2** fracción en ALERT | ALERT conocidas / (decididas + faltantes) | ALERT conocidas / decididas | (ALERT conocidas + faltantes) / (decididas + faltantes) |

**Decisión por medida:** `cumple` si el máximo ≤ límite · `no_cumple` si el mínimo > límite · **`no_concluyente`** si el límite cae dentro de [mínimo, máximo].
Una entidad cumple si cumple L1 y L2; no cumple si no cumple alguno; si no, es `no_concluyente`.

**Un α** es *elegible* solo si **las seis entidades de selección cumplen de forma concluyente**. Si alguna es `no_concluyente`, ese α **queda como no concluyente**: no se elige ni se descarta.
Se publica además la cota de Poisson al 95 % de los avisos observados (0,37/h con 8 h y 0 avisos; 1,5/h con 2 h). No decide.

## 5. Elección de α (regla del chat, con el caso no concluyente)

1. Datos: solo el control de la 4B y la campaña A nueva (4C). No se usa ningún dato de B.
2. Se consideran los α **elegibles** (§4).
3. De ellos, el que tenga más **episodios C0 de la 4C** (población principal, observación completa) con anomalía del IF atribuible y `t_det + u < t_fin_eval`. Los indeterminados no cuentan como detección.
4. Empate: el α **menor**.
5. Sin elegibles: si algún α es `no_concluyente`, el resultado es **«no concluyente por cobertura»** (no se elige ninguno ni se afirma que ninguno cumple); si todos `no_cumple`, **«ningún α cumple el límite de la 4B»**. En ambos casos el α desplegado sigue como está y no se presenta como elegido.

Efectos que no deben sorprender: las ventanas ALERT de α 0,01 son un subconjunto de las de 0,03 y estas de las de 0,05, así que el empate en episodios será lo habitual; los avisos no tienen esa monotonía (una racha larga puede partirse al bajar α), y por eso cada α se evalúa por separado.

## 6. Decisiones que se piden

- ☐ L1 ≤ 1 aviso/entidad·hora y L2 ≤ 10 %, **como propuestas operativas** (§3).
- ☐ Unidad «aviso» con separación < 60 s y mínimo de 2 h C0 por entidad de selección (§1–§2).
- ☐ Ventanas faltantes por cotas, con `no_concluyente` (§4).
- ☐ Población de selección = los seis perfiles; Kali, DC1 y las demás IP se reportan aparte (§2).
- ☐ Regla de elección de α con el caso «no concluyente por cobertura» (§5).
