# Protocolo 4C: campaña A nueva en sombra (congelado antes de ejecutar)

> **Estado: preparado, no ejecutado.** Este protocolo no autoriza la 4C ni la campaña B. La 4C se solicita aparte,
> después de cerrar la 4A ([PROCEDIMIENTO §5.3](PROCEDIMIENTO-ETAPA4.md#53-periodo-de-observación-de-la-4a)) y la 4B
> ([PROTOCOLO-4B](PROTOCOLO-4B-CONTROL.md)), y con las [condiciones antes de instalar](README.md#5-condiciones-antes-de-instalar)
> cumplidas.

## 1. Qué no cambia y qué sí

| No cambia (Etapa 3, `ec78ca5`) | Cambia frente al 3B |
|---|---|
| Modelo, escalador, esquema de 28 características, umbrales α 0,05 / 0,03 / 0,01 (verificados contra la calibración en `config-campana-4c.json`), reglas heurísticas | Motor candidato `ec78ca5` con `--disparo eventos` y `--state-dir _state-e4` (sombra, sin `--enforce`) |
| 5 escenarios × 5 repeticiones, parámetros y tiempos 60/120/90 de `escenarios.json` | Semilla `20261102` y orden publicado en [ORDEN-4C.md](ORDEN-4C.md) |
| 7 configuraciones derivadas; α **no se elige** | Anillo PCAP de 5 s (`-G 5`) en lugar de 15 s; cierre con margen 300 s |
| OBJETIVOS-Y-CRITERIOS v3 (categorías, ε 0,01 s, clases C0–C3) | La vía rápida, el publicador v2, el relé v2 y el agente v2 en sombra existen y se miden **aparte** |
| Origen Kali `10.10.20.30`, lista blanca `10.10.10.20` y `10.10.30.10` | Salud de captura con criterios fijados ([SALUD-CAPTURA](SALUD-CAPTURA.md)) |

## 2. Calendario

| Tramo | Requisito |
|---|---|
| Archivo | Abierto (`s10`) ≥ 10 min antes de `desde` del control (`b01` exige ≥ 230 s) |
| Control normal | 30 min declarados con `b01 4c` antes de empezar, `desde` en el futuro y ≥ 230 s tras el factor 1,0 |
| Batería | Se lanza (`g01`) solo después de `hasta` del control; ≈ 1 h 56 min ([ORDEN §3](ORDEN-4C.md#3-duración-total-estimada)) |
| Cierre | No antes de `fin_ultimo + 300 s`, con las 5 condiciones de §5.6 |
| Rotación | El intervalo [inicio del archivo, cierre] **no** contiene la rotación diaria de `eve.json`: se lee antes con `systemctl list-timers logrotate.timer` y se desplaza el inicio si cae dentro. Una rotación (copytruncate) detiene `s30` |
| Total | ≈ 2 h 45 min – 3 h con el archivo abierto |

## 3. Marcas de tiempo que se publican, por episodio

Cada una con su fuente y su reloj. No se mezclan:

| Marca | Fuente | Reloj |
|---|---|---|
| Inicio y fin del **generador** | `marcas.jsonl` (`reloj.pared_utc` de los eventos `inicio` y `fin`) | Kali |
| Inicio y fin del **tráfico observado** | `trafico_observado.py`: primer y último paquete del origen al destino y servicio del episodio en el PCAP archivado (en escaneos, SYN sin ACK) | Sensor1 |
| **Evidencia** | `window_end` de la primera ventana con señal atribuible | Sensor1 |
| **Disponibilidad** | `disponible_utc` (`registro_escrito_en` del ciclo) | Sensor1 |
| **Emisión** | emisiones reales del motor; vía rápida `emitido_en` (aparte) | Sensor1 |
| **Publicación** | primera propuesta del publicador v2 para el origen: `traza.jsonl` `publicado_en`, `regla`, `accion`, `tipo` | Sensor1 |
| **Entrega** | primera `destinos.srv-dmz.entregado_en` del relé v2 posterior a esa publicación | Bastión |
| **Respuesta** | solo la **propuesta**: en sombra nadie aplica, no hay `t_apl` ni `t_efecto` | — |

Las diferencias entre relojes se acotan con `relojes-4c.log` (`p10b` antes del lanzamiento y al final, en `b20`).
Una latencia entre marcas de hosts distintos se publica con ese desfase al lado.

## 4. Referencia del escaneo breve (fijada antes de ejecutar)

El escaneo breve dura ≈ 18 s; en el 3B el fin del generador incluía el cierre de `nmap` y no siempre coincidía con
el fin de la ráfaga. En la 4C su categoría **principal** se calcula contra la ráfaga real:

- `t_ini_ref` = primer SYN observado del origen al destino;
- `t_fin_eval` = mín(último SYN observado, fin del generador);
- **oportuna** = señal atribuible con `disponible ≤ t_fin_eval + ε` (ε = 0,01 s);
- sin tráfico observado o sin captura que cubra la ventana, la referencia es `no_determinable` y se conserva la
  categoría con la referencia del generador (no se inventa).

Para los otros cuatro escenarios la categoría principal sigue siendo la de OBJETIVOS v3 (referencia del
generador); la de tráfico se publica como información. Herramienta: `scripts/referencia_trafico_4c.py`
(probada offline con datos sintéticos, `tests/test_referencia_trafico_4c.py`, 5 pruebas), paso 9 de `s50`.

## 5. Secuencia

Herramientas: las de [PROTOCOLO-4B §7.1](PROTOCOLO-4B-CONTROL.md#71-herramientas-al-bastión-y-al-sensor-una-vez-para-4b-y-4c)
(ya copiadas y verificadas para la 4B; si no, se copian igual) y los guiones de
`etapa4-preparacion-2026-11-02/guiones/` lanzados con `r4.sh`. En lo que sigue:

```
P="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
G="$P/etapa4-preparacion-2026-11-02/guiones"
```

### 5.1 Requisitos de inicio (I1–I8)

`[LAPTOP Git Bash → BASTIÓN → SENSOR1, BASTIÓN, SRV-DMZ]` → lo ejecuto yo las verificaciones sin sudo y **lo
ejecutas tú** `CON_SUDO=1 verificar_srvdmz.sh` (motivo: lee la traza del agente y el ruleset nft con sudo), igual que
en [PROCEDIMIENTO §5.1](PROCEDIMIENTO-ETAPA4.md#51-servicios-versión-cargada-firma-entrega-y-sombra).

- **Esperado:** I1–I8 de [SALUD-CAPTURA §4.1](SALUD-CAPTURA.md#41-inicio-4b-y-4c), incluido I5 de la 4C:
  0 `kernel_drops` de Suricata en los 30 min previos.
- **Parada:** cualquier `FALLO` o criterio sin cumplir. Sin medida no es cero: un criterio sin lectura no se cumple.
- Además: hora de `logrotate.timer` fuera del intervalo (§2) y `piloto-con-dns` cerrado o declarado compatible por
  Mark (README §5).

### 5.2 Escenarios en la Kali y comprobación (c03)

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo.

```
scp -i ~/.ssh/id_ed25519 "$P/etapa4-preparacion-2026-11-02/escenarios-4c.json" gadmin@10.10.10.30:cf-e4/
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'sha256sum ~/cf-e4/escenarios-4c.json && scp -o BatchMode=yes ~/cf-e4/escenarios-4c.json kali:cf-campana-A/escenarios/escenarios-4c.json && echo "[ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): copia de escenarios-4c.json]" >> ~/cf-e4/accesos-kali-preparacion.log'
bash "$G/r4.sh" c03_kali_e4.sh kali
```

- **Esperado:** sha256 `73c0b204…` en el bastión; c03 con cuatro `OK`, `procesos de carga: 0`, `generadores: 0`,
  `NTPSynchronized=yes`.
- **Parada:** cualquier `FAILED` o `PARAR`.

### 5.3 Endpoint de fuerza bruta

Hoy `ppi-brute-lab` está **inactive/disabled** (ESTADO-OBSERVADO §3); en el 3A se arrancó y en el 3B se paró.

`[LAPTOP Git Bash → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuto yo: `adminsrvdmz` tiene `NOPASSWD: ALL`
(lectura `sudo -n -l` del 2-nov, [ESTADO §3](ESTADO-OBSERVADO-LABORATORIO.md#3-cadena-de-publicación-relé-y-agentes)),
como el `stop` del 3B. Solo arranca el endpoint de laboratorio; no se habilita.

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'sudo -n systemctl start ppi-brute-lab; echo rc=\$?; systemctl is-active ppi-brute-lab; systemctl is-enabled ppi-brute-lab'"
```

- **Esperado:** `rc=0`, `active` y `disabled` (no se habilita al arranque).
- **Parada:** `rc` ≠ 0 (sudo ya no permitido sin contraseña): entonces lo ejecuta Mark con `ssh -t` y el mismo
  `sudo systemctl start ppi-brute-lab`.

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo (preparación desde el bastión, excluido del motor):

```
bash "$G/r4.sh" c05_brute_prep_e4.sh bastion completa
```

- **Esperado:** `servicio: active/disabled`, 401, 401, 200, 404.
- **Parada:** servicio inactivo o códigos distintos.

### 5.4 Archivo, clientes y control de 30 min

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo.

```
bash "$G/r4.sh" s10_sensor_archivo_e4.sh sensor 4c
```

- **Esperado:** `primero: … OK live-….pcap` (de ahí `INICIO_ARCHIVO`), tres PID vivos, `arranque del motor (epoch)`.
- **Parada:** `PARAR`.

`[LAPTOP Git Bash → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuto yo (`sudo -n` permitido en ese host
para `cyberflow-lab.target`, como en el 3B y la 4B).

```
bash "$G/r4.sh" k01_clientes_factor1_e4.sh clientes 4c
```

- **Esperado:** seis `vivo=si`. **Parada:** `PARAR` o algún `vivo=NO`.

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo, ≥ 230 s después del factor y ≥ 10 min después de
`INICIO_ARCHIVO`; `HASTA = DESDE + 30 min`.

```
bash "$G/r4.sh" b01_bastion_control_e4.sh bastion 4c <DESDE_ISO> <HASTA_ISO> <INICIO_ARCHIVO_ISO>
```

- **Esperado:** `control declarado [DESDE, HASTA]` y una línea de vigilancia.
- **Parada:** las de `b01` (DESDE en el pasado, < inicio + 230 s, duración < 1 800 s).

Durante el control: `[BASTIÓN gadmin]` → lo ejecuto yo, lectura cada 10 min: `tail -3 ~/cf-e4/4c/vigilancia.log`.
Sin accesos a la Kali ni a srv-dmz.

### 5.5 Batería

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1, SRV-DMZ, KALI]` → lo ejecuto yo, después de `HASTA`.

```
bash "$G/r4.sh" g01_lanzar_bateria_e4.sh bastion <HASTA_ISO>
```

- **Esperado:** sombra demostrada en sensor (`candidato=1 enforce=0`) y srv-dmz (`aplicar_en_procesos=0
  tablas_cyberflow=0 eventos_aplicacion=0`), 401 del endpoint, relojes sin `desfase|<=1 s: NO`,
  `comando: …escenarios-4c.json…` y un PID.
- **Parada:** cualquier `PARAR`.

Durante la batería (≈ 1 h 56 min): `[BASTIÓN gadmin]` → lo ejecuto yo, lectura cada 10 min de
`tail -3 ~/cf-e4/4c/vigilancia.log`. **Ningún** acceso a la Kali hasta `b20`; cualquier acceso se anota en
`accesos-kali.log`.

- **Pausa (P1–P5)** y **cancelación (X1–X3)**: [SALUD-CAPTURA §4.2](SALUD-CAPTURA.md#42-durante). Una pausa no
  reordena ni repite episodios: los afectados se clasifican con su clase de salud.
- **X2** (un evento `aplicacion` o un cambio del ruleset nft) cancela la 4C y activa la reversión
  ([PROCEDIMIENTO §7](PROCEDIMIENTO-ETAPA4.md#7-reversión)).

### 5.6 Fin de la batería y cierre

`[LAPTOP Git Bash → BASTIÓN gadmin → KALI (lectura), SENSOR1]` → lo ejecuto yo, cuando el generador haya terminado
(≈ lanzamiento + 1 h 57 min).

```
bash "$G/r4.sh" b20_fin_bateria_e4.sh bastion
```

- **Esperado:** `generador rc=0`, tres sha256 de `marcas.jsonl` iguales (Kali, bastión, sensor), `fin_ultimo=<epoch>`,
  `relojes-4c.log` copiado a `~/cf-e4/4c/copias/`.
- Si aún no han pasado 300 s desde `fin_ultimo`, la traza del relé no se copia: se repite `b20` después de la hora
  que indica (las copias anteriores se rehacen idénticas o para con `PARAR`).
- **Parada:** `PARAR`.

Cinco condiciones del cierre (como el 3B, con ficheros de 5 s y margen 300 s): 1) PCAP con `OK` cuyo inicio + 5 ≥
`fin_ultimo + 300`; 2) `archivar.log` sin `FALLO` ni `PERDIDO`; 3) EVE con eventos posteriores a `fin_ultimo + 300`;
4) decisiones en vivo con `window_end ≥ fin_ultimo + 60`; 5) repetición con `rc=0`.

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo. `<FIN_EPOCH>` es el `fin_ultimo` de `b20`;
`<FIN_MAS_300_ISO>` = `date -u -d @$(( ${FIN_EPOCH%.*} + 300 )) +%FT%TZ`.

```
bash "$G/r4.sh" s20_verificar_cierre_e4.sh sensor 4c <FIN_EPOCH>
bash "$G/r4.sh" s30_replay_e4.sh sensor 4c <INICIO_ARCHIVO_ISO> <FIN_MAS_300_ISO>
```

Cuando `~/cf-e4/4c/replay/rc.txt` diga `rc=0`:

```
bash "$G/r4.sh" s40_cierre_e4.sh sensor 4c
```

- **Esperado:** s20 `RESULTADO 1-4: CUMPLE`; replay `rc=0`; s40 `archivador rc=0`, 0 FALLO/PERDIDO,
  `servicios: mismos PID y NRestarts`, `--enforce en argv: ''`.
- **Parada:** s20 `NO CUMPLE` (se espera y se repite); replay sin `rc=0`; copytruncate detectado por s30.

### 5.7 Restauración

`[LAPTOP Git Bash → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuto yo.

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'bash ~/cf-e4/4c/clientes_restaurar.sh'"
```

- **Esperado:** target `active` y seis unidades `active`.

`[LAPTOP Git Bash → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuto yo (`NOPASSWD: ALL`, como en el 3B).

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'sudo -n systemctl stop ppi-brute-lab; echo rc=\$?; systemctl is-active ppi-brute-lab'"
```

- **Esperado:** `rc=0` e `inactive` (estado previo a la 4C).
- **Parada:** `rc` ≠ 0: lo para Mark con `ssh -t`.

Comprobación posterior del endpoint. `[LAPTOP Git Bash → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuto yo
(lectura):

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'wc -l < /opt/brute-lab/brute.log; tail -n 3 /opt/brute-lab/brute.log; systemctl is-active ppi-brute-lab'" | tee "$P/etapa4-preparacion-2026-11-02/out_brute_post_4c.txt"
```

- **Esperado:** el número de líneas creció durante la batería (los 5 episodios de fuerza bruta escribieron) y el
  servicio está `inactive`. El recuento por episodio sale de `destinos-3b.csv` (`s50` paso 1).

### 5.8 Análisis

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo. `<INV_DESDE>` = `INICIO_ARCHIVO`;
`<INV_HASTA>` = inicio del último PCAP `OK` + 5 s.

```
bash "$G/r4.sh" s50_analisis_e4.sh sensor 4c <INV_DESDE_ISO> <INV_HASTA_ISO> <DESDE_ISO> <HASTA_ISO>
```

- **Esperado:** `rc=0` en los pasos a–c y 1–9, y `SHA256SUMS`.
- **Parada:** `PARAR: herramientas con hash distinto` o `el código candidato no verifica`.

## 6. Salud y evaluabilidad

- Clase de cada episodio en `[inicio − 60, fin + 60]` con el journal del tcpdump **del anillo** (IF, heurísticos,
  híbridos) y, aparte, con el de la **vía rápida** (`s50` paso 7).
- Evaluable en la población principal solo C0 o C1 con Suricata medido; C2 y C3 se publican con su motivo
  ([SALUD-CAPTURA §4.3](SALUD-CAPTURA.md#43-qué-es-evaluable)).
- El número de PCAP no prueba continuidad: la prueban los saltos del anillo, `FALLO`/`PERDIDO` y las lecturas
  SIGUSR1 acotadas.

## 7. Sombra = detección oportuna, nada más

En la 4C no se aplica nada. Se publica **detección oportuna** (y su latencia) por configuración, la vía rápida aparte
y la **propuesta** del publicador con su entrega a srv-dmz. No se publica bloqueo, tiempo de contención ni efecto,
y una propuesta no se cuenta como respuesta aplicada.

## 8. Contabilidad que se publica

| Nivel | Definición |
|---|---|
| Planificados | 25 (ORDEN-4C) |
| Ejecutados | episodios con `inicio` y `fin` en `marcas.jsonl`, con su `estado` (completo, timeout, fallo) |
| Admitidos | ejecutados que cumplen la población principal de `analizar_3b` (criterios v2 del 3B) **y** clase C0/C1 |
| Excluidos | el resto, cada uno con su motivo (población, salud C2/C3, tráfico no observado) y visibles en las tablas |

Las 7 configuraciones se comparan sobre la **misma** población común. Los totales del 3B se citan al lado, diciendo
que el motor, el disparo y la rotación son distintos.

## 9. Publicación

Carpeta nueva `etapa4-4c-<fecha>/`: evidencia descargada por tar a través del bastión, `SHA256SUMS` de `copias/` y
`analisis/` verificados, `MANIFIESTO.sha256` contra los bytes de GitHub, tabla por familia y configuración con las
tres α, tabla de marcas (§3) por episodio, contabilidad (§8), horas por clase y la nota de que la campaña B no
queda autorizada por la 4C.
