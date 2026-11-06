# Preparación de E-carga v2, revisión r3: S14 con tiempo desconocido (06-nov, noche)

**Estado: defecto de S14 corregido en banco. E-carga NO se ha ejecutado ni programado.** No se ha arrancado ningún
generador, no se ha lanzado ningún ataque, no se ha activado ninguna restricción, no se ha modificado ningún servicio
desplegado y no se ha iniciado la 4B, la 4C ni la campaña B. El modelo IF, las 28 características, α, los heurísticos y
la política de respuesta no se han tocado. Tampoco los umbrales, la duración ni la cobertura de S14, K1–K5 ni los demás
S. La ejecución exige una orden posterior y explícita de Mark (§8).

**Qué sustituye.** Esta r3 sustituye, de [`PREPARACION-ECARGA-v2-r2.md`](PREPARACION-ECARGA-v2-r2.md) (`b863634`,
sha256 `78dfa8ca…`, ver `../evidencia/13-correccion-s14/protocolo-v2-r3.sha256`):
- §2: las referencias (producto `902991e` en lugar de `a12deae`);
- §3: S14, que ahora sigue el protocolo **r4** §3.6.1.1;
- en §6, §7 y §8:
  - el paquete `P = ~/cf-e4/paquete-902991e` en lugar de `paquete-a12deae`;
  - la carpeta de resultados, que pasa a ser `evidencia/14-ecarga-ejecucion/` porque la 13 es esta corrección.

El resto de la r2 sigue vigente: §1, §4, §5 y la secuencia de §6 y §7, con esos dos cambios.

Protocolo: [`PROTOCOLO-CARGA-v2.md`](../PROTOCOLO-CARGA-v2.md) **r4** (§0.3, §3.6.1.1 y §3.5, punto 13).

## 1. Defecto, causa y corrección

**Defecto** (`evaluar_s14.py` 2026-11-06.1, producto `a12deae`). La cadena de posible saturación empezaba en el primer
par saturado válido. Un hueco **inmediatamente anterior** no se contaba.

**Reproducción exacta.** CPU 100 % y PSI `cpu some` 50 % en [D+100, D+108), D = 1794194100:
- todas las lecturas presentes → `S14 = false`;
- `psi = None` en las muestras D+100 ≤ t < D+103 → con `a12deae`, `S14 = true`.

Los pares (D+99, D+100) a (D+102, D+103) no son válidos, así que [D+99, D+103) son 4 s sin medida pegados a 5 s
saturados, [D+103, D+108). El episodio pudo durar 9 s. Cobertura 99,89 % y hueco máximo 4 s: §3.6.1 se cumple, y por eso
la cobertura no lo detectaba.

**Causa.** Dos niveles:
- **En el código**, el bucle abría la cadena «posible» solo en un par saturado. Los huecos de detrás y de dentro sí se
  sumaban (por eso el caso de un hueco en mitad, hallado antes de publicar `a12deae`, sí daba `null`). Los de delante y
  los del borde de inicio, no. La línea base usaba el mismo algoritmo y además no tenía estado «dudoso»: un posible
  episodio con hueco delante no contaba como episodio, y la base parecía limpia.
- **En el texto de la r3**, §3.6.1 hablaba de «huecos **intercalados**», sin decir qué pasa antes, después o en los
  bordes.

**Corrección** (`evaluar_s14.py` 2026-11-06.2, en las cinco componentes porque todas usan `analizar()`):
1. `linea_temporal()` divide [desde, hasta) en intervalos contiguos **S** (par válido saturado), **N** (par válido no
   saturado) y **U** (todo lo que no cubre un par válido: par > 4 s; dato ausente o ilegible; contador que retrocede;
   hilo con otro PID; y el tramo entre un borde y la primera o la última muestra). Un par se recorta a
   [max(t_a, desde), min(t_b, hasta)).
2. `analizar()` recorre los **tramos posibles**: sucesiones máximas de S y U. Solo un N corta. Duración posible =
   fin − inicio.
   - Episodio **demostrado**: S contiguos, sin U entre ellos, que suman ≥ 8 s.
   - **Dudoso**: tramo con algún U, duración posible ≥ 8 s y sin episodio demostrado. Se informa `desde`, `hasta`,
     `duracion_posible_s`, `saturado_observado_s`, `desconocido_s`, `desconocido_antes_s` y `toca_borde`.
   - La comparación con 8 s es inclusiva (tolerancia 1e-6).
3. `evaluar()`:
   - **ventana con episodio:**
     - `false` solo si la línea base tiene cobertura suficiente, **sin episodios ni dudosos**;
     - base con episodios → `null` («también en la línea base»);
     - base **dudosa** → `null` («línea base dudosa: "nueva" no demostrable»);
     - base sin cobertura → `null`.
   - **ventana sin episodio:**
     - cobertura insuficiente → `null`;
     - algún dudoso → `null`;
     - si no → `true`.

Lo que no se hace:
- no se interpola;
- un dato ausente no se convierte en «no saturado»;
- no se suman tramos separados por un N válido.

La cobertura (≥ 99 %, sin U > 4 s) se sigue exigiendo igual, pero ya no basta sola.

`construir_entrada.py` 2026-11-06.3 exige `evaluar_s14 2026-11-06.2`: con la 2026-11-06.1 deja S14 en `null`.

## 2. Reproducción: antes y después

Salidas completas en `../evidencia/13-correccion-s14/repro-a12deae.txt` y `repro-nuevo.txt` (guion `repro_s14.py`,
banco Docker sin red).

| Paso | `a12deae` (evaluar_s14 2026-11-06.1) | `902991e` (evaluar_s14 2026-11-06.2) |
|---|---|---|
| A) lecturas completas | S14 `false` (saturación nueva, 1 episodio) | S14 `false` (igual) |
| B) `psi` ausente en [D+100, D+103) | componente CPU `true`, S14 **`true`**, «sin episodios», `dudosos: []` | componente CPU `null`, S14 **`null`**: «1 posible episodio ≥ 8 s con datos ausentes (5 s saturados observados + 4 s desconocidos)», `duracion_posible_s` 9, `desconocido_antes_s` 4 |
| B) cobertura | 99,89 %, hueco máximo 4 s, `ok` | igual: la cobertura no cambia |
| C) punta a punta | S14 `true`, «estable con carga suficiente», `habilita_condicion_3` **true**, **rc 0** | S14 `null`, «no demostrable», `habilita_condicion_3` **false**, **rc 1** |

## 3. Casos temporales: esperado y obtenido

Valores **obtenidos** impresos por la herramienta, no solo «la prueba pasa»: `../evidencia/13-correccion-s14/tabla_casos.py`
→ `tabla-casos-nuevo.txt` (0 discrepancias) y `tabla-casos-a12deae.txt` (12 discrepancias).

Notación: D = inicio de la ventana; S, U y N en segundos. «Ausente» = muestras sin el campo, que invalidan los pares de
[a−1, b).

| Caso | Datos | Tramo posible | Esperado | `902991e` | `a12deae` |
|---|---|---|---|---|---|
| Reproducción (antes) | sat [100,108), psi ausente [100,103) | U4 + S5 = 9 | `null` | `null` | **`true`** |
| Antes, < 8 | sat [104,109), ausente [103,104) | U2 + S5 = 7 | `true` | `true` | `true` |
| Antes, = 8 | sat [104,109), ausente [102,104) | U3 + S5 = 8 | `null` | `null` | **`true`** |
| Antes, > 8 | sat [104,109), ausente [101,104) | U4 + S5 = 9 | `null` | `null` | **`true`** |
| Después, < 8 | sat [100,105), ausente [106,107) | S5 + U2 = 7 | `true` | `true` | `true` |
| Después, = 8 | sat [100,106), ausente [107,108) | S6 + U2 = 8 | `null` | `null` | `null` |
| Después, > 8 | sat [100,106), ausente [107,109) | S6 + U3 = 9 | `null` | `null` | `null` |
| Dentro, < 8 | sat [100,106), ausente [102,103) | S1 + U2 + S3 = 6 | `true` | `true` | `true` |
| Dentro, = 8 | sat [100,108), ausente [103,104) | S2 + U2 + S4 = 8 | `null` | `null` | `null` |
| Dentro, > 8 | sat [100,110), ausente [104,106) | S3 + U3 + S4 = 10 | `null` | `null` | `null` |
| Saturación demostrada con hueco | sat [100,120), ausente [115,116) | S14 contiguos | `false` | `false` | `false` |
| Datos completos sin saturación | — | todo N | `true` | `true` | `true` |
| Datos completos, 8 s saturados | sat [100,108) | S8 | `false` | `false` | `false` |
| Hueco aislado | ausente [500,502) | U3 entre N | `true` | `true` | `true` |
| Tramos separados por N | sat [100,105) y [106,111), ausente [108,109) | S5 · N1 · S1+U2+S2 = 5 | `true` (no se suman) | `true` | `true` |
| Borde de inicio de la ventana, 8 s | sin muestras [D−2, D+2), sat [2,8) | U2 + S6 = 8 | `null` | `null` | **`true`** |
| Borde de inicio de la ventana, 7 s | sin muestras [D−3, D+1), sat [1,7) | U1 + S6 = 7 | `true` | `true` | `true` |
| Borde de fin de la ventana, 9 s | sin muestras [H−2, H+2), sat [3591,3597) | S6 + U3 = 9 | `null` | `null` | `null` |
| Borde de fin de la ventana, 7 s | sin muestras [H−2, H+2), sat [3593,3597) | S4 + U3 = 7 | `true` | `true` | `true` |
| Base limpia + episodio en la ventana | ventana sat [100,120) | — | `false` («nueva») | `false` | `false` |
| Base dudosa, hueco antes | base sat [13,18), psi ausente [11,13) | base U3 + S5 = 8 | `null` | `null` | **`false`** |
| Base dudosa, hueco después | base sat [10,15), ausente [16,18) | base S5 + U3 = 8 | `null` | `null` | `null`* |
| Base dudosa en su borde de inicio | base sin muestras [BD−2, BD+2), sat [2,8) | base U2 + S6 = 8 | `null` | `null` | **`false`** |
| Base con hueco aislado | base psi ausente [100,102) | — | `false` | `false` | `false` |
| CPU, hilos, softirq, disco y memoria | S5 / S8 / campo ausente [101,104) + sat [104,109) | 5 / 8 / U4 + S5 = 9 | `true` / `false` / `null` | `true` / `false` / `null` en las cinco | `true` / `false` / **`true`** en las cinco |

\* `a12deae` acierta el valor, pero por un motivo erróneo: trata la base como «saturada», cuando lo correcto es
«dudosa».

En todos los casos de ventana la cobertura es suficiente (`ok`). Eso confirma que la cobertura sola no decide.

## 4. De punta a punta (`construir_entrada.py` → `evaluar_ecarga.py veredicto`)

Se comprueban el valor de S14, el veredicto, `habilita_condicion_3` y el rc, no el texto del motivo.

| Caso | S14 | Veredicto | `habilita_condicion_3` | rc | `a12deae` |
|---|---|---|---|---|---|
| Evidencia completa, sin saturación | `true` | estable con carga suficiente | true | 0 | igual |
| Saturación demostrada de 8 s exactos | `false` | no estable | false | 1 | igual |
| Saturación demostrada de 30 s | `false` | no estable | false | 1 | igual |
| **Reproducción**: psi ausente antes de la saturación | **`null`** | **no demostrable** | **false** | **1** | `true`, estable con carga suficiente, **true**, **rc 0** |

El evaluador `evaluar_ecarga.py` 2026-11-06.4 (`53e9f7bd…`) no cambia.

## 5. Pruebas y regresiones

| Ejecución | Resultado | Evidencia (`../evidencia/13-correccion-s14/`) |
|---|---|---|
| `tests/test_etapa4_ecarga_prep.py`, versión nueva, usuario 65534 | **85 pasan**, 0 fallan, 0 omitidas | `banco-nuevo-65534.txt` |
| Lo mismo, como root | **85 pasan**, 0 fallan, 0 omitidas | `banco-nuevo-root.txt` |
| `-k regresion` contra `a12deae` | **12 fallan, 26 pasan**, 47 no seleccionadas | `banco-a12deae-regresiones.txt` |
| Suite completa del producto, usuario 65534 (con el repo de documentación) | **1 013 pasan**, 0 fallan, 47 omitidas (§5.1) | `suite-completa-65534.txt` |
| Suite completa, root + `NET_ADMIN` (red aislada) + repo de documentación | **1 057 pasan**, 0 fallan, 3 omitidas | `suite-completa-root.txt` |
| `test_dashboard_gui_contract.py` en el portátil (con node) | intermitente por el entorno (§5.2) | `gui-node-portatil.txt` |

Contra `a12deae`:
- **Fallan las 12 regresiones de S14:**
  - las tres «antes» de `test_s14_tiempo_desconocido`;
  - borde de inicio de la ventana;
  - base dudosa por hueco antes;
  - base dudosa en su borde;
  - las cinco componentes;
  - la de punta a punta.

  Cada una falla en la aserción del defecto: `True is None`, o `False is None` en la base.
- **Pasan las 26 regresiones de arranque, parada, lecturas y PCAP.** Es lo esperado: `a12deae` ya traía esas
  correcciones, y sus regresiones fallaban con `c7f24510`/`e83f4be6` (`../evidencia/12-correccion-preparacion/banco-anterior-regresiones.txt`).
  Se volvieron a ejecutar y siguen pasando.

**Corrección del banco, no del producto.** `test_agente_sin_proceso_da_aplicar_cero` (y otras dos llamadas a
`muestreo(lab, "seco", 0)`) fallaba de forma intermitente con `muestras.txt` vacío:
- el guion fija `FIN = int(time.time())` y muestrea `while date <= FIN`, así que si el segundo cambia entre las dos
  lecturas no toma ninguna muestra;
- la carrera ya estaba en las pruebas de `a12deae`;
- se dio un margen de 2 s en las tres llamadas.

No cambia el guion.

### 5.1 Omisiones (comprobadas, no atribuidas al entorno sin verificarlo)

- Root: las 3 de siempre.
  - Las 2 de `chmod 000` no tienen sentido como root, y en la pasada 65534 corren y pasan.
  - La de `node` se omite porque la imagen no tiene `node`; en el portátil corre (§5.2).
- 65534: 47.
  - 33 de `test_etapa4_p4_instaladores.py` («banco Linux como root»);
  - 9 de `test_etapa2_correcciones.py` («necesita root»);
  - 1 de `test_etapa2_correcciones.py` y 3 de `test_etapa2_cadena.py` («root y nft»);
  - 1 de `node`.

  Las 44 de root y `nft` corren y pasan en la pasada root: 1 013 + 44 = 1 057.
- La r2 contaba 53 omitidas sin root. Su salida guardada solo conserva las últimas líneas, así que la diferencia de 6
  no se atribuye a ninguna causa. Las 47 de ahora están listadas una a una en `suite-completa-65534.txt`.

### 5.2 Prueba de la GUI en el portátil: intermitente, no atribuible a este cambio

`test_served_demo_denies_outside_whitelist_and_serves_allowed_source` falla en algunas corridas con
`OSError: [WinError 6] Controlador no válido` o `[WinError 50]`, en `subprocess.Popen` → `DuplicateHandle` /
`CreateProcess`. Es decir, **antes** de que arranque el panel.

| Lanzamiento | Corridas | Pasan las 5 |
|---|---|---|
| `cmd /c "… < NUL 2>&1"` (como en la r2) | 4 | 1 |
| `Start-Process` con stdin, stdout y stderr redirigidos a ficheros | 5 | 3 |
| Solo esa prueba (`-k whitelist`) | 1 | 1 |

Ni la prueba ni `scripts/engine/dashboard.py` cambian en `902991e`: el commit toca solo `deploy/etapa4/ecarga/` y
`tests/test_etapa4_ecarga_prep.py`. En la r2 dio 5 de 5 en una corrida.

Queda como **intermitencia del entorno Windows de la sesión, no resuelta**. No la oculta ningún reintento: los
recuentos están arriba y las salidas en la evidencia. Las otras 4 pruebas de la GUI pasan siempre.

## 6. Referencias exactas

**Producto `902991e`** (`902991ec077c9495a99e1075cb26af35ae980507`), rama `recuperacion/etapa4a-pendientes-20261106`.
**No se ha fusionado en `main`**, que sigue en `7b275b8`. Ubicación canónica: `deploy/etapa4/ecarga/`.
- `SHA256SUMS`: sha256 `e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80`.
- Evaluador: `deploy/etapa4/sensor1/evaluar_ecarga.py` **2026-11-06.4**, sha256 `53e9f7bd…c5d23f`, sin cambios.

| Fichero | Versión | sha256 | ¿Cambia respecto a `a12deae`? |
|---|---|---|---|
| `evaluar_s14.py` | **2026-11-06.2** | `e8075ac954a120fcb4098d8d7b063ee989ef33e957e4ffded1f15246ff04d3fa` | **sí** (era `ba2ba3b9…`, 2026-11-06.1) |
| `construir_entrada.py` | **2026-11-06.3** | `7c6b43cad2f166ce5d87648c42d85f251b81c842fd9b52896a016b2b5f312a79` | **sí** (era `9fa51ea5…`, 2026-11-06.2) |
| `README.md` | — | `0849d1f8a2796ef4c27e2a2f8391e7dcdcdb085ea6f311df3dcd51948fc6daaf` | sí (versiones) |
| `generadores.sh` | 2026-11-06.2 | `0badeac51ccf2339122412a7607b01176b22f97413e927134bb11ab208a3f662` | no |
| `muestreo_bastion.sh` | 2026-11-06.2 | `35c3248fd9157b0cc9c12d9c1d6aec3ea1112233a99bfa6cea1582ead26d459f` | no |
| `guardia.py` | 2026-11-06.2 | `37581e901103353fc27d15958d0601948c6da88b2625c3be8959fd2536a8dc0d` | no |
| `sensor1_muestreadores.sh` | 2026-11-06.2 | `25fb732ddc15bc83f1f1a79e6e9ccb7ca0cd867a2dfd48270a26dd9ba03c915b` | no |
| `muestreo_s14.py` | 2026-11-06.1 | `c4ef7c845df49c1c63e16b2e92d8a71c1f517fab007359864122131eff88e67f` | no |
| `sensor1_post.sh` | 2026-11-06.2 | `9be5ed13ef7e781a268326f0708e46af30caf0af8a35252ead3d43b42d6ec13b` | no |
| `derivar_pcap.py` | 2026-11-06.2 | `64b51deaad50c2fa8751248d24313f7b9af1d3fb975e085b783475505ba0c7fc` | no |
| `derivar_bastion.py` | 2026-11-06.2 | `09c4a0dfd8610be719719f4fe1fa06c501d7e68a45c8f64e16bb7ff4e1f3ec38` | no |

Hay una sola copia de trabajo, `deploy/etapa4/ecarga/` en el producto. `a12deae` sigue identificable en GitHub y en
los hosts, pero **no se usa**.

La plantilla `TRAZABILIDAD.PLANTILLA-SIN-RESULTADOS.json` muestra `construir_entrada 2026-11-06.1` porque es de la r1
y solo ilustra la estructura. La traza real la escribe la herramienta con su `VERSION`.

## 7. Paquete en los hosts: PENDIENTE antes de P0

> **Nota posterior (06-nov): guiones SUSTITUIDOS.** Los dos guiones de abajo
> (`../evidencia/13-correccion-s14/paquete_902991e.sh` y `op_host_902991e.sh`) **no deben usarse**:
> - podían terminar con rc 0 aunque fallara la verificación de un host;
> - su manifiesto interno podía listarse a sí mismo.
>
> Se conservan sin modificar como evidencia. Los sustituyen los guiones r2 de
> [`traslado-902991e-r2/`](traslado-902991e-r2/), probados en banco (33/33). Las instrucciones, los códigos de salida y
> la recuperación están en [`TRASLADO-PAQUETE-902991e-r2.md`](TRASLADO-PAQUETE-902991e-r2.md). La copia sigue **sin
> ejecutar**.

**No se ha copiado el paquete de `902991e` a los hosts.** El intento de copia (solo copiar y verificar, como el de
`a12deae`) lo bloqueó el control de permisos de la sesión, por ser una escritura remota. El encargo autorizaba código,
pruebas aisladas y documentación, así que no se buscó otra vía.

Los guiones están preparados y **no se han ejecutado**:
- `../evidencia/13-correccion-s14/paquete_902991e.sh`:
  - aborta si la rama remota no es `902991e`, si el evaluador no es `53e9f7bd…` o si `ecarga/SHA256SUMS` no es
    `e001352c…`;
  - no sobrescribe nada.
- `op_host_902991e.sh`:
  - deja `paquete-a12deae.NO-USAR.txt` junto a `paquete-a12deae`, sin tocar su contenido;
  - imprime las `VERSION` de `evaluar_s14` y `construir_entrada`.

En los hosts sigue `~/cf-e4/paquete-a12deae`, con `evaluar_s14` 2026-11-06.1. **No sirve para S14 ni para construir la
entrada** (protocolo r4 §3.5, punto 13).

## 8. Estado y veredictos (separados)

| Pregunta | Respuesta | Base |
|---|---|---|
| **¿Corregido en banco?** | **Sí, para el defecto descrito y los casos de §3.** | Reproducción exacta: `null`, «no demostrable», rc 1. 0 discrepancias en la tabla de casos. 12 regresiones que fallan con `a12deae` y pasan ahora. 85/85 en el banco de E-carga. Suite root 1 057 sin fallos. No se declara «todo resuelto» por el número de pruebas: la regla se probó con datos sintéticos de una sola forma de ausencia por caso, y la GUI en el portátil sigue intermitente (§5.2) |
| **¿Validado en vivo?** | **No.** | Pendiente: copiar el paquete de `902991e` a los hosts (§7) y repetir P0 con él. No se ha medido en Sensor1 el patrón real de huecos del muestreo de 1 s con carga; si fuera frecuente, S14 podría quedar `null` a menudo. Eso daría «no demostrable», no un falso «estable». Siguen pendientes las medidas en vivo de la r2: arranque y parada con el systemd real, coste y cobertura del muestreo S14, y retención del anillo con carga |
| **¿Preparación lista?** | **No del todo.** | Falta la copia del paquete (§7). Después, la orden de Mark, que incluye aprobar la **r4** |
| **¿E-carga ejecutada o programada?** | **No.** | Este encargo no autoriza ejecutarla ni pasar a la 4B o la 4C |

Orden necesaria, igual que en la r2 §8, con estos cambios:
- protocolo **r4**;
- paquete `902991e`;
- resultados en `evidencia/14-ecarga-ejecucion/`, sea cual sea el resultado.
