# Comandos de la revisión 3B, en orden

**Alcance.** Solo se han leído los datos originales. En el sensor se escribió únicamente en un directorio nuevo,
`/home/m4rk/cf-3b-revision-20261101`. No se lanzaron ataques ni se tocaron servicios, configuración, motor ni
cortafuegos, y no se usó sudo.

**Variables de los comandos.**

- `E` = `../ejecucion-3b-2026-11-01/evidencia/sensor`.
- `S` = copia local descomprimida de `$E/copias/motor_decision.log.gz` y `$E/replay/motor_decision.log.gz`, con los
  mismos sha256 que en el sensor (`bf51f308…` y `4b93caa4…`; véase `resultados/sensor/sha256-entradas.txt`).

## 0. Criterios publicados antes del reanálisis

`[LAPTOP Git Bash]` → lo ejecuté yo. El commit `191b043` contiene solo `CRITERIOS-REVISION.md` y `.gitattributes`.

## 1. Pruebas

`[LAPTOP Git Bash]` → lo ejecuté yo, desde `campana-2026-10-26-deteccion-respuesta/`.

```
python -I revision-3b-2026-11-01/pruebas/test_revision_3b.py            # OK: 36 comprobaciones
python -m pytest -q revision-3b-2026-11-01/pruebas/test_revision_3b.py  # 9 passed
python tests/test_analizar_3b.py                                          # OK: 90 comprobaciones (sin cambios)
python tests/test_herramientas.py                                         # 222 comprobaciones pasaron (sin cambios)
python tests/regresion_alfa.py                                            # 0 diferencias en 7 configuraciones
```

`test_herramientas.py` se ejecuta sin `-I` porque importa `regresion_alfa` desde su propio directorio. Las pruebas
existentes no se han modificado.

## 2. Sensor: respaldos v2, integridad v2 y recálculo v2

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo, con las llaves del bastión y sin contraseñas.

```
bash r.sh s70_revision_sensor.sh sensor   # guiones/s70_revision_sensor.sh (herramientas v2 embebidas en base64)
```

El guion copia las herramientas originales desde `~/cf-3b-20261101T0721Z/herramientas` (mismos hashes que en
`REFERENCIAS-Y-HASHES.md` del 3B) y comprueba sus hashes en `resultados/sensor/sha256-herramientas.txt`. Después:

- ejecuta `generar_respaldos_v2.py` (que llama a la v1 sin cambios en `_v1/`);
- ejecuta `verificar_integridad_v2.py`;
- lanza `recalcular_caracteristicas_v2.py` en segundo plano (`setsid nohup`).

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo. Son lecturas para el diagnóstico de Suricata:

```
bash r.sh s69_config_suricata.sh sensor   # stats.interval = 8 (resultados/sensor/config-suricata-stats.txt)
bash r.sh s71_rafagas_pcap.sh sensor      # ráfagas de 10/100 ms por intervalo de stats -> rafagas-por-intervalo.json
```

Descarga (`[LAPTOP Git Bash]`):

```
ssh gadmin@10.10.10.30 "ssh m4rk@10.10.60.11 'cd ~/cf-3b-revision-20261101 && tar czf - …'" | tar xzf -
```

## 3. Análisis y diagnósticos locales

`[LAPTOP Git Bash]` → lo ejecuté yo, desde `scripts/`, con `analizar_3b.py` sin modificar (`27e67fd1…`).

```
# reproducción del original (idéntico salvo la ruta del inventario)
python analizar_3b.py --marcas $E/copias/marcas.jsonl --motor $S/motor_decision.log --config $E/herramientas/config-campana-3b.json \
  --ciclos $E/copias/ciclos.jsonl --inventario $S/replay.log --inventario-rango "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z" \
  --destinos $E/analisis/destinos-3b.csv --integridad $E/analisis/integridad.json --calidad-fuentes $E/analisis/calidad-fuentes.json \
  --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "campaña A repetida (3B) 2026-11-01" --salida <tmp>
# revisado: los mismos argumentos con --integridad resultados/sensor/integridad-v2.json
#   --salida revision-3b-2026-11-01/resultados/analisis-revisado
```

Desde `revision-3b-2026-11-01/`:

```
python herramientas/comparar_original_revisado.py --original $E/analisis/analisis-3b/analisis-3b.json \
  --revisado resultados/analisis-revisado/analisis-3b.json --motor $S/motor_decision.log --config $E/herramientas/config-campana-3b.json \
  --calidad $E/analisis/calidad-fuentes.json --respaldos-v2 resultados/sensor/respaldos-v2 \
  --integridad-original $E/analisis/integridad.json --integridad-v2 resultados/sensor/integridad-v2.json --salida resultados/comparacion
python herramientas/diagnostico_demora.py --analisis resultados/analisis-revisado/analisis-3b.json --motor $S/motor_decision.log \
  --ciclos $E/copias/ciclos.jsonl --archivador $E/copias/archivar.log --marcas $E/copias/marcas.jsonl --salida diagnosticos/demora.json
python herramientas/diagnostico_suricata.py --stats $E/analisis/suricata-stats.json --rafagas resultados/sensor/rafagas-por-intervalo.json \
  --muestras $E/copias/muestras.jsonl --ciclos $E/copias/ciclos.jsonl --salida diagnosticos/suricata-descartes.json
python herramientas/diagnostico_recalculo.py --v1 $E/analisis/caracteristicas.jsonl --v2 resultados/sensor/caracteristicas-v2.jsonl \
  --config $E/herramientas/config-campana-3b.json --analisis resultados/analisis-revisado/analisis-3b.json \
  --salida diagnosticos/recalculo-v1-v2.json
python herramientas/diagnostico_heuristico_replay.py --vivo $S/motor_decision.log --replay $S/replay.log \
  --salida diagnosticos/replay-vs-vivo.json
```

## 4. Manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
find . -type f ! -name MANIFIESTO.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFIESTO.sha256 && sha256sum -c MANIFIESTO.sha256
```
