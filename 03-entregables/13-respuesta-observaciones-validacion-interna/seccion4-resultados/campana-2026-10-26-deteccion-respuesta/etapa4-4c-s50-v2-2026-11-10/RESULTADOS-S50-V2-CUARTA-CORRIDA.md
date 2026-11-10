# Resultados de `s50` v2 sobre la cuarta corrida de la Campaña A (10-nov-2026)

**Estado:** análisis completo sobre las copias (sin tocar la captura ni la v1). Sombra: nadie aplicó respuesta («respuesta aplicada» = no medida). Commit local, **no publicado**. Los resultados son de **una** corrida de 25 episodios (5 por familia) en un laboratorio, con α **sin elegir**.

## Ejecución
- **Código de salida: 0** («ANÁLISIS COMPLETO» 2026-11-10T04:33:08.766Z); 15 pasos OK (`a1 a2 a3 b c 1 2 3 d 4 5 6 7 8 9`), 0 fallidos. `SHA256SUMS` de `analisis-v2` (primera línea `# COMPLETO …`) verifica con 0 discrepancias.
- **Sensor1:** `/home/m4rk/cf-e4/4c/analisis-v2/` (180 ficheros). **v1 conservada sin cambios:** `/home/m4rk/cf-e4/4c/analisis/` (176 ficheros, `SHA256SUMS` verifica). Log: `/home/m4rk/cf-e4/4c/s50-v2.log`.
- **Copia local verificada** (180 ficheros, huella del manifiesto `826b965e3f2df4ce…`): `evidencia/analisis-v2/` de esta carpeta. Tabla por episodio: `evidencia/analisis-v2/analisis-4c/TABLA-3B.md`; datos completos: `analisis-4c/analisis-3b.json`.
- **Parámetros:** inventario 2026-11-09T20:45:38Z → 23:53:51Z (INV_HASTA = corte del replay `s30`, desviación documentada en la 4B); control 21:23:00Z → 21:53:00Z.
- **Entradas:** captura de 3 h 08 min, 25 episodios completos, inventario de **13 344 ventanas requeridas, 13 344 decididas a tiempo**, 0 tardías, 0 ausentes (cobertura 1,0); salud: 25 episodios `completa`, Suricata `cero_explicito` ×25; descartes de tcpdump 0 (PID 1440, 449 lecturas SIGUSR1).

## Población principal: 21 de 25
| Familia | Principal | Fuera (exploratorios) |
|---|---|---|
| Inundación HTTP | 5 | 0 |
| Fuerza bruta HTTP | 5 | 0 |
| DNS inusual | 5 | 0 |
| Escaneo sostenido | 5 | 0 |
| Escaneo breve | **1** (r4) | **4** (r1, r2, r3, r5) |

**Motivo de cada exclusión (los 4 iguales):** `integridad no apta` por un único requisito, `cobertura_durante` («durante incompleta»: 0 anclas esperadas de la Kali en un barrido de ~5 s). Los demás 11 requisitos están verificados y la fuente es `completa`. Detalle y tratamiento en `ESCANEOS-BREVES-SIN-ANCLAS.md` (la regla no se cambió). Los 21 episodios de la principal cumplen inventario, fuente completa, integridad apta y evidencia de destino.

## α y configuraciones
Se evaluaron **tres α: 0,05, 0,03 y 0,01** (umbrales de score del IF recalibrado −0,5695, −0,5899 y −0,6224; el IF alerta con score por debajo del umbral), más el componente heurístico solo. Son **siete configuraciones derivadas** del mismo motor: **IF solo** (`IF_0.05`, `IF_0.03`, `IF_0.01`), **heurísticos solos** (`HEUR`) e **híbrido** (`HIB_α = IF_α OR HEUR`, tres α). **α no se elige** (protocolo 4C): se informan los tres.

## Resultado por configuración
Categorías por episodio: **oportuna** (alerta dentro del horizonte), **solo_posterior** (alerta, pero tarde), **ausencia_con_observacion_suficiente** (no alertó pese a observación completa) y **no_evaluable**.

### Población principal (n = 21): afirmable con las salvedades del final
| Familia (n) | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 |
|---|---|---|---|---|---|---|---|
| Inundación HTTP (5) | 5 oportuna | 5 | 5 | 5 | 5 | 5 | 5 |
| Fuerza bruta HTTP (5) | 5 oportuna | 5 | 5 | 5 | 5 | 5 | 5 |
| DNS inusual (5) | 2 oportuna, 3 ausencia | 2, 3 | 1, 4 | 5 oportuna | 5 | 5 | 5 |
| Escaneo sostenido (5) | 5 oportuna | 5 | 5 | 5 | 5 | 5 | 5 |
| Escaneo breve (**1**, r4) | solo_posterior | solo_posterior | ausencia | solo_posterior | solo_posterior | solo_posterior | solo_posterior |
| **Total oportunas (de 21)** | **17** | **17** | **16** | **20** | **20** | **20** | **20** |

- **IF solo:** perfecto en inundación, fuerza bruta y escaneo sostenido; en DNS inusual solo 2/5 (0,05 y 0,03) y 1/5 (0,01), y no alerta en r2, r3 y r5 pese a observación suficiente. Bajar α (0,01) pierde un episodio más de DNS.
- **Heurísticos solos:** oportunos en 20 de 21 (los cuatro tipos, DNS incluido); solo fallan en el único escaneo breve de la principal (r4, `solo_posterior`).
- **Híbrido:** 20 de 21 con los tres α; el heurístico cubre el DNS que el IF pierde. Con los datos de esta corrida **HIB no mejora a HEUR** en episodios (20 = 20); la diferencia entre híbrido y heurístico está en el control (abajo).
- **Emisiones oportunas por componente (principal):** al menos una emisión oportuna en 20 de 21 episodios; señal del IF en 17 (inundación 5, fuerza bruta 5, sostenido 5, DNS 2), regla prevista para la familia en 20, otra regla en 0.

### Exploratorios (4 escaneos breves fuera de la principal): no entran en ningún recuento principal
| Config. | r1 | r2 | r3 | r5 |
|---|---|---|---|---|
| IF 0,05 / HIB 0,05 | solo_posterior | solo_posterior | **oportuna** (3,13 s) | solo_posterior |
| IF 0,03 / HIB 0,03 | solo_posterior | solo_posterior | solo_posterior | solo_posterior |
| IF 0,01 | no_evaluable | no_evaluable | solo_posterior | no_evaluable |
| HEUR / HIB 0,01 | solo_posterior | solo_posterior | solo_posterior | solo_posterior |

Lectura: el barrido breve (~5 s) casi nunca se detecta a tiempo con ninguna configuración; solo r3 lo hace con α = 0,05. Es una observación sobre 4 episodios sin observación completa: **no concluye**.

### Control (tráfico legítimo, 21:23–21:53Z): falsas alarmas
Población C0 completa del control: **2 218 ventanas**, todas C0 (Suricata sin descartes). Es una medida distinta de la principal de episodios y no depende de la exclusión de los escaneos breves.

| Config. | Falsas alarmas | Tasa |
|---|---|---|
| IF 0,05 / HIB 0,05 | 323 | 14,56 % |
| IF 0,03 / HIB 0,03 | 200 | 9,02 % |
| IF 0,01 / HIB 0,01 | 54 | 2,43 % |
| HEUR | 0 | 0,00 % |

El heurístico no añade falsas alarmas al híbrido (HIB = IF en el control): su coste en falsas alarmas lo marca el α del IF.

## Salvedades que deben acompañar a cualquier cita
1. **Una sola corrida** de 5 repeticiones por familia, en un laboratorio y en **modo sombra**: no se mide respuesta aplicada ni tiempos de aplicación (eso es la Campaña B).
2. **Escaneo breve: n = 1** en la principal; su duración (~5 s con `nmap -n`) es consecuencia de un cambio de diseño del 9-nov y no es comparable con el escaneo breve de la 3B.
3. **α no elegido**: IF_0,05 tiene 14,56 % de falsas alarmas en control; IF_0,01 las reduce a 2,43 % pero pierde un episodio de DNS más.
4. Las categorías «oportuna» dependen del horizonte y de las ventanas definidas en `analizar_3b.py` (hash fijado); este informe no las redefine.
5. El espejo SPAN tuvo cortes durante la sesión del 9-nov; en la ventana de esta corrida el análisis de salud no encontró huecos (anillo/vía C0, 25 episodios C0).
6. **Procedencia de los umbrales:** el analizador deja constancia de `procedencia: no_verificada` («fuente no accesible aquí: …/calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json»). Los tres α usados son los de `config-campana-4c.json` (verificados contra la calibración en la preparación, según el protocolo 4C); el umbral desplegado en el motor es −0,56940, prácticamente el de α = 0,05 (−0,56946). El orden `IF_0.01 ⊆ IF_0.03 ⊆ IF_0.05` se respeta.
7. Las tres corridas **canceladas** del 9-nov (X1, X3, X3) se analizan aparte (`../etapa4-4c-ajustes-2026-11-09/INFORME-TRES-BATERIAS-CANCELADAS-2026-11-09.md`) y **no se mezclan** con estos resultados.
