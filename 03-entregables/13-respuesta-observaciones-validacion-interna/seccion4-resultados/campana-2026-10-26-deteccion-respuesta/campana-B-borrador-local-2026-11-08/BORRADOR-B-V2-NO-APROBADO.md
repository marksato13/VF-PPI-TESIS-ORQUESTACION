> **BORRADOR LOCAL, SIN APROBAR, SIN PUBLICAR.** Texto de la v2 que se presentó solo en el chat el 07-nov. No es un protocolo: la campaña B no tiene
> protocolo ni condiciones fijadas. Las decisiones DB-1 a DB-15 siguen abiertas. DB-3 se sustituye por `etapa4-4b-enmienda-p1-2026-11-08/DB-3-PROPUESTA.md`
> (S pasa a ser L1 y L2 como propuestas operativas, y las ventanas faltantes se tratan por cotas). El cronograma de §8 es el del 07-nov y está superado.

# Borrador v2 de la Campaña B (solo en el chat, sin aprobar)

**Leyenda de cada decisión:**
- **[A]** solo necesita tu aprobación.
- **[E]** necesita evidencia que todavía no existe.
- **[A+E]** necesita las dos cosas.

Esta versión corrige tres puntos de la v1:
- **Escaneo breve:** la v1 decía que «se espera que falle». La vía rápida ya cambió eso; ahora el resultado esperado es desconocido.
- **10.10.20.26:** la v1 lo trataba como un fallo sin corregir. La corrección existe; lo que falta es la prueba en vivo.
- **Las 8 h de la 4B**, explicadas en el §3.

## 1. Vía rápida del escaneo breve

**Probado en reproducción** (`etapa3-deteccion-temprana-2026-11-02/VIA-RAPIDA-ESCANEO.md` y cierre técnico `ec78ca5`):
- **Regla:** `port_scan_temprano` con K = 8, W = 2 s y g = 0,1 s, alternativa C (flujo continuo).
- **Batería de 120 ejecuciones:** en las 120, la restricción quedó aplicada y descartando paquetes **antes del último SYN**. El margen mínimo fue de 1,77 s.
- **Alternativa C con carga:** aplicada a los 0,98 / 1,59 / 1,62 s (p50 / p95 / máximo) desde el primer SYN. Margen mínimo hasta el último SYN: 2,98 s.
- **Banco con VLAN:** 60/60 aplicadas antes del último SYN.
- **Sobre el archivo del 3B:** 10 disparos, todos de la Kali hacia srv-dmz, y 0 sobre otros pares.

**Límites de esa evidencia:**
- Reutiliza los mismos 5 escaneos del 3B, así que no es una confirmación independiente.
- Un replay no reacciona al bloqueo.
- El transporte era local, con un único destino y una carga sintética.

**Pendiente en vivo:**

| Qué falta | Dónde se mide |
|---|---|
| Retardo del espejo SPAN y del búfer de Sensor1 | 4C (t_det) y B |
| Transporte SSH real del relé al agente | **Solo en B** (t_apl) |
| CPU de Sensor1 con motor, Suricata y detector a la vez | E-carga de hoy y 4C |
| Falsos disparos de la vía rápida sin ataques (M1d) | 4B |
| Reacción de nmap real a los descartes | **Solo en B** (E3) |

**Para B:**
- Hay que verificar por hash que el código desplegado contiene la vía rápida con K = 8. **[E]**
- ☐ **DB-12 [A]**: declarar antes de B que `port_scan_temprano` cuenta como la regla prevista `port_scan` en E1. Si no se declara, un BLOCK correcto de la vía rápida no validaría E1.
- Para la vía rápida, t_det = instante de disponibilidad de la señal en `senales-rapidas.jsonl`.

## 2. LIMIT a 10.10.20.26

**Probado en reproducción** (`HTTP-CONFUSIONES-Y-RENOVACIONES.md` §3 y `VALIDACION.md`):
- **Causa:** el umbral de `http_abuse` era de 100 peticiones/60 s, y el pico legítimo de 10.10.20.26 fue de 117.
- **Umbral nuevo:** 600/60 s, 5,1 veces ese pico. Una inundación lo alcanza en ~2–4 s (entre ~160 y ~300 peticiones/s).
- **Replay del 3B:** las ventanas de `http_abuse` sobre .26 pasan de 6 a 0, y se conservan las 75 detecciones propias de inundación.
- **Pruebas unitarias:** 10, incluidos el pico legítimo (no dispara) y el umbral justo.
- **Cambio relacionado:** la rama «ráfaga» de `port_scan` exige ahora `unique_dst_port_ratio_30s ≥ 0,1`, así que las colas de inundación ya no se confunden con escaneos.

**Límites:**
- Es un solo día del mismo laboratorio.
- Son **ventanas** de decisión, no restricciones aplicadas.
- P3 (≤ 1 % del tiempo restringido) no se ha medido con el umbral nuevo.

**Pendiente en vivo:**
- 4B con los 6 perfiles a factor 1,0: 0 propuestas de `http_abuse` y 0 LIMIT hipotéticos sobre legítimos (M1b y M1e).
- B: E4 sin fallos.
- Verificar por hash que el publicador y el motor desplegados llevan el umbral 600.

☐ **DB-11 [E]** pasa a ser una **puerta de evidencia**: si la 4B muestra alguna propuesta sobre .26 (o cualquier otro legítimo), B no se ejecuta con el agente activo.

## 3. Corrección de la condición de las 8 h de la 4B

La v1 decía «4B ≥ 2 h» como condición previa y planificaba «4B de 8 h» como si fueran lo mismo. Según `PROTOCOLO-4B-CONTROL.md` (versión corregida) y `PRESUPUESTO-FALSAS-ALARMAS.md`:
- **8 h seguidas** son necesarias solo para **afirmar P2** (≤ 1 intervalo de LIMIT por entidad legítima y jornada).
- **2 h es el mínimo publicable.** Con 2 h, P2 se declara «sin violación observada en 2 h», sin extrapolar. La cota de 0 intervalos en unas 20 entidad·hora es ≈ 1,2 por entidad·8 h, que no es inferior a 1.
- **Una interrupción de más de 5 min parte el control.** Cada tramo C0 continuo de ≥ 30 min se publica por separado, y **los tramos no se suman** para llegar a 8 h.
- B **no** puede usar sus propios episodios para afirmar P2.

**Condición corregida para B:** 4B publicada con ≥ 2 h C0 y la puerta DB-11 cumplida. Si no hay 8 h C0 seguidas, B puede ejecutarse, pero el informe dice «P2 no afirmado».

☐ **DB-5 [A]**: confirmar los valores de P2 y P3, y si aceptas ejecutar B sin P2 afirmado.

## 4. Cómo medir el efecto de LIMIT (E3, inundación HTTP)

☐ **DB-2 [A]** sobre el umbral θ y la persistencia.

- **Serie principal (SPAN):** en bloques de 1 s, conexiones que srv-dmz:80 acepta del origen (SYN-ACK de 10.10.30.10:80 hacia 10.10.20.30). Cada `curl --max-time 2` abre una conexión nueva.
  - El SPAN se copia en el conmutador, antes del descarte en srv-dmz, así que también ve los intentos descartados.
  - El EVE sirve de serie de apoyo solo si la clase es C0. En C1 se usa solo el SPAN.
- **Base B0:** la media de los 10 bloques de [t_apl − 10 s, t_apl), como dice la MATRIZ.
- **t_efecto:** el inicio del primer bloque k ≥ t_apl en el que la serie cumple ≤ (1 − θ)·B0 **y se mantiene así durante 5 bloques seguidos**. La persistencia es una propuesta nueva, para que un hueco puntual no cuente como efecto.
  - θ = 0,5 es la propuesta de la MATRIZ.
  - Ojo: `limit rate over 100/second drop` limita **paquetes**, no peticiones. Cada petición son varios paquetes, así que se espera una reducción muy superior al 50 %. Que no aparezca sería un hallazgo.
- **«El generador siguió intentando»:** en esos mismos bloques, los SYN del origen hacia :80 (SPAN) se mantienen en ≥ 50 % de su tasa en B0. Además, la salida de los 8 bucles de `curl` muestra intentos después de t_apl.
- **Comprobación cruzada:** el contador nft de la regla de límite crece entre t_apl y t_fin_eval. Se lee dos veces, en el agente y en la relectura final.
- **E2 en LIMIT:** el set contiene solo 10.10.20.30, porque el cubo de 100/s es compartido.
- **Incertidumbre:** la de t_efecto es el ancho del bloque (1 s) más la del reloj de Sensor1 (§5).

## 5. Incertidumbre de los relojes

☐ **DB-13 [A]**

- **Relojes que intervienen:**
  - Sensor1: SPAN, t_det y vía rápida;
  - Kali: marcas de inicio y fin;
  - srv-dmz: t_apl y contadores;
  - bastión: el que hace las mediciones.
  - DC1 no se mide mientras esté en observación.
- **Medición en solo lectura**, al empezar, cada 30 min y al terminar, sin tocar NTP ni chrony:
  - lectura de `chronyc tracking`;
  - 10 muestras por host desde el bastión: offset = t_remoto − (t_envío + t_recepción)/2, con una incertidumbre de RTT/2.
  - Por host, u_h = máx(|offset| + RTT/2) de toda la sesión.
- **Por comparación:** u = máx(ε, u_a + u_b + incertidumbre propia de la marca), con ε = 0,01 s como mínimo. La marca propia es, por ejemplo, el bloque de 1 s de t_efecto.
  - **Cumple** si t_x + u < t_fin_eval.
  - **Falla** si t_x − u ≥ t_fin_eval.
  - **Indeterminado** en cualquier otro caso; no cuenta como éxito ni como fallo.
- **Si un host supera 1 s,** la sesión es C3, un fallo del experimento (§5 publicado).
- No se corrigen marcas a posteriori con el offset medido. Solo se ensancha u.

## 6. Escenarios: srv-dmz o en observación

| Escenario | Regla prevista | Dónde se restringe | Qué se evalúa en B |
|---|---|---|---|
| Escaneo sostenido | `port_scan` → BLOCK | srv-dmz | E1–E5 |
| Escaneo breve | `port_scan` / `port_scan_temprano` (DB-12) → BLOCK | srv-dmz | E1–E5. Resultado esperado: **desconocido** (§1). |
| Fuerza bruta HTTP | `brute_force` → BLOCK | srv-dmz | E1–E5 |
| Inundación HTTP | `http_abuse` (600/60 s) → LIMIT | srv-dmz | E1–E5, con el efecto medido según el §4 |
| DNS inusual | `dns_entropy` | DC1, pendiente | **Observación:** E1 y E4. E2, E3 y E5 se publican como «respuesta no evaluable: falta el punto de aplicación». Se ejecuta en su posición del orden aleatorio, con limpieza D5 después. |

**Salvaguarda [E]:** comprobar en seco que el agente de srv-dmz ignora las entradas con `alcance = "dns"`. ☐ **DB-4 [A]**

## 7. Parada, reversión y vuelta a sombra si se pierde el SSH

**Disparadores de parada** (☐ **DB-8 [A]**):
- **P1:** una restricción real a cualquier entidad distinta de 10.10.20.30.
- **P2':** una regla sin caducidad o en un punto no previsto.
- **P3:** pérdida del SSH de gestión.
- **P4:** un fallo de control atribuible a una restricción (E4).
- **P5:** dos reinicios, o un reloj de más de 1 s.

Un E1, E2 o E3 fallido no detiene la campaña: cuenta como fallo.

**Reversión normal R0–R7:** igual que en la v1. Primero se copian con hash el ruleset, el set y el estado de escalada. Después se desactiva el timer del agente, se ejecuta `nft delete table inet cyberflow`, se comprueba que la tabla no está, se verifica E4 y el publicador vuelve a sombra con limpieza D5. Al final se pasan los verificadores con rc 0 y se publica.

**Diseño a prueba de pérdida de SSH** (condiciones previas):
- **Todo elemento del set con `timeout`:** se verifica en la relectura de cada episodio. **[E]**
- **Comportamiento sin relé [E]:** comprobar en seco que el agente no aplica entradas viejas si el relé deja de entregar.
- **Fin automático en srv-dmz** (☐ **DB-14 [A]**, con tu sudo al empezar). Es una unidad temporal; desaparece si srv-dmz se reinicia, y en ese caso el agente tampoco vuelve a aplicar hasta que se active.

`[srv-dmz, tu cuenta con sudo]` → **lo ejecutas tú** (sudo con contraseña)
```bash
sudo systemd-run --on-active=4h --unit=cf-b-fin /bin/sh -c 'nft list table inet cyberflow > /root/cf-b-fin-ruleset.txt; systemctl disable --now <timer del agente>; nft delete table inet cyberflow'
```

**Si se pierde el SSH:**
1. Detengo el orquestador: no sale ningún episodio más. Anoto la hora; es P3.
   `[LAPTOP Git Bash]` → **lo ejecuto yo**
2. **Sin tocar nada,** reintento la conexión cada 30 s durante la caducidad máxima del set + 60 s. Las restricciones vigentes caducan solas.
3. **Si vuelve el SSH bastión → srv-dmz:** reversión R0–R7. **Prioridad:** apagar el agente de srv-dmz. Con el agente apagado ya no se aplica nada, aunque Sensor1 siga sin conexión. Así se vuelve a sombra de hecho.
4. **Si no vuelve en 15 min:**

   `[srv-dmz consola, tu cuenta con sudo]` → **lo ejecutas tú** (sin SSH solo queda la consola)
   ```bash
   sudo nft list table inet cyberflow > ~/parada-B-sin-ssh.txt; sudo systemctl disable --now <timer del agente>; sudo nft delete table inet cyberflow; sudo nft list tables
   ```
   Si lo que cayó fue el enlace laptop → bastión, lo mismo se puede hacer desde el bastión.
5. **Cuando vuelva el SSH con Sensor1:** el publicador vuelve a la configuración de sombra de la 4A y paso los verificadores.
6. **Clasificación** (☐ **DB-15 [A]**): propongo añadir, **antes de B**, «pérdida del canal de gestión» a la lista cerrada de fallos del experimento. La lista no admite causas nuevas después de ver resultados.

## 8. Cronograma (domingo 8-nov, hora de Perú)

Depende de que hoy se cumplan la 4A y la puerta G.

| Hora | Bloque |
|---|---|
| sáb ~21:30–23:20 | Análisis de la E-carga, fase R (tu sudo) y declaración de la 4B ≥ 230 s después de fijar el factor |
| 23:20 – 07:20 | 4B. Solo se afirma P2 si salen 8 h C0 seguidas. |
| 11:25 – 13:21 | 4C |
| hasta ~15:10 | Cierre de 4B y 4C, puerta DB-11 y publicación del α con su hash |
| 15:10 – 19:05 | Preparación de B: hashes del código, salvaguardas, D5 en seco, semilla, unidad `cf-b-fin` |
| 19:05 – 19:40 | Preflight: rotación, aprendizaje y primera medición de relojes |
| 19:40 | Tu orden de arranque |
| 19:45 – ~22:40 | 25 episodios en ranuras de ~7 min |
| ~22:45 | Reversión R0–R7 |

## Decisiones pendientes

| Id | Tipo | Decisión |
|---|---|---|
| DB-1 | [A] | E1–E5 con las aclaraciones de la v1 (reloj de srv-dmz, cubo compartido, corte frente a final natural) |
| DB-2 | [A] | θ = 0,5 con persistencia de 5 bloques (§4) |
| DB-3 | [A+E] | Regla de α con el valor S. Necesita la 4B y la 4C. |
| DB-4 | [A+E] | DNS en observación, con la salvaguarda `alcance=dns` probada |
| DB-5 | [A] | Valores de P2 y P3, y ejecutar B sin P2 afirmado |
| DB-6 | [A+E] | D5 ensayado en seco: caducidad o retirada |
| DB-7 | [A+E] | Agente y código de B por hash: vía rápida K = 8 y umbral 600 |
| DB-8 | [A] | Disparadores de parada |
| DB-9 | [A] | Franja del §8 |
| DB-10 | [A] | Semilla del orden aleatorio |
| DB-11 | [E] | 0 propuestas sobre legítimos en la 4B |
| DB-12 | [A] | `port_scan_temprano` cuenta como regla prevista |
| DB-13 | [A] | Método de relojes |
| DB-14 | [A] | Unidad de fin automático en srv-dmz |
| DB-15 | [A] | «Pérdida del canal de gestión» como fallo del experimento |
