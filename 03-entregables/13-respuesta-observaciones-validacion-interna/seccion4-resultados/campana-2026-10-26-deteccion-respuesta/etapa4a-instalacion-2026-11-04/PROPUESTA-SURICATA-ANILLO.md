# Propuesta: anillo af-packet de Suricata en ens37 (PREPARADA, NO EJECUTADA)

> **Estado: no aplicada.** Requiere la decisión de Mark, sudo en Sensor1 y reiniciar Suricata. Nada de este documento
> se ejecutó el 04-nov. Diagnóstico de partida: [README §8](README.md#8-descartes-de-suricata-diagnóstico).

## 1. Problema

Suricata descarta paquetes en ráfagas cortas:
- 7 descartes en la ventana de observación (03:05:47);
- 164 a las 01:42:11 y 198 a las 02:08:27 del 04-nov;
- 58 423 el 03-nov, en horas de campaña y demo.

La NIC y los dos tcpdump sobre la misma interfaz no pierden nada (0 descartes del kernel, `rx_missed 0`). La CPU, el
disco y la rotación están descartados como causa.

Para la 4C, un descarte de Suricata saca el periodo de C0 y hace fallar I5. Con los perfiles de descarga actuales,
I5 puede impedir el arranque de la 4C en cualquier momento.

## 2. Hipótesis (no demostrada)

`cluster_type: cluster_flow` envía cada flujo entero a un solo worker. El anillo por defecto de ese worker es
pequeño: `ring-size` sin fijar. Una descarga HTTP grande (2 469 paquetes de 10.10.20.26 en el intervalo de 03:05:47)
llena el anillo de ese hilo aunque la media del enlace sea baja (p50 212 pps) y la CPU esté libre.

Lo que sería coherente con la hipótesis: descartes concentrados en un worker, en los intervalos con flujos grandes.
No se pudo comprobar por hilo, porque `stats.log` no se lee por worker en la configuración actual.

## 3. Cambio propuesto (mínimo)

Fichero `/etc/suricata/suricata.yaml`, bloque `af-packet:` de `interface: ens37`. Solo se añade una línea:

```yaml
af-packet:
  - interface: ens37
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    ring-size: 16384        # NUEVO (4A-propuesta): anillo por worker; por defecto es mucho menor
```

Opcional, en un **segundo paso separado** (solo si el primero no basta): `ethtool -G ens37 rx 4096`. El anillo RX de
vmxnet3 está en 1024 de un máximo de 4096. Este cambio no persiste al reiniciar sin una unidad o un udev.

Lo que **no** se toca: `threads`, `cluster_type`, las reglas (no hay; solo EVE), `max-pending-packets`, el modelo, el
motor, la captura del motor y la vía rápida.

Coste de memoria estimado: unas decenas de MB por worker (4 workers). El host tiene 6,8 GB libres.

## 4. Procedimiento

### 4.1 Respaldo

`[SENSOR1 m4rk] → lo ejecutas tú (sudo con contraseña)`

```bash
R=~/respaldos-etapa4/suricata-$(date -u +%Y%m%dT%H%M%SZ); mkdir -p $R
sudo cp -a /etc/suricata/suricata.yaml $R/
sudo tail -c 200000 /var/log/suricata/stats.log > $R/stats-antes.log
sudo chown -R m4rk: $R && (cd $R && sha256sum * > SHA256SUMS && sha256sum -c SHA256SUMS)
```

### 4.2 Cambio y prueba de sintaxis

`[SENSOR1 m4rk] → lo ejecutas tú (sudo con contraseña)`

```bash
sudoedit /etc/suricata/suricata.yaml          # añadir solo la línea ring-size bajo interface: ens37
sudo diff $R/suricata.yaml /etc/suricata/suricata.yaml   # debe mostrar UNA línea añadida
sudo suricata -T -c /etc/suricata/suricata.yaml -v 2>&1 | tail -5   # "Configuration provided was successfully loaded"
```

Si `-T` falla, se restaura el YAML (§5) y no se reinicia.

### 4.3 Aplicación

`[SENSOR1 m4rk] → lo puede ejecutar Claude (restart de suricata está en NOPASSWD)`

```bash
sudo -n systemctl restart suricata && sleep 20 && systemctl is-active suricata
sudo -n journalctl -u suricata --since -2min --no-pager | grep -iE 'ring|af-packet|error|warn' | tail -20
```

**Consecuencias del reinicio:**
- Los contadores acumulados vuelven a cero.
- Queda un hueco de unos segundos en EVE.
- I5 exige 30 min limpios desde el reinicio.
- No afecta al motor, a la captura del motor, a la vía rápida ni al publicador, que son procesos independientes.

### 4.4 Medida (≥ 60 min, mismos perfiles, sin generar tráfico)

Se repite la medida de la 4A:
- muestras de `capture.kernel_packets` y `capture.kernel_drops`;
- volumen HTTP por cliente hacia srv-dmz;
- pps de ens37.

**Comparación:** descartes por cada 10⁶ paquetes, y descartes en los intervalos con un flujo de más de 1 000
paquetes, frente a la línea de la 4A (7 / 937 757 en 60 min, con 3 descargas grandes).

### 4.5 Criterio

| Resultado en ≥ 60 min | Decisión |
|---|---|
| 0 descartes, con al menos el mismo volumen de descargas que la 4A | se mantiene; I5 queda en manos de la carga real |
| Menos descartes, pero no 0 | se mantiene y se valora el paso opcional `ethtool` (de nuevo con respaldo, prueba y medida) |
| Igual o peor, o error en el journal, o Suricata inestable | **reversión** (§5); la hipótesis queda refutada y se investiga por worker |

## 5. Reversión

`[SENSOR1 m4rk] → lo ejecutas tú (sudo con contraseña para el cp)`

```bash
sudo cp -a $R/suricata.yaml /etc/suricata/suricata.yaml
sudo suricata -T -c /etc/suricata/suricata.yaml && sudo systemctl restart suricata && systemctl is-active suricata
```

Si se aplicó el paso opcional: `sudo ethtool -G ens37 rx 1024`.

La reversión no toca nada de la cadena v2 ni de la demo.

## 6. Relación con los criterios congelados

Esta propuesta **no** cambia ningún criterio:
- I5 sigue exigiendo 0 descartes en los 30 min previos;
- durante la ejecución rigen los criterios congelados de pausa, cancelación y clasificación;
- la población principal sigue siendo solo C0.

Solo intenta que la captura de Suricata deje de perder paquetes. Si no se aplica, la 4C sigue siendo posible, pero
cada descarte la retrasa o saca periodos de C0.
