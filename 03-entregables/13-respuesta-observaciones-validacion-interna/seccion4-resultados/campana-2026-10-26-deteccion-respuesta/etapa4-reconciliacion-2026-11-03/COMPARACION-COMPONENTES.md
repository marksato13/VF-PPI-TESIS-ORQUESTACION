# Comparación por componente: investigación frente a demostración (2026-11-03)

Columnas:

- **Antes de la demo:** lo que había en el Sensor1 según la lectura del 2-nov (`etapa4-preparacion-2026-11-02/ESTADO-OBSERVADO-LABORATORIO.md`): motor 24f8a80 y cadena v1 del snapshot as-deployed f57ca00.
- **Candidata:** rama `candidato/etapa3-20261102` @ 3a9f26b. El código que se instala es ec78ca5.
- **Publicada:** rama `as-deployed-sensor-20261006` @ ca66db5.
- **Laboratorio:** blobs y sha256 leídos en la máquina, en solo lectura, el 2026-11-04 entre 00:54 y 01:04 UTC (`evidencia/laboratorio/`).

Los commits de la demo, en orden, son estos (todos en as-deployed; ninguno toca la rama candidata):

1. `6d560d8`, `3e6f849`: panel.
2. `5a9eb11`, `72a7a40`, `4e7e59b`: agente v1 (alcance, liberación, gracia).
3. `e41480a`: panel, acuse y relé.
4. `3f84a3c`: panel.
5. **`866ebbf`**: demo defendible.
6. `04e8b99`: Preparar demo.
7. `7f4e8b6`: panel ligero.
8. **`4ea1c68`**: política A+C e `icmp_flood`.
9. `46e8596`, `0cc1125`: contadores del panel.
10. `3f1bd9c`: G1–G3.
11. **`ca66db5`**: vuelta a la política de las campañas.

## 1. Detector: lo que **no** cambió en ningún sitio

| Componente | Antes de la demo | Candidata | Publicada (ca66db5) | Laboratorio | Diferencia funcional | Efecto sobre evaluaciones | Recomendación |
|---|---|---|---|---|---|---|---|
| Esquema y 28 características (nombre, orden, capa, ventana, unidad, fuente) | idéntico | idéntico | idéntico | blob `9560ce9` (en ningún commit, por los bytes), **semánticamente idéntico** a 7b275b8, 24f8a80, 6b6ef82, ec78ca5, 3a9f26b, f57ca00 y ca66db5 | ninguna | ninguno | Conservar. Comparación en `evidencia/laboratorio/comparacion-esquema-28.txt` |
| Fórmulas (`extract_multilayer.py`, `_v2`, `_v3`, `acumular_v3`) | iguales | iguales | iguales | mismos blobs en **todas** las referencias | ninguna | ninguno | Conservar |
| Modelo y escalador (pipeline IF, el escalador va dentro) | `if_limpio_2026_10_desplegable.joblib` | misma ruta (drop-in `etapa4.conf`) | — | sha256 `df547da0…a2fd60` = `model_sha256` del manifiesto; sklearn 1.9.0, numpy 2.5.1 | ninguna | ninguno | No reentrenar ni recalibrar (fuera del encargo) |
| Manifiesto y umbral desplegado | `manifest-if-limpio-2026-10.json`, umbral −0,5693969936 | mismo | — | sha256 `b3ad6805…aa2a9e7`; FPR validación 0,050005, prueba 0,045261 | ninguna | ninguno | Conservar |
| α 0,05 / 0,03 / 0,01 | analizador | `UMBRALES_ALFA` de `publicar_feed_v2.py` (calibración 24-oct: −0,56946 / −0,58985 / −0,62239) y analizador | — | — | ninguna | ninguno | **Mantener las tres en la comparación, sin elegir.** El 0,05 calibrado difiere en 6·10⁻⁵ del umbral del manifiesto: se publican los dos, como en el 3B |

## 2. Motor y captura

| Componente | Antes de la demo | Candidata | Publicada | Laboratorio | Diferencia funcional | Efecto | Recomendación |
|---|---|---|---|---|---|---|---|
| `motor_decision.py`, `motor_incremental.py` | 24f8a80 | ec78ca5 (`b652582d…`, `95f3cd2e…`) | 7b275b8 (as-deployed **no** coincide con el laboratorio) | **24f8a80** (blobs `068c025`, `1197907`) | ec78ca5: disparo por eventos, horizonte fijado por ventana, recuperación al arrancar, `decision_if`, `auth_failure` {histórico, vista, autoriza}, `heuristicos` (todas las reglas), vistas HTTP y DNS, deduplicación del espejo. **Sin cambios en modelo, escalador, 28 características ni umbrales** (49a29db, replays del cierre de la Etapa 3) | La 4C es la primera medida en vivo de ec78ca5. Los registros de 24f8a80 solo guardan la regla de mayor prioridad | Instalar ec78ca5 en sombra (4A). No usar ca66db5 como base del motor: no es lo que corre |
| `heuristicos.py` | 2026-10-06.2 (ráfaga sin ratio de puertos, `http_abuse` ≥ 100/60 s sobre columnas del IF) | 2026-11-02.1: ráfaga `port_scan` con ratio ≥ 0,1; `http_abuse` 600/60 s y `brute_force` sobre la vista HTTP; `dns_entropy` sobre la vista DNS (≥ 30 consultas, ≥ 0,8 nombres únicos); sin `icmp_flood` | 2026-10-06.2 (ca66db5 devolvió el de e41480a) | `ec0fe9e` = pre-demo | **866ebbf** subió el ratio de la ráfaga a 0,2 y `http_abuse` a 200; **4ea1c68** añadió `icmp_flood` (≥ 200 pps y ≥ 80 % ICMP → BLOCK); ca66db5 retiró ambos | Los ajustes de la demo resolvían por su cuenta los mismos falsos positivos que la candidata resuelve con las vistas. `icmp_flood` no tiene equivalente en la candidata: con `if_senal`, un flood ICMP solo da señal del IF | Base: la de la candidata. **No trasladar** 0,2 ni 200 (calibrados a ojo para la demo). `icmp_flood`: propuesta aparte, con escenario y control propios; no entra en 4A–4C |
| Captura (`ppi-motor-capture`) | tcpdump `-i ens37 -G 15`, sin `-W` | drop-in `-G 5`, más `cf-tcpdump-estadisticas` (SIGUSR1) | — | `-G 15` | anillo de 5 s y contadores de descartes medidos | Las clases C0–C3 dependen de las estadísticas SIGUSR1 | Instalar el drop-in en la 4A |
| Exclusiones | `--excluir` (gestión) y `--excluir-protocolos 112,240` | iguales | — | iguales | ninguna | El canal SSH bastión↔Kali **no** se excluye (alimenta las ventanas de la Kali) | Igualar la exposición con `k20` (§5 del README) |

## 3. Publicación, transporte y aplicación

| Componente | Antes de la demo | Candidata | Publicada | Laboratorio | Diferencia funcional | Efecto | Recomendación |
|---|---|---|---|---|---|---|---|
| Publicador | v1 `publicar_feed.py` (f57ca00): el modelo solo publica LIMIT en la primera ALERT; renueva al reprocesar | v2 `publicar_feed_v2.py` (`5733f17d…`), `--politica if_senal`: **el IF puntúa y da señal (`senales-if.jsonl`), solo las reglas autorizan**; cada acción nace de un `evento_id`; renovación solo con evidencia reciente; `NUNCA_BLOQUEAR_V2` | v1 de ca66db5: `MODELO_SOLO_ACTUA=True`, `MARGEN_MARGINAL=0`, `MIN_VENTANAS_MODELO=1` (equivale al de antes), con dos añadidos: a igual severidad gana la regla (cambia el motivo, no la acción) y liberaciones «Preparar demo» dentro del feed firmado | `8d368d9` = **ca66db5**. ExecStart con `--umbrales 2026-10-06.1`; el feed declara 2026-10-06.2 | 866ebbf (margen 0,05 y 3 ventanas), **4ea1c68** (el modelo solo no publica: política A) y **ca66db5** (vuelta al modelo que actúa) | La política A de la demo se parecía a `if_senal`, pero por otra vía (sin señales separadas ni `evento_id`) | Base: v2 `if_senal`. **No usar** la política A de la demo. Las liberaciones del feed son útiles en la campaña B, no en 4A |
| Relé | v1 `relay-feed.sh` (scp cada 10 s) | `relay_eventos.py` (`e24aefb2…`) y `ppi-relay-eventos.service`; el v1 sigue en paralelo | v1 + **e41480a** (devuelve el acuse del host al sensor) | md5 = ca66db5 + `\r\n` final | e41480a añade el acuse | Ninguno en la detección | v1 intacto en la 4A (como estaba previsto); v2 se instala aparte |
| Agente srv-dmz | v1 `agente_enforce.py`, **disabled/inactive** el 2-nov | v2 `agente_enforce_v2.py` (`00b9d7ba…`), perfil `dmz`, helper con perfil impuesto, **sin `--aplicar`** | v1 con alcance `nunca`/`solo` (`5a9eb11`), liberación humana y gracia (`72a7a40`, `4e7e59b`), Preparar demo (`04e8b99`) y acuse (`e41480a`) | **ppi-enforce-agent.timer enabled/active desde el 03-nov 02:50 UTC con `--aplicar --sudo`**; tabla `inet cyberflow` con un LIMIT a **10.10.20.21** (cliente legítimo) a las 01:04 UTC del 04-nov | El laboratorio **aplica**, no está en sombra | **Bloquea la 4A:** `estado_sombra.py` daría rc 1 y la medida de control quedaría contaminada | Fase **P0** (Mark, autorización expresa): parar y deshabilitar el timer v1 y retirar la tabla v1, con respaldo. El instalador corregido (b2f2994) para si no se hizo. Alcance, liberación humana, gracia y acuse son útiles para la campaña B: portarlos al v2 aparte, con pruebas |
| Renovación de medidas | v1: reprocesa las últimas decisiones cada 10 s (renueva sin evidencia nueva) | v2: solo con evidencia reciente; ec78ca5 retira las 8 renovaciones sin evidencia del replay | v1 | v1 | — | Afecta a la duración de las medidas y a las cuentas de la campaña B | Base v2 |
| Liberación manual | no había | no hay | gracia, `--liberar` por detector y «Preparar demo» por feed firmado | presente (v1) | — | Solo con respuesta activa | Conservar el diseño como propuesta para la campaña B; no se instala en la 4A |

## 4. Panel

| Componente | Antes de la demo | Candidata | Publicada | Laboratorio | Diferencia funcional | Efecto | Recomendación |
|---|---|---|---|---|---|---|---|
| `dashboard.py` | f57ca00 | sin cambios del panel | ca66db5: recorte, Escenario en vivo, acuse, Preparar demo, panel ligero (`7f4e8b6`), contadores, **G1–G3** (`3f1bd9c`); `MODELO_SOLO_ACTUA` y `MARGEN_MARGINAL` copiados en Python y JS | `9604d11` = ca66db5 | El panel **calcula su propia acción** a partir de `motor_decision.log` con la política v1 (el modelo solo → LIMIT). No lee el feed v2 ni las señales | **En la 4A–4C el panel no corresponde a lo publicado:** el motor candidato escribe en el mismo log y el panel mostraría LIMIT del modelo que `if_senal` no publica. Tampoco ve la aplicación del agente v2 | Las mejoras visuales se conservan en as-deployed, por separado. Para integrarlas con la candidata, el panel debe leer `senales-if.jsonl`, la traza del publicador v2 y la del agente v2, y separar anomalía, decisión, medida publicada, aplicación confirmada y efecto observado. Mientras tanto, la evidencia de 4A–4C sale de los ficheros, no del panel |
| Copia local en `producto-main` | — | — | — | — | `scripts/engine/dashboard.py` con 336+/39− sin confirmar | — | Conservada en `evidencia/git/preservado-producto-main-dashboard.patch`; no se toca |

## 5. Pruebas (detalle en PRUEBAS-Y-OMISIONES.md)

| Referencia | Resultado |
|---|---|
| Recuperación b2f2994 (Linux, Docker) | ver `evidencia/pruebas/pytest-completo-linux-docker-b2f2994.txt` |
| ca66db5 con su conftest (Windows) | 28 fallos, 476 pasan, 16 omitidas |
| 3f1bd9c (etiqueta de la demo, Windows) | 22 fallos, 498 pasan |
| Las 16 omitidas | fallan en ca66db5 sin el conftest y pasan las 16 en 3f1bd9c |
| Diferencia ca66db5 − 3f1bd9c | `test_almacen_decisiones::test_la_ventana_nueva_vuelve_sostenida_a_la_anterior` falla en ca66db5 y **no** está entre las omitidas (depende de `MIN_VENTANAS_MODELO`). Los otros 5 (`test_f1_dataset_builder`) fallan en las dos por un error de Windows (`WinError 6`) según cómo se lancen |
