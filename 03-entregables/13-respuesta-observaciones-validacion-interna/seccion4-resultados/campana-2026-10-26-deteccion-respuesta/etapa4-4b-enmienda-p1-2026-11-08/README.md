# Enmienda P1 a la 4B: Suricata medido por EVE `stats` (2026-11-08)

**Estado: preparada y probada en banco. NO publicada, NO instalada, NO usada.** La publicación y la orden de inicio de la 4B las confirma Mark por separado.
Original sin cambios: [`PROTOCOLO-4B-CONTROL.md`](../etapa4-reconciliacion-2026-11-03/documentos-corregidos/PROTOCOLO-4B-CONTROL.md) y `etapa4-preparacion-2026-11-02/guiones/`.

## 1. Defecto que corrige

`stats.log` de Suricata 7 no escribe `capture.kernel_drops` cuando vale 0. Los guiones de la 4B (`s10`, `s50`) y `control_4b.py` usaban la
`salud_captura` congelada (`ec78ca5`, 2026-11-02.2), que lee `stats.log` y devuelve «sin bloque con capture.kernel_drops» = «Suricata sin medida» = **C3 en toda ventana**.
Lectura real del Sensor1, 08-nov 13:38Z: la congelada da `{"ok": false}`; la de P1 (2026-11-06.1, EVE) da `cero_explicito` con 513 724 paquetes en 30 min.
El banco lo reproduce: con los guiones originales, las 2 644 ventanas del control del 3B salen C3 y ninguna C0.

## 2. Qué cambia (y qué no)

| Fichero | Cambio |
|---|---|
| `guiones/s10_sensor_archivo_e4.sh` | El muestreador de salud es `~/cyberflow-e4/herramientas-20261106/salud_captura.py` (hash fijado `274b4d61…`, y su `SHA256SUMS` verifica). **Antes de crear nada** exige una medida EVE de Suricata (`cero_explicito` o `descartes`); `ausente`, `desactualizada`, `error_lectura` o `cobertura_insuficiente` = PARAR. Guarda `salud/suricata-eve-inicio.json` |
| `guiones/s50_analisis_e4.sh` | `SC` es la de P1 con hash fijado; exige `copias/eve-segmento.json` (lo copia `s30`). Pasos `a2` y `a3` (periodo completo) llevan `--suricata-eve`; el paso `b` también; el paso `7` (4C) mide Suricata por episodio con EVE. Imprime el estado de Suricata de cada periodo |
| `scripts/control_4b.py` 2026-11-08.1 | Con `--suricata-eve`, **cada ventana y el periodo completo** quedan en una categoría de Suricata: `cero_descartes` (C0), `descartes` (C1) o `datos_faltantes` (C3, con su estado: `ausente`, `desactualizada`, `error_lectura`, `cobertura_insuficiente`). Nuevas claves: `detector.suricata_por_ventana` (decididas y no evaluadas, estados y tramos con datos faltantes), `periodo_completo` (con tabla por hora) y `fuentes.suricata_eve` (hashes). Sin `--suricata-eve` se comporta como la 2026-11-02.1 |
| `herramientas/herramientas-e4.sha256` | Igual que la de la reconciliación, con el hash nuevo de `control_4b.py` (`f68cbf7f…`) |

**No cambian:** el modelo, el escalador, las 28 características, los umbrales 0,05/0,03/0,01, los heurísticos, las clases C0–C3 (SALUD-CAPTURA §3), I1–I8, la definición de población C0, ni la duración. **I5 (0 `kernel_drops` en los 30 min previos) sigue siendo solo para el inicio de la 4C**; en la 4B basta que Suricata esté medido.

**Pendiente para la 4C, fuera de esta enmienda:** el paso `3` de `s50` (`suricata-stats.json`) sigue leyendo `stats.log` y fallaría con Suricata 7 (sin `kernel_drops`), con lo que quedarían omitidos los pasos `5`, `6` y `c` de la 4C.

## 3. Pruebas (todas en banco, sin red, usuario 65534)

| Prueba | Resultado | Fichero |
|---|---|---|
| Unitarias: `control_4b` con EVE (tres categorías, periodo completo, estados faltantes, guardas), las 5 originales de `control_4b` y 9 de `limites_db3` | **31 passed** | `evidencia/banco/pytest-enmienda.txt` |
| Recorrido completo `s50` (4b) con datos REALES del 3B (motor, ciclos, inventario) + salud/EVE sintéticos, 4 corridas | **todas OK** | `evidencia/banco/recorrido-completo-RESULTADO.txt` y las salidas `recorrido-completo-*` |
| `s10` en un Sensor1 simulado (systemctl y motor falsos, muestreador REAL de P1, EVE sintético), 13 comprobaciones | **todas OK** | `evidencia/banco/banco-s10.txt` |

Corridas del recorrido completo: **A** guiones originales + salud congelada (defecto reproducido: 2 644 ventanas C3, 0 C0) · **B** guiones enmendados, EVE sano (2 644 C0 y las cifras del control publicado del 3B: IF 395/254/83, HEUR 92, HIB 466/336/171; periodo completo C0) ·
**C** con una ráfaga de 23 descartes, un hueco de EVE de 100 s y stats sin `kernel_drops` (2 232 C0 / 73 C1 / 339 C3; periodo completo C3 con 23 descartes parciales informados, sin afirmar total; los dos tramos de datos faltantes localizados; clases dentro de las cotas de un oráculo geométrico independiente) ·
**D** sin segmento EVE (`s50` se detiene con rc 2).
`s10`: sano (rc 0, muestreador P1, medida inicial `cero_explicito`) y cinco casos de parada: EVE sin `kernel_drops`, EVE detenida, hueco de EVE, hash de la herramienta distinto del fijado y carpeta ya existente.

**Límites de las pruebas.** Los datos de salud y EVE son sintéticos: prueban el código, no son una medida del laboratorio. En `s10` solo se sustituye el hash del archivador (el real, `2181af5f…`, no se puede ejecutar en el banco); lo comprueba la prueba S0. No se probó `s30` (replay) ni `s20`/`s40`, que la enmienda no toca. El recorrido real contra el Sensor1 es la propia 4B.

## 4. Hashes

| Fichero | sha256 (16 primeros) |
|---|---|
| `guiones/s10_sensor_archivo_e4.sh` | `52d023a5a734c1fb` |
| `guiones/s50_analisis_e4.sh` | `b476890fcea944ac` |
| `scripts/control_4b.py` | `f68cbf7f21216448` |
| `scripts/limites_db3.py` (referencia de DB-3, no se usa en la 4B) | `e9b500b6ab9d15b4` |
| `salud_captura.py` de P1 (Sensor1, producto `313f8f8`) | `274b4d61` (completo en `s10` y `s50`) |

## 5. Cómo se instalaría (solo tras la orden de Mark; el 7.1 del protocolo cambia en dos ficheros)

`[LAPTOP Git Bash]` → lo ejecuto yo. Igual que §7.1, pero `control_4b.py` y `herramientas-e4.sha256` salen de esta carpeta, y los guiones `s10`/`s50` se ejecutan desde ella con `r4.sh`:
`G="…/etapa4-4b-enmienda-p1-2026-11-08/guiones"` para `s10` y `s50`; el resto de guiones (`k01`, `b01`, `s20`, `s30`, `s40`, `p10b`) siguen en `etapa4-preparacion-2026-11-02/guiones`, y `k20` y `r4.sh` en la reconciliación.
Se esperan las mismas 12 líneas `OK` en el bastión y en el Sensor1, con el nuevo `herramientas-e4.sha256`.
