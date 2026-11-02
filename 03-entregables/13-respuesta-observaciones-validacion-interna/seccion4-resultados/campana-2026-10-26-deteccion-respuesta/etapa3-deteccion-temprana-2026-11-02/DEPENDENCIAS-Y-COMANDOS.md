# Dependencias, commits, hashes y comandos

Todo se ejecutó en el portátil. **Ningún comando ha tocado el laboratorio**: no hay despliegue, reinicios, reglas, ataques ni campañas. Los datos del 3B se usaron en copia local y en solo lectura.

## Commits (rama `candidato/etapa3-20261102`, repo `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`)

Base: `6b6ef82` (código del cierre de la Etapa 2), con la documentación `20e8630`.

| Commit | Contenido |
|---|---|
| `0d9123a` | vía rápida de escaneo: detector por par y herramientas de anatomía y rejilla |
| `7aeea04` | publicador con renovación por evidencia y destino de la vía rápida; alternativa Suricata (solo banco); K = 8; ensayo en tiempo real |
| `0e971b2` | vista DNS de los heurísticos; dns_entropy con n ≥ 30; atribución y envolvente del LIMIT |
| `f7775af` | LIMIT DNS candidato: 30/minuto, ráfaga 18, solo UDP/53 |
| `b1ee393` | vista HTTP; http_abuse 600/60 s; port_scan en ráfaga exige puertos distintos (**motor del replay validado**) |
| `1851403` | diagnóstico del contrato flow_duration y de los flujos atribuidos a excluidos |
| `d983a2a` | unidades candidatas (vía rápida en flujo y publicador con señales rápidas); vía rápida por episodio; contador final de descartes |
| `6fbfe00` | ensayo del LIMIT DNS en el banco |
| `71b3ab6` | resumen de la batería de la vía rápida |
| **`585da7b`** | la matriz de trazabilidad del panel refleja las vistas HTTP/DNS (prueba actualizada). **Commit recomendado** |

La rama se publica como rama, **sin fusionar en `main`**: en este repo `main` (`7b275b8`) es lo desplegado en Sensor1, igual que con `candidato/etapa2-20261101`.

Después de `b1ee393`, el único cambio en `scripts/engine/motor_decision.py` es un comentario (`d983a2a`).

## Entradas (las congeladas de la Etapa 2)

| Entrada | sha256 |
|---|---|
| Modelo `if_limpio_2026_10_desplegable.joblib` | `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60` |
| `eve-segmento.json` (3B, 07:24–10:06) | `b7bf61a20a88d789c6fa6dedabd9cf1d6dbe08166da0b9cc24ab2d9a5ae9318f` |
| `marcas.jsonl` (orquestador del 3B) | `276314a81176a0eb914785f0a51738e0256aba48168ce05d9f1f016936d4243a` |
| Anillo re-troceado de 5 s | 2 535 ficheros (el mismo de la Etapa 2) |
| Archivo PCAP del 3B | 846 ficheros |

Segmentos del banco (generados con `scripts/etapa3/segmento_pcap.py` y `segmento_dns_dc1.py`):

| Segmento | sha256 |
|---|---|
| `escaneo_breve-r1.pcap` | `f259871791def87ad144f7d0826e03a2110d8a14b1c926f94fad07f1a34a8267` |
| `escaneo_breve-r2.pcap` | `fa6a2e589a8e3126b221853a8f24f57592c8c70f083301f296b95746d0d3c340` |
| `escaneo_breve-r3.pcap` | `25ba187b4f3d5bdb350285adca6ec8267d12c72ed9d2a8ef62762a2827ec96e1` |
| `escaneo_breve-r4.pcap` | `3f12f8d87220e723fbaa69b6a32eb066c83627ba71b4edc929783dbc1ca798f4` |
| `escaneo_breve-r5.pcap` | `cb828458c3137884c8339fca921e256b79cad95246d259d215fb34d5db1a2779` |
| `carga-inundacion_http-r3.pcap` | `2e29fdb64b7314ccbfc23076458430f937f338290c159aaef44a35005e60a993` |
| `dns_inusual-r1.pcap` (DNS → DC1) | `dcd2204955fdaeecae8f9595672a3f282fbd9f8cfc06c640d9859b8c6d99160e` |
| `dns_inusual-r2.pcap` | `71a71cac5345e9ac360cbd6984edf95aa6e6a1eda7a7dc5fd72676c965e4f88a` |
| `dns_inusual-r3.pcap` | `7ffd6efc6bd0b6c9266e566a992b962d7fbb66d8d6600413527923481b0c2d2e` |
| `dns_inusual-r4.pcap` | `4da118529717394597e07f5fa811c13a42ec79a28fda45126b0e96a0a17c326c` |
| `dns_inusual-r5.pcap` | `e3b678283f9845d998745da739000be79ab989c605785636e150789a90983f18` |

Los segmentos no se publican: contienen tráfico del laboratorio.

## Entornos

| Entorno | Versiones |
|---|---|
| Portátil (Windows 11, Git Bash) | Python 3.13.5 para las herramientas; `venv-modelo` con Python 3.14.3, scikit-learn 1.9.0 y numpy 2.5.1 para el motor |
| Banco `cyberflow-etapa3-banco:1` (`sha256:59f94126…98c0`) | Python 3.13, tcpreplay 4.5.1, tcpdump 4.99.5, nftables 1.1.3, Suricata 7.0.10; `--privileged --network none` |

## Comandos

### Análisis offline

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python scripts/etapa3/anatomia_escaneos.py ...          # resultados/via-rapida/anatomia-*.json
python scripts/etapa3/evaluar_regla_temprana.py ...     # rejilla-temprana.json, rapido-3b-k8.jsonl
python scripts/etapa3/margen_legitimo.py ...            # margen-legitimo.json
python scripts/etapa3/atribucion_dns.py eve-segmento.json resultados/dns/atribucion-dns-3b.json
python scripts/etapa3/evaluar_dns_heuristica.py eve-segmento.json marcas.jsonl resultados/dns/dns-heuristica-3b.json
python scripts/etapa3/politica_limit_dns.py eve-segmento.json resultados/dns/politica-limit-dns-3b.json
python scripts/etapa3/matriz_reglas.py <motor_decision.log> marcas.jsonl <salida>.json
python scripts/etapa3/contrastar_http_pcap.py / http_no_registrado.py / picos_http.py ...   # resultados/http/
python scripts/etapa3/distribucion_flow_duration.py / sensibilidad_flow_duration.py ...     # resultados/contrato/
python scripts/etapa3/flujos_excluidos.py ...           # resultados/contrato/flujos-excluidos-8.json
```

Los argumentos exactos de cada herramienta están en su cabecera (`Uso:`).

### Replay completo y análisis

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
bash guiones/correr_completo_e3.sh     # replay_motor.py (4694e38) con el motor de la rama; ~17 min
bash guiones/analizar_e3.sh            # analizar_3b.py SIN MODIFICAR + comparar_25 + comparar_completos
                                       # + via_rapida_episodios + matriz_reglas
python ../etapa2-cierre-pendientes-2026-11-01/herramientas/rendimiento_secuencial.py \
  marcas.jsonl <replay> resultados/rendimiento/e3-b1ee393-e5-eventos.json
bash guiones/ensamblar_e3.sh           # copia y comprime (gzip -n -9) en resultados/
```

### Banco

`[LAPTOP Git Bash → Docker]` → lo ejecuté yo.

```
MSYS_NO_PATHCONV=1 docker run --rm --privileged --network none -v <repo>:/src:ro -v <seg>:/seg:ro -v <out>:/out \
  cyberflow-etapa3-banco:1 bash -c 'cp -a /src /w && rm -rf /w/.git && cd /w && \
  python3 deploy/pruebas-aisladas/ensayo_via_rapida.py /seg /out C,A1,A2,B 3'
MSYS_NO_PATHCONV=1 docker run --rm --privileged --network none -v <repo>:/src:ro -v <seg-dns>:/seg:ro -v <out>:/out \
  cyberflow-etapa3-banco:1 bash -c 'cp -a /src /w && rm -rf /w/.git && cd /w && \
  python3 deploy/pruebas-aisladas/ensayo_limit_dns.py /seg /out'
```

### Pruebas

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python -m pytest -q -p no:cacheprovider tests/test_etapa3_dns.py tests/test_etapa3_http.py \
  tests/test_etapa3_publicador.py tests/test_escaneo_temprano.py tests/test_motor_incremental.py tests/test_motor_completitud.py
# → 68 passed, 2 subtests passed
```

`[LAPTOP Git Bash → Docker]` → lo ejecuté yo. Suite completa (nft y openssl reales):

```
MSYS_NO_PATHCONV=1 docker run --rm --privileged --network none -v <repo>:/src:ro cyberflow-etapa3-banco:1 \
  bash -c 'cp -a /src /w && rm -rf /w/.git && cd /w && python3 -m pytest -q -rs -p no:cacheprovider'
# → resultados/pruebas/pytest-completo-docker.txt : 626 passed, 1 skipped (sin node) en 585da7b
```

La primera ejecución (en `71b3ab6`) dio 1 fallo: `test_vista_vivo.py::test_matriz_de_trazabilidad` esperaba que `brute_force` leyera `http_auth_failure_ratio_60s`. La matriz se calcula leyendo `heuristicos.py` y era correcta: tras la Etapa 3, `brute_force` lee la vista HTTP. Se actualizó la prueba (`585da7b`), no la matriz.

```
```

Mutaciones (deben hacer fallar las pruebas): `guiones/mutar.py` cambia 8 condiciones, una cada vez:

- vía rápida: umbral K, copias del espejo y refractario;
- publicador: renovación solo con evidencia nueva;
- vista DNS: copias del espejo y reenvíos;
- vista HTTP: registros tardíos;
- port_scan: puertos distintos en la rama ráfaga.

Con cada mutación falla al menos una prueba (`resultados/pruebas/mutaciones.txt`; 8/8 «MUERTA»). El guion restaura los ficheros byte a byte.

### Verificación del manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo, sobre un clon disperso desde GitHub.

```
sha256sum -c MANIFIESTO.sha256
```
