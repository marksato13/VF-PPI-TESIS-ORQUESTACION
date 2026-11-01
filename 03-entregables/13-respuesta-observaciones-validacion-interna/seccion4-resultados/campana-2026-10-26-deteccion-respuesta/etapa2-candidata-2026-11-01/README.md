# Etapa 2: desarrollo y validación técnica de la candidata (1-nov-2026)

**Alcance.** Todo se hizo en una rama candidata, en un banco aislado (Docker `--network none`) o en replays sobre datos archivados del 3B. **No se desplegó, reinició ni reconfiguró nada del laboratorio. No se activaron agentes, no se ejecutaron ataques, no se instaló nada en DC1 y no se avanzó a la Etapa 3.** Las únicas acciones sobre el laboratorio fueron lecturas de solo lectura en el sensor, srv-dmz y DC1.

- Código: rama `candidato/etapa2-20261101`, commit **`2be53351fb47d03628d96c179078bf00c8105813`** (ver [REFERENCIAS.md](REFERENCIAS.md)).
- Convención de cada dato:
  - **MEDIDO**: observado en el sensor (lectura), en el banco con procesos y nft reales, o en los datos archivados;
  - **SIMULADO**: replay del motor con reloj simulado y la CPU del portátil, o el publicador real alimentado con decisiones de replay;
  - **PENDIENTE**: no hecho.

## Documentos

| Documento | Puntos del encargo |
|---|---|
| [PROTOTIPO-ROTACION-Y-DISPARO.md](PROTOTIPO-ROTACION-Y-DISPARO.md) | 1, 4: rotación de 5 s, disparo por eventos, 7 replays, contenido frente a disponibilidad, tiempos, memoria, reinicio y retraso |
| [DIAGNOSTICO-DESCARTES-SURICATA.md](DIAGNOSTICO-DESCARTES-SURICATA.md) | 3: descartes por capas, hipótesis, cambios candidatos y procedimiento reversible (no aplicado) |
| [CONTRATO-FEED-V2.md](CONTRATO-FEED-V2.md) | 5, 6: contrato firmado con destino y alcance, pruebas de aislamiento y cadena |
| [INSTRUMENTACION-Y-PERMISOS.md](INSTRUMENTACION-Y-PERMISOS.md) | 5, 7: identificadores por punto, helper root restringido y permisos |
| [PRESUPUESTO-ESCANEO-Y-REGLAS-E3.md](PRESUPUESTO-ESCANEO-Y-REGLAS-E3.md) | 6, 8, 9: presupuesto del escaneo breve, N de DNS, atribución DNS, HTTP/escaneo, renovaciones sin tráfico, 7 configuraciones, limpieza |
| [PROCEDIMIENTO-INSTALACION-REVERSION.md](PROCEDIMIENTO-INSTALACION-REVERSION.md) | 7: instalación, comprobación y reversión (preparado, **no ejecutado**) |
| [MATRIZ-REQUISITOS.md](MATRIZ-REQUISITOS.md) | 10: requisito → implementación → prueba → evidencia → estado |
| [REFERENCIAS.md](REFERENCIAS.md) | 2: commits, ramas y sha256 |
| `resultados/` | Salidas literales: pytest, ensayos, comparación de replays, tasa DNS, renovaciones y reinicio |
| `evidencia/` | Lecturas de solo lectura del sensor (Suricata por capas y AF_PACKET) |
| `herramientas/` | Copias exactas de los scripts usados, para reproducir sin la rama |
| `MANIFIESTO.sha256` | Integridad de todo lo anterior |

## Resultados principales

**1. Rotación y disparo** (SIMULADO, tramo 08:40–09:05 del 3B, 5 episodios):

- Con la rotación de 5 s y el disparo por eventos (r4), la latencia mediana ventana → decisión baja de **13,7 a 3,9 s** en las ventanas con tráfico. La detección de la fuerza bruta y del DNS baja de unos 29 a **unos 10 s** desde el inicio del episodio.
- **Las 28 características y las anclas de 10 s se conservan.** Las decisiones son iguales en 2231 de 2231 ventanas comunes; la clase α en 2229 de 2231.
- La única característica sensible a la rotación es `flow_duration_mean_30s`, que también varía entre los PCAP originales y los emulados de 15 s.
- **La cola p90 no mejora** (unos 38 s): la limita la escritura tardía del EVE.
- Memoria sin cambios (unos 860 MB de pico); el doble de ciclos, cada uno más ligero.
- **En el Sensor1 no se ha medido nada de esto** (P-1).

**2. Escaneo breve** (MEDIDO en el PCAP archivado; tiempos SIMULADOS):

- El episodio dura 18 s, pero **la ráfaga real dura unos 4,9 s** (08:47:40,0–44,9, 2016 SYN).
- La primera ventana de 10 s que la contiene termina 5,1 s **después** del último SYN.
- **Con capturas por ficheros no se puede cortar mientras dura**, ni siquiera con 5 s y una regla temprana. La cota estimada es unos 3,8 s después del fin, sin contar el ssh.
- Hoy se decide 27,5 s después del fin; el candidato lo haría 8,5 s después.
- Cortarlo durante la ráfaga exige inspección en línea: es un cambio de arquitectura y no se propone.

**3. Renovaciones sin tráfico** (SIMULADO con el `incorporar` real del publicador v2):

- La misma decisión releída no renueva nada (probado).
- Pero las ventanas **sin tráfico propio** del origen (cola de las reglas de 60 s) crean **63 de las 115 entradas** del tramo. Prorrogan la restricción hasta unos 190 s y aportan peldaños de escalera, hasta 126 s después del fin del ataque.
- Filtrarlas (R-E3.1) deja 52 entradas **sin perder ninguna detección**. **No está implementado.**

**4. Límite DNS ineficaz** (MEDIDO en el EVE archivado):

- El escenario va a 2,3 consultas/s, y el N candidato del helper es 5/s: **el LIMIT de DNS no recortaría el escenario.**
- Los clientes legítimos tienen picos de hasta 9 en 1 s y no pasan de 0,9/s sostenido en 10 s.
- 90/minuto (1,5/s) con ráfaga 10 separaría con poco margen y solo recortaría el escenario en torno a un 35 %.
- Decisión D-N, pendiente de Mark. El helper sigue con 5/s.

**5. Falsas alarmas reales** (MEDIDO sobre las reglas en el replay):

- DC1 dispara `dns_entropy` en todo el tramo (78 ventanas): reenvía a pfSense consultas `*.francos-sac.com` que acaban en NXDOMAIN. No se restringe porque está en NUNCA.
- El cliente legítimo **10.10.20.26** dispara `http_abuse` en 2 ventanas, y el candidato le pondría un LIMIT.
- La métrica de alarmas se corrigió para contar las de otras IPs durante los episodios.
- HEUR: 5/5 detecciones y 81 falsas alarmas en total. IF α = 0,05: 279.

**6. Cadena por eventos** (MEDIDO en el banco, sin ssh): 20 de 20 decisiones confirmadas en nft, con p50 de **1,43 s** desde `logged_at`. Reintento ante un destino ausente, reinicio del agente sin pérdidas y repetición sin entradas nuevas.

**7. Pruebas** (MEDIDO, banco `cyberflow-etapa2-banco:2`):

- Etapa 2: **76/76**.
- Batería base: **461 OK y 1 omitida**. Los 18 fallos previos eran por falta de `git` en la imagen :1; ya está corregido.
- Ensayo netns DNS: **8/8**.
- Ensayo de la cadena: **PASA**.

## Resumen final

| | |
|---|---|
| **Implementado** (rama candidata) | Disparo por cierre de fichero; instrumentación con `decision_id`, `ciclo_n`, `disparo` y todas las reglas; troceador y arnés de replay; feed v2 firmado con destino, alcance, secuencia y caducidad; publicador con `if_senal` y sin renovación por reprocesar; relé por eventos con reintento; agente v2; helper root con validación JSON y sudoers sin argumentos; perfiles dmz y dns en tablas propias; LIMIT y contadores por origen; DC2 en NUNCA; limpieza D5 en seco; unidades y procedimiento de instalación y reversión. |
| **Probado** | En el banco: contrato y rechazos, helper con nft real, aislamiento DNS (netns), cadena completa sin ssh y limpieza. En replay: equivalencia de contenido con 5 s, latencias, retraso, reinicio y siete configuraciones. Detalle en la [MATRIZ](MATRIZ-REQUISITOS.md). |
| **Pendiente** | P-1, ciclo del motor candidato en el Sensor1. P-2, latencia ssh del relé. P-3, efecto de `-G 5` en los descartes y el disco. P-4, replays del 3B completo. P-5, causa de la deriva de `flow_duration_mean_30s`. M-S1, anillo AF_PACKET efectivo (sudo de Mark). Desfase de reloj de DC1. Kernels reales de srv-dmz y DC1 (solo comprobados sobre el papel). Requisitos R-E1 (regla temprana), R-E2 (atribución DNS), R-E3.1 (sin colas) y R-E3.4 (umbral de `http_abuse`), **no implementados**. Decisiones de Mark: α, D-N (valor de N para DNS) y si se aplica R-E3.1. |
| **¿Se puede empezar la Etapa 3?** | **No sin decisiones previas de Mark.** Lo técnico de la cadena está listo para instalarse **en sombra** siguiendo el procedimiento. Pero, si se pasara a aplicar tal cual: (a) un cliente legítimo (10.10.20.26) recibiría LIMIT; (b) las colas sin tráfico prorrogarían las restricciones; (c) el LIMIT de DNS no actuaría sobre el escenario. Recomendación: aprobar o rechazar R-E3.1, R-E3.4 y D-N; autorizar la instalación en sombra (sin `--aplicar`) para medir P-1 y P-2; y solo después pasar a aplicar. **Nada de esto se ha iniciado.** |
