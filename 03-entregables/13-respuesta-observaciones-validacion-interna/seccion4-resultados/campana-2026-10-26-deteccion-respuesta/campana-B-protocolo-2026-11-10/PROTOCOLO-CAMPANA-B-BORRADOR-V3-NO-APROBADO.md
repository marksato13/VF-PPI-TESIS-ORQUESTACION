> **BORRADOR v3, NO APROBADO, SIN EJECUTAR, SIN PUBLICAR.** Se escribe el 10-nov-2026 para que Mark lo revise al cerrar la Campaña A. No activa nada: el agente de srv-dmz y el publicador siguen en sombra. La ejecución de B se autoriza **por separado**, con fecha y hora, y la publicación también. Sustituye al borrador v2 del 08-nov (`../campana-B-borrador-local-2026-11-08/`), que se conserva.

# Protocolo de la Campaña B (respuesta en vivo) — borrador v3

**Objetivo (OBJETIVOS-Y-CRITERIOS §1.2):** comprobar la **aplicación y el efecto** de la respuesta sobre tráfico real: 25 episodios (5 por escenario) con E1–E5 evaluadas por separado. B **no sustituye a A** en la comparación de detectores.

**Qué mide solo B:** `t_apl` (regla cargada en el host), el transporte real publicador → relé → agente, y la reacción de `nmap` real a la restricción (E3). La A no tiene ninguna de esas medidas.

## 1. Lo que cambió desde el borrador v2

| # | Hallazgo (evidencia) | Efecto en B |
|---|---|---|
| 1 | **A cerrada y publicada** (`main` = `64b0742`): cuarta corrida 25/25, 25 episodios C0, inventario 13 344/13 344 a tiempo; 21 de 25 en la población principal; 3 α evaluados sin elegir. | Puerta «A cerrada» cumplida. |
| 2 | **DB-11 (propuestas sobre legítimos), con los datos de A y de la 4B:** el publicador v2 hizo **0 propuestas** en las 8 h de la 4B (2026-11-08 18:00Z → 11-09 02:00Z) y en el control de 30 min de la A; la vía rápida emitió **0 señales** en ambos. | La puerta se cumple **por los datos**. Límites: un solo día, 6 perfiles, modo sombra. Mark decide si basta (DB-11, DB-5). |
| 3 | **DB-3: ningún α elegible** en la 4B (1, 2 y 3 de 6 perfiles cumplen L1/L2 con α 0,05, 0,03 y 0,01; navegación, aplicación y errático no cumplen con ninguno). Con la política `if_senal` (D3) el IF **solo señala**: no escribe restricciones; las restricciones salen de los heurísticos. | B **no depende de α**. DB-3 deja de ser puerta de B y pasa a «α no se elige para la respuesta; se documenta» (DB-17). El IF seguiría generando señales, no restricciones. |
| 4 | **Escaneo breve con `nmap -n` dura ≈ 5 s** (4,6–5,0 s; 18 s sin `-n`). Por ventana, 4/5 fueron `solo_posterior` en A. La **vía rápida** (`port_scan_temprano`, K = 8, W = 2 s, g = 0,1 s) emitió 1 señal en **5/5** a 0,37–1,16 s del inicio (adenda local `ADENDA-VIA-RAPIDA-ESCANEOS.md`). | El escaneo breve de B es la primera prueba real de si la restricción se aplica **dentro de ~5 s**: resultado **desconocido**. E3 puede salir indeterminado por diseño (el barrido termina antes del efecto). Hay que declararlo antes. |
| 5 | **DNS:** el IF no alertó en 3 de 5 episodios (todos los α); `dns_entropy` detectó 5/5 (A). No hay punto de aplicación en DC1. | DNS sigue **en observación** (solo E1 y E4). |
| 6 | **Operación (4 corridas el 09-nov):** tres canceladas por causas ajenas al detector (vigía antiguo, DNS inverso de `nmap`, espejo SPAN intermitente), un reinicio del Sensor1 sin aviso, una caída de red de 18 min. | Preflight y vigilancia de §6 (lecciones incorporadas). |
| 7 | **No existe** (no la encontré en el repositorio) herramienta de análisis de E2–E5, y la instrumentación `t_apl`/`t_efecto` de D7 no está verificada en el producto desplegado (hay un «acuse de aplicación» en el panel, `producto-panel-v2/tests/test_acuse_aplicacion.py`, por revisar). | Trabajo previo de §5: sin esto B no puede medir su objetivo. |

## 2. Diseño

- **Episodios:** 25 = 5 × {DNS inusual, inundación HTTP, escaneo breve, escaneo sostenido, fuerza bruta HTTP}; orden aleatorio con semilla fijada **antes** (DB-10); ranuras de ≈ 7 min (≈ 3 h para los 25). Generador de A (`generar_campana.py` 99e6bdae…) con el esquema `nmap -n` (45f743d2…) para comparabilidad (DB-16).
- **Fallos del experimento:** lista cerrada de OBJETIVOS §5 + «pérdida del canal de gestión» (DB-15). Un fallo del experimento se repite una vez como `rN-bis`; un fallo del detector o de la cadena cuenta y no se repite.
- **Calidad de la evidencia:** clases C0–C3 de OBJETIVOS §6.1; población principal = C0 con integridad apta. Con el `s50` v2 (Suricata por EVE, descartes de tcpdump desde SIGUSR1) como base del análisis de integridad.

| Escenario | Regla prevista | Dónde se restringe | En A (referencia, no predice B) | En B se evalúa |
|---|---|---|---|---|
| Escaneo sostenido | `port_scan` → BLOCK | srv-dmz | por ventana 5/5 oportuna; vía rápida 5/5 a 0,23–0,25 s | E1–E5 |
| Escaneo breve | `port_scan` / `port_scan_temprano` (DB-12) → BLOCK | srv-dmz | por ventana 1/5 oportuna (IF 0,05); vía rápida 5/5 a 0,37–1,16 s | E1–E5; resultado **desconocido** (§1.4) |
| Fuerza bruta HTTP | `brute_force` → BLOCK | srv-dmz | 5/5 oportuna | E1–E5 |
| Inundación HTTP | `http_abuse` (umbral 600/60 s) → LIMIT | srv-dmz | 5/5 oportuna | E1–E5; efecto según §3 |
| DNS inusual | `dns_entropy` | DC1 (sin punto de aplicación) | HEUR 5/5 oportuna; IF 2/5 | solo E1 y E4 (E2, E3, E5: «no evaluable: falta el punto de aplicación») |

## 3. Medición del efecto y de los relojes (se mantiene el borrador v2 §4–§5)

- **E3 en LIMIT (inundación):** serie de conexiones aceptadas por srv-dmz:80 desde el SPAN, bloques de 1 s; base B0 = media de los 10 bloques previos a `t_apl`; `t_efecto` = primer bloque con ≤ (1 − θ)·B0 sostenido 5 bloques; θ = 0,5 (DB-2). Hay que comprobar que el generador **siguió intentando** (SYN del origen ≥ 50 % de B0, y salida de los `curl`), y que el contador de la regla crece entre `t_apl` y el fin.
- **E3 en BLOCK (escaneos, fuerza bruta):** cesan las respuestas del destino al origen mientras el generador sigue intentando (SPAN o salida del generador).
- **Relojes (DB-13):** medición en solo lectura al empezar, cada 30 min y al terminar; incertidumbre por comparación u = máx(ε = 0,01 s, u_a + u_b + marca propia); cumple si `t_x + u < t_fin_eval`, falla si `t_x − u ≥ t_fin_eval`, **indeterminado** en el resto; un host con desfase > 1 s vuelve la sesión C3. Medidos el 09-nov: sensor +0,005, Kali +0,007, srv-dmz +0,007, clientes +0,007 s.
- **Escaneo breve:** como el barrido dura ≈ 5 s, se publica además el **margen** `t_fin_eval − t_apl` aunque E3 sea indeterminado.

## 4. Puertas previas (todas deben estar ☑ antes de pedir la orden de arranque)

| Puerta | Estado hoy |
|---|---|
| G1 Campaña A cerrada y publicada | ☑ `64b0742` |
| G2 4B con ≥ 2 h C0 | ☑ ≈ 8 h C0 por perfil; P2: «sin violación observada», afirmación a decidir (DB-5) |
| G3 DB-11 (0 propuestas sobre legítimos) | ☑ por los datos (§1.2); Mark confirma |
| G4 Código desplegado por hash: vía rápida K = 8 y `http_abuse` 600 (DB-7) | ☑ 10-nov: hashes del publicador, motor, heurísticos y escalada en el Sensor1 iguales a `producto-etapa3`/`producto-recuperacion`; `SHA256SUMS` 87/87; `http_abuse` 600/60 s. Ver PREPARACION §14. Límite: ficheros, no memoria de los procesos |
| G5 Instrumentación `t_pub`, `t_relay`, `t_apl` y `counter` nft en las reglas (D7) en srv-dmz | ☐ **sin verificar**; ver §1.7 |
| G6 Herramienta de análisis de E2–E5 con pruebas y mutaciones, hash fijado | ☑ 10-nov: `analizar_b.py` (sha256 `9bb630db…`), 31 pruebas y 39/39 mutaciones muertas en el banco; falta fijar el hash definitivo tras las decisiones DB-2/E3 |
| G7 Salvaguardas en seco: el agente ignora `alcance = dns` (DB-4); sin relé no aplica entradas viejas; todo elemento con `timeout`; D5 (caducidad/retirada, DB-6) | ☐ |
| G8 Reversión R0–R7 redactada y ensayada en seco | ◐ 10-nov: R0–R5 en `guiones/b_revertir_srvdmz.sh` (seco por omisión) con 17 pruebas con órdenes simuladas; R6–R7 (E4 y publicador/D5) por escribir; **no ensayada contra srv-dmz real** |
| G9 Unidad `cf-b-fin` de fin automático en srv-dmz (DB-14, sudo de Mark) | ◐ `guiones/b_activar_srvdmz.sh` la programa con `systemd-run`; la cuenta `adminsrvdmz` tiene `NOPASSWD: ALL` en srv-dmz, así que **no hace falta el sudo de Mark** allí (sí en el Sensor1) |
| G10 Decisiones DB-1, 2, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17 | ☐ (§9) |
| G11 Cierre de B compatible con el aplazamiento de logrotate (`cf-4b-rotacion` exige la estructura de cierre `s40`; para B hay que definirla) | ◐ 10-nov: `armar/cierre --fase b` (o 4c) admite el árbol de B con `replay/rc.txt` = rc del orquestador; 5 pruebas en banco (incluido que el tope absoluto devuelve logrotate si B nunca cierra). Faltan las variantes `FASE=b` de s10/s20/s40 (hoy solo admiten 4b\|4c) o usar FASE=4c tras archivar `~/cf-e4/4c` de A |
| **G12 (nueva)** Herencia de restricciones entre episodios (D5) | ◐ En A, 23 de 25 episodios empezaban con una propuesta BLOCK sobre la Kali vigente 7+ min. Mark eligió (10-nov) la **limpieza D5 por episodio**: `herramientas/d5_episodio.py`, 19 pruebas y 24/24 mutaciones en banco. Falta integrarla en el orquestador y ensayarla en seco en los hosts. Ver `PREPARACION-B-RESULTADOS-2026-11-10.md` §10 y §12 |

## 5. Trabajo previo (sin tocar el sistema desplegado; todo en banco)

1. Analizador de B: E1–E5 por episodio, resultado `cumple / fallo / indeterminado / fallo del experimento`, contabilidad (planificados, ejecutados, admitidos, excluidos), intervalos de Clopper-Pearson de OBJETIVOS §4, y las métricas `t_det − t_inicio`, `t_apl − t_det`, `t_apl − t_inicio`, margen y `t_efecto − t_inicio`. Pruebas con datos sintéticos de diseño conocido y mutaciones, como en `s50` v2.
2. Verificar (o implementar en la rama candidata) la instrumentación D7 y probarla en srv-dmz **sin activar** el agente (`con_aplicar = 0`).
3. Redactar R0–R7 y el procedimiento de pérdida de SSH (borrador v2 §7) como guiones con rc explícito; ensayarlos en seco.
4. Definir el cierre de B (equivalente a `s40`/`s30`) para que `cf-4b-rotacion` pueda reanudar logrotate tras un cierre verificado.

## 6. Preflight del día de B (lecciones del 09-nov)

1. **06:45 – revisión:** servicios con `NRestarts = 0`, disco ≥ 20 GB libres, estado de logrotate, relojes. El Sensor1 se reinició sin aviso el 09-nov (19:24Z): comprobar `uptime`.
2. **Aplazamiento de logrotate** con `cf-4b-rotacion armar --tope <hasta + 5 h> --fase b` (sudo de Mark), verificado antes de empezar.
3. **Prueba del espejo: 30 min seguidos** en `ens37`, muestreo de 1 s, sin ningún segundo < 20 pkt/s. Una excepción solo con orden expresa de Mark y por escrito. Si falla, no se arranca.
4. **Vigilancia solo desde el bastión**, leyendo ficheros locales; **ningún sondeo `ssh` a la Kali durante la batería** (el 09-nov un paquete suelto de sshd Kali → bastión cruzó el SPAN y canceló una corrida). Todo `ssh` dentro de guiones lleva `-n`.
5. Verificadores de entorno (bastión, Sensor1, srv-dmz con `CON_SUDO` autorizado por Mark) y renovación de I5 inmediatamente antes de lanzar.
6. Control normal nuevo de 30 min antes de los episodios (E4 línea base).
7. Hashes de guiones y herramientas verificados en cada host antes de usarlos; nada se ejecuta con un hash distinto.

## 7. Parada, reversión y pérdida de SSH

Disparadores de parada (DB-8): **P1** restricción real a cualquier entidad distinta de 10.10.20.30; **P2'** regla sin caducidad o en un punto no previsto; **P3** pérdida del SSH de gestión; **P4** fallo de control atribuible a una restricción (E4); **P5** dos reinicios o un reloj > 1 s. Un E1, E2 o E3 fallido no detiene la campaña: cuenta como fallo.

Pérdida de SSH, reversión R0–R7 y fin automático `cf-b-fin`: **procedimiento del borrador v2 §7** (apagar primero el agente de srv-dmz; esperar la caducidad máxima del set + 60 s; consola de srv-dmz si no vuelve en 15 min). Pendiente de §5.3: guiones reales y ensayo.

## 8. Cronograma tipo (duraciones medidas en la A)

| Bloque | Duración |
|---|---|
| Preflight + prueba del espejo + control normal | ≈ 1 h 30 min |
| 25 episodios en ranuras de ≈ 7 min | ≈ 3 h |
| Cierre (`b20`, replay, copias, restauración, reversión) | ≈ 45 min |
| Análisis (en la A: 51 min con el recálculo de características) + analizador de B | ≈ 1 h |
| **Total** | **≈ 6 h 15 min**, sin contar pausas |

Debe cerrar con holgura **antes** de la rotación diaria de las 19:00 de Perú o llevar el aplazamiento verificado. Recomendación: arrancar la prueba del espejo antes de las 08:00 de Perú.

## 9. Decisiones para Mark

| Id | Decisión |
|---|---|
| DB-1 | E1–E5 con las aclaraciones de la v1 (reloj de srv-dmz, cubo compartido, corte frente a final natural) |
| DB-2 | θ = 0,5 con persistencia de 5 bloques |
| DB-5 | Valores de P2 y P3; si se afirma P2 con las 8 h de la 4B; si se ejecuta B sin P2 afirmado |
| DB-6 | D5 en seco: caducidad o retirada |
| DB-7 | Verificación por hash de agente, publicador y motor |
| DB-8 | Disparadores de parada |
| DB-9 | Franja |
| DB-10 | Semilla del orden aleatorio |
| DB-11 | Confirmar que los datos de §1.2 bastan como puerta |
| DB-12 | `port_scan_temprano` cuenta como regla prevista (afecta a E1 del escaneo breve y a la lectura de A) |
| DB-13 | Método de relojes |
| DB-14 | Unidad `cf-b-fin` (tu sudo) |
| DB-15 | «Pérdida del canal de gestión» como fallo del experimento |
| **DB-16** (nueva) | Mantener `nmap -n` en B (episodios breves de ≈ 5 s, comparables con A). Recomendado: sí. Alternativa: quitarlo y volver a ≈ 18 s, pero reaparece el DNS inverso a 10.10.10.21 |
| **DB-17** (resuelta por Mark el 10-nov) | **α = 0,01** para el experimento, umbral congelado −0,6223889502095352, solo para las señales del IF (`senales-if.jsonl`); con `if_senal` no restringe. Ver `PREPARACION-B-RESULTADOS-2026-11-10.md` §1. El umbral del motor desplegado (−0,5693969936322356) no se cambia sin orden aparte |
| **DB-18** (resuelta el 10-nov) | Adenda de la vía rápida publicada (SHA `f8cef33a470b983cdb93115b6c63543572fd1472`) |
| DB-3, DB-4 | DB-3 queda sustituida por DB-17; DB-4 sigue como G7 |

## 10. Lo que no cambia

Detector, modelo IF, escalador, 28 características, α desplegado (−0,5693969936322356), heurísticos, política de respuesta (`if_senal`), criterios de OBJETIVOS-Y-CRITERIOS y el Word. La A y sus tres cancelaciones no se mezclan con B. Si cualquier puerta de §4 falla, B no se ejecuta.
