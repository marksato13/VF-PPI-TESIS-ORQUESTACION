# Corrección de D5: sets de aplicación frente al contador `descartes_limite` (banco, 11-nov-2026)

**Estado: preparada y probada EN BANCO. NO desplegada, NO instalada en ningún host, NO usada.** Para revisión antes de desplegar o lanzar otra corrida. **B3 se conserva como corrida parcial de 6 episodios** (evidencia en `corrida-2026-11-11\` y `~/cf-e4/4c-B3-parcial-6ep-20261111T0620Z`); los veredictos de **B2** y **B3** no se tocan. El D5 desplegado (`herramientas\d5_episodio.py`, `85c71124…`) **no se modificó**.

## Defecto
`d5_episodio.srv_nft` contaba cualquier presencia del origen en `descartes_limite` como «presente en nftables». Ese set es un **contador dinámico de instrumentación** (paquetes descartados por exceder la tasa); las únicas reglas de la cadena hacen match en `@bloqueados` y `@limitados`, de modo que una entrada ahí **no descarta nada**. Además `retirar_origen` solo limpia los sets de aplicación (`SETS = ("bloqueados","limitados")`, helper l. 60/216), así que tras un episodio LIMIT con descartes la entrada sobrevivía y la puerta se bloqueaba (B3, tras el episodio 6, 05:56:55Z).

## Cambio (`d5_episodio_corregido.py`, generado por `hacer_d5_corregido.py` con 2 sustituciones exactas)
- `srv_nft`: `presente`/`donde` cuentan **solo** los sets de aplicación; el contador se informa aparte en `residual` y **nunca se borra** ni se modifica (ninguna operación del helper lo toca).
- **Fallo cerrado** si el estado no se puede verificar: helper que falla, `estado` de tipo erróneo, sets de aplicación ausentes o ilegibles (antes un listado sin `sets` daba «ausente» y pasaba), `descartes_limite` mal formado → `ok: False` (la puerta no pasa).
- `Puerta.una_vez`: el resultado añade `residual_conservado` y los pasos `nft_antes`/`nft_despues` llevan el residual → queda en `puertas-D5.jsonl`.
- `srv_estado` (P1) sin cambios (ya ignoraba el contador; probado).

## Pruebas (imagen de banco `cyberflow-etapa3-banco:1`, `--network none`, usuario 65534, sistema de ficheros de solo lectura)
**39 de 39 pasan:** 20 nuevas (`test_d5_descartes_limite.py`) + las 19 de la suite existente `tests\test_d5.py` contra el D5 corregido (`test_d5_regresion_corregido.py`, solo cambia el import).
- **Reproducción del episodio 6 con el JSON real del helper** (sets vacíos; 10.10.20.30 en `descartes_limite`: 74 paquetes, 5.546 B):
  - D5 desplegado: `presente=True, donde=['descartes_limite']` y **la puerta se bloquea** (reproduce el fallo real).
  - D5 corregido: `presente=False`, residual `{descartes_limite: {paquetes 74, bytes 5546, …}}`; **la puerta pasa** y lo conserva (en el paso, en `residual_conservado` y en el nftables simulado, sin borrarlo; el helper solo recibe `listar` y un `retirar_origen`).
  - Estado completo del episodio 6 (regla en `limitados` + residual): se retira del set, `nft_despues` limpio, la puerta pasa.
  - Solo residual, sin regla: la puerta pasa **sin** llamar a `retirar_origen`.
  - Contador de **otra** IP: no se atribuye al origen.
- **Sigue bloqueando:** restricción que no se retira en `limitados`; en `bloqueados`; el agente que reaplica tras la limpieza; **8 casos de estado no verificable** (helper falla, sin estado, estado de tipo erróneo, sets ausentes, falta `limitados`, set `None`, sin clave `sets`, contador mal formado); lectura posterior a la retirada que falla.
- **Derivación de banco:** `hacer_d5_episodio_banco.py` sobre el corregido da 3 sustituciones sin fallos; el derivado conserva la corrección (comprobado: residual conservado y fallo cerrado).
- **Mutaciones: 9 de 9 eliminadas** (`resultado-mutaciones.txt`): reintroducir el defecto, `presente` siempre False, ignorar sets ausentes / estado erróneo / contador mal formado, no informar el residual, no conservarlo en el resultado, mirar solo `limitados`, tratar un listado fallido como vacío.

## Límites (lo que NO se probó)
- **Solo banco** (nftables, helper, publicador simulados; el JSON de `listar` es el real de srv-dmz). No se probó en los hosts; su efecto en vivo con la cadena completa (relé, agente, helper real) requeriría una corrida o un ensayo autorizado.
- **No se ejecutaron** los tests de integración del banco con systemd/OpenSSH real (`propuestas\d5-sin-reinicio\test_*`) contra el derivado corregido; sí la suite de D5 y la derivación.
- La corrección **no toca el helper** ni `retirar_origen`; si se prefiere que `retirar_origen` también reinicie el contador, es un cambio aparte (el helper ya lo reinicia en el siguiente `anadir` a `limitados`).
- No modifica B2 ni B3: ningún resultado se recalcula con ella.

## Para desplegar (decisión de Mark, no hecha)
1. Revisar este informe y el diff (`d5_episodio_corregido.py` frente a `herramientas\d5_episodio.py`: `hacer_d5_corregido.py`). 2. Regenerar `d5_episodio_banco.py` desde el corregido con `hacer_d5_episodio_banco.py`, actualizar `SHA256SUMS` del paquete y copiar al bastión (`~/cf-b/herramientas/`, con respaldo y verificación de hashes). 3. Preflight y aceptación (`aceptar` del bastión) antes de otra corrida.

Hashes: `d5_episodio_corregido.py` 00c1bb29…, `hacer_d5_corregido.py` 734e1f45…, `test_d5_descartes_limite.py` d832bfb7…, `test_d5_regresion_corregido.py` 46084dfe…, `hacer_regresion_y_mutaciones.py` 68ec1aae…. Documento separado sobre E3 de la inundación: `..\..\LIMITACION-GENERADOR-E3-INUNDACION.md`.
