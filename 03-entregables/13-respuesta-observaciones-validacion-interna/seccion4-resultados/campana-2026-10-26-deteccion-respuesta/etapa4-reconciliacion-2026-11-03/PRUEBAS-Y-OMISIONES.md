# Pruebas y omisiones (reconciliación 2026-11-03)

Todas las salidas están en `evidencia/pruebas/`. `[LAPTOP]` → lo ejecuté yo. Los contenedores usan la imagen local
`cyberflow-etapa3-banco:1`, la misma del 2-nov.

## 1. Candidata de recuperación (producto, rama `recuperacion/etapa4a-20261103` @ b2f2994)

| Prueba | Dónde | Resultado | Fichero |
|---|---|---|---|
| Suite completa | Linux (Docker, `--cap-add NET_ADMIN`, `CAMPANA_DIR` = este repositorio) | **709 passed, 1 skipped** (sin node para el JS del panel) | `pytest-completo-linux-docker-b2f2994.txt` |
| Referencia 3a9f26b, 2-nov | Linux (Docker) | 708 passed, 2 skipped | `etapa4-correcciones-2026-11-02/evidencia/pruebas/` |
| Suite completa | Windows | 672 passed, 22 failed, 16 skipped: `test_f1_dataset_builder` (`WinError 6` al crear subprocesos), `test_f1_preflight` (bash de WSL), `test_feed` (claves en Windows), `test_storage_audit` (lsblk) y un reintento del helper; ninguno toca el código de la 4A | `suite-3a9f26b-windows.txt` |
| Condición previa v1 de `instalar_srvdmz_sombra.sh` | Linux (Docker) | **7/7** | `ensayo-precondicion-v1.txt` |
| Paquete de la candidata | Git Bash | 86 ficheros; el código es **idéntico** al paquete del 2-nov; solo cambian `deploy/etapa4/README.md`, `srvdmz/instalar_srvdmz_sombra.sh`, el nuevo `banco/ensayo_precondicion_v1.sh` y `VERSION-ETAPA4` | `evidencia/paquete/SHA256SUMS` |

La primera ejecución en Docker sin `NET_ADMIN` ni el repositorio de documentación dio 4 fallos de `nft`
(«Operation not permitted») y 6 omisiones de la compuerta. Se repitió en las condiciones del banco del 2-nov: no se
cambió ninguna prueba ni ninguna expectativa.

## 2. Herramientas de documentación corregidas

| Prueba | Resultado | Fichero |
|---|---|---|
| `herramientas/test_etiquetas_reconciliacion.py`: 6 casos nuevos y las **20 pruebas originales** de `tests/test_analizar_3b.py` y `tests/test_referencia_trafico_4c.py` contra las versiones nuevas (precargadas en `sys.modules`; sus expectativas no se tocan) | **26 passed** | `etiquetas-windows.txt` |
| Originales contra los originales | 20 passed | — |
| Reanálisis del 3B revisado con el analizador original y el nuevo | Categorías de las 7 configuraciones, población principal y recuento total de emisiones oportunas **idénticos**; se añaden las columnas por componente | `evidencia/reanalisis-3b-etiquetas/` |
| Banco de `g01` (SSH simulado, órdenes inofensivas, contenedor desechable) | **A–D OK**. A: el original para siempre con «ya hay un generador» sin generador alguno. B: el corregido lanza y lista 1 PID, el del python. C: detecta un generador vivo. D: ignora los señuelos que `pgrep -f` contaría (2) | `banco-g01.txt` |
| Banco de `k20` (canal simulado) | **8/8** | `banco-k20.txt` |

## 3. Las 16 omisiones de `tests/conftest.py` (rama as-deployed, ca66db5)

`tests/conftest.py` solo existe en as-deployed (lo añadió ca66db5). **No está en la candidata ni en la rama de
recuperación**, que no omite nada por política. Se comprobó cada omisión de dos formas:

1. con `--noconftest` en ca66db5, **las 16 fallan**;
2. en la etiqueta `demo-politica-AC-2026-11-03` (3f1bd9c), **las 16 pasan**.

Por tanto describen la política de la demo y no son regresiones ocultas del motor de las campañas. Ficheros:
`demo16-en-ca66db5-sin-conftest.txt` y `demo16-en-3f1bd9c.txt`.

| # | Prueba | Qué afirma (política de la demo) | Por qué falla con la de las campañas | ¿Omisión justificada? |
|---|---|---|---|---|
| 1 | `test_publicar_feed::DecisionesAEntradas::test_alerta_marginal_del_modelo_no_se_publica` | una ALERT a menos de 0,05 del umbral no se publica | `MARGEN_MARGINAL=0`: se publica (LIMIT a .21) | Sí: margen de la demo |
| 2 | `…::test_alerta_suelta_del_modelo_no_se_publica` | una ALERT suelta no basta | `MIN_VENTANAS_MODELO=1`: basta | Sí |
| 3 | `…::test_dos_ventanas_claras_no_bastan` | hacen falta 3 ventanas | 1 ventana basta | Sí |
| 4 | `…::test_politica_a_el_modelo_solo_no_publica` | `MODELO_SOLO_ACTUA` es False | es True | Sí: política A |
| 5 | `test_heuristico_icmp::IcmpFlood::test_el_flood_de_la_demo_bloquea` | la regla `icmp_flood` existe y bloquea | la regla se retiró (TypeError por `None`) | Sí: regla solo de la demo |
| 6 | `…::test_version_subida` | `VERSION_UMBRALES` = 2026-11-03.2 | es 2026-10-06.2 | Sí |
| 7 | `test_port_scan_rafaga_web::PortScan::test_250_descargas_al_puerto_80_no_son_escaneo` | con ratio 0,2 la ráfaga web no es `port_scan` | sin ratio: `port_scan`/BLOCK | Sí: umbral de la demo (la candidata lo resuelve con ratio 0,1) |
| 8 | `…::test_cliente_a_una_peticion_por_segundo_no_es_abuso` | `http_abuse` ≥ 200 | umbral 100: 122 req/60 s es abuso | Sí: umbral de la demo |
| 9 | `…::test_flood_de_la_demo_sigue_siendo_abuso` | el flood da `http_abuse`/LIMIT | gana `port_scan`/BLOCK | Sí |
| 10 | `test_alertas_panel::ReglaDeAccion::test_anomalia_del_modelo_solo_queda_para_revision` | el panel no da acción al modelo solo | el panel da LIMIT «anomalía del modelo» | Sí: espejo de la política A en el panel |
| 11 | `test_alertas_panel::AccionesVigentes::test_contadores_por_accion` | contadores sin el modelo solo (1,0,1) | (1,1,2) | Sí |
| 12 | `test_alertas_panel::Simulador::test_cada_ataque_produce_la_accion_del_motor_de_reglas` | el simulador sigue la política A | sigue la de las campañas | Sí |
| 13 | `test_escenario_vivo::Marginal::test_borde_del_umbral_es_marginal` | margen 0,05 en el panel | margen 0 | Sí |
| 14 | `test_escenario_vivo::Marginal::test_contadores_separan_relevantes` | ídem | ídem | Sí |
| 15 | `test_historial_acciones::Historial::test_una_alerta_suelta_del_modelo_no_es_episodio` | 3 ventanas para un episodio del modelo | 1 basta | Sí |
| 16 | `test_historial_acciones::Historial::test_una_racha_es_un_episodio_y_gana_la_accion_mas_severa` | la racha cuenta 1 episodio | cuenta 4 | Sí |

**Prueba 17, no omitida y en fallo (regresión de ca66db5 en su propia suite):**
`test_almacen_decisiones::Almacen::test_la_ventana_nueva_vuelve_sostenida_a_la_anterior` espera que 2 ALERT sean
«suelta» y la 3.ª las vuelva «sostenida». Con `MIN_VENTANAS_MODELO=1`, 2 ALERT ya son «sostenida»: falla en ca66db5
y pasa en 3f1bd9c. Depende de la política igual que las 16, pero el conftest no la lista. **No se ha corregido ni
omitido**: as-deployed no es la base de la recuperación, y ocultarla cambiando la lista sería justo lo que el encargo
prohíbe. Se recomienda parametrizarla por la política (o fijar `MIN_VENTANAS_MODELO` dentro de la prueba) cuando se
trabaje en el panel.

Totales en Windows: ca66db5 con su conftest, 28 failed, 476 passed, 16 skipped; 3f1bd9c, 22 failed, 498 passed.
De la diferencia de 6 fallos, 1 es la prueba 17. Los otros 5 (`test_f1_dataset_builder`) fallan en las dos
referencias cuando se lanzan aislados (`WinError 6`), así que son del entorno.
