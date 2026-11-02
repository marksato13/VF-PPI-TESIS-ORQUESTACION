# Dependencias y comandos

Todo se ejecutó en el portátil. **Ningún comando toca el laboratorio.** En los comandos, `<scratchpad>` es el directorio de trabajo de la sesión y `<repo-motor>`, la copia de la rama `candidato/etapa2-20261101`.

## Copias de trabajo por versión

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
git -C <repo-motor> worktree add C:/Users/markp/AppData/Local/Temp/w953  953a436
git -C <repo-motor> worktree add C:/Users/markp/AppData/Local/Temp/wcand 4694e38   # 862404e + arnés
git -C <repo-motor> worktree add C:/Users/markp/AppData/Local/Temp/wopt  6b6ef82
```

## Regresiones sobre la versión anterior (deben fallar)

`[LAPTOP Git Bash]` → lo ejecuté yo. Se ejecutan los tests de `862404e` contra el motor de `953a436`.

```
python -m pytest -v -p no:cacheprovider tests/test_motor_incremental.py
# → resultados/pruebas/regresiones-sobre-953a436.txt : 4 fallos
```

## Corridas secuenciales (una cada vez)

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
bash guiones/correr_secuencial.sh       # sec-ref-953a436, sec-cand-862404e, perfil-ref, perfil-cand
bash guiones/correr_secuencial_opt.sh   # sec-opt-6b6ef82, perfil-opt-6b6ef82
```

Cada corrida invoca el arnés de `4694e38` con el mismo `--` hacia el motor:

```
python -I replay_motor.py --motor scripts/engine/motor_decision.py --pcap-dir anillo-e5-completo \
  --eve eve-segmento.json --desde 2026-11-01T07:24:40Z --hasta 2026-11-01T10:05:40Z --reloj coste --salida <out> -- \
  --model-path if_limpio_2026_10_desplegable.joblib --manifest-path manifest-if-limpio-2026-10.json \
  --detector-name if_limpio_2026_10 --entity-network 10.10.0.0/16 --excluir <11 IP de gestión/sensor> \
  --excluir-protocolos 112,240 --history-seconds 230 --step-seconds 10 --disparo eventos \
  --volcar-caracteristicas <out>/caracteristicas.jsonl
```

## Análisis

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python herramientas/rendimiento_secuencial.py marcas.jsonl replay/<corrida> resultados/rendimiento/<corrida>.json
python herramientas/tabla_rendimiento.py resultados/rendimiento/TABLA-SECUENCIAL.md <ref>.json <cand>.json <opt>.json
python herramientas/comparar_completos.py replay/<a> replay/<b> resultados/comparaciones/<a>-vs-<b>.json
bash guiones/analizar_pendientes.sh     # analizar_3b.py sin modificar + comparar_25.py
cd <repo-motor> && python herramientas/diagnostico_14.py archivo-pcap eve-segmento.json \
  replay/sec-ref-953a436/motor_decision.log replay/sec-opt-6b6ef82/motor_decision.log \
  resultados/diagnostico/diagnostico-14.json
python herramientas/tabla_14.py resultados/diagnostico/diagnostico-14.json <tabla>.md
bash guiones/ensamblar_pendientes.sh    # copia y comprime (gzip -n -9) las salidas en resultados/
```

## Pruebas

`[LAPTOP Git Bash → Docker]` → lo ejecuté yo.

```
MSYS_NO_PATHCONV=1 docker run --rm --privileged -v <repo-motor>:/src:ro cyberflow-etapa2-banco:2 \
  bash -c 'cp -a /src /w && rm -rf /w/.git && cd /w && python3 -m pytest -v -rs -p no:cacheprovider'
# → resultados/pruebas/pytest-completo-v-6b6ef82.txt : 580 passed, 1 skipped (sin node)
```

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python -m pytest -v -p no:cacheprovider tests/test_motor_incremental.py tests/test_motor_completitud.py
# → resultados/pruebas/pytest-motor-windows-6b6ef82.txt : 22 passed, 2 subtests passed
```

## Verificación del manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo. Se hace con un clon disperso desde GitHub.

```
sha256sum -c MANIFIESTO.sha256
```

## Lo que queda para el Sensor1 (no ejecutado: requiere autorización e instalación)

`[Sensor1 cyberflow]` → lo ejecutarías tú, o yo con autorización expresa, porque instalar y reiniciar está fuera de este encargo.

1. Instalar `6b6ef82` en modo sombra, siguiendo `../etapa2-cierre-tecnico-2026-11-01/PROCEDIMIENTO-INSTALACION-REVERSION.md`.
2. Medir R1–R4 en vivo con el mismo criterio (`CRITERIO-ACEPTACION-RENDIMIENTO.md`).
