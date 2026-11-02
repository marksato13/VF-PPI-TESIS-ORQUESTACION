# Matriz del cierre técnico de la Etapa 2

**Código:** rama `candidato/etapa2-20261101`, commits `3083f60` y `953a436`, sobre la base `2be5335`.

**Estados:**

- **Cerrado:** hay prueba y evidencia en este cierre.
- **Pendiente en vivo:** solo se puede comprobar en el laboratorio, y este encargo no permite hacerlo.
- **Etapa 3:** fuera del alcance de la Etapa 2.

Ningún punto se declara cerrado solo por pruebas unitarias cuando su efecto depende del laboratorio.

| # | Observación | Corrección | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|
| 10 | Pruebas | — | Suite completa en el banco :2 (Python 3.13.5, sklearn 1.4.2) con `953a436`; motor en Windows (Python 3.14.3, sklearn 1.9.1) | `resultados/pruebas/pytest-completo-v.txt`: 575 pasadas, 1 omitida (falta node); `pytest-motor-windows.txt`: 17 pasadas | Cerrado (no prueba el laboratorio) |
| 2.1 | El relé podía entregar una firma nueva con el feed anterior, o al revés | El relé solo entrega una pareja estable (dos lecturas iguales de feed y firma), de forma atómica, y la reintenta | `test_etapa2_correcciones.py` (firma nueva con feed anterior, feed nuevo con firma anterior, corrección de firma, lectura inestable, entrega parcial) | `resultados/pruebas/pytest-completo.txt` | Cerrado (banco) |
| 2.2 | El agente no reintentaba tras un fallo del helper | Reintento hasta confirmar; un feed repetido no amplía la caducidad | Pruebas «reintento tras fallo del helper» y «destino ausente + reinicio del relé + repetido» | ídem | Cerrado (banco) |
| 2.3 | Relé real por SSH | Comando forzado `cf-feed-ssh.sh`, cuenta `cffeed` nologin, feed 640 | S1–S5 (`ensayo_ssh_unidades.sh`, banco :3) | `resultados/ensayos/ensayo-ssh-unidades.*` | Cerrado en banco. Latencia SSH real: pendiente en vivo |
| 3 | El perfil del helper lo elegía quien lo invocaba | Perfil fijo por host, leído de un fichero de root (DC1 `dns`, srv-dmz `dmz`); se rechazan los perfiles cruzados | Perfil cruzado, operaciones fuera del contrato, nunca `ruleset`, C9 y S7 | `resultados/ensayos/ensayo-netns-dns.json` | Cerrado (banco). Instalación del fichero: pendiente en vivo |
| 4 | Características y scores distintos según la rotación y el disparo | Horizonte de entrada fijado por ventana | `HorizontePorVentana`; replays r1–r7 del tramo; completo cand frente a ref | Tramo: 0 de 1400 vectores distintos en las 7 configuraciones (antes, hasta 198 y 4 reglas). Completo: 0 de 9244 (`tramo-cierre.json`, `tramo-anterior.json`, `completo-cand-vs-ref.json`) | Cerrado (replay) |
| 4a | Conjunto de registros: ventanas vacías no causales | Se registra (E, A) si E tiene paquetes o L7 en (A−60, A] (`REGISTRO_S`) | Analizador del 3B sin ventanas ausentes del origen | Inventario 0 ausentes; 22 ventanas vacías menos en el control (2644 → 2622), con las mismas falsas alarmas | Cerrado (replay) |
| 4b | Diferencia de contrato: 230 s en el motor frente a hasta unos 15–20 min en el entrenamiento | No se corrige; **no se concluye que haya que reentrenar** | Cortes del bosque; replay de sensibilidad con 900 s | `cortes-flow-duration.json`, `sens900-*.json`; `DIAGNOSTICO…` §5.4 | Etapa 3 (medir el dataset de entrenamiento y decidir) |
| 4c | 14 `ventana_no_regenerada` en el completo (ninguna del origen ni del control) | No se corrige ahora (obligaría a repetir los replays) | Recalculo de la atribución en 2 casos | `verif-no-regeneradas.txt`: 0 observaciones en su propio horizonte; 10 y 9 con el horizonte de la ancla anterior | Etapa 3 (ajuste de la contabilidad de pendientes) |
| 5 | El reinicio perdía el historial (r7) | Reanudación desde la última ventana, rebobinado de EVE, relectura del anillo y `historial_completo` | `HorizontePorVentana`; r7; r8 con 6 reinicios durante cada tipo de tráfico | r8: 2378/2378 claves, 0 de 1822 vectores distintos, 0 duplicados y 0 pérdidas; recuperación de EVE completa en los 6 (`r8-vs-r8ref.json`) | Cerrado (replay). Rotación real de `eve.json`: pendiente en vivo |
| 6 | Validación offline de los 25 episodios | `analizar_3b.py` sin modificar sobre los replays completos | 25 episodios × 7 configuraciones, control y alarmas sobre otras entidades | 0 diferencias de categoría con el 3B en vivo revisado; población principal 15/25 con las mismas exclusiones; control con las mismas falsas alarmas (`VALIDACION-3B-25-EPISODIOS.md`) | Cerrado (replay). Continuidad ≤ 20 s en la inundación (r5): no resuelta |
| 6b | «Señal antes del fin» en `escaneo_breve-r1` | Corregido en las conclusiones (C10) | Lectura de la regla que dispara y del EVE | `brute_force` por 40 peticiones curl concurrentes; `port_scan` llega 5,9 s después del fin | Cerrado (conclusión) |
| 7 | El LIMIT no distinguía coincidencias de descartes | Set `descartes_limite` por origen, separado del contador del elemento | C8 (por debajo y por encima del límite, dos orígenes, renovación, caducidad); pruebas LIMIT con nft real | `resultados/ensayos/ensayo-netns-dns.json` | Cerrado (banco). Efecto en DC1: pendiente en vivo |
| 8 | Procedimiento de instalación y reversión | Revisado contra los scripts reales (P1–P8) y probado en el banco donde se puede | S6 (sudoers), S8 (`systemd-analyze`) | `PROCEDIMIENTO-INSTALACION-REVERSION.md` | Cerrado en banco. Venv de Sensor1 y sudo `Defaults`: pendiente en vivo |
| 9 | Conclusiones sobregeneralizadas | C1–C11 | — | `CONCLUSIONES-CORREGIDAS.md` | Cerrado |
| 9b | DNS a 5/s ineficaz | Queda pendiente: no se convierte en BLOCK ni se pide un número | C8 mide coincidencias, descartes y efecto | ídem | Etapa 3 |
