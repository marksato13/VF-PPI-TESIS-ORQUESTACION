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
que copiarlos no necesita sudo. Sí necesitan sudo el reinicio del servicio y el cambio en `/etc/logrotate.d`.

**Qué deja de escribirse:** `logs/_state/eve_window.jsonl`. Ningún otro componente lo lee (comprobado con búsqueda
en el repositorio). Queda con su última fecha de modificación.

**Qué se escribe de nuevo:**
- `logs/_state/ciclos.jsonl`: un registro `ciclo` cada ~10 s, de unos 0,9 kB, lo que da unos 8 MB al día.
- En cada registro `decision` y `ventana_no_evaluada`, el campo `decidido_en`.
- En el registro de arranque, los campos `procesamiento: "incremental"` y `ciclos_path`.

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

`[SENSOR1 m4rk]` → lo ejecutas tú (`sudo` pide tu contraseña)

```bash
sudo cp -p /etc/logrotate.d/cyberflow /etc/logrotate.d/cyberflow.antes-paso2
sudo install -m 0644 -o root -g root ~/cf-paso2/logrotate-cyberflow.nuevo /etc/logrotate.d/cyberflow
sudo logrotate -d /etc/logrotate.d/cyberflow 2>&1 | grep -E "error|considering"   # sin "error"
```

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
import json, collections
r = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/motor_decision.log")][-20000:]
k = collections.Counter((x["entity_ip"], x["window_end_utc"]) for x in r if x.get("event") == "decision")
print("decisiones duplicadas:", sum(n - 1 for n in k.values() if n > 1))
print("decidido_en > logged_at:", sum(1 for x in r if "decidido_en" in x and x["decidido_en"] > x["logged_at"]))
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
- hay 0 decisiones duplicadas;
- `decidido_en` ≤ `logged_at` en todos los registros;
- el panel responde.

El rendimiento en vivo (p95 por debajo de 10 s, también con carga) es el objeto del paso 2. No se da por
demostrado con estas comprobaciones.

## 7. Reversión

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
sudo install -m 0644 -o root -g root /etc/logrotate.d/cyberflow.antes-paso2 /etc/logrotate.d/cyberflow   # si se aplicó el paso 5
```

`[SENSOR1 m4rk]` → lo ejecuto yo (comprobación)

```bash
grep '"motor_startup"' ~/cyberflow/logs/motor_decision.log | tail -1 | grep -c procesamiento   # 0: es 7b275b8
ls -la --time-style=+%H:%M ~/cyberflow/logs/_state/eve_window.jsonl                         # vuelve a actualizarse
```

Los registros que escribió el candidato son compatibles con los consumidores de 7b275b8 (`publicar_feed.py`, el
panel y el analizador): mismas claves, mismo significado de `logged_at` y campos añadidos que esos consumidores
ignoran.

Ni 7b275b8 ni el candidato leen `motor_decision.log` al arrancar. Tras un reinicio, cada uno parte del anillo de PCAP
y de la cola de EVE recientes, acotados por antigüedad. En R4, que reinicia el mismo motor a mitad de la inundación,
ninguno de los dos produjo duplicados. El reinicio cruzado (candidato → 7b275b8) no se probó offline; por eso conviene
comprobar los duplicados con el segundo script del apartado 6 también después de la reversión. `ciclos.jsonl` puede
quedarse o borrarse; no lo lee nadie más.
