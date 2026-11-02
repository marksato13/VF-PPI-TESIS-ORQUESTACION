# Protocolo 4B: control normal nuevo (congelado antes de ejecutar)

Fijado el **2026-11-02**, antes de la 4A. **No se ajusta a la vista de los resultados.** Una desviación obliga a parar, documentarla y decidir antes de seguir; no se corrige en el análisis.

**Requisitos para empezar:**

- 4A cerrada ([PROCEDIMIENTO §5.3](PROCEDIMIENTO-ETAPA4.md#53-periodo-de-observación-de-la-4a));
- criterios de inicio I1–I8 ([SALUD-CAPTURA §4.1](SALUD-CAPTURA.md#41-inicio-4b-y-4c));
- petición expresa de Mark para la 4B.

## 1. Qué no cambia

Todo lo de [PROTOCOLO-CAMPANA-A-REPETIDA §1](../preparacion-3a-2026-11-01/PROTOCOLO-CAMPANA-A-REPETIDA.md#1-qué-no-cambia) salvo el código, que es el candidato ec78ca5 (`config-campana-4c.json` → `codigo`):

- modelo, escalador y 28 características;
- historia de 230 s y paso de 10 s;
- umbral desplegado y umbrales de análisis 0,05 / 0,03 / 0,01, verificados contra la calibración de 4.1 por igualdad exacta;
- heurísticos y extractores;
- las 7 configuraciones.

## 2. Duración y calendario

| Parámetro | Valor congelado |
|---|---|
| Duración | **8 h** seguidas, [desde, desde + 8 h]. Es la que PRESUPUESTO pide para afirmar P2 |
| Mínimo publicable | 2 h (DISEÑO v3). Si se cancela o se interrumpe antes de 8 h, se publica lo que haya cubierto con sus clases, y **P2 no se afirma** |
| Tramo publicable | Solo tramos C0 continuos. Las horas C1/C2 se publican aparte y las C3 no cuentan |
| Calendario | Laborable o fin de semana, se declara en `control-declarado.json`. El envoltorio fija el factor 1,0, de modo que la curva horaria no se aplica (§3) |
| Ventana de rotación | El intervalo **no** puede contener la rotación diaria de `eve.json`. Se lee antes la hora con `systemctl list-timers logrotate.timer` y, si cae dentro, se desplaza `desde`. Motivo: `copytruncate` invalida el segmento EVE del replay (`s30_replay_e4.sh` para) |

## 3. Tráfico legítimo

- Los **seis perfiles** a **factor 1,0** con el envoltorio `clientes_factor1.py` (`69d79937…`), que no modifica `clientes_lab.py` (`ae5134a7…`). Es el procedimiento aprobado del paso 2 y del 3B, en `guiones/k01_clientes_factor1_e4.sh`.
- **Configuración efectiva documentada:** `k01` guarda en `~/cf-e4/4b/config-efectiva.txt` del host de clientes:
  - los argumentos de cada unidad (`argv-<perfil>.txt`: ritmo, servidor, DNS);
  - el estado del target;
  - la zona horaria;
  - los sha256 del envoltorio, del generador y de `clientes_config.py`;
  - la hora UTC de inicio del factor 1,0.

  Ritmos nominales observados el 2-nov:

  | Perfil | Ritmo |
  |---|---|
  | ofimática | 3,0 |
  | navegación | 1,5 |
  | descargas | 8,0 |
  | aplicación | 2,0 |
  | ligero | 12,0 |
  | errático | 5,0 (ráfagas ×6) |

- **Intensidad estable declarada:** factor 1,0 durante todo el control. **No** se usa la banda natural (curva 0,12–1,0), porque mezclaría intensidades distintas dentro del mismo control.
- **Al terminar:** `clientes_restaurar.sh` (para los envoltorios y arranca `cyberflow-lab.target`, que vuelve a la curva horaria).

## 4. Calentamiento y requisitos temporales

| Requisito | Valor |
|---|---|
| Desde el archivo | `desde ≥ inicio_archivo + 230 s` (historia del motor; `b01` lo comprueba) |
| Desde el factor | `desde ≥ inicio del factor 1,0 + 230 s` |
| Desde reinicios | `desde ≥ último arranque de ppi-motor / ppi-motor-capture + 600 s` (I1) |
| Cierre | `hasta ≤ cierre_archivo − 120 s`, con cierre ≥ `hasta + 300 s` y las 5 condiciones (`s20` + replay) |
| Declaración | Antes de `desde` (`b01` aborta si `desde` ya pasó) |

## 5. Métricas (M1), separadas y por clase

Cada ventana `w` se clasifica por [w − 60, w] con [SALUD-CAPTURA §3](SALUD-CAPTURA.md#3-clases-del-periodo-objetivos-y-criterios-v3-61-sin-cambios). **Población principal = C0.** C1 y C2 se publican aparte; C3 no entra en ninguna tasa. Nada se suma entre clases.

| # | Métrica | Herramienta | Notas |
|---|---|---|---|
| M1a | Falsas alarmas del **IF por α** (0,05 / 0,03 / 0,01) por ventana: tasa entre decididas, con cotas sobre las requeridas del inventario | `analizar_3b.py --control` (cobertura y cotas) y `control_4b.py` (por clase y por entidad) | Mismo `score_samples`, tres cortes, «score < umbral» estricto e IF válido solo con paquetes en 10 s |
| M1b | **Heurísticos por regla** (`heuristico.heuristico`), más la regla heredada `auth_failure_heuristic` registrada como ALERT | `control_4b.py` | Por clase |
| M1c | HEUR y las tres HIB | ambas | Como en el 3B; se publican, pero **no** sustituyen a M1a ni a M1b |
| M1d | **Vía rápida**: señales de `senales-rapidas.jsonl` con `t_evidencia` en el control | `control_4b.py` | Sin ataques, toda señal es falsa alarma. Se publica con la clase de la vía rápida por hora (journal de **su** tcpdump) |
| M1e | **Propuestas** del publicador v2 en sombra, por tipo, regla, acción y entidad; las `rechazada` aparte | `control_4b.py` | Una propuesta no es una detección ni una restricción: nadie la aplica |
| M1f | **Emisiones reales** del motor (ALERT por detector) | `control_4b.py` | Aparte de las 7 configuraciones derivadas |
| M1g | Cobertura del inventario (requeridas, decididas a tiempo/tardías, no evaluadas, ausentes) | `analizar_3b.py` | Sin umbral automático de cobertura |

**Población:** todas las entidades con ventanas en el intervalo. El DNS 10.10.10.20 está dentro (es excepción de respuesta, no de población) y `exclusiones_poblacion` está vacía.

**Comprobación offline de las herramientas** (`evidencia/control-4b/`):

- `control_4b.py` reproduce el control publicado del 3B: 2 644 ventanas; IF 395/254/83; HEUR 92; HIB 466/336/171.
- `analizar_3b.py` acepta un control sin episodios (marcas vacías) con la misma cobertura (2 644/2 644).
- Pruebas: 49 superadas.

## 6. Salud durante el control

Criterios de **pausa** y **cancelación** de [SALUD-CAPTURA §4.2](SALUD-CAPTURA.md#42-durante). En la 4B «pausa» significa:

- el tramo afectado se marca;
- si dura más de 5 min, el control **se parte**. Cada tramo C0 continuo de ≥ 30 min se publica por separado, y no se suman tramos para llegar a las 8 h;
- la decisión de seguir o cancelar la toma Mark.

X1, el 20 %, se cuenta en la 4B sobre **horas** de control en C2 o C3.

## 7. Comandos

Herramientas en `etapa4-preparacion-2026-11-02/guiones/` (lanzador `r4.sh`) y en `~/cf-e4/herramientas/` del sensor. En lo que sigue, `G` es `"/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4-preparacion-2026-11-02/guiones"`.

### 7.1 Herramientas al bastión y al sensor (una vez para 4B y 4C)

`[LAPTOP Git Bash]` → lo ejecuto yo.

```
P="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
cd "$P" && git status --short scripts etapa4-preparacion-2026-11-02 && git log -1 --format=%H
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'mkdir -p ~/cf-e4/herramientas'
scp -i ~/.ssh/id_ed25519 "$P"/scripts/{analizar.py,analizar_3b.py,poblacion.py,calidad_fuentes.py,extraer_evidencia_destino.py,recalcular_caracteristicas.py,generar_respaldos.py,verificar_integridad.py,control_4b.py,referencia_trafico_4c.py} \
  "$P"/etapa4-preparacion-2026-11-02/{config-campana-4c.json,escenarios-4c.json,herramientas-e4.sha256} gadmin@10.10.10.30:cf-e4/herramientas/
scp -i ~/.ssh/id_ed25519 "$P"/etapa4-preparacion-2026-11-02/guiones/{c05_brute_prep_e4.sh,p10b_relojes.sh} gadmin@10.10.10.30:cf-e4/
```

`[BASTIÓN gadmin]` → lo ejecuto yo.

```
cd ~/cf-e4/herramientas && sha256sum -c herramientas-e4.sha256
ssh -o BatchMode=yes sensor1 'mkdir -p ~/cf-e4/herramientas' && scp ~/cf-e4/herramientas/* sensor1:cf-e4/herramientas/
ssh -o BatchMode=yes sensor1 'cd ~/cf-e4/herramientas && sha256sum -c herramientas-e4.sha256'
```

- **Esperado:** las 12 líneas `OK` en el bastión y en el sensor (`herramientas-e4.sha256`: diez scripts, `config-campana-4c.json` `f177d9bb…` y `escenarios-4c.json` `73c0b204…`).
- **Parada:** cualquier `FAILED`.
- La copia se hace desde el commit publicado (paso `git status` limpio en `scripts` y la carpeta): los bytes son LF y coinciden con GitHub.

### 7.2 Secuencia

**1. Requisitos de inicio.** `[LAPTOP Git Bash → BASTIÓN → SENSOR1, BASTIÓN, SRV-DMZ]` → lo ejecuto yo las partes sin sudo y **lo ejecutas tú** `CON_SUDO=1 verificar_srvdmz.sh` (motivo: traza del agente y reglas efectivas; ver [PROCEDIMIENTO §5.1](PROCEDIMIENTO-ETAPA4.md#51-servicios-versión-cargada-firma-entrega-y-sombra)).

- **Esperado:** las tres verificaciones OK, más I1–I8.
- **Parada:** cualquier `FALLO`.

**2. Archivo y muestreo.** `[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo.

```
bash "$G/r4.sh" s10_sensor_archivo_e4.sh sensor 4b
```

- **Esperado:**
  - `primero: … OK live-….pcap` (de él sale `inicio_archivo`);
  - los tres PID vivos;
  - `arranque del motor (epoch)`.
- **Parada:** `PARAR`.

**3. Clientes a factor 1,0.** `[LAPTOP Git Bash → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuto yo (`sudo -n` permitido en ese host para `cyberflow-lab.target`, como en el 3B).

```
bash "$G/r4.sh" k01_clientes_factor1_e4.sh clientes 4b
```

- **Esperado:** seis `vivo=si` y conexiones de 10.10.20.2x.
- **Parada:** `PARAR` o algún `vivo=NO`.

**4. Declaración.** Se hace ≥ 230 s después del factor, con `desde` en el futuro y `hasta = desde + 8 h`. `[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo. `<INICIO_ARCHIVO>` es el instante del primer `OK` (paso 2), en ISO.

```
bash "$G/r4.sh" b01_bastion_control_e4.sh bastion 4b <DESDE_ISO> <HASTA_ISO> <INICIO_ARCHIVO_ISO>
```

- **Esperado:** `control declarado [DESDE, HASTA]` y una línea de vigilancia.
- **Parada:** cualquiera de las de `b01`.

**5. Durante el control.** Sin accesos a la Kali ni a srv-dmz. `[BASTIÓN gadmin]` → lo ejecuto yo cada 30–60 min (lectura).

```
tail -3 ~/cf-e4/4b/vigilancia.log
```

**Parada (pausa):**

- `NR=` sube;
- `motor` no está `active`;
- la línea de tcpdump muestra un `dropped by kernel` que crece;
- `arch:` deja de estar en `OK`.

**6. Fin del control y cierre.** No antes de `hasta + 300 s`. `[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo. `<HASTA_EPOCH>` = `date -d <HASTA_ISO> +%s`.

```
bash "$G/r4.sh" s20_verificar_cierre_e4.sh sensor 4b <HASTA_EPOCH>
bash "$G/r4.sh" s30_replay_e4.sh sensor 4b <INICIO_ARCHIVO_ISO> <HASTA_MAS_300_ISO>
```

Cuando `~/cf-e4/4b/replay/rc.txt` diga `rc=0`:

```
bash "$G/r4.sh" s40_cierre_e4.sh sensor 4b
```

- **Esperado:**
  - s20 `RESULTADO 1-4: CUMPLE`;
  - replay `rc=0`;
  - s40 `archivador rc=0`, 0 FALLO/PERDIDO y `servicios: mismos PID y NRestarts`.
- **Parada:** s20 `NO CUMPLE`. Se espera y se repite.

**7. Restaurar clientes.** `[LAPTOP Git Bash → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuto yo.

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'bash ~/cf-e4/4b/clientes_restaurar.sh'"
```

- **Esperado:** target `active` y seis unidades `active`.

**8. Análisis.** `[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo.

- `<INV_DESDE>` = `inicio_archivo`.
- `<INV_HASTA>` = `cierre_archivo` (el inicio del último PCAP `OK` + 5 s).

```
bash "$G/r4.sh" s50_analisis_e4.sh sensor 4b <INV_DESDE_ISO> <INV_HASTA_ISO> <DESDE_ISO> <HASTA_ISO>
```

- **Esperado:** `rc=0` en cada paso y `SHA256SUMS`.
- **Resultado:** `control-4b.json` (por clase, α, regla, vía rápida y propuestas) y `analisis-4b/analisis-3b.json` (cobertura y cotas).

## 8. Publicación

- Carpeta nueva `etapa4-4b-<fecha>/`, con la evidencia descargada como en el 3B (tar por SSH, `SHA256SUMS` verificados y `MANIFIESTO.sha256`).
- **Tabla M1** por clase.
- Horas C0 / C1 / C2 / C3.
- Si se alcanzan las 8 h C0, se dice si P2 se afirma; si no, se dice que no se afirma.
- Ninguna cifra se compara con la del 3B sin decir que el motor, el disparo y la rotación son distintos.
