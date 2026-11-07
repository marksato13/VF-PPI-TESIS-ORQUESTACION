# Banco de temporización a 8× — pendiente, no publicado

Dos suites completas de E-carga ejecutadas en contenedores sin red, en serie y sin otra prueba Docker en paralelo. La única modificación del producto, sin commit, está en `tests/test_etapa4_ecarga_guardia_s7.py`: recorrido a 8× y timeout de 900 s; fin/parada de `test_c1_arranque_normal_y_parada_a_su_hora` a 30/25 s. No se cambiaron guiones de producción ni criterios.

- `nueva-8x-65534.txt`: `RC_PYTEST=1`, 221 pasaron; `test_regresion_cruce_arranque_parcial` recibió C1 rc 2 en vez de rc 3.
- `nueva-8x-root.txt`: `RC_PYTEST=1`, 221 pasaron; `test_puerta_solicitud_previa[PARADA-NO-CONFIRMADA]` recibió el motivo `T_g ya pasó al llegar a C1`.

La causa no está demostrada. Esta carpeta es evidencia local **sin commit y sin publicación**. Las salidas fallidas anteriores permanecen intactas en la evidencia 21 publicada.