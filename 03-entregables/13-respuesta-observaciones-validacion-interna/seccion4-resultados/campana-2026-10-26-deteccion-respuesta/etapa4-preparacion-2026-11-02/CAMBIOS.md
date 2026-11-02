# Nota de cambios — preparación de la Etapa 4 (2026-11-02)

## Repositorio de documentación (`orquestacion-limpio`, `main`)

**Nuevo:** `etapa4-preparacion-2026-11-02/` completa (README, MATRIZ, ESTADO-OBSERVADO, SALUD-CAPTURA, PROCEDIMIENTO,
PROTOCOLO-4B, PROTOCOLO-4C, ORDEN-4C, OBSERVACION-DNS, configuraciones, `herramientas-e4.sha256`, guiones y evidencia),
con `.gitattributes` `* -text` para que los bytes publicados sean los hashados.

**Scripts de análisis (`../scripts/`):**

| Fichero | Cambio | Prueba |
|---|---|---|
| `calidad_fuentes.py` | `--duracion-pcap` (por defecto 15: reproduce el 3B; la Etapa 4 usa 5) | `tests/test_calidad_fuentes_rotacion.py` (4) |
| `control_4b.py` (nuevo, 2026-11-02.1) | Control normal por clase de salud, α, regla, entidad, vía rápida y propuestas | `tests/test_control_4b.py` (4) + regresión exacta contra el control del 3B |
| `referencia_trafico_4c.py` (nuevo, 2026-11-02.1) | Marcas por episodio y categoría del escaneo breve contra la ráfaga observada | `tests/test_referencia_trafico_4c.py` (5) |

Ningún otro script de análisis cambia: `analizar.py`, `analizar_3b.py`, `poblacion.py`, `extraer_evidencia_destino.py`,
`recalcular_caracteristicas.py`, `generar_respaldos.py` y `verificar_integridad.py` son los del 3B.

**Correcciones en `etapa3-cierre-tecnico-2026-11-02/`** (avisos al principio; el texto publicado se conserva):
`README.md`, `MATRIZ.md` (7b275b8 y `kernel_drops`), `DEPENDENCIAS-Y-COMANDOS.md`, `PROCEDIMIENTO-ETAPA4.md`
(marcado como sustituido). Su `MANIFIESTO.sha256` se regenera.

## Repositorio del producto

Sin cambios en esta tanda: `candidato/etapa3-20261102` sigue en `acc6588` (herramientas de la Etapa 4 sobre `ec78ca5`);
no se fusiona en `main` (`7b275b8`).

## Correcciones del 2026-11-02 (tarde), posteriores a d3464bf

Detalle completo en [etapa4-correcciones-2026-11-02](../etapa4-correcciones-2026-11-02/README.md). Aquí, solo lo que
cambia dentro de esta carpeta:

| Fichero | Cambio |
|---|---|
| `SALUD-CAPTURA.md` | Versión `.2` de `salud_captura.py` (`f9cf801`); cobertura SIGUSR1 con tolerancia 30 + 2 s (§2.1); nota de implementación de P1–P5/X1–X3 y lectura de X1 sobre los 25 planificados (§4.2) |
| `PROTOCOLO-4C-CAMPANA-A.md` | §5.2 copia `scripts-4c/` a la Kali y c03 con seis hashes; §5.5 `g01` con el respaldo de srv-dmz, `estado_sombra.py`, vigía, permiso y canal de control persistente (sustituye «ningún acceso a la Kali»); §5.6 `rc=3` = cancelada |
| `PROCEDIMIENTO-ETAPA4.md`, `README.md` | Herramientas `f9cf801`, rama en `3a9f26b`, paquete con 85 ficheros |
| `ORDEN-4C.md` | El orden lo calcula `plan_orden`, igual en `c586d813…` y en `99e6bdae…` (no cambia) |
| `evidencia/paquete/` | `SHA256SUMS` y `.sha256` del paquete reconstruido (`426de9de…`) |
| `guiones/g01`, `b20`, `c03`, `r4`, `s50` | Compuerta, canal de control, rc 3, propagación de errores y ejecución parcial verificable |
| `MANIFIESTO.sha256` | Regenerado |

`config-campana-4c.json` (`f177d9bb…`, campo informativo `herramientas: acc6588`) **no** se toca: su hash está fijado
en `herramientas-e4.sha256`, en ORDEN-4C y en PROTOCOLO-4B, y el campo no interviene en ningún cálculo.

## Lo que no cambia

Modelo, escalador, 28 características, umbrales, reglas de detección, los tres arreglos de la Etapa 3, el Word, el
laboratorio (nada instalado, reiniciado, habilitado ni deshabilitado), la imagen Docker y la evidencia temporal.
