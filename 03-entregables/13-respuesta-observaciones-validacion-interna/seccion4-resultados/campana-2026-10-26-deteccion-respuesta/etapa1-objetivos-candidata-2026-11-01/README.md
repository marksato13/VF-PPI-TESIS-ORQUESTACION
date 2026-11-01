# Etapa 1 de 5 · Objetivos y criterios de la candidata (versión 3, 1-nov-2026)

**Versión 3:** consolida las decisiones sobre la versión 2 (`c1de49d`), que corregía la versión 1 (`2482a40`). Cambios en [CAMBIOS-RESPECTO-c1de49d.md](CAMBIOS-RESPECTO-c1de49d.md) y [CAMBIOS-RESPECTO-2482a40.md](CAMBIOS-RESPECTO-2482a40.md).

**Qué se hizo:**

- criterios y diseño de la evaluación;
- simulador offline y documentación;
- verificación del contrato de características;
- estudio de viabilidad de la respuesta DNS en DC1, con consultas de **solo lectura**.

**Qué no se hizo:**

- no se modificó el producto desplegado, ningún servicio ni el modelo, el escalador, los umbrales, las reglas o el vector de entrada;
- no se instaló ningún agente;
- no hubo controles, ataques ni campañas;
- no se activó ninguna restricción;
- no se editó el Word ni se sobrescribió evidencia histórica.

> **El protocolo de evaluación NO está congelado.** Antes de congelar faltan:
>
> - **D1:** las comprobaciones técnicas en DC1 (el punto de aplicación ya está resuelto);
> - **D3:** implementar `if_senal` en la rama candidata (la política ya está adoptada);
> - **D6:** confirmar los valores de LIMIT;
> - confirmar D5, D7 y D8.
>
> Nada está listo para desplegar. Detalle en la [matriz D1–D8](DECISIONES.md).

## Decisiones y estado

| Id | Estado |
|---|---|
| D1 | Punto de aplicación **DC1 resuelto**. DC1 es **Samba 4.22.10 sobre Debian 13**, no Windows: se recomienda **nftables en DC1** limitado a UDP/TCP 53 y al origen. Compatibilidad concreta pendiente; despliegue no autorizado. |
| D2 | **Decidida:** detectar y actuar durante el escaneo breve, sin prolongarlo |
| D3 | **Adoptada `if_senal`**: el IF señala y no restringe por sí solo; α 0,05 / 0,03 / 0,01 conservados |
| D4 | **Decidida:** 25 episodios por campaña, 5 por escenario |
| D5 | Recomendada: limpieza verificada solo del origen de ensayo, en srv-dmz y DC1 |
| D6 | P1 = 0 BLOCK y P4 = 0 transacciones fallidas: **aceptados**. P2 (≤ 1 intervalo por 8 h) y P3 (≤ 1 % del tiempo): **propuesta pendiente** |
| D7 | Recomendada: instrumentar no es activar |
| D8 | Recomendada: `t_fin_eval = min(ref, observado)`; corte por respuesta ≠ fin natural |

**Contrato del IF:** 28 características = L3 9 + L4 8 + L7 11 (17 PCAP + 11 EVE). El esquema ampliado tiene 31 (+3 L2), que el IF no usa. [CONTRATO-CARACTERISTICAS.md](CONTRATO-CARACTERISTICAS.md).

## Contenido

| Fichero | Qué contiene |
|---|---|
| [DECISIONES.md](DECISIONES.md) | Matriz única D1–D8 en tres planos (alcance o diseño / compatibilidad pendiente / autorización futura); política D3 consolidada |
| [D1-VIABILIDAD-DC1.md](D1-VIABILIDAD-DC1.md) | Informe de viabilidad de la respuesta DNS en DC1, con evidencia y referencias oficiales |
| [CONTRATO-CARACTERISTICAS.md](CONTRATO-CARACTERISTICAS.md) | Contrato 28/31 y comprobación reproducible |
| [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) | Objetivo; poblaciones y unidades; marcas; E1–E5 (E1 con tres resultados); diseño de 25; fallos; calidad de la evidencia |
| [MATRIZ-ESCENARIOS.md](MATRIZ-ESCENARIOS.md) | Los 5 escenarios; regla prevista; punto de aplicación (DNS en DC1) |
| [PRESUPUESTO-TEMPORAL.md](PRESUPUESTO-TEMPORAL.md) | Tramos y clases; cadena con consumidor perdido; escaneo breve por tramos |
| [PRESUPUESTO-FALSAS-ALARMAS.md](PRESUPUESTO-FALSAS-ALARMAS.md) | M1–M4; control 3B por política y α; presupuesto D6 y cómo se medirá |
| [DISENO-VALIDACION.md](DISENO-VALIDACION.md) | Recorrido de 6 pasos; **trabajo offline de la Etapa 2 en orden** |
| [REFERENCIAS.md](REFERENCIAS.md) | HEAD, commits y lecturas en vivo |
| `herramientas/presupuesto_e2e.py` v3 · `tablas_e2e.py` v3 · `contrato_caracteristicas.py` | Simulador, tablas y contrato (solo lectura) |
| `pruebas/test_presupuesto_e2e.py` | 43 comprobaciones offline, 0 fallos |
| `contrato/` | esquemas v2 y v3, extractor y manifiesto desplegado; lectura del sensor |
| `d1-dc1/` | scripts y salida de las lecturas de DC1 y del bastión |
| `codigo-desplegado/` | publicador, escalada y agente desplegados (sin cambios) |
| `resultados/` | `presupuesto-e2e.json`, `TABLAS-E2E.md`, `presupuesto-e2e.stdout`, `contrato-caracteristicas.json` |
| `MANIFIESTO.sha256` | sha256 de todos los ficheros |

## Reproducir (solo lectura)

Lo ejecuto yo: `[LAPTOP Git Bash]`, desde esta carpeta.

```bash
B=..; X="$B/ejecucion-3b-2026-11-01/evidencia"; export PYTHONDONTWRITEBYTECODE=1
python -I -B herramientas/presupuesto_e2e.py --marcas "$X/bastion/kali/corrida/marcas.jsonl" \
  --decisiones "$X/sensor/copias/motor_decision.log.gz" --ciclos "$X/sensor/copias/ciclos.jsonl" \
  --analisis "$B/revision-3b-2026-11-01/resultados/analisis-revisado/analisis-3b.json" \
  --control "$X/sensor/control-declarado.json" --publicador codigo-desplegado/publicar_feed.py \
  --escalada codigo-desplegado/escalada.py --salida resultados/presupuesto-e2e.json
python -I -B herramientas/tablas_e2e.py
python -I -B herramientas/contrato_caracteristicas.py --esquema contrato/multilayer-v2.json \
  --ampliado contrato/multilayer-v3.json --manifiesto contrato/manifest-if-limpio-2026-10.json \
  --extractor contrato/extract_multilayer_v2.py --salida resultados/contrato-caracteristicas.json
python -I -B pruebas/test_presupuesto_e2e.py
sha256sum -c MANIFIESTO.sha256
```

## Poblaciones (no se mezclan)

| Población | n | Uso |
|---|---|---|
| 3B original | 25 ejecutados | histórico |
| Revisión del 3B | 15 admitidos | histórico |
| Control normal del 3B | 22 entidades, 33 min, con restricciones **hipotéticas** simuladas | desarrollo |
| Futura campaña A (sombra, detección) | 25 nuevos | prueba |
| Futura campaña B (respuesta) | 25 nuevos | prueba |

Las simulaciones no son aplicaciones reales: `t_apl` real y `t_efecto` valen «no aplica», y las demoras desconocidas (activación nft y efecto) no se suman como cero.

## Siguiente trabajo (Etapa 2, offline, en orden)

1. Diagnosticar los descartes de Suricata.
2. Prototipo de captura más rápida y evaluación por eventos (mismas 28 entradas en las mismas ventanas).
3. Instrumentar la publicación, la distribución y la aplicación (srv-dmz y DC1).
4. Presupuesto completo del escaneo breve (depende de 2 y 3).
5. Regresiones de atribución DNS al cliente y de separación HTTP/escaneo.
6. Limpieza D5 ensayada en seco.
7. D1: ensayo de las reglas nft de DC1 fuera de DC1.
8. D1: agente de DC1 en la rama candidata (depende de 7).
9. D3: `if_senal` en el publicador candidato.

Detalle en [DISENO-VALIDACION.md](DISENO-VALIDACION.md).
