# Paso 2 — instalación del motor candidato y reversión

Procedimiento para **cuando se autorice** la validación en vivo (paso 2). En el paso 1 no se ejecutó nada de
esto: el motor desplegado sigue siendo 7b275b8 (`motor_decision.py` sha256 `e2b2eb53…`).

## 0. Qué se instala

| Archivo en el sensor | Origen (repo del código, commit `24f8a80`) | sha256 | Cambio |
|---|---|---|---|
| `/home/m4rk/cyberflow/scripts/engine/motor_decision.py` | `scripts/engine/motor_decision.py` | `6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e` | sustituye a `e2b2eb535091ea0fb7aa08054aa8cc4eff295a4e678269cba5d4a5ee5d95bc73` |
| `/home/m4rk/cyberflow/scripts/engine/motor_incremental.py` | `scripts/engine/motor_incremental.py` | `a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168` | **nuevo** (el motor lo importa) |
| `/etc/logrotate.d/cyberflow` | generado con `scripts/setup/cyberflow_config.py --mostrar` | — | añade `logs/_state/ciclos.jsonl` a la estrofa existente |

**No cambian**: modelo, manifiesto, esquema desplegado (`configs/features/multilayer-v2.json`, sha256 `e032a1a2…`, que
difiere del de 7b275b8 y es el que usaron todas las corridas del paso 1), `heuristicos.py` (`10deb05d…`),
`extract_multilayer_v2.py` (`7130edae…`), `extract_multilayer_v3.py` (`5adbfbf4…`) ni la unidad `ppi-motor.service`.

**Argumentos:** los mismos que hoy. Las dos opciones nuevas no se usan en producción:

- `--ciclos-path`: si se omite, el registro va a `/home/m4rk/cyberflow/logs/_state/ciclos.jsonl`, que está dentro de
  `ReadWritePaths=/home/m4rk/cyberflow/logs` (`ProtectSystem=strict`).
- `--verificar-equivalencia`: solo para validación offline, porque duplica el cálculo.

**Permisos:** los dos `.py` son de `m4rk:m4rk` con modo `0664`, igual que el actual. El servicio corre como `m4rk`, así
que copiarlos no necesita sudo. Sí necesitan sudo el reinicio del servicio, el respaldo y el cambio de la
configuración de logrotate, y la comprobación global de logrotate.

**Respaldo de logrotate en una ubicación exclusiva:** `/var/backups/cyberflow-paso2/`, un directorio creado solo
para este procedimiento (`root:root`, `0700`). El respaldo **no** puede quedar en `/etc/logrotate.d/`:
`/etc/logrotate.conf` incluye todo ese directorio (`include /etc/logrotate.d`, línea 25), así que una copia allí se
leería como configuración y duplicaría la entrada de `motor_decision.log`.

Esto ya ocurre hoy. Una lectura sin sudo de `logrotate -d /etc/logrotate.conf`, hecha el 1-nov, termina con rc=1 y
estos errores:

- `cyberflow.anterior:9 duplicate log entry for /home/m4rk/cyberflow/logs/motor_decision.log`;
- `suricata.orig-cyberflow:1 duplicate log entry` para `/var/log/suricata/fast.log` y `/var/log/suricata/eve.json`.

En los dos casos logrotate se salta el fichero entero. Son respaldos antiguos que quedaron dentro de
`/etc/logrotate.d/`. Este procedimiento **no** los toca: moverlos es una decisión aparte de Mark. Lo que hace es
registrar la línea base y exigir que la instalación no añada errores nuevos.

**Qué deja de escribirse:** `logs/_state/eve_window.jsonl`. Ningún otro componente lo lee (comprobado con búsqueda
en el repositorio). Queda con su última fecha de modificación.

**Qué se escribe de nuevo:**
- `logs/_state/ciclos.jsonl`: un registro `ciclo` cada ~10 s, de unos 0,9 kB, lo que da unos 8 MB al día.
- En cada registro `decision` y `ventana_no_evaluada`, el campo `decidido_en`.
- En el registro de arranque, los campos `procesamiento: "incremental"` y `ciclos_path`.

## 0.1 Cómo se evitan los duplicados al arrancar: `claves_ya_registradas()`

Los dos motores **sí leen `motor_decision.log` al arrancar**. La función `claves_ya_registradas()` es idéntica en
7b275b8 (`scripts/engine/motor_decision.py`, líneas 274–301, llamada en la 365) y en el candidato 24f8a80 (líneas
293–320, llamada en la 416):

1. **Lectura.** Lee los **últimos 16 MiB** del fichero vigente, `logs/motor_decision.log`, apuntado por `--log-path`.
   Si el fichero es mayor, descarta la primera línea, que puede estar cortada.
2. **Filtrado.** De las líneas que contienen `"window_end_utc"` y son JSON válido, toma las de los eventos `decision` y
   `ventana_no_evaluada`, y carga sus claves `(entity_ip, window_end_utc)` en `scored_windows`.
3. **Uso de las claves.** Una ventana cuya clave está en `scored_windows` no se vuelve a decidir ni a registrar como no
   evaluada (candidato: líneas 704, 712 y 871).
   - En el candidato, además, el punto de partida de las filas pendientes de cada entidad (A_min, la primera ancla del
     rango no puntuada) se calcula con esas mismas claves. Un reinicio retoma el trabajo justo después de lo ya
     registrado.
4. **Tope.** `scored_windows` se acota a 20 000 claves (`MAX_SCORED_WINDOWS`), descartando primero las más antiguas.
   Si al arrancar se cargan más, el primer ciclo conserva las 20 000 más recientes según el orden del registro.

**Por qué basta.** Tras un reinicio, el motor solo regenera ventanas de los últimos `history_seconds` (230 s), que son
los PCAP del anillo y el EVE recientes. Por eso necesita las claves de unos pocos minutos. 16 MiB son decenas de miles
de registros (unos 0,6 kB cada uno en el registro de la campaña A), muchas horas incluso al ritmo de la campaña.

**Límites:**

- **Solo el fichero vigente.** No lee `motor_decision.log.1`. Si el motor se reinicia en los ~230 s siguientes a una
  rotación (la ejecución diaria de logrotate; `maxsize 200M` solo se evalúa en esa ejecución), las ventanas decididas
  justo antes de rotar no están en el fichero nuevo y podrían repetirse. Para revisarlo: buscar duplicados en `motor_decision.log` y `motor_decision.log.1` juntos.
- **Registros no escritos.** Una ventana decidida que aún no llegó al fichero cuando el proceso muere no se recupera, y
  tras el reinicio se decide otra vez. En el registro no queda duplicada, pero su primera decisión se pierde.
  - En 7b275b8 esa ventana abarca como mucho un registro, porque escribe cada decisión al tomarla.
  - En el candidato abarca el lote de un ciclo, porque escribe una vez al final del ciclo. `systemctl restart` envía
    SIGTERM y el motor no lo intercepta, así que puede caer a mitad de ciclo.
  - Con `--enforce`, la acción de bloqueo ya aplicada de ese lote se repetiría sin registro previo. En el paso 2 el
    motor corre en observación, sin `--enforce`.
- **Líneas corruptas.** Una línea corrupta o cortada se ignora, y su clave no se recupera.

**Qué está probado:**

- **Reinicio del mismo motor.** En R4 (7b275b8 y candidato) y R5 (candidato 9b4cf2b) el arnés reinicia `main()` a las
  09:05, a mitad de la inundación, con el mismo `--log-path`, así que `claves_ya_registradas()` lee lo escrito antes.
  Resultado: 0 duplicados en las dos versiones y 2300 registros iguales entre ellas.
- **Qué no ejercita.** El arnés corta entre ciclos, no a mitad de uno, así que no prueba el límite de los registros no
  escritos. Tampoco prueba la rotación.

**No probado:**

- **Reversión cruzada candidato → 7b275b8.** Por lectura del código, los registros del candidato tienen los mismos
  campos `event`, `entity_ip` y `window_end_utc`, así que 7b275b8 recuperaría sus claves igual. Esto **no se probó
  offline**.
- **Instalación referencia → candidato.** Tampoco se probó. Por eso el apartado 6 y el 7 comprueban los duplicados
  después de instalar y después de revertir.

## 1. Comprobaciones previas

`[SENSOR1 m4rk]` → lo ejecuto yo (solo lectura)

```bash
cd /home/m4rk/cyberflow
sha256sum scripts/engine/motor_decision.py scripts/engine/heuristicos.py \
          scripts/features/extract_multilayer_v2.py scripts/features/extract_multilayer_v3.py
# esperado: e2b2eb53…  10deb05d…  7130edae…  5adbfbf4…  (si motor_decision.py no es e2b2eb53, PARAR)
systemctl is-active ppi-motor ppi-motor-capture suricata
df -h /home | tail -1                                  # margen para ciclos.jsonl
tail -n 1 logs/motor_decision.log | cut -c1-200        # el motor está decidiendo ahora
ls -la logs/motor_decision.log*                        # hora de la última rotación (ver 0.1)
```

## 2. Traer los archivos del commit

`[LAPTOP PowerShell]` → lo ejecuto yo

```powershell
cd "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-candidato"
git fetch origin; git archive -o $env:TEMP\candidato-24f8a80.tgz 24f8a80
scp $env:TEMP\candidato-24f8a80.tgz gadmin@10.10.10.30:cf-stage/
```

`[BASTIÓN gadmin]` → lo ejecuto yo

```bash
scp cf-stage/candidato-24f8a80.tgz sensor1:
```

`[SENSOR1 m4rk]` → lo ejecuto yo

```bash
rm -rf ~/cf-paso2 && mkdir -p ~/cf-paso2/producto-24f8a80
tar -xzf ~/candidato-24f8a80.tgz -C ~/cf-paso2/producto-24f8a80
cd ~/cf-paso2/producto-24f8a80
sha256sum scripts/engine/motor_decision.py scripts/engine/motor_incremental.py
# esperado: 6c274d9e…  a403307a…
~/cyberflow/.venv/bin/python -m unittest tests.test_motor_incremental tests.test_cyberflow_config   # debe dar OK
```

## 3. Copia de seguridad e instalación de los archivos

`[SENSOR1 m4rk]` → lo ejecuto yo (sin sudo: los archivos son de m4rk)

```bash
cd /home/m4rk/cyberflow/scripts/engine
cp -p motor_decision.py motor_decision.py.7b275b8-e2b2eb53          # copia para la reversión
sha256sum motor_decision.py.7b275b8-e2b2eb53                        # e2b2eb53…
install -m 0664 ~/cf-paso2/producto-24f8a80/scripts/engine/motor_incremental.py motor_incremental.py
install -m 0664 ~/cf-paso2/producto-24f8a80/scripts/engine/motor_decision.py    motor_decision.py
sha256sum motor_decision.py motor_incremental.py                    # 6c274d9e…  a403307a…
~/cyberflow/.venv/bin/python -m py_compile motor_decision.py motor_incremental.py
~/cyberflow/.venv/bin/python motor_decision.py --help | grep -E "ciclos-path|verificar-equivalencia"
```

El servicio en marcha sigue usando el código que ya cargó en memoria; el cambio se aplica al reiniciarlo.

## 4. Reinicio del servicio

Conviene no reiniciar en los ~230 s siguientes a una rotación del registro (ver 0.1).

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo systemctl restart ppi-motor
```

## 5. Rotación de `ciclos.jsonl`

`[SENSOR1 m4rk]` → lo ejecuto yo (genera el fichero; solo lectura sobre /etc)

```bash
python3 ~/cf-paso2/producto-24f8a80/scripts/setup/cyberflow_config.py \
    --config /home/m4rk/cyberflow/configs/cyberflow.toml --mostrar \
  | awk '/^### \/etc\/logrotate.d\/cyberflow$/{p=1; getline; next} p && /^=+$/{exit} p' \
  | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > ~/cf-paso2/logrotate-cyberflow.nuevo
diff /etc/logrotate.d/cyberflow ~/cf-paso2/logrotate-cyberflow.nuevo
# esperado: solo el comentario y la línea de rutas, que pasa a
# /home/m4rk/cyberflow/logs/motor_decision.log /home/m4rk/cyberflow/logs/_state/ciclos.jsonl {
```

No uses `cyberflow_config.py --escribir`: regenera **todas** las unidades de systemd, y aquí solo hay que tocar este
fichero.

**5.1 Respaldo exclusivo y línea base global**

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo install -d -m 0700 -o root -g root /var/backups/cyberflow-paso2
sudo cp -p /etc/logrotate.d/cyberflow /var/backups/cyberflow-paso2/logrotate.d-cyberflow.antes-paso2
sudo sha256sum /etc/logrotate.d/cyberflow /var/backups/cyberflow-paso2/logrotate.d-cyberflow.antes-paso2
#   los dos hashes deben coincidir
sudo logrotate -d /etc/logrotate.conf > ~/cf-paso2/logrotate-global-antes.txt 2>&1
echo "rc=$?" | tee ~/cf-paso2/logrotate-global-antes.rc
```

La salida completa queda en `~/cf-paso2/logrotate-global-antes.txt`, sin filtrar, y el código de salida en el `.rc`.
Se espera rc≠0 por los errores que ya existían (apartado 0). Se revisa entera con
`less ~/cf-paso2/logrotate-global-antes.txt`.

**5.2 Instalación y comprobación global posterior**

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo install -m 0644 -o root -g root ~/cf-paso2/logrotate-cyberflow.nuevo /etc/logrotate.d/cyberflow
sudo logrotate -d /etc/logrotate.conf > ~/cf-paso2/logrotate-global-despues.txt 2>&1
echo "rc=$?" | tee ~/cf-paso2/logrotate-global-despues.rc
```

`[SENSOR1 m4rk]` → lo ejecuto yo (compara las dos salidas completas guardadas; no las sustituye)

```bash
cat ~/cf-paso2/logrotate-global-antes.rc ~/cf-paso2/logrotate-global-despues.rc
diff ~/cf-paso2/logrotate-global-antes.txt ~/cf-paso2/logrotate-global-despues.txt
```

Criterios:
- el rc posterior es igual al de la línea base;
- en el `diff` no aparece ninguna línea `error:` nueva;
- la salida posterior lista `/home/m4rk/cyberflow/logs/_state/ciclos.jsonl` bajo el patrón de `motor_decision.log`.

Si aparece un error nuevo, se revierte con el apartado 7.2.

## 6. Comprobaciones posteriores (primeros 30 minutos)

`[SENSOR1 m4rk]` → lo ejecuto yo (solo lectura)

```bash
systemctl is-active ppi-motor && journalctl -u ppi-motor --since "-10 min" --no-pager | tail -20   # sin Traceback
grep '"motor_startup"' ~/cyberflow/logs/motor_decision.log | tail -1 | grep -o '"procesamiento": "[a-z]*"'
#   → "procesamiento": "incremental"
tail -n 3 ~/cyberflow/logs/_state/ciclos.jsonl | cut -c1-300      # un registro nuevo cada ~10 s
python3 - <<'EOF'
import json, statistics
c = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/_state/ciclos.jsonl")][-180:]   # ~30 min
d = sorted(x["duracion_s"] for x in c)
print("ciclos", len(d), "p50", d[len(d)//2], "p95", d[int(.95*(len(d)-1))], "max", d[-1],
      ">9.5 s", sum(x > 9.5 for x in d), "no_evaluadas", sum(x["no_evaluadas"] for x in c))
EOF
python3 - <<'EOF'
# Duplicados a traves del reinicio: el registro vigente y, si existe, el rotado (limite de claves_ya_registradas)
import collections, json, os
regs = []
for p in ("/home/m4rk/cyberflow/logs/motor_decision.log.1", "/home/m4rk/cyberflow/logs/motor_decision.log"):
    if os.path.exists(p):
        regs += [json.loads(x) for x in open(p) if x.strip()][-20000:]
k = collections.Counter((x["entity_ip"], x["window_end_utc"]) for x in regs
                        if x.get("event") in ("decision", "ventana_no_evaluada"))
print("claves duplicadas:", sum(n - 1 for n in k.values() if n > 1))
print("decidido_en > logged_at:", sum(1 for x in regs if "decidido_en" in x and x["decidido_en"] > x["logged_at"]))
EOF
```

`[BASTIÓN gadmin]` → lo ejecuto yo

```bash
curl -sk -o /dev/null -w '%{http_code}\n' https://10.10.60.11:8788/    # 401, como antes: el panel sigue leyendo el registro
```

Criterios mínimos para dar por buena la instalación:
- el servicio está activo y no hay trazas de error;
- el arranque registra `procesamiento: incremental`;
- `ciclos.jsonl` crece con cada ciclo;
- hay 0 claves duplicadas;
- `decidido_en` ≤ `logged_at` en todos los registros;
- el panel responde;
- logrotate no tiene errores nuevos frente a la línea base (5.2).

El rendimiento en vivo (p95 por debajo de 10 s, también con carga) es el objeto del paso 2. No se da por demostrado
con estas comprobaciones.

## 7. Reversión

**7.1 Motor**

`[SENSOR1 m4rk]` → lo ejecuto yo (sin sudo)

```bash
cd /home/m4rk/cyberflow/scripts/engine
install -m 0664 motor_decision.py.7b275b8-e2b2eb53 motor_decision.py
sha256sum motor_decision.py                      # e2b2eb53…
rm -f motor_incremental.py                       # opcional: 7b275b8 no lo importa
```

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo systemctl restart ppi-motor
```

**7.2 logrotate (solo si se aplicó el apartado 5.2)**

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo install -m 0644 -o root -g root /var/backups/cyberflow-paso2/logrotate.d-cyberflow.antes-paso2 /etc/logrotate.d/cyberflow
sudo sha256sum /etc/logrotate.d/cyberflow /var/backups/cyberflow-paso2/logrotate.d-cyberflow.antes-paso2   # iguales
sudo logrotate -d /etc/logrotate.conf > ~/cf-paso2/logrotate-global-revertido.txt 2>&1
echo "rc=$?" | tee ~/cf-paso2/logrotate-global-revertido.rc
```

`[SENSOR1 m4rk]` → lo ejecuto yo

```bash
diff ~/cf-paso2/logrotate-global-antes.txt ~/cf-paso2/logrotate-global-revertido.txt   # sin errores nuevos frente a la línea base
```

El respaldo de `/var/backups/cyberflow-paso2/` se conserva hasta cerrar el paso 2.

**7.3 Comprobación tras revertir**

`[SENSOR1 m4rk]` → lo ejecuto yo

```bash
grep '"motor_startup"' ~/cyberflow/logs/motor_decision.log | tail -1 | grep -c procesamiento   # 0: es 7b275b8
ls -la --time-style=+%H:%M ~/cyberflow/logs/_state/eve_window.jsonl                         # vuelve a actualizarse
```

Después se repite el script de claves duplicadas del apartado 6, porque la reversión cruzada candidato → 7b275b8
**no se probó offline** (ver 0.1).

Los registros que escribió el candidato son compatibles con los consumidores de 7b275b8 (`publicar_feed.py`, el
panel y el analizador): mismas claves, mismo significado de `logged_at` y campos añadidos que esos consumidores
ignoran. `ciclos.jsonl` puede quedarse o borrarse; no lo lee nadie más.
