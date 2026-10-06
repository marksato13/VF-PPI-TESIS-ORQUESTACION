# Estado y decisiones

## 1. Objetivo del experimento

Determinar, bajo los mismos ataques controlados y la misma linea base, como se
comparan CyberFlow y Suricata en tiempo de deteccion, cobertura y falsos positivos.
La afirmacion es de deteccion temprana, no de prediccion completa del ataque.

## 2. Ya realizado

- Se actualizaron las IP vigentes del laboratorio: Kali `10.10.20.30`, clientes
  `10.10.20.20`-`10.10.20.26` y servidor `10.10.30.10`.
- Se creo la VM `suricata-comparator` con Ubuntu 24.04.2.
- La VM tiene `ens34` de gestion en `10.10.60.13/24`.
- El acceso por clave desde el bastion fue verificado:
  `adminsuricata@10.10.60.13`.
- `ens37` existe y esta sin IP, reservado para captura.
- pfSense-A y pfSense-B fueron consultados por SSH en modo lectura.
- pfSense tiene VLAN 20 (`10.10.20.0/24`), VLAN 30 (`10.10.30.0/24`) y VLAN 60
  (`10.10.60.0/24`) activas.
- El CORE-STACK confirma una sesion SPAN local con origen en `Gi1/0/23` y
  `Gi2/0/23`, destino actual `Gi2/0/19`, encapsulacion `Replicate` e ingress
  deshabilitado.
- `Gi2/0/19` esta en estado de monitorizacion y ha transmitido `623076` paquetes;
  es el destino SPAN existente, no un puerto de acceso normal.
- La sesion incluye ambos puertos origen en sentido `Both`. La salida detallada
  aportada de `Gi1/0/23` confirma enlace a 100 Mb/s; falta la salida equivalente
  de `Gi2/0/23` para afirmar su estado fisico actual.
- Las capturas ESXi aportadas muestran Sensor1 (`MOTOR DE PEPA`), Sensor2
  (`MOTOR DE PEPA V2`) y el comparador (`VM-SURICATA`) en `172.17.25.2`.
- En Sensor1 y el comparador, adaptador 1 = `VLAN60 (Connected)` y adaptador 2 =
  `PG-CYBERFLOW-SPAN (Connected)`. Ambos muestran 4 vCPU, 8 GB de RAM y disco
  virtual de 40 GB.
- La comprobacion SSH de esta sesion confirma en el comparador: `ens34` UP con
  `10.10.60.13/24`; `ens37` administrativamente DOWN, sin IP, RX/TX = 0 y MAC
  `00:0c:29:c8:ad:ec`. `tcpdump` esta disponible; `suricata` no aparece en PATH.
  Detalle y limites de esta comprobacion en `05-VERIFICACION-SPAN-ESXI.md`.

## 3. Estado de los componentes

| Componente | Estado |
|---|---|
| CyberFlow en Sensor1 | Activo, modo observacion |
| Suricata en Sensor1 | Activo y usado por la telemetria de CyberFlow |
| Sensor2 | Activo como replica |
| VM comparadora | Suricata 7.0.3 instalado, ET Open y YAML aplicados y validados con `-T`; servicio disabled/inactive |
| Interfaz de captura de VM comparadora | Configuracion aplicada: `ens37` UP/LOWER_UP sin IPv4 ni IPv6; RX 98 paquetes al verificar, gestion intacta; reinicio no ensayado |
| Segundo destino SPAN | No requerido para la topologia mostrada; se reutiliza `Gi2/0/19` y el PG compartido |
| VLAN/promiscuo efectivos del PG | Pendientes de inspeccion; no aparecen en las capturas |
| Equivalencia de captura | Pendiente de verificar con trafico y contadores de ambos receptores |
| Recepcion pasiva continua | PROMISC aplicado en comparador; RX crece sin tcpdump; equivalencia de PCAP aun pendiente |
| Sincronizacion de relojes | Ambos sin NTP sincronizado; ~180 s de desfase; ver nota 07 |
| Descartes de interfaz | `rx_dropped` crece en ambos receptores; no equiparar automaticamente con drops de Suricata |
| Nueva VLAN | No aprobada ni necesaria para P0 |
| Bloqueo `nftables` | No se activa para este experimento |

Actualizacion posterior a la consulta SSH: Mark ejecuto la prueba pasiva propuesta.
Se capturaron 20 paquetes con etiquetas VLAN 10, 60 y 100; tcpdump informo 76
paquetes recibidos por filtro y 0 descartados por kernel. Queda confirmada la
recepcion inicial del espejo en el comparador. No se verificaron aun VLAN 20/30
ni igualdad de entrada con Sensor1. Hay repeticiones aparentes de trafico de
sincronizacion y observacion del mismo flujo SSH antes/despues del enrutamiento;
cuantificar ambas antes de definir el tratamiento comun para el experimento.

Mark ejecuto despues `06-configurar-captura.sh` con sudo. Se comprobaron por
SSH los archivos creados, el estado networkd de `ens37`, IPv6 deshabilitada
solo en esa interfaz, y `ens34` y ruta por defecto conservadas. El respaldo
quedo en `/root/suricata-capture-backup.AjYbubPy`. Ver
`06-PREPARACION-CAPTURA.md`. Persistencia tras reinicio aun no comprobada.

Diagnostico adicional en `07-RECEPCION-Y-RELOJES.md`: la interfaz del
comparador necesita modo promiscuo persistente para recibir SPAN sin tener
`tcpdump` abierto, y los relojes de ambos hosts aun no permiten comparar
tiempos de deteccion.

Tras la aplicacion de PROMISC y una nueva muestra de 15 s, RX crece en ambos
receptores (Sensor1 +1822, comparador +1776); ver la actualizacion de la nota
07. Mark transfirio el bundle offline y ejecuto la instalacion en el comparador;
servicio detenido por diseno (`09-INSTALACION-SURICATA.md`). En Sensor1 el archivo
de reglas cargado esta vacio; se preparo una instantanea ET Open para el
comparador, recibida y validada en modo prueba (`12-REGLAS-ET-OPEN.md`).

Mark aplico la configuracion definitiva en la VM comparadora. Respaldo en
`/root/suricata-compare-backup.NnRaLU8Z`; version, hashes, modo pasivo y estado
disabled/inactive comprobados por SSH. En ese momento aun no se habia ejecutado
el servicio con trafico ni se habia corrido el experimento con Kali.

Actualizacion: Mark ejecuto el piloto IDS pasivo de 75 s; EVE registro 3 eventos
stats y 10 HTTP de VLAN 10, sin alertas ni JSON invalido. Suricata capturo
paquetes, cargo 53013 reglas y quedo inactive/disabled. No hubo ataque ni
medicion comparativa. Ver `16-PILOTO-PASIVO-20261002.md` y
`17-NTP-PROPUESTA.md`.

## 4. Decisiones vigentes

1. No crear otra VLAN para el P0.
2. Mantener la gestion de la VM comparadora en VLAN 60.
3. Mantener la interfaz de captura separada, sin IP ni gateway.
4. Comparar primero deteccion; el bloqueo inline queda para una fase posterior.
5. No editar pfSense ni CORE-STACK sin un plan aprobado, respaldo y rollback.
6. Reutilizar `PG-CYBERFLOW-SPAN` en el mismo host. Un puerto destino SPAN no
   corresponde necesariamente a una sola VM: el vSwitch puede distribuir las
   copias a varios receptores con la politica de recepcion adecuada.
7. `Connected` en ESXi y `UP` en Ubuntu son estados distintos. La segunda tarjeta
   ya esta conectada en ESXi; su estado DOWN no demuestra falta de cable o PG.

## 5. Resultados de CyberFlow que sirven como referencia

- FPR recalibrado sobre trafico normal retenido: `4,45 %`.
- TPR de la corrida real de Kali: `69 %` global.
- Ataques HTTP: `100 %` de deteccion en la corrida documentada.
- Latencia de bloqueo previa en F6: mediana aproximada de `8 s`.
- Duracion configurada del bloqueo: `120 s`.

Estas cifras no se mezclan: cada resultado debe conservar su dataset, escenario,
modelo, umbral y modo de operacion.
