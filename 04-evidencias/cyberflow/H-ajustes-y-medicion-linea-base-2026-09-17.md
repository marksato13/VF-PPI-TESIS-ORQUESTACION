# Ajustes del sensor y primera medición de la línea base

**2026-09-17.** Continuación de `G-suricata-2026-09-17.md`.

---

## 1. Disco ampliado

`03_ESTADO_DEL_SENSOR.md` §1 decía «40 GB (antes 19 GB, ampliado)». Se amplió el disco
virtual, **no el volumen lógico**: `sda` 40 GB, `sda3` 36,9 GB, LV 18,5 GB.

```
antes:  /dev/mapper/ubuntu--vg-ubuntu--lv   19G  6,5G   11G  38% /
        vg_free  18,47g

sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
  Size changed from 18,47 GiB (4729 extents) to <36,95 GiB (9458 extents).
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
  The filesystem is now 9684992 (4k) blocks long.

despues: /dev/mapper/ubuntu--vg-ubuntu--lv   37G  6,5G   29G  19% /
```

## 2. Tope de registros

El `logrotate` del paquete traía `rotate 14` y `compress`, pero **ni frecuencia ni
límite de tamaño**: heredaba la rotación semanal de `/etc/logrotate.conf` y nada
impedía que una ráfaga de captura llenara la raíz entre dos rotaciones. Un `/` lleno
tumba la máquina, incluido el SSH de gestión.

Añadido: `daily`, `maxsize 500M`, `rotate 7`, `notifempty`, `delaycompress`.
Copia previa en `/etc/logrotate.d/suricata.orig-cyberflow`. Validado con
`logrotate -d`: sin errores.

## 3. DNS del sensor silenciado

```
sudo resolvectl dns ens34 ""
resolvectl status ens34  ->  Current Scopes: none
getent hosts archive.ubuntu.com  ->  ya no intenta resolver
```

**Es un cambio en caliente: se pierde al reiniciar.** Persistirlo requiere editar
netplan — ver §6.

## 4. Dos defectos encontrados en `/etc/netplan/50-cloud-init.yaml`

```yaml
    ens37:
      dhcp4: true      # <- la interfaz de CAPTURA pide DHCP en cada arranque
    ens38:
      dhcp4: true      # <- esta interfaz NO EXISTE en la maquina
```

`03` §2 documenta `ens37` como «sin IP». La configuración dice lo contrario: pide DHCP
y por tanto **emite**, que es lo que una sonda pasiva no debe hacer. Y `ens38` es un
resto del diseño de cuatro patas que retrasa el arranque esperando una interfaz
fantasma.

**No aplicado.** Reescribir la red de una máquina remota puede dejarla incomunicada.
Pendiente de Mark — ver §6.

## 5. Medición de la línea base — 95 s de captura, 1647 paquetes

### 5.1 Qué se está observando de verdad

| Tipo | Paquetes | % |
|---|---|---|
| STP / PVST+ (`01:00:0c:cc:cc:cd`) | 470 | 29 % |
| VRRP / CARP (`01:00:5e:00:00:12`) | 441 | 27 % |
| pfsync y otros sin puertos (VLAN 100) | ~511 | 31 % |
| **Unicast IP con puertos** | **211** | **13 %** |

**El 87 % de lo que ve el sensor es plano de control de los switches y del
cortafuegos.** El tráfico real, el que las 27 features pretenden medir, son 211
paquetes en 95 segundos — poco más de 2 por segundo. Y una parte es nuestro propio SSH
de gestión y NTP entre `10.10.40.10` y `10.10.10.20`.

### 5.2 Reparto por VLAN

```
vlan 100  529     vlan 10   266     vlan 60   159     vlan 40   104
vlan 90    96     vlan 30    96     vlan 20    96     vlan 70    96
vlan 99    96     vlan 50    96     sin etiqueta 11   vlan 1      2
```

Las VLAN 20, 30, 50, 70, 90 y 99 tienen **exactamente 96 paquetes cada una**: es un
BPDU por VLAN, no tráfico. Confirma `02_INFRAESTRUCTURA.md` §4.1 — las VLAN de usuarios
están vacías — y lo agrava: no es que haya poco tráfico, es que **no hay ninguno**.

### 5.3 Duplicación entre VLAN — mucho menor de lo previsto

```
paquetes unicast IP        : 211
claves distintas           : 105
claves vistas en >1 VLAN   : 5
tasa de duplicacion        : 4,8 %
```

Ejemplos confirmados:
```
10.10.60.11:22  -> 10.10.10.30:53694   visto en vlan [10, 60]
10.10.40.10     -> 10.10.10.20:123     visto en vlan [10, 40]
```

**La duplicación existe y es real, pero afecta al 4,8 % de las claves, no al 100 %.**
La clave usada —`(ip_orig, puerto, ip_dst, puerto, seq, longitud)`— es imperfecta:
colapsa paquetes UDP sin número de secuencia. **La cifra es indicativa, no definitiva.**

## 6. Lo que queda pendiente de Mark

| # | Asunto | Por qué no lo hice |
|---|---|---|
| 1 | **netplan**: quitar `nameservers`, `ens37: dhcp4: false`, borrar `ens38` | Reescribir la red de una máquina remota puede dejarla sin acceso |
| 2 | Regla pfSense `10.10.60.11 → 10.10.10.20:53` | Infraestructura de Franco's |
| 3 | Cambiar el espejo a `tx` | Infraestructura de Franco's — **y la medición dice que ya no es prioritario** |
| 4 | **Generar tráfico** | Es una decisión de alcance, no técnica |

## 7. Un dato que contradice el traspaso

`02_INFRAESTRUCTURA.md` §5 dice que **pfSense-B no responde a nada**. En la captura,
la MAC `00:0c:29:b2:5f:32` —el extremo de `10.10.100.3` en la VLAN de sincronización—
**emite 200 paquetes** y recibe 281.

A nivel de enlace **pfSense-B está vivo y hablando por la VLAN 100**. Puede seguir sin
responder a sondeos IP desde la VLAN 10, que es como se midió entonces; las dos cosas
son compatibles. Pero «no responde a nada» ya no es exacto y conviene rehacer esa
medición desde la VLAN 100.
