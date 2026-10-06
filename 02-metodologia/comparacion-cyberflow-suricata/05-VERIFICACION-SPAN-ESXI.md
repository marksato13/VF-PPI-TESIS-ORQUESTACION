# Verificacion del camino SPAN compartido

Fecha de registro: 2026-10-01. Fuentes: tres capturas ESXi aportadas por Mark,
salidas del CORE-STACK pegadas en la conversacion y consulta SSH de solo lectura.
Las imagenes son la fuente visual; no se ha exportado la configuracion de ESXi.

## 1. Confirmado por las capturas

| Dato | Sensor1 | Comparador |
|---|---|---|
| Host ESXi | `172.17.25.2` | `172.17.25.2` |
| Nombre de VM | `MOTOR DE PEPA` | `VM-SURICATA` |
| Hostname | `cyberflow-sensor` | `suricata-comparator` |
| IP de gestion | `10.10.60.11` | `10.10.60.13` |
| Adaptador 1 | `VLAN60 (Connected)` | `VLAN60 (Connected)` |
| Adaptador 2 | `PG-CYBERFLOW-SPAN (Connected)` | `PG-CYBERFLOW-SPAN (Connected)` |
| Recursos configurados | 4 vCPU, 8 GB RAM, 40 GB disco virtual | 4 vCPU, 8 GB RAM, 40 GB disco virtual |

Sensor2 (`MOTOR DE PEPA V2`, hostname `cyberflow-sensor2`) tambien figura en el
inventario del mismo host. La compatibilidad de VM mostrada como ESXi 8.0 U2 no
confirma por si sola la version exacta del hipervisor.

## 2. Comprobacion SSH ejecutada

Ruta: Windows -> `gadmin@10.10.10.30` -> `adminsuricata@10.10.60.13`, con
autenticacion por clave y comprobacion estricta de host conocido.

Comandos de consulta en el comparador:

```bash
hostname
id -un
ip -br addr
ip -s link show dev ens37
command -v tcpdump
command -v suricata
```

Resultados relevantes:

```text
hostname: suricata-comparator
usuario: adminsuricata
ens34: UP, 10.10.60.13/24
ens37: DOWN, sin IP, flags BROADCAST,MULTICAST (sin UP)
ens37 MAC: 00:0c:29:c8:ad:ec
ens37 RX/TX: 0 paquetes, 0 bytes
tcpdump: /usr/bin/tcpdump
suricata: no encontrado en PATH
```

`ens37` esta administrativamente apagada dentro de Ubuntu. Esto no contradice
`Connected` en ESXi ni demuestra un fallo del SPAN. Cero paquetes con la interfaz
apagada no permite evaluar si llegan copias al adaptador virtual.

## 3. Conclusion y comprobaciones pendientes

La asociacion virtual necesaria ya existe. El diseno reutiliza `Gi2/0/19` y
`PG-CYBERFLOW-SPAN`, sin requerir un segundo puerto destino fisico. La recepcion
efectiva sigue pendiente de comprobar.

En ESXi falta inspeccionar:

- Tipo de vSwitch y uplink fisico que alimenta el PG.
- VLAN ID `4095` si es vSwitch estandar, o trunk de VLAN si es distribuido.
- Modo promiscuo efectivo y posibles excepciones por puerto.
- MAC del adaptador 2, que debe corresponder a `00:0c:29:c8:ad:ec`.
- Estado de conexion al encender la VM; la captura solo confirma conexion actual.

Para recepcion pasiva no es obligatorio habilitar MAC Address Changes ni Forged
Transmits. No cambiar esos permisos como paso automatico del experimento.

## 4. Siguiente prueba propuesta, aun no ejecutada

En una terminal de `adminsuricata@suricata-comparator`, despues de confirmar la
MAC de captura:

```bash
sudo ip link set dev ens37 up
ip -br addr show dev ens37
sudo timeout 15 tcpdump -i ens37 -nn -e -c 20
ip -s link show dev ens37
```

La activacion es temporal; no configura una IPv4 estatica ni hace persistente el
estado. Verificar despues si Ubuntu genera una direccion IPv6 link-local o aplica
alguna configuracion automatica: el receptor final debe quedar sin IP.
`tcpdump` solicita modo promiscuo durante la captura; el PG debe permitirlo.
La prueba muestra cabeceras, sin volcar payload ni crear un PCAP. Si el limite de
15 s se alcanza antes de 20 paquetes, evaluar lo recibido y los contadores; el
codigo de timeout por si solo no prueba un fallo.

Criterio inicial: interfaz UP, sin direcciones IP, RX creciendo y trafico de
otras MAC/VLAN esperado en el espejo. Ver algunos paquetes solo prueba recepcion;
la equivalencia de entrada requiere una medicion simultanea con Sensor1 y control
de drops/duplicados antes de la campana formal.

Si hay que deshacer esta prueba y la interfaz estaba DOWN al inicio:

```bash
sudo ip link set dev ens37 down
```

No se ejecutaron cambios de interfaz, instalaciones, capturas ni pruebas de ataque
durante la comprobacion registrada en esta nota.

## 5. Actualizacion: prueba ejecutada por Mark

La salida aportada posteriormente muestra hora de captura `00:32:11` (sin fecha
ni zona horaria en tcpdump; no se infieren). Se ejecuto la activacion temporal y
la captura propuesta, con estos resultados:

- `ens37`: UP/LOWER_UP, MAC `00:0c:29:c8:ad:ec`.
- IPv6 link-local generada: `fe80::20c:29ff:fec8:adec/64`; no se muestra IPv4.
- tcpdump: 20 paquetes capturados, 76 recibidos por filtro, 0 descartados por kernel.
- Contador de interfaz al terminar: RX 96 paquetes / 15952 bytes; TX 1 paquete /
  90 bytes; errores y descartes mostrados en cero.
- Etiquetas preservadas: VLAN 10, 60 y 100. No hay VLAN 20/30 en esta muestra.
- Se recibe trafico entre otras MAC: camino SPAN hacia el comparador confirmado.

Los contadores de tcpdump y de interfaz tienen alcances distintos; 20 capturados
frente a 76 recibidos por filtro no demuestra perdida. Cero drops en esta muestra
breve tampoco demuestra ausencia de perdida bajo carga ni en el switch/hipervisor.

Se observan paquetes de protocolo IP 240 compatibles con pfsync, aparentemente
repetidos varias veces con microsegundos de separacion. Sin PCAP completo no se
afirma identidad byte a byte ni causa unica. Ademas, el mismo flujo SSH aparece
en VLAN 10 y 60 con cabeceras Ethernet distintas, consistente con observacion
antes/despues del enrutamiento. No confundir estas copias con nuevos eventos o
retransmisiones TCP sin verificarlas.

Siguiente trabajo: configurar captura persistente sin DHCP/IPv6 link-local solo
en `ens37`, verificar VLAN 20/30 y comparar entradas simultaneas con Sensor1.
Definir tratamiento equivalente de gestion, control y duplicados para ambos
detectores antes de medir paquetes/s o deteccion. No se ha aplicado esa
configuracion persistente ni modificado la captura del Sensor1.

### Referencias

- [Broadcom: configuracion de VLAN en vSphere 8](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/vsphere-networking/isolate-network-traffic-by-using-vlans/vlan-configuration.html): VGT conserva etiquetas; `4095` corresponde al vSwitch estandar.
- [Broadcom: modo promiscuo en vSwitch estandar](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/vsphere-security/securing-vsphere-networking/securing-vsphere-standard-switches/promiscuous-mode-operation.html): recepcion de tramas destinadas a otras MAC.
