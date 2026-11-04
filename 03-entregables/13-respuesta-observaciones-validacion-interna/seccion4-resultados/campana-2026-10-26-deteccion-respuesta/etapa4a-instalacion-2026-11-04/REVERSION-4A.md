# Reversión de la 4A (instalación en sombra del 04-nov-2026)

**Cuándo se revierte:** si se cumple un criterio de parada, o si Mark decide volver a la base 24f8a80.

**Criterios de parada:**
- un evento de aplicación;
- una tabla `cyberflow` en srv-dmz;
- un agente con `--aplicar`;
- reinicios del motor o de la captura;
- una captura C3 sostenida;
- una decisión de Mark.

El 04-nov no se cumplió ninguno, así que **no se revirtió**.

**Principio:** ninguna reversión reactiva la demo.
- La línea base de srv-dmz (`srvdmz-20261104T015754Z`) se tomó **después** de la P0: agente v1 apagado y ruleset
  vacío.
- El volcado de la tabla de la demo (`~/respaldo-cyberflow-v1-20261104T0138Z.nft`) **no se carga** en ningún paso.

**Orden:** primero srv-dmz (el punto de aplicación), luego el bastión (el relé) y luego Sensor1 (el detector). El
panel se revierte por separado, porque su versión no forma parte de los hashes del detector.

## 1. srv-dmz: agente v2

`[SRV-DMZ adminsrvdmz] → lo ejecuto yo (sudo NOPASSWD para este usuario)`

```bash
bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/revertir_srvdmz.sh ~/respaldos-etapa4/srvdmz-20261104T015754Z
```

**Qué hace:**
- para y deshabilita el agente v2;
- restaura las unidades del respaldo;
- copia la traza del agente a `~/respaldos-etapa4/srvdmz-evidencia-<fecha>`;
- comprueba que el ruleset es igual a la línea base (vacío).

Se probó **dos veces en vivo**, a las 02:15 y a las 02:18 del 04-nov, con resultado «REVERSIÓN OK». Las salidas están
en `evidencia/02-instalacion/`.

**Comprobación:**
`bash ~/cf-e4/paquete-c1bd845/deploy/etapa4/srvdmz/verificar_srvdmz.sh` → el agente v2 está inactivo, `nft list
tables` sale vacío y v1 sigue `disabled`.

## 2. Bastión: relé v2

`[BASTIÓN gadmin] → lo ejecutas tú (sudo con contraseña)`

```bash
bash ~/cf-e4/paquete/deploy/etapa4/bastion/revertir_bastion.sh ~/respaldos-etapa4/bastion-20261104T015600Z
```

Para y deshabilita `ppi-relay-eventos` y restaura las unidades. El relé v1 no se toca: estaba antes de la 4A y sigue
igual.

## 3. Sensor1: detector

`[SENSOR1 m4rk] → lo ejecutas tú (sudo con contraseña)`

```bash
bash ~/cf-e4/paquete/deploy/etapa4/sensor1/revertir_sensor1.sh ~/respaldos-etapa4/sensor1-20261104T021028Z
```

**Qué hace:**
- quita los drop-ins `etapa4.conf` del motor y de la captura;
- para y deshabilita `ppi-publicar-feed-v2`, `ppi-via-rapida@ens37` y `cf-tcpdump-estadisticas.timer`;
- retira el logrotate de la 4A y la llave de servicio del relé;
- reinicia motor y captura con la base **24f8a80** en `~/cyberflow`.

`~/cyberflow-e4/ec78ca5` y `~/feed-v2` se **conservan** como evidencia.

**Comprobación:**
- `/proc/<pid motor>/cmdline` apunta a `~/cyberflow/scripts/engine/motor_decision.py`, sin `--enforce`;
- `( cd ~/cyberflow && sha256sum -c ~/respaldos-etapa4/sensor1-20261104T021028Z/cyberflow-codigo.sha256 )`. Tras la
  reversión del panel (§4) debe dar 0 fallos. Si se revierte Sensor1 sin revertir el panel, solo falla
  `scripts/engine/dashboard.py`.

## 4. Panel (independiente)

`[SENSOR1 m4rk] → lo ejecuto yo (sin sudo para copiar; restart de ppi-dashboard en NOPASSWD)`

```bash
P=~/respaldos-etapa4/panel-20261104T033157Z
( cd $P && sha256sum -c SHA256SUMS ) &&
cp -a $P/dashboard.py ~/cyberflow/scripts/engine/dashboard.py &&
sha256sum ~/cyberflow/scripts/engine/dashboard.py     # a5186d2e… = ca66db5, el panel de la demo
sudo -n systemctl restart ppi-dashboard && systemctl is-active ppi-dashboard
```

`cadena_v2.py` puede quedarse, porque ca66db5 no lo importa. Si se quiere quitar del todo, se mueve a
`~/respaldos-etapa4/` y no se borra.

**Para volver a a27889d:** se copian `dashboard.py` y `cadena_v2.py` de `~/cf-e4/panel-a27889d/` y se reinicia
`ppi-dashboard`. Hashes esperados:
- `dashboard.py`: 16e7f430…db274;
- `cadena_v2.py`: 8dbaa377…24869.

**Alternativa sin cambiar ficheros:** añadir `--sin-cadena-v2` a la unidad. Exige sudo con contraseña para editarla.
Con esa opción, el panel a27889d se comporta como el de la demo.

**No usar `desplegar_panel.py`**: borra los `.bak` más antiguos.

## 5. Después de cualquier reversión

- Se registra en la carpeta de evidencias de la etapa: hora, salida y comprobaciones.
- Los respaldos y las evidencias no se borran.
- La demo **no** queda activa. Reactivarla es una decisión aparte de Mark: cargaría el volcado v1 y reactivaría el
  agente v1, y queda fuera del alcance de esta reversión.
