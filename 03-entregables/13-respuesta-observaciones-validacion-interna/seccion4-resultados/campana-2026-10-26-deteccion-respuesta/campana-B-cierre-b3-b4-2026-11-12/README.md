# Paquete de cierre de la Campana B (B3 + B4), 12-nov-2026

Cierra la Campana B como **dos tramos de los 25 episodios previstos**: **B3** (episodios 1-6) y **B4** (episodios 7-25). Rama `campana-b-cierre-publicable`: un solo commit sobre la base `f8cef33a470b983cdb93115b6c63543572fd1472`. Ruta del paquete: `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/campana-B-cierre-b3-b4-2026-11-12/`.

## Que contiene
| Ruta | Contenido |
|---|---|
| `CONSOLIDADO-25-EPISODIOS.md` | Tabla de los 25 episodios (tramo, estados, E1-E5), denominadores, los ocho `incompleto_timeout`, motivos de indeterminacion de E3 y de no aplicabilidad, cobertura por familia y limitaciones abiertas |
| `HISTORIAL-CAMPANA-B.md` | Corridas, ensayos y correcciones con sus nombres e IDs reales (incluida B1 y B2): que se probo, por que se detuvo, donde esta la evidencia |
| `balances/` | `BALANCE-B3-PARCIAL.md` y `BALANCE-B4.md` **originales** (B4 hasta su cierre tecnico y analisis del 12-nov; la parte anadida despues esta en `reanalisis/`) |
| `reanalisis/` | Reanalisis de E1 por destino bajo el criterio vigente, con pruebas, regresion y trazabilidad por episodio; evidencia complementaria de E3 (no formal) |
| `resultados/` | `resultados-por-episodio.csv/.json` (los 25, con E1-E5, evidencia o motivo, criterio, version del analizador y hashes), salidas crudas de los analizadores y del reanalisis |
| `criterios/` | Criterio E3 fijado el 11-nov y sus antecedentes; limitacion del generador de inundacion. El criterio E1-E5 de origen es `OBJETIVOS-Y-CRITERIOS.md` (ya versionado; ver `INDICE-EVIDENCIA.md`, seccion C) |
| `analisis/` | Scripts y pruebas de los analizadores y del reanalisis, y el constructor de este paquete |
| `pruebas/` | Ejecucion de las pruebas al construir el paquete, y lo que no se pudo re-ejecutar |
| `manifiestos/` | Hashes de los PCAP crudos (514 de B3, 2343 de B4) y de clientes/intentos/salidas; los PCAP **no** estan en el paquete |
| `INDICE-EVIDENCIA.md`, `SHA256SUMS` | Indice con hashes y referencias a los originales; suma de verificacion de este paquete |

## Ejecutar el analisis desde otro equipo

**Requisitos:** Windows (los scripts usan rutas con `\`), Python 3.10 o posterior (probado con 3.14) y solo biblioteca estandar; `pytest` unicamente para las pruebas. Sin dependencias de red.

### 1. Lo que se puede hacer sin la evidencia cruda
Desde `analisis/` (sin `python -I`, que aisla `sys.path`):
- `python -m pytest -q -p no:cacheprovider test_analizar_b.py test_e1_por_destino.py` -> 45 pruebas (comprobado sobre un checkout limpio de esta rama).
- Verificar el paquete: `sha256sum -c SHA256SUMS` desde esta carpeta.
- Leer `resultados/` y `CONSOLIDADO-25-EPISODIOS.md`; no necesitan nada mas.
- `test_instrumentacion.py` **no** es ejecutable desde este paquete: necesita `muestreador_set.py`, `inundacion_instrumentada.sh`, `clientes_factor1_tx.py` (no incluidos) y el banco Docker del producto de la etapa 3 (ver `pruebas/PRUEBAS-EJECUTADAS.md`).

### 2. Insumos para reproducir el analisis (NO estan en el repositorio)
Se obtienen de los hosts del laboratorio (rutas en `INDICE-EVIDENCIA.md`, seccion B) o del autor, y se comprueban con `manifiestos/`. Se organizan en **dos carpetas**, una por tramo:

| Carpeta | Ficheros que leen los scripts | Origen |
|---|---|---|
| `--b3` (tramo B3) | `bastion/corrida/marcas.jsonl`; `cf-b3-agente.jsonl`; `cf-b3-set-lecturas.jsonl`; `evid/traza.jsonl`; `bastion/compuerta/puertas-D5.jsonl`; `bastion/vigia/vigia.jsonl`; `pcap/*.pcap` (514, hashes en `manifiestos/pcap-B3.sha256`); `cf-b3-clientes/transacciones-*.tsv`; `cf-b3-kali/intentos/intentos-*.tsv`; `resultado-b3.json` | marcas y salidas: Kali; traza: srv-dmz; vigia/compuerta: bastion; PCAP y publicador: Sensor1; transacciones: clientes |
| `--b4` (tramo B4) | `kali/corrida/marcas.jsonl`; `agente-B4.jsonl`; `set-lecturas.jsonl`; `evid/traza.jsonl`; `bastion/compuerta/puertas-D5.jsonl`; `bastion/vigia/vigia.jsonl`; `pcap/*.pcap` (2343, `manifiestos/pcap-B4.sha256`); `clientes/transacciones-*.tsv`; `kali/intentos/intentos-*.tsv`; `kali/corrida/salidas/`; `resultado-b4.json` | igual que B3 |
| generados | `span-origen-b3.pkl` y `span-origen-b4.pkl` (los crea `span_extract2.py` desde los PCAP, dentro de la carpeta `--b4`); `resultado-e1-por-destino-25.json` (lo crea `aplicar_e1_destino_25.py`) | local |

`resultado-b3.json`, `resultado-b4.json` y `resultado-e1-por-destino-25.json` tambien estan en `resultados/` de este paquete. **`analizar_b3.py` y `analizar_b4.py` sobrescriben `resultado-b3.json` / `resultado-b4.json` en la carpeta indicada**: trabaje sobre una copia.

### 3. Rutas fijas al equipo del autor y como cambiarlas
Los scripts de `analisis/` se conservan **tal como se ejecutaron** (su hash esta citado en `resultados/resultados-por-episodio.csv`, columna `analizador`); por eso no se editaron. Rutas fijas:

| Script | Linea(s) | Ruta fija | Uso |
|---|---|---|---|
| `analizar_b3.py` | 12 | `C:\Users\<usuario>\cf-b3` (`W`) | carpeta de evidencia de B3 |
| `analizar_b4.py` | 12 | `C:\Users\<usuario>\cf-b4` (`W`) | carpeta de evidencia de B4 |
| `aplicar_e1_destino_25.py` | 3, 5, 7 | `C:\Users\<usuario>\cf-b4`, `...\cf-b3\resultado-b3.json` | resultados y SPAN extraido |
| `aplicar_e1_destino.py` | 3, 5 | `C:\Users\<usuario>\cf-b4` | reanalisis previo (16 episodios de B4) |
| `span_extract.py` | 7 | `C:\Users\<usuario>\cf-b4` | extrae el SPAN de B4 (Kali -> srv-dmz) |
| `span_extract2.py` | 8, 16 | `C:\Users\<usuario>\cf-b3\pcap`, `...\cf-b4\pcap`, `...\cf-b4\span-origen-*.pkl` | extrae el SPAN de B3 y B4 |
| `scan_rates.py` | 7 | `C:\Users\<usuario>\cf-b4` | puertos y SYN de los escaneos |
| `cmp2.py`, `cmp3.py`, `cmp_contadores.py` | 2 | `C:\Users\<usuario>\cf-b4` | SPAN frente a contadores |
| `consolidar.py` | 2, 3, 17 | `C:\Users\<usuario>\cf-b4`, `...\cf-b3\resultado-b3.json`, `...\cf-b3\bastion\vigia\vigia.jsonl` | tabla previa de 25 episodios |
| `analizar_b3.py`, `analizar_b4.py`, `scan_rates.py`, `span_extract.py`, `span_extract2.py` | 4 o 9 (`BASE`) | `<carpeta de trabajo del autor>\campana-B-protocolo-2026-11-10` | solo anade carpetas del autor a `sys.path`; en otro equipo no existe y no importa: los modulos se importan de `analisis/` |
| `construir_paquete.py` (+ `textos_paquete.py`) | 7, 12 | `REPO`, `W3`, `W4` | **generador del autor** de la primera version del paquete; necesita ademas la carpeta de trabajo `campana-B-protocolo-2026-11-10` (no publicada); **no esta pensado para ejecutarse en otro equipo** |

**Como cambiarlas, sin tocar los scripts:** `analisis/ejecutar_analisis.py` lee el script tal cual, sustituye en memoria esas dos carpetas (para cualquier usuario de Windows) por las que indique y lo ejecuta (desde `analisis/`):

```
python -X utf8 ejecutar_analisis.py --b3 D:\evidencia\cf-b3 --b4 D:\evidencia\cf-b4 span_extract2.py
python -X utf8 ejecutar_analisis.py --b3 D:\evidencia\cf-b3 --b4 D:\evidencia\cf-b4 analizar_b3.py
python -X utf8 ejecutar_analisis.py --b3 D:\evidencia\cf-b3 --b4 D:\evidencia\cf-b4 analizar_b4.py
python -X utf8 ejecutar_analisis.py --b3 D:\evidencia\cf-b3 --b4 D:\evidencia\cf-b4 aplicar_e1_destino_25.py
```
Orden de reproduccion: `span_extract2.py` -> `analizar_b3.py` y `analizar_b4.py` -> `aplicar_e1_destino_25.py`. `-X utf8` evita errores de codificacion en la consola de Windows. **Datos personales en los scripts:** los scripts originales conservan literal la ruta del equipo del autor, que incluye su nombre de usuario de Windows (en `analizar_b3.py`, `analizar_b4.py`, `aplicar_e1_destino*.py`, `span_extract*.py`, `scan_rates.py`, `cmp*.py`, `consolidar.py`, y en `construir_paquete.py`/`textos_paquete.py`), **para no alterar sus hashes**; el lanzador `ejecutar_analisis.py` no contiene ningun nombre de usuario (reconoce cualquiera). Alternativa: editar las constantes de la tabla (el script cambiaria de hash y la columna `analizador` dejaria de coincidir).

**Reproducibilidad comprobada (12-nov, antes del push):** con las carpetas de evidencia del autor accedidas por otra ruta (jecutar_analisis.py --b3 ... --b4 ...), nalizar_b3.py, nalizar_b4.py y plicar_e1_destino_25.py regeneraron esultado-b3.json, esultado-b4.json y esultado-e1-por-destino-25.json **byte a byte identicos** a los de esultados/. span_extract2.py no se volvio a ejecutar (tarda varios minutos); se uso el SPAN ya extraido.

## Reglas aplicadas
- **Balances originales conservados**; E1 por destino es un **reanalisis** bajo el criterio vigente, con su codigo y pruebas.
- **Veredictos formales de E3 sin cambios** (5 cumple, 15 indeterminado, 5 no aplica) y **ocho `incompleto_timeout` conservados**.
- **Limitacion abierta:** discrepancia entre el SPAN y los contadores de srv-dmz. El ensayo del contador y la repeticion de los escaneos quedan **fuera del alcance** de este cierre.
- `balances/BALANCE-B4.md` es el original salvo una ruta de equipo personal (linea 5), sustituida por `<carpeta de evidencia B4>`; `balances/BALANCE-B3-PARCIAL.md` es identico al original.
- Excluidos: PCAP crudos, credenciales, registros sensibles (ver `INDICE-EVIDENCIA.md`, seccion F).

## Criterio escrito (E1-E5)
`OBJETIVOS-Y-CRITERIOS.md` (filas E1-E5, lineas 93-97): ruta `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md`, en el commit `f8cef33a470b983cdb93115b6c63543572fd1472` (ultima modificacion del fichero: `8ad1984`, blob `888f66482572`). Ya publicado en `origin/main`; ver `INDICE-EVIDENCIA.md`, seccion C.

## Generador del paquete
`analisis/construir_paquete.py` y `analisis/textos_paquete.py` generaron la primera version del paquete. El `README.md` y el `INDICE-EVIDENCIA.md` se revisaron a mano despues (rutas de acceso a los hosts, instrucciones de ejecucion), por lo que ya no coinciden con lo que el generador produciria.
## Verificar
Desde esta carpeta: `sha256sum -c SHA256SUMS` (incluye .gitattributes; `* -text` conserva los bytes exactos).
