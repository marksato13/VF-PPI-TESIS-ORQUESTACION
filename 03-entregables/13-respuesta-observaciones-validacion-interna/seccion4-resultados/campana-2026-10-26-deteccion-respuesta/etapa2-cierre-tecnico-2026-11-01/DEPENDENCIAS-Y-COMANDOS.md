# Dependencias y comandos del cierre técnico

Todo se ejecutó fuera del laboratorio: en el portátil y en contenedores Docker locales. **No se desplegó, instaló ni reinició nada** en el Sensor1, DC1, srv-dmz ni ningún otro equipo. No se lanzaron ataques ni campañas.

## 1. Entornos

| Entorno | Uso | Versiones |
|---|---|---|
| venv del modelo (portátil) | replays con el modelo real | Python 3.14.3, scikit-learn 1.9.0, numpy 2.5.1, scipy 1.18.0, joblib 1.5.3 (`resultados/venv-modelo-freeze.txt`). Sin `InconsistentVersionWarning`: el manifiesto del modelo declara sklearn 1.9.0 |
| Python del sistema (portátil) | comparadores, analizador, pruebas del motor | Python 3.14.3, scikit-learn 1.9.1. Las pruebas del motor usan modelos sintéticos, no el desplegable |
| Banco `cyberflow-etapa2-banco:2` | suite completa (575 pruebas), netns/nft, helper como root | Python 3.13.5, scikit-learn 1.4.2, numpy 2.2.4. Imagen `sha256:2ece1c60…4b8c` |
| Banco `cyberflow-etapa2-banco:3` | SSH real y unidades systemd (S1–S8) | :2 + openssh-server/cliente + systemd (`deploy/pruebas-aisladas/Dockerfile.ssh`). Imagen `sha256:fdeee562…236` |

## 2. Comandos

En los comandos, `$S` es el directorio de trabajo temporal de la sesión: datos del 3B, anillos y salidas brutas, fuera del repositorio. Los guiones están en `guiones/`; los resultados copiados (comprimidos) en `resultados/`.

### 2.1 Pruebas

`[BANCO Docker root]` → lo ejecuté yo.

```
docker run --rm --privileged -v <worktree>:/src:ro cyberflow-etapa2-banco:2 \
  bash -c 'cp -a /src /w && rm -rf /w/.git && cd /w && python3 -m pytest -v -rs -p no:cacheprovider'
# → resultados/pruebas/pytest-completo-v.txt : 575 passed, 1 skipped (sin node)
```

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python -m pytest -v -p no:cacheprovider tests/test_motor_incremental.py tests/test_motor_completitud.py
# → resultados/pruebas/pytest-motor-windows.txt : 17 passed
```

Los ensayos del banco (`resultados/ensayos/`) son de la fase anterior de este mismo cierre, con el código de enforcement de `3083f60`, que no ha cambiado:

- `deploy/pruebas-aisladas/ensayo_netns_dns.py` (C0–C9) y `ensayo_cadena_eventos.py`, ejecutados en `[BANCO Docker root]`;
- `ensayo_ssh_unidades.sh` (S1–S8), ejecutado en `[BANCO Docker root]` con la imagen :3.

### 2.2 Replays

`[LAPTOP Git Bash]` → lo ejecuté yo, con el venv del modelo y desde el worktree de la rama candidata en `953a436`.

```
PREF=cierre  bash guiones/correr_replays_cierre.sh     # tramo 08:40–09:05: r1..r7
PREF=cierre8 bash guiones/correr_r8.sh                 # 08:30–09:05: r8ref y r8 (6 reinicios)
PREF=completo bash guiones/correr_completo_ref.sh      # 07:24:40–10:05:40, archivo 15 s, periódico
PREF=completo bash guiones/correr_completo_cand.sh     # 07:24:40–10:05:40, anillo 5 s, eventos
PREF=sens HIST=900 DESDE=2026-11-01T08:45:30Z bash guiones/correr_sens900.sh   # sensibilidad
```

Se ejecutaron hasta 5 replays a la vez (14 núcleos), lanzados con `Start-Process` desde `[LAPTOP PowerShell]` para que sobrevivieran a un corte de la sesión. Las latencias de disponibilidad (reloj `coste`) incluyen esa concurrencia.

r2, r3 y r8ref terminaron antes de un corte de la sesión; los demás se relanzaron con el mismo código. Los hashes del motor son los de `resultados/hash-codigo-replays.txt` en todos.

### 2.3 Comparaciones y análisis

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python herramientas/comparar_cierre.py --referencia <r2> --otros <r1 r3 r4 r5 r6 r7> --marcas marcas.jsonl \
  --esquema configs/features/multilayer-v2.json --desde 2026-11-01T08:41:00Z --hasta 2026-11-01T09:04:00Z \
  --salida resultados/comparaciones/tramo-cierre.json
# igual con los tramo-* de la entrega anterior → tramo-anterior.json
# r8 frente a r8ref, 08:34–09:04 → r8-vs-r8ref.json
# completo cand frente a ref, 07:29–10:04 → completo-cand-vs-ref.json
# sens900 frente a r2, 08:46–09:04 → sens900-vs-r2.json
bash guiones/analizar_completos.sh                     # analizar_3b.py sin modificar → resultados/analisis-3b-*
python herramientas/comparar_25.py <vivo revisado> <ref> <cand> resultados/comparaciones/comparacion-25-episodios.json
python herramientas/tablas_cierre.py ... > resultados/comparaciones/tablas-25-y-breves.md
python herramientas/desglose_breves.py <archivo-pcap> marcas.jsonl resultados/comparaciones/desglose-escaneos-breves.json
python herramientas/rendimiento_episodios.py marcas.jsonl <replay> resultados/comparaciones/rendimiento-<replay>.json
python herramientas/alarmas_otras.py marcas.jsonl <cand>/motor_decision.log guiones/umbrales-alfa.json \
  resultados/comparaciones/alarmas-otras-entidades-cand.json
python herramientas/tope_duracion.py configs/features/multilayer-v2.json <r2>/caracteristicas.jsonl 08:41 09:04 \
  resultados/comparaciones/tope-duracion-tramo.json
$S/venv-modelo/Scripts/python.exe -I herramientas/cortes_duracion.py <modelo.joblib> <manifiesto.json> \
  resultados/comparaciones/cortes-flow-duration.json
python herramientas/sens_clases.py <r2> <sens900> configs/features/multilayer-v2.json guiones/umbrales-alfa.json \
  08:46 09:04 resultados/comparaciones/sens900-clases.json
python herramientas/verif_no_regenerada.py <archivo-pcap> 10.10.30.10 2026-11-01T09:27:00Z 2026-11-01T09:26:40Z
python herramientas/verif_no_regenerada.py <archivo-pcap> 10.10.10.21 2026-11-01T09:34:30Z 2026-11-01T09:34:20Z
# → resultados/comparaciones/verif-no-regeneradas.txt
sha256sum -c esp-pcap.sha256                          # 844/844 PCAP = voluminosos-sha256.txt del sensor
```

### 2.4 Manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo, desde esta carpeta.

```
find . -type f ! -name MANIFIESTO.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFIESTO.sha256
sha256sum -c MANIFIESTO.sha256
```

Tras el push, el manifiesto se verificó contra los bytes descargados de GitHub (README, §8).

## 3. Lo que queda para Mark (no ejecutado)

Nada de este cierre exige ahora una acción en el laboratorio. Lo pendiente en vivo (README, §7) requiere sudo con contraseña en el Sensor1 o en los destinos: lo ejecutarías tú cuando se autorice la instalación.
