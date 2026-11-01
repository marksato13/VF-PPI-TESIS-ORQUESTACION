# Paso 2 — protocolo técnico fijado antes de generar carga

Identificador: `20261101T0254Z`. Fijado el 2026-11-01 a las 03:17 UTC, antes de la primera inundación. Este fichero
se guarda en el sensor (`~/cf-paso2-20261101T0254Z/PROTOCOLO-PASO2.md`) con su sha256 antes de la carga y no se
modifica después; cualquier desviación se documenta aparte en el informe.

Estas son **pruebas de ingeniería del motor**. No son episodios de la campaña A ni de la B, no usan su generador de
25 episodios y sus resultados no se mezclan con los confirmatorios.

## Versiones

| Elemento | Valor |
|---|---|
| Motor instalado | `motor_decision.py` `6c274d9e…` + `motor_incremental.py` `a403307a…` (código `24f8a80`) |
| Motor anterior (reversión) | `e2b2eb53…` (7b275b8), copia en `~/cf-paso2-20261101T0254Z/respaldo-operativo/` |
| Modelo / manifiesto | `if_limpio_2026_10_desplegable.joblib` `df547da0…` / `manifest-if-limpio-2026-10.json` `b3ad6805…` |
| Umbral operativo | −0,5693969936 (registro de arranque); no se cambia |
| Esquema desplegado | `multilayer-v2.json` `e032a1a2…` (se conserva; el del commit, `1445ccd4…`, no se instala) |
| Heurísticos / extractores | `10deb05d…` / v2 `7130edae…`, v3 `5adbfbf4…` |
| Argumentos | idénticos a los iniciales (`--step-seconds 10 --history-seconds 230`, sin `--enforce`) |
| Captura / IDS | tcpdump 4.99.4 en ens37, ficheros de 15 s; Suricata 7.0.3 |
| Generador de ataque | `generar_campana.py` `c586d813…`, `esquema_campana.py` `e762e604…`, `escenarios.json` `67798012…` |
| Generador legítimo | `clientes_lab.py` `ae5134a7…` sin modificar, con el envoltorio `clientes_factor1.py` `69d79937…` |
| Archivador | `archivar_captura.sh` `2181af5f…`, intervalo 20 s |

## Carga

**Legítima.** Seis perfiles (.21–.26) con los argumentos de sus unidades y factor horario fijado en 1,0 (hora punta de
un día laborable). Arrancados a las 03:03:25 UTC.

**Ataque.** Escenario `inundacion_http` con el comando del constructor aprobado: origen Kali 10.10.20.30, destino
`http://10.10.30.10/`, 8 bucles concurrentes de `curl -s -o /dev/null --max-time 2` durante 90 s, timeout de
seguridad 150 s. Tres repeticiones técnicas (`T1`, `T2`, `T3`) con `kali_episodio_tecnico.py`, que llama a
`generar_campana.correr_episodio` sin modificarlo. No se cambia la intensidad.

## Secuencia e intervalos

| Fase | Inicio | Fin |
|---|---|---|
| Calentamiento tras reinicio | 03:14:01 | 03:17:51 (230 s) |
| Preparación (HTTP, HTTPS, auth; marcadas) | 03:15:43 | contexto de 230 s hasta 03:19:34 |
| **Normal evaluado** | **03:20:00** | inicio real de T1 (≥ 30 min, no antes de 03:50:00) |
| T1, T2, T3 | inicio y fin reales de las marcas del generador | |
| Recuperación tras cada Tk | fin real de Tk | fin real + 230 s |
| Cierre final | fin de la recuperación de T3 | +10 min de contexto posterior antes de parar el archivador |

Un episodio solo empieza si se cumplen las cuatro condiciones siguientes:
- han pasado ≥ 230 s desde el fin real del anterior;
- los 6 últimos ciclos duran menos de 9,5 s;
- `ventanas_pendientes` no crece;
- no queda ningún `curl` en la Kali.

## Condiciones para el análisis (por `inicio_ciclo` de cada ciclo)

- **calentamiento**: [reinicio, reinicio + 230 s]
- **normal**: [03:20:00, inicio T1)
- **inundación Tk**: [inicio real Tk, fin real Tk]
- **recuperación Tk**: (fin real Tk, fin real Tk + 230 s]
- **entre episodios / cierre**: el resto. Se informa aparte y no se suma a «normal».

## Métricas

Por condición y por repetición:

1. **Duración del ciclo.** Número de ciclos, p50, p95 y máximo; ciclos de más de 9,5 s y de más de 10 s, todos listados.
2. **Tiempo por etapa.** p50, p95 y máximo de `etapas_s`.
3. **Disponibilidad de los datos.** `marca_pcap` y `marca_eve` frente a `inicio_ciclo`.
4. **Inventario de ventanas.** Decididas, pendientes, no evaluadas y ausentes:
   - la referencia es una repetición offline del mismo motor sobre el PCAP archivado y el segmento EVE conservado (`replay_motor.py`);
   - una ventana es «ausente» si la referencia la decide y en vivo no hay ni decisión ni `ventana_no_evaluada`.
5. **Retraso.** `decidido_en − window_end` y `registro_escrito_en − window_end`, como cota superior de la disponibilidad del registro.
   - La precisión depende del reloj del sensor (NTP, desfase < 1 ms frente al bastión).
   - La duración del ciclo **no** es una latencia de detección.
6. **Recursos.** CPU del motor, RSS, memoria disponible, swap (pswpin/pswpout), PSI de memoria y errores del journal.
7. **Archivado y descartes.** Estado del archivador (vistos/archivados/perdidos); `rx_drop` de ens37; `capture.kernel_drops` de Suricata (stats.log).
8. **Tráfico observado.** Peticiones y respuestas HTTP del episodio en el EVE (origen 10.10.20.30 → 10.10.30.10:80), separadas de los intentos del generador.
9. **Duplicados.** Claves `(entity_ip, window_end_utc)` en el registro vigente y en el rotado, separando las anteriores a la instalación de las nuevas.

## Criterios de aceptación (alcance probado)

- Sin fallos del motor ni de las fuentes: servicio activo, sin trazas, captura y Suricata activos, archivador sin pérdidas.
- 0 duplicados nuevos y 0 ventanas ausentes sin explicar.
- Duración del ciclo por debajo de 10 s en todas las condiciones, incluida la inundación. Se informan todos los ciclos de más de 9,5 s y el margen; no basta con el p95.
- Sin acumulación creciente de retraso ni de pendientes; recuperación comprobada tras cada inundación.
- Sin agotamiento de memoria: swap sin actividad (pswpout sin cambios) y memoria disponible > 1 GB.
- Evidencia completa y atribución temporal comprobable.

**La detección se evalúa aparte y no forma parte de la aceptación del rendimiento.** Se informa qué señal emitió el
motor (`ALERT` del modelo con los tres α comparativos solo como lectura, o un heurístico) para la entidad
10.10.20.30, con sus tiempos. No se cambia el umbral, no se elige α y no se prolonga la carga.
