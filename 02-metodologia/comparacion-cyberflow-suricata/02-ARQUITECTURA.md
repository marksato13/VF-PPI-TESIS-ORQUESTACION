# Arquitectura de comparacion

## Opcion P0 recomendada

```text
Kali 10.10.20.30
        |
        v
pfSense VLAN 20 -> VLAN 30 -> srv-dmz 10.10.30.10
        |
        v
CORE-STACK SPAN
        |
        v
PG-CYBERFLOW-SPAN en ESXi
        |--------------------|
        v                    v
Sensor1                 VM comparadora
CyberFlow               Suricata
10.10.60.11             10.10.60.13
ens37 captura           ens37 captura
```

Las capturas aportadas confirman que ambas segundas tarjetas ya estan conectadas
a `PG-CYBERFLOW-SPAN` en el mismo ESXi `172.17.25.2`. Se reutiliza el destino
fisico `Gi2/0/19`: el vSwitch puede distribuir las tramas a ambas VMs. Falta
verificar la politica efectiva y la recepcion, no crear otro destino fisico.

## Interfaces de la VM comparadora

| Interfaz | Uso | IP | Regla |
|---|---|---|---|
| `ens34` | Gestion SSH | `10.10.60.13/24` | Gateway `10.10.60.1` |
| `ens37` | Captura SPAN | Ninguna | Sin gateway, sin DHCP |

El PG debe permitir recibir tramas destinadas a otras MAC (modo promiscuo) y
conservar las etiquetas 802.1Q. En un vSwitch estandar, VLAN ID `4095` corresponde
a VGT y conserva los tags; no es una VLAN que haya que crear en el CORE-STACK.
En un switch distribuido se comprueba el rango de VLAN de su trunk.

Correccion respecto al plan inicial: `MAC Address Changes` y `Forged Transmits`
no necesitan estar en Accept por el solo hecho de capturar pasivamente. Controlan
cambios de MAC y transmision con MAC de origen distinta. Inspeccionar sus valores
y posibles excepciones por puerto, sin cambiarlos automaticamente.

Las capturas no muestran el VLAN ID, la politica de seguridad, el vSwitch/uplink
ni la MAC de cada adaptador. La MAC observada de `ens37` en el comparador es
`00:0c:29:c8:ad:ec`; contrastarla con el adaptador 2 en ESXi.

## Escenarios

### A. Deteccion, recomendada para P0

Dos receptores observan el mismo espejo. No se crea VLAN ni se pone ningun sensor
inline. Se comparan las alertas, ventanas y timestamps.

### B. Bloqueo, posterior a P0

Requiere una rama de laboratorio o un camino inline independiente. Puede exigir
VLAN nueva, reglas pfSense, puertos trunk, grupo de puertos ESXi y rollback. No se
mezcla con el P0 porque cambia el alcance y el riesgo operativo.

## Estado de la sesion SPAN

La salida actual del CORE-STACK confirma:

```text
Sources:      Gi1/0/23, Gi2/0/23
Destination:  Gi2/0/19
Encapsulation: Replicate
Ingress:      Disabled
```

`Gi2/0/19` es el destino existente y esta en estado de monitorizacion. El host y
PG compartidos ya estan confirmados por las capturas. El estado `line protocol
down (monitoring)` de este puerto es propio de su funcion SPAN.

La salida de `Gi1/0/23` muestra 100 Mb/s y la del destino 1000 Mb/s. Registrar
esa capacidad real al definir las cargas. Los contadores acumulados sin errores
no prueban ausencia de perdida durante un ensayo futuro.

Compartir PG no garantiza por si solo igualdad de captura: medir drops,
duplicados, VLAN y flujos observados en ambos receptores durante un intervalo
comun. Las VMs tambien comparten recursos del hipervisor; misma vCPU/RAM no
equivale a independencia fisica ni a igual tiempo de CPU disponible.

No se debe habilitar ni reutilizar un puerto de acceso como destino sin confirmar
su conexion fisica, el host ESXi receptor y el Port Group asociado.
