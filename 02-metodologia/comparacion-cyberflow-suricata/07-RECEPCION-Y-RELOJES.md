# Recepcion SPAN y relojes: diagnostico previo a la comparacion

Fecha de observacion: 2026-10-02 UTC. Lecturas SSH sin privilegios; no se
ejecutaron ataques ni cambios en Sensor1, pfSense o el CORE-STACK.

## Recepcion de la interfaz de captura

Durante una medicion de 10 s en cada maquina:

| Equipo | Estado antes de corregir | RX inicial/final | RX dropped inicial/final |
|---|---|---|---|
| Sensor1 `10.10.60.11` | `ens37` PROMISC, UP | 706135 / 706710 (+575) | 160368 / 160508 (+140) |
| Comparador `10.10.60.13` | `ens37` UP, no PROMISC | 98 / 98 (+0) | 0 / 0 (+0) |

Estas mediciones se hicieron en llamadas independientes; sus intervalos son
proximos, no perfectamente simultaneos. La prueba de Mark con `tcpdump` si
habia recibido trafico en el comparador porque la captura activa PROMISC
temporalmente. Tras salir `tcpdump`, `ip -d link show` indico `promiscuity 0`.

Se preparo `07-activar-promisc.sh` para anadir `Promiscuous=yes` al bloque
`[Link]` del archivo networkd dedicado al comparador, con respaldo y verificacion
de gestion. La opcion esta documentada en el manual local de systemd.network 255.
El script se copio a `/home/adminsuricata/07-activar-promisc.sh` y se verifico
con `bash -n`, pero aun **no se ejecuto con sudo**.

Los descartes de Sensor1 aumentaron en +140 durante los 10 s observados, a la
vez que RX subio +575. No concluir que sea un 24 % de todos los paquetes del
trafico ni que el hardware sea la causa: son contadores de interfaz con
semantica propia. Investigar la tendencia bajo el mismo intervalo y contrastar
con estadisticas de Suricata antes de un resultado de deteccion comparativa.
`ethtool -S ens37` en Sensor1 no mostro errores RX ni caidas contabilizadas
por el driver vmxnet3, por lo que aun falta localizar en que capa crece
`rx_dropped`. Esto no invalida la necesidad de medirlo.

## Sincronizacion

Ambos hosts tienen UTC y `systemd-timesyncd` activo, pero
`System clock synchronized: no`, servidor `n/a (ntp.ubuntu.com)` y
`Packet count: 0`. Lecturas cercanas mostraron una diferencia aproximada de
180 segundos entre Sensor1 y el comparador. El desfase debe medirse de nuevo
en una unica corrida cuando se vaya a comparar tiempos.

pfSense-A y B tienen `ntpd` escuchando en `10.10.60.1:123`; `ntpq -pn` en ambos
mostro una fuente seleccionada (`*`) con reach 377 y offsets de pocos ms.
Sin embargo, las consultas UDP/123 desde **ambos** hosts de VLAN 60 hacia
`10.10.60.1` y `10.10.10.20` agotaron el plazo de 3 s. Que exista el servicio
NTP no demuestra que la politica pfSense permita acceder desde VLAN 60. No se
ha cambiado ninguna regla. `08-probar-ntp.py` solo consulta NTP; no cambia
el reloj ni instala paquetes.

El bastion tiene reloj sincronizado por NTP, pero no tiene un servicio UDP/123
escuchando. Su hora puede servir de referencia para diagnostico, no equivale a
una sincronizacion automatica de los sensores.

## Actualizacion tras configurar PROMISC

Mark ejecuto `07-activar-promisc.sh` con sudo en el comparador; el archivo
networkd contiene `Promiscuous=yes`. La NIC quedo `PROMISC,UP,LOWER_UP`, sin
direccion IP. En su primera muestra RX crecio de 1336 a 1784 en 10 s.
Respaldo: `/root/suricata-promisc-backup.2aaK95Ry`. Persistencia tras reinicio
aun no verificada.

Mediciones posteriores en ventanas proximas de 15 s:

| Equipo | RX inicial/final | `rx_dropped` inicial/final |
|---|---|---|
| Sensor1 | 743047 / 744869 (+1822) | 167498 / 167723 (+225) |
| Comparador | 6837 / 8613 (+1776) | 1138 / 1365 (+227) |

La diferencia de 46 paquetes en contadores no mide por si sola perdida de una
solucion frente a otra: las ventanas no fueron exactamente simultaneas y el
trafico propio puede diferir. `rx_dropped` en ambas NIC crece de forma similar,
pero no equivale a `capture.kernel_drops` de Suricata. En la muestra leida de
`/var/log/suricata/stats.log` de Sensor1 aparece `capture.kernel_packets`
creciendo; no se encontro un contador `capture.kernel_drops` en esos bloques.
El driver vmxnet3 tampoco mostro errores ni `drv dropped rx total` en
`ethtool -S ens37`. Falta verificar perdidas a nivel de captura con una
medicion pareja y carga de ensayo.

## Instalacion del comparador

Suricata no esta instalado en `10.10.60.13`. `apt-cache policy` muestra como
candidato `1:7.0.3-1build3`, y Sensor1 ejecuta Suricata `7.0.3 RELEASE`.
El comparador no tiene DNS operativo confirmado ni salida a repositorios; no
intentar una instalacion en red sin verificar disponibilidad. Planificar
instalacion offline con dependencias, fijar reglas y version/sha de configuracion
antes de medir. La version igual no garantiza reglas o modos de captura iguales.

## Gate antes de medir tiempos

1. El comparador debe recibir pasivamente sin dejar `tcpdump` abierto.
2. Medir drops de ambos receptores bajo el mismo intervalo y aclarar sus causas.
3. Establecer una fuente horaria alcanzable y validar sincronizacion/offset de
   ambos hosts y de Kali. Una regla UDP/123 minima desde las IP necesarias a
   un NTP interno es una opcion **por aprobar**, no una configuracion aplicada.
4. Fijar un limite de desfase aceptable compatible con la resolucion de la
   metrica antes de ejecutar ataques. No corregir un desfase de minutos solo
   restando una constante sin medir drift e incertidumbre.
