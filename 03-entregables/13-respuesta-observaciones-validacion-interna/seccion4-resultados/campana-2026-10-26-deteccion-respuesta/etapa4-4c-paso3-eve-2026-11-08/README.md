# Paso 3 de `s50` para la 4C: Suricata por EVE en vez de `stats.log` (2026-11-08)

**Estado: LISTO PARA REVISIÓN (08-nov, revisado de nuevo sin cambios en el guion). NO publicado, NO instalado, NO usado.** Es solo para la 4C; la 4B no ejecuta el paso 3.
La 4C usa el mismo `s40` que la 4B: si se instala el `s40` v2 de `../etapa4-4b-enmienda-p1-2026-11-08/guiones/` (copias comprobadas), también rige para la 4C; este paso 3 no depende de él.
Depende de la enmienda P1 de la 4B ([`../etapa4-4b-enmienda-p1-2026-11-08/`](../etapa4-4b-enmienda-p1-2026-11-08/README.md), publicada).

## Diagnóstico

El paso 3 de `s50` (4C) construía `suricata-stats.json` leyendo `capture.kernel_drops` de `stats.log`. Suricata 7 no escribe ese contador cuando vale 0.
Lectura real del Sensor1 (08-nov 13:3xZ, `evidencia/diagnostico-real-stats-log-y-eve.txt`): 326 bloques en la cola de `stats.log`, **0 líneas `capture.kernel_drops`**, 0 muestras
con paquetes y descartes; el mismo paso 3 original sale «sin muestras de stats.log…». En el EVE real, 400 de 400 eventos `stats` traen `kernel_drops` (0 en todos).
Consecuencia en la 4C: el paso 3 falla y quedan **omitidos 5, 6 y c** (respaldos, integridad y análisis), con resultado PARCIAL; y el paso 7 original da C3 en todos los episodios.

## Corrección

`guiones/s50_analisis_e4.sh` = el `s50` enmendado de la 4B con el paso 3 leyendo los eventos `stats` del segmento EVE (`copias/eve-segmento.json`), mismo formato de salida
(`momento`, `timestamp`, `kernel_packets`, `kernel_drops`) más `uptime_s` y `arranque_estimado`. Los eventos sin contadores completos se cuentan y se omiten (nunca se escriben como cero);
un EVE ilegible, con líneas stats inválidas o contradictorias, o sin ningún evento con `kernel_drops`, hace fallar el paso (y los dependientes quedan omitidos). Solo difiere del `s50` de la 4B en la cabecera y en `p_3`.
`generar_respaldos.py` no cambia: sigue calculando el delta con la primera y la última muestra del periodo, sin detectar reinicios ni huecos; eso lo cubre la clasificación C0/C1/C3 del paso 7, que sí usa la medida EVE completa.

## Pruebas (banco, sin red, usuario 65534): 11 comprobaciones, todas OK (`evidencia/banco-4c-s50.txt`)

| Corrida | Resultado |
|---|---|
| R1 · guion 4C, EVE con ráfaga de 23 descartes y hueco de 100 s | rc 0, COMPLETO; paso 3 OK; 5, 6, c y 7 OK; episodios C0 / C1 (`descartes`) / C3 (`cobertura_insuficiente`); el consumidor ve +23 solo en el periodo del episodio con la ráfaga |
| R2 · guion ORIGINAL con `stats.log` sin `kernel_drops` (como el real) | rc 1, PARCIAL; paso 3 en fallo; 5, 6 y c omitidos; paso 7 original C3 en los tres episodios (defecto reproducido) |
| R3 · EVE con una línea stats corrupta | rc 1; paso 3 en fallo con el motivo; 5, 6, c y 9 omitidos; sin `SHA256SUMS` completo |
| R4 · EVE sano | rc 0; los tres episodios C0 / `cero_explicito` |
| D1 | el guion difiere del de la 4B solo en comentarios y en `p_3` |

**Límites:** las herramientas de análisis de los pasos 1, 2, 4, 5, 6, 8, 9 y c son dobles que escriben su salida (como `ensayo_errores_s50_r4.sh`); se prueban de verdad el paso 3, el paso 7, la verificación de hashes y la propagación de errores. Datos de salud y EVE sintéticos.
No se ejecutó la 4C completa en el banco.

## Hashes

| Fichero | sha256 (16) |
|---|---|
| `guiones/s50_analisis_e4.sh` | `7477f4c5ae651a4c` |
| `tests/banco_4c_s50.sh` | `cc6d8a475adfd81e` |

Sigue pendiente, aparte de esto: **I5** (0 `kernel_drops` en los 30 min previos al inicio real de la 4C, con `salud_captura i5`) y el resultado de la 4B.
