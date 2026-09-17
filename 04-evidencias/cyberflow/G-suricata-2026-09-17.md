# Bloque G — Suricata sobre `ens37`

**Ejecutado el 2026-09-17 sobre `cyberflow-sensor` (10.10.60.11).**
Todo lo que figura aquí tiene un comando y su salida detrás.

---

## 1. Precondición que falló, y cómo se resolvió sin tocar pfSense

El sensor **no tiene salida a Internet**. Medido:

```
curl --max-time 10 https://github.com          -> 000, Resolving timed out
curl --max-time 8  http://91.189.91.83         -> 000, Connection timed out
dig @10.10.10.20 / @10.10.10.21 / @10.10.60.1 / @8.8.8.8  -> todos timed out
ping 10.10.60.1                                -> 0% perdida, 0,46 ms
```

El gateway responde, pero **nada atraviesa pfSense**. No es un fallo de DNS: tampoco
pasa el tráfico por IP directa. `resolvectl` muestra que el sensor apunta a `8.8.8.8`
y `1.1.1.1`, servidores externos inalcanzables desde la VLAN 60.

> `03_ESTADO_DEL_SENSOR.md` §3 atribuía este fallo al enrutamiento asimétrico de las
> cuatro patas antiguas y lo daba por resuelto con el diseño de dos interfaces.
> **No lo está.** Hay una sola ruta por defecto y la salida sigue bloqueada. La causa
> es el filtrado de pfSense hacia la VLAN 60, no la configuración del sensor.

**Solución aplicada: túnel SSH temporal, sin cambios en pfSense.** El bastión sí tiene
salida (`archive.ubuntu.com` y `security.ubuntu.com` responden 200). Se reenviaron dos
puertos al sensor **solo mientras duró cada comando**, sin dejar ningún proceso activo:

```bash
ssh -R 18080:archive.ubuntu.com:80 -R 18081:security.ubuntu.com:80 \
    m4rk@10.10.60.11 "sudo apt-get update && sudo apt-get install -y suricata"
```

El espejo de Perú (`pe.archive.ubuntu.com`) **no sirve por túnel**: rechaza la petición
porque la cabecera `Host` pasa a ser `127.0.0.1:18080`. Con `archive.ubuntu.com`
funciona. Las fuentes de `apt` se restauraron al terminar.

## 2. Lo instalado

```
Suricata 7.0.3 RELEASE
Features: NFQ PCAP_SET_BUFF AF_PACKET HAVE_PACKET_FANOUT LIBCAP_NG LIBNET1.1 ...
```

## 3. Cambios de configuración

| Fichero | Cambio | Copia previa |
|---|---|---|
| `/etc/suricata/suricata.yaml` línea 18 | `HOME_NET: "[10.10.0.0/16]"` (era `192.168/16, 10/8, 172.16/12`) | `suricata.yaml.orig-cyberflow` |
| `/etc/suricata/suricata.yaml` línea 615 | `- interface: ens37` (era `eth0`) | ídem |
| `/etc/suricata/suricata.yaml` línea 616 | `checksum-checks: no` (añadida) | ídem |
| `/etc/systemd/system/cyberflow-capture-nic.service` | nueva | no existía |

`checksum-checks: no` porque en tráfico espejado las sumas de verificación vienen
calculadas por la NIC del emisor y llegan inválidas; validarlas descartaría paquetes
buenos.

**No se tocó `/etc/default/suricata`.** Tiene `RUN=no`, `LISTENMODE=nfqueue` e
`IFACE=eth0`, pero la unidad de systemd **no lo lee**: arranca con
`ExecStart=/usr/bin/suricata -D --af-packet -c /etc/suricata/suricata.yaml`. Es un
fichero vestigial; conviene saberlo porque induce a error.

**La sección `pcap:` sigue apuntando a `eth0`** (línea 807). No se usa en modo
`--af-packet`. Se deja como está por el principio de cambio mínimo.

## 4. La unidad que deja la interfaz lista al arranque

`03` §4 dejó `promisc on` puesto a mano, y eso se pierde al reiniciar. Ahora es
persistente:

```ini
[Unit]
Description=CyberFlow: prepara ens37 para captura pasiva
Before=suricata.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/ip link set ens37 up promisc on
ExecStart=-/usr/sbin/ethtool -K ens37 gro off lro off tso off gso off
ExecStart=-/usr/sbin/sysctl -qw net.ipv6.conf.ens37.disable_ipv6=1
ExecStop=-/usr/sbin/ip link set ens37 promisc off
```

Las tres razones, por orden: sin promiscuo la vNIC filtra el espejo · las descargas
GRO/LRO/TSO/GSO recomponen segmentos y **falsearían el tamaño de trama y las tasas** ·
IPv6 desactivado porque una sonda pasiva no debe emitir (`ens37` llevaba 629 paquetes
transmitidos por *neighbor solicitation*).

```
systemctl is-active cyberflow-capture-nic  -> active
promiscuity 1
/proc/sys/net/ipv6/conf/ens37/disable_ipv6 -> 1
```

## 5. Criterio de aceptación — cumplido

```
suricata -T -c /etc/suricata/suricata.yaml -v   -> sin errores
systemctl is-active suricata                    -> active
wc -l /var/log/suricata/eve.json                -> 7  ... 30 s ... 25
```

Tipos de evento: `dns`, `flow`, `stats`.

**Flujos reales de Franco's, con la etiqueta de VLAN en el JSON:**

```
vlan [60]  10.10.60.11  -> 8.8.8.8          TCP
vlan [60]  10.10.60.10  -> 10.10.10.20      TCP
vlan [10]  10.10.10.30  -> 239.255.255.250  UDP
vlan [60]  10.10.60.11  -> 1.1.1.1          UDP  dns
vlan [10]  10.10.10.30  -> 10.10.10.1       UDP
```

**Estadísticas de captura tras 80 s:**

```
kernel_packets : 1559
kernel_drops   : 0
decoder pkts   : 1582
decoder vlan   : 1573
decoder invalid: 0
```

`kernel_drops = 0` y `decoder invalid = 0`. **1573 de 1582 paquetes llevan etiqueta
de VLAN**: la fuente de la feature de distribución de VLAN queda confirmada de punta a
punta, no solo en `tcpdump` sino en el `eve.json` que consumirá el motor.

## 6. Vuelta atrás

```bash
sudo systemctl disable --now suricata
sudo systemctl disable --now cyberflow-capture-nic
sudo rm /etc/systemd/system/cyberflow-capture-nic.service
sudo cp /etc/suricata/suricata.yaml.orig-cyberflow /etc/suricata/suricata.yaml
sudo systemctl daemon-reload
sudo apt-get purge -y suricata          # requiere el tunel solo si se reinstala
```

## 7. Lo que queda abierto

| # | Asunto | Por qué importa |
|---|---|---|
| 1 | **Sin reglas de detección.** `No rule files match /var/lib/suricata/rules/suricata.rules` | Para CyberFlow no hacen falta: consume `flow` y eventos de protocolo, no alertas por firma. **Sí harán falta** para la comparación con Wazuh de `05` §5, que necesita alertas. `suricata-update` requiere el túnel |
| 2 | **Duplicación entre VLAN** | Cada paquete enrutado aparece dos veces, una por VLAN. Infla toda feature de tasa ×2 |
| 3 | **Efecto del observador** | El SSH de gestión y los intentos de DNS del propio sensor se capturan a sí mismos |
| 4 | **El disco no está ampliado** | `sda` = 40 GB, `sda3` = 36,9 GB, pero el volumen lógico son **18,5 GB**. Hay ~18 GB sin usar. `03` §1 dice «40 GB, ampliado»: se amplió el disco virtual, no el volumen |
| 5 | **Salida a Internet** | Sigue bloqueada. Cada actualización necesitará el túnel mientras no se abra en pfSense |
