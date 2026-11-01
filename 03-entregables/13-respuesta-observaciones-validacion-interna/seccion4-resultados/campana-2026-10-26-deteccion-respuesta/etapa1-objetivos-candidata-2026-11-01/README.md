# Etapa 1 de 5 · Objetivos y criterios de la candidata (1-nov-2026)

Esta etapa contiene **solo** criterios, el diseño de la evaluación y la documentación. No se implementaron mejoras, no se desplegó nada, no se ejecutaron ataques ni controles y no se activó el enforcement. Los resultados anteriores (3A, 3B y su revisión) se conservan sin cambios.

> **Estado: protocolo NO congelado.** Quedan 8 decisiones de Mark (D1–D8). Esta etapa **no autoriza** cambios desplegados, nuevas campañas ni bloqueos.

## Contenido

| Fichero | Qué contiene |
|---|---|
| [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) | Objetivo operativo; separación de las campañas A y B; marcas t_inicio…t_efecto; métricas; calidad de la evidencia (C0–C3); criterio cuantitativo (Clopper-Pearson); fallos del experimento frente a fallos del detector; **decisiones pendientes D1–D8** |
| [MATRIZ-ESCENARIOS.md](MATRIZ-ESCENARIOS.md) | Los 7 elementos para cada uno de los 5 escenarios, con su estado (definido / provisional / pendiente) |
| [PRESUPUESTO-TEMPORAL.md](PRESUPUESTO-TEMPORAL.md) | La cadena captura → efecto, con cada valor clasificado (medido / configurado / estimado / desconocido); el presupuesto por episodio; las variantes V0/V1/V2; la incompatibilidad del escaneo breve |
| [PRESUPUESTO-FALSAS-ALARMAS.md](PRESUPUESTO-FALSAS-ALARMAS.md) | Cuatro medidas separadas (M1–M4); referencia del control 3B por α; presupuesto provisional P1–P5 |
| [DISENO-VALIDACION.md](DISENO-VALIDACION.md) | Recorrido de las Etapas 2–5 con condiciones de entrada, parada, salida y reversión; congelación; tráfico normal nuevo |
| [REFERENCIAS.md](REFERENCIAS.md) | Commits consultados de ambos repos; versiones desplegadas frente a las del repo; cadencias medidas |
| `herramientas/presupuesto_e2e.py` | Simulador de la cadena (solo lectura) con el código **desplegado** extraído literalmente |
| `herramientas/tablas_e2e.py` | Genera `resultados/TABLAS-E2E.md` |
| `pruebas/test_presupuesto_e2e.py` | 17 comprobaciones, 0 fallos. El simulador reproduce **exactamente** el feed y el estado de escalada finales reales del 3B. |
| `codigo-desplegado/` | `publicar_feed.py` f7bc4c7d, `escalada.py` 7d80ab4a y `agente_enforce.py` 2985c123, tal como están en el sensor y en srv-dmz |
| `resultados/` | `presupuesto-e2e.json`, `TABLAS-E2E.md`, `presupuesto-e2e.stdout` |
| `MANIFIESTO.sha256` | sha256 de todos los ficheros de la carpeta (`sha256sum -c MANIFIESTO.sha256`) |

## Reproducir (solo lectura)

Lo ejecuto yo: `[LAPTOP Git Bash]`, desde esta carpeta.

```bash
B=..; X="$B/ejecucion-3b-2026-11-01/evidencia"
python -I herramientas/presupuesto_e2e.py --marcas "$X/bastion/kali/corrida/marcas.jsonl" \
  --decisiones "$X/sensor/copias/motor_decision.log.gz" --ciclos "$X/sensor/copias/ciclos.jsonl" \
  --analisis "$B/revision-3b-2026-11-01/resultados/analisis-revisado/analisis-3b.json" \
  --control "$X/sensor/control-declarado.json" --publicador codigo-desplegado/publicar_feed.py \
  --escalada codigo-desplegado/escalada.py --salida resultados/presupuesto-e2e.json
python -I herramientas/tablas_e2e.py
python -I pruebas/test_presupuesto_e2e.py
sha256sum -c MANIFIESTO.sha256
```

---

## Explicación sencilla

### 1. Qué debe demostrar la candidata

Que, ante cada tipo de ataque, el sistema **detecta y aplica la restricción en el servidor antes de que el ataque termine**, y que esa restricción **tiene efecto**, todo ello sin castigar a los usuarios legítimos.

Para afirmarlo con un 95 % de confianza y una tasa mínima del 80 % hacen falta unos **14 episodios válidos por tipo de ataque**, sin fallos (o 22 con un fallo como máximo, si se decide así de antemano). Con las 5 repeticiones actuales solo se puede describir lo ocurrido, no demostrarlo.

### 2. Qué lo impide hoy

- **Escaneo breve (≈ 18 s):** la cadena actual llega siempre tarde (0/5). Ni siquiera una cadena instantánea bastaría (1/5, y por una señal equivocada): la señal aparece en la 2.ª o 3.ª ventana de 10 s. Hace falta cambiar a la vez la captura y la cadena (Etapa 2) y el heurístico (Etapa 3).
- **DNS inusual:** no hay dónde aplicar la respuesta. El ataque va a DC1 y el agente solo existe en srv-dmz.
- **Falsas alarmas:**
  - Con el IF convertido en LIMIT, el control normal de 33 min habría restringido entre 3 y 9 clientes legítimos, algunos durante casi todo el control, con cualquiera de los tres α.
  - El heurístico DNS dispara 88 veces sobre el propio resolvedor.
- **Contaminación entre episodios:** la escalada guarda la memoria. El atacante del laboratorio ya estaba en el nivel 3, así que con el agente activo 24 de los 25 episodios habrían empezado ya bloqueados.
- **Evidencia:** los descartes de Suricata dejaron fuera 9 de 25 episodios, y de la inundación HTTP solo se admitió 1.
- **Medición:** hoy no se registra cuándo aplica el agente (t_apl) ni si la regla corta algo (t_efecto), porque las reglas no llevan `counter`.

### 3. Decisiones pendientes (Mark)

| Id | Decisión |
|---|---|
| D1 | Punto de aplicación para el DNS (o dejarlo solo como detección) |
| D2 | Objetivo del escaneo breve |
| D3 | Qué hace el IF ante una anomalía (LIMIT, solo señal, persistencia) |
| D4 | Evidencia mínima y número de episodios (propuesta: 0,80 al 95 %, n = 14 o 22 con ≤ 1 fallo) |
| D5 | Limpieza verificada del estado y de las reglas entre episodios |
| D6 | Presupuesto operativo de falsas alarmas (propuesta P1–P5) |
| D7 | Activar el agente y añadir contadores nft |
| D8 | Duración de referencia de nmap (propuesta: la mínima observada) |

### 4. Siguiente trabajo concreto de la Etapa 2 (sin desplegar hasta que Mark lo decida)

1. **Causa de los descartes de Suricata:**
   - correlacionar `kernel_drops` con CPU, hilos y ring de af-packet en los 21 intervalos con descartes del 3B (los datos ya están en `revision-3b/diagnosticos/suricata-descartes.json`);
   - proponer la configuración, cuyo cambio decide Mark.
2. **Instrumentación de la cadena** en la rama candidata:
   - t_pub (lectura y escritura del feed);
   - t_apl (hora y retorno del commit nft, lote y lectura del set);
   - `counter` en las reglas;
   - corregir `--umbrales` y el comentario del relé;
   - pruebas unitarias.
3. **Prototipo offline** de la captura y la cadena por eventos (lectura incremental del PCAP con la regla de paquetes decodificados, ciclo por inotify, publicación por push):
   - medir con los PCAP del 3B la cota del peor caso por episodio;
   - exigir la equivalencia de las **28 características** frente al motor actual.
4. **Procedimiento de limpieza entre episodios** (D5): retirada verificada del estado de escalada y de los sets, escrito y probado en seco, sin activar el agente.
