# DB-3 · versión final para revisión (08-nov-2026)

**Estado: las cinco reglas de §4 fueron aprobadas por Mark el 08-nov-2026 (chat), incluidos los seis perfiles obligatorios y el mínimo de 2 h C0 por perfil. Publicada; sin usar todavía.** Sustituye a [`DB-3-PROPUESTA.md`](DB-3-PROPUESTA.md) solo en lo que se indica abajo; el resto de la propuesta (§1–§5) queda tal cual.
No cambia el α desplegado, el modelo, el umbral, los heurísticos ni la política de respuesta. B no usa nada de esto.

## 1. Qué cambia respecto a la propuesta

| Antes (propuesta) | Ahora |
|---|---|
| Las reglas de §2 y §4 estaban escritas pero la elegibilidad de un α no estaba probada como conjunto | Está implementada en una sola función, `evaluar_alfa()` (`scripts/analisis_db3.py`), y probada: **32 pruebas de DB-3** (`tests/test_db3_elegibilidad.py` 23, `tests/test_limites_db3.py` 9) más el banco de punta a punta con datos reales del 3B (`tests/banco_db3.sh`, 19 comprobaciones) |
| «Una entidad con menos de 2 h C0 queda no concluyente» | Igual, con una precisión que la implementación ya tenía y que ahora está escrita: si por las cotas ya `no_cumple`, **sigue `no_cumple`** (no se rebaja a no concluyente por falta de horas; 2 h solo impide declarar `cumple`) |
| Los seis perfiles | Un α es elegible solo con **los seis presentes**. Un perfil sin ninguna ventana se informa como `sin_ventanas` y el α queda `no_concluyente` (o `no_cumple` si otro ya no cumple) |

## 2. Lo que las pruebas fijan (todas en `tests/test_db3_elegibilidad.py`)

1. Seis perfiles con 720 ventanas C0 (2,0 h) y sin avisos → elegible.
2. Falta cualquiera de los seis (6 casos) → no elegible, `sin_ventanas`. Cinco buenos más Kali y DC1 → no elegible.
3. 719 ventanas C0 (1,997 h) en cualquiera de los seis (6 casos) → `no_concluyente`, con «menos de 2.0 h»; 720 exactas → bastan.
4. Las horas son de ventanas **C0 decididas**, no de ventanas requeridas.
5. Un perfil con 100 de 720 ventanas en ALERT (13,9 % > 10 %) → `no_cumple`; el α no es elegible aunque haya 2 h.
6. L1: 2 avisos en 2 h (1,0/h) cumple; 3 avisos (1,5/h) no cumple.
7. Ventanas faltantes que abren las cotas → nunca `cumple`; no se tratan como ALERT ni como PERMIT.
8. Kali, DC1 y otras IP no bloquean ni completan los seis; se reportan aparte.
9. Los 33 min del 3B (198 ventanas) no dan ningún α elegible.
10. Valores por defecto: **2,0 h, L1 = 1,0, L2 = 0,10, separación 60 s, perfiles 10.10.20.21–.26**; cambiar el mínimo exige pasar el parámetro a la vista.
11. La elección entre α ignora los no elegibles; si ninguno lo es y alguno es `no_concluyente`, el resultado es «no concluyente por cobertura».

## 3. Declaración sobre los datos de desarrollo

Con el control de 33 min del 3B (2 644 ventanas; datos de desarrollo) los tres α salen `no_cumple` y ninguno llega a 2 h C0. **Se conoce y no se usó** para elegir L1, L2, el mínimo de 2 h ni la separación de 60 s. Es un antecedente, no un resultado.
En el 3B, los perfiles .22, .24 y .26 son los que no cumplen en los tres α (informativo).

## 4. Qué se aprueba

- ☑ L1 ≤ 1 aviso/entidad·hora y L2 ≤ 10 %, como propuestas operativas (propuesta §3).
- ☑ Unidad «aviso» (separación < 60 s) y mínimo de **2 h C0 por entidad de selección**, con la precisión de §1 (`no_cumple` se mantiene).
- ☑ Ventanas faltantes por cotas, con `no_concluyente` (propuesta §4).
- ☑ Población de selección = los seis perfiles, **todos obligatorios**; Kali, DC1 y las demás IP aparte (propuesta §2).
- ☑ Regla de elección de α con el caso «no concluyente por cobertura» (propuesta §5).

## 5. Cómo se usa tras la 4B

`analisis_db3.py` lee el motor vivo, el inventario (replay), la salud y el EVE de la 4B (mismos argumentos que `control_4b.py`) y escribe `db3-4b.json` con, por α: veredicto, las seis entidades, y las demás IP aparte. No escribe en ningún host. Se ejecuta en el portátil sobre las copias, nunca en el Sensor1.
