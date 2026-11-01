# Etapa 1 de 5 · Objetivos y criterios de la candidata (versión 2, 1-nov-2026)

**Versión 2:** corrige y consolida la versión 1 (`2482a40`). Los cambios están en [CAMBIOS-RESPECTO-2482a40.md](CAMBIOS-RESPECTO-2482a40.md).

**Qué se hizo:** solo criterios, el diseño de la evaluación, el simulador offline y la documentación.

**Qué no se hizo:**

- no se modificó el producto desplegado, ningún servicio ni el modelo, los umbrales o las reglas;
- no hubo controles, ataques ni campañas;
- el agente sigue **inactivo**;
- no se editó el Word ni se sobrescribió ninguna evidencia histórica.

> **El protocolo de evaluación NO está congelado.** Quedan pendientes esenciales: **D1** (punto de aplicación DNS en DC1: cambio de alcance), **D3** (política del IF) y **D6** (cifras del presupuesto de falsas alarmas). Detalle en la [matriz única de decisiones](DECISIONES.md).

## Diseño adoptado

- **25 episodios por campaña, 5 por escenario** ([D4](DECISIONES.md), decidida por el usuario): una campaña A (sombra) y una campaña B (respuesta), cada una con 25 episodios nuevos de la candidata congelada.
- **Meta de desarrollo:** detección y respuesta oportunas en los 25 episodios. Es una meta que se comprueba, no una garantía.
- Se publican todos los fallos, exclusiones y resultados tardíos.

## Contenido

| Fichero | Qué contiene |
|---|---|
| [DECISIONES.md](DECISIONES.md) | **Matriz única D1–D8**: estado, recomendación, fundamento, consecuencias y etapa; comparación de puntos de aplicación DNS; comparación de políticas del IF |
| [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) | Objetivo; poblaciones y unidades; campañas A y B; marcas y métricas; **cumplimiento por episodio E1–E5**; diseño de 25; fallos del experimento y del detector; calidad de la evidencia (C0–C3 corregidas) |
| [MATRIZ-ESCENARIOS.md](MATRIZ-ESCENARIOS.md) | Los 5 escenarios × elementos; regla prevista; errores de atribución del 3B |
| [PRESUPUESTO-TEMPORAL.md](PRESUPUESTO-TEMPORAL.md) | Tramos con su clase (M/C/S/D); modelo de la cadena con consumidor perdido; escenarios favorable y alto; escaneo breve por tramos |
| [PRESUPUESTO-FALSAS-ALARMAS.md](PRESUPUESTO-FALSAS-ALARMAS.md) | M1–M4; control 3B por política × α (restricciones hipotéticas, con renovaciones); propuesta P1–P5 |
| [DISENO-VALIDACION.md](DISENO-VALIDACION.md) | Recorrido de 6 pasos; trabajo offline de la Etapa 2 que puede empezar ya; dependencias |
| [REFERENCIAS.md](REFERENCIAS.md) | HEAD y commits consultados; versiones desplegadas frente a las del repo; cadencias |
| [CAMBIOS-RESPECTO-2482a40.md](CAMBIOS-RESPECTO-2482a40.md) | Observación → corrección → evidencia |
| `herramientas/presupuesto_e2e.py` | Simulador v2 (solo lectura) con el código desplegado extraído literalmente |
| `herramientas/tablas_e2e.py` | Genera `resultados/TABLAS-E2E.md` |
| `pruebas/test_presupuesto_e2e.py` | 31 comprobaciones offline, 0 fallos; el docstring enumera los campos comparados con el feed y el estado reales |
| `codigo-desplegado/` | publicador f7bc4c7d, escalada 7d80ab4a y agente 2985c123 (sin cambios) |
| `resultados/` | `presupuesto-e2e.json`, `TABLAS-E2E.md`, `presupuesto-e2e.stdout` (regenerados) |
| `MANIFIESTO.sha256` | sha256 de todos los ficheros (`sha256sum -c MANIFIESTO.sha256`) |

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
python -I -B pruebas/test_presupuesto_e2e.py
sha256sum -c MANIFIESTO.sha256
```

## Explicación sencilla

1. **Qué debe demostrar la candidata.** En cada uno de los 25 episodios de la campaña B:
   - que detecta el ataque con la regla correcta mientras dura;
   - que la restricción se aplica de verdad en el servidor antes del fin;
   - que corta o limita el ataque mientras el atacante sigue intentándolo;
   - que no perjudica a los usuarios legítimos;
   - que la restricción se retira bien.

   En la campaña A (sombra) se compara la detección de los detectores con el ataque completo. Con 5 episodios por escenario se describe lo que pasa y su incertidumbre; no se promete una tasa.
2. **Qué lo impide hoy.**
   - **Escaneo breve:** la regla tiene evidencia en ventanas que cierran después del fin, y la captura y la cadena añaden 15–28 s. Hacen falta las dos mejoras a la vez.
   - **DNS:** no hay dónde aplicar la respuesta; la recomendación es actuar en DC1.
   - **Tráfico legítimo:** si el IF restringe por sí solo, afecta a entre 3 y 9 clientes legítimos en 33 min (hipotético). Si solo señala, a uno, por un heurístico que hay que corregir.
   - **Errores de atribución:** `brute_force` durante escaneos, `port_scan` en la inundación y `dns_entropy` sobre el resolvedor.
   - **Calidad de la evidencia:** los descartes de Suricata, que también afectan al IF.
   - **Medición:** faltan registros de aplicación y contadores.
3. **Decisiones pendientes esenciales:** D1 (agente en DC1), D3 (que el IF solo señale) y D6 (cifras del presupuesto de falsas alarmas). D5, D7 y D8 tienen recomendación; D2 y D4 están decididas.
4. **Siguiente trabajo de la Etapa 2** (offline, sin desplegar; detalle en [DISENO-VALIDACION.md](DISENO-VALIDACION.md)):
   - diagnosticar los descartes de Suricata;
   - prototipo de captura incremental con ciclo por eventos, comparando las 28 características;
   - cadena por eventos e instrumentación en la rama candidata;
   - medir el escaneo breve por tramos con el prototipo;
   - empezar la regla temprana de escaneo, la atribución DNS al cliente y la separación del abuso HTTP, con regresiones;
   - escribir el procedimiento de limpieza D5 y ensayarlo en seco.
