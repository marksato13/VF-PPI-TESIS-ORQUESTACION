# Matriz requisito → implementación → prueba → evidencia → estado (Etapa 2)

Estados:

- **Probado:** hay evidencia literal en `resultados/` o en `evidencia/`.
- **Implementado, no probado:** el código existe pero falta la prueba o su evidencia.
- **Medido:** hay un dato, pero no se ha cambiado nada.
- **Pendiente:** no hecho.
- **Requiere a Mark:** necesita sudo, autorización o una decisión.

Ninguna fila se da por superada sin evidencia. Rutas de código relativas a la rama `candidato/etapa2-20261101`, cuyo hash está en [REFERENCIAS.md](REFERENCIAS.md).

| # | Requisito del encargo | Implementación | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|
| 1.1 | Reducir la espera de captura | Rotación de 5 s **emulada** (`trocear_pcap.py`); en el sensor sigue siendo `tcpdump -G 15`, porque no se ha reconfigurado nada | Replays r2 (15 s) frente a r3/r4 (5 s) | `comparacion-replays-tramo.json` | Probado en replay; **no instalado** |
| 1.2 | Reducir la espera de procesamiento | `--disparo eventos` en `motor_decision.py` (por cierre de fichero, sondeo 0,25 s, plazo = paso) | `test_etapa2_disparo.py` (9) y replays r4–r7 | `pytest-etapa2.txt`, `comparacion-replays-tramo.json` | Probado en replay y en pruebas unitarias |
| 1.3 | Medir la cadena completa | `decision_id`, `ciclo_n` y `disparo` en el motor; trazas del publicador, el relé y el agente (`INSTRUMENTACION-Y-PERMISOS.md`) | `ensayo_cadena_eventos.py` | `ensayo-cadena-eventos.json` | Probado en el banco; **sin el tramo de ssh** |
| 1.4 | Separar srv-dmz de DC1 | Feed v2 con `destino`/`alcance`, perfiles dmz y dns, tablas distintas | pytest (destinos simultáneos), netns C7 | `pytest-etapa2.txt`, `ensayo-netns-dns.json` | Probado en el banco |
| 2 | Commits y hashes | — | — | `REFERENCIAS.md` | Hecho |
| 2.b | Banco de pruebas reproducible | `Dockerfile` (imagen :2 con git) | Batería completa | `pytest-etapa2.txt`: 76/76 de la Etapa 2; 461 OK y 1 omitida en la base | Probado |
| 3 | Diagnóstico de descartes de Suricata por capas | — (solo lecturas) | Lecturas acumuladas y deltas en el sensor | `DIAGNOSTICO-DESCARTES-SURICATA.md`, `evidencia/sensor-*.txt` | Medido. El anillo AF_PACKET efectivo no se pudo leer (M-S1 necesita sudo) → **requiere a Mark** |
| 3.b | Cambios candidatos y procedimiento reversible | C1–C4 descritos, **no aplicados** | — | `DIAGNOSTICO-DESCARTES-SURICATA.md` | Preparado |
| 4.1 | Rotación de 5 s con anclas de 10 s y 28 características | Sin cambios en el extractor ni en el esquema | Replay r3 frente a r2: mismas claves; vectores distintos acotados | `comparacion-replays-tramo.json` → `contenido_vs_referencia` | Probado (ver `PROTOTIPO-ROTACION-Y-DISPARO.md`) |
| 4.2 | Comparar claves, deduplicación, atribución, características, scores y α | `comparar_replays.py` | r1, r3–r7 frente a r2 | ídem | Probado |
| 4.3 | Ficheros retrasados, vacíos, incompletos, rotaciones y reinicios | Lector de ficheros cerrados; `--retraso-cierre`, `--reiniciar-en` | `test_etapa2_disparo.py`; r6 (retraso de 3 s), r7 (reinicio) | `pytest-etapa2.txt`, `comparacion-replays-tramo.json` | Probado |
| 4.4 | Separar contenido de disponibilidad | `comparar_replays.py`: `contenido` y `disponibilidad` | — | ídem | Probado |
| 4.5 | No usar ficheros abiertos ni EVE futuro | `list_closed_pcap_files`; arnés con la disponibilidad EVE por máximo acumulado | `test_fichero_abierto_no_dispara`; arnés de replay | `pytest-etapa2.txt` | Probado |
| 4.6 | Tiempos por etapa, memoria y acumulación | `ciclos-arnes.jsonl` (duración, RSS, pico), `pendientes_por_ciclo` | Replays | `comparacion-replays-tramo.json` → `disponibilidad` | Medido |
| 5.1 | Publicador, relé y agentes por eventos | `publicar_feed_v2.py --seguir`, `relay_eventos.py`, `agente_enforce_v2.py --seguir` | `ensayo_cadena_eventos.py` | `ensayo-cadena-eventos.json` | Probado en el banco |
| 5.2 | Firma y caducidad | ed25519 sobre el JSON canónico; `expira`, `hasta` ≤ 3720 s | pytest (firma inválida, caducado, del futuro) | `pytest-etapa2.txt` | Probado |
| 5.3 | Duplicados, fuera de orden, reinicios, fallos de comunicación | `secuencia`, `repetido`, `id_duplicado`; reintento por destino en el relé; el agente no avanza la secuencia si falla el helper | pytest y el ensayo de la cadena (reinicio del agente dmz, dc1 ausente) | `pytest-etapa2.txt`, `ensayo-cadena-eventos.json` | Probado |
| 5.4 | No renovar por reprocesar | `hasta` fijado una vez por `evento_id` desde `logged_at` | `test_agente_releer_mismo_id_no_renueva`, `test_reprocesar_mismo_evento_no_renueva`, el ensayo de la cadena (`decision_repetida_genero_nuevos = 0`) | ídem | Probado. **Observación SIMULADA con el publicador real:** las ventanas sin score crean 63 de 115 entradas y prorrogan la restricción hasta unos 190 s (`renovaciones-sin-trafico-*.json`). Requisito R-E3.1, **no implementado** |
| 6.1 | Agente DNS con nft en un entorno aislado | Perfil `dns` del helper (tabla `inet cyberflow_dns`, solo `th dport 53`) | netns C1–C5 | `ensayo-netns-dns.json` | Probado en el banco (no en DC1) |
| 6.2 | Feed con alcance y destino firmados; srv-dmz comprueba `alcance` | `validar_v2` | pytest (alcance `all` del v1 rechazado, par no permitido) | `pytest-etapa2.txt` | Probado |
| 6.3 | Acciones simultáneas sobre la misma IP con destinos distintos | `id` por (ip, destino, alcance, acción, evento); escalera por `ip@destino` | pytest y netns C7 | ídem | Probado |
| 6.4 | Entradas antiguas o con alcance desconocido | `version_no_soportada`, `alcance_desconocido`, `entrada_caducada` | pytest | ídem | Probado |
| 6.5 | DC2 en las excepciones sin excluirlo de la evaluación | NUNCA += 10.10.10.21 en el publicador, el agente y el helper; el motor no lo excluye | pytest (rechazo del helper y publicador) | ídem | Probado |
| 6.6 | Caducidad, reinicio y reversión | Timeout nativo de nft; `desinstalar` | netns C4/C5, pytest (ciclo real del helper) | ídem | Probado |
| 6.7 | Justificar N o reconocer que no separa (unas 2,3 consultas/s) | `tasa_dns_por_origen.py` | — | `tasa-dns-por-origen.json`; `PRESUPUESTO-ESCANEO-Y-REGLAS-E3.md` §3 | **Medido: N = 5/s NO separa.** 90/min con ráfaga 10 separaría con margen pequeño; decisión D-N de Mark |
| 7.1 | Contadores por origen y acción | `counter` por elemento y por regla | netns C6 (cubos por origen) | `ensayo-netns-dns.json` | Probado |
| 7.2 | Helper root restringido en lugar de `sudo nft -f -` | `cf_nft_helper.py` + sudoers sin argumentos | 16 rechazos + lote mixto + orden con argumentos | `pytest-etapa2.txt` | Probado en el banco |
| 7.3 | Instalación y reversión preparadas | `PROCEDIMIENTO-INSTALACION-REVERSION.md`, unidades y sudoers en `deploy/enforcement/candidato-etapa2/` | — | — | Preparado, **no ejecutado** (requiere a Mark) |
| 8 | `if_senal` en el publicador; 7 configuraciones y 3 α | `acciones_de(politica="if_senal")`; `siete_configuraciones` | pytest (`if_senal` no restringe); replays | `comparacion-replays-tramo.json` | Probado (tramo de 25 min). α sin elegir |
| 9.1 | Presupuesto del escaneo breve | Análisis del PCAP y los replays | — | `PRESUPUESTO-ESCANEO-Y-REGLAS-E3.md` §1 | Medido: no se puede cortar durante el escaneo con ficheros |
| 9.2 | Requisitos: regla temprana, atribución DNS, HTTP/escaneo, tráfico confundible | R-E1, R-E2, R-E3 (incluido R-E3.4: `http_abuse` contra el cliente legítimo 10.10.20.26) | — | ídem §2–4 | Requisitos escritos; **no implementados** |
| 9.4 | Efecto del reinicio del motor | Replay r7 | `efecto_reinicio.py` | `efecto-reinicio-r7.json` | Simulado: 16 ventanas cambian durante unos 50 s, todas a menos alarma |
| 9.3 | Limpieza en seco (respaldo, publicador, escalada, dos agentes, comprobación) | `limpiar_origen.py`, `retirar_origen` | 3 pruebas de limpieza | `pytest-etapa2.txt` | Probado en el banco |
| 10 | Entregables en Git y manifiesto | Esta carpeta | `MANIFIESTO.sha256` verificado contra origin | `REFERENCIAS.md` | Ver `README.md` |
