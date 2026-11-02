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

## Lo que no cambia

Modelo, escalador, 28 características, umbrales, reglas de detección, los tres arreglos de la Etapa 3, el Word, el
laboratorio (nada instalado, reiniciado, habilitado ni deshabilitado), la imagen Docker y la evidencia temporal.
