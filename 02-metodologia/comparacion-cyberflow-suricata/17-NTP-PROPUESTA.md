# Propuesta de sincronizacion horaria para el experimento

**Solo propuesta; no aplicar en pfSense ni en Sensor1 sin aprobacion expresa de
Mark.** Los cambios de hora de un sensor con servicios activos pueden alterar
logs, timers y ventanas temporales del modelo.

## Evidencia

- Sensor1 `10.10.60.11` y comparador `10.10.60.13` usan UTC,
  `systemd-timesyncd` activo pero indican `NTPSynchronized=no`, servidor
  `n/a (ntp.ubuntu.com)` y contador de paquetes NTP cero.
- Una consulta de prueba sin privilegios a `10.10.60.1:123` desde ambas VMs
  agoto 3 s. Tambien expiraron `10.10.10.20:123`, y desde el comparador
  `10.10.60.2:123` y `10.10.60.3:123`.
- pfSense-A y B tienen ntpd escuchando en interfaz VLAN60. `ntpq -pn` mostro
  upstream seleccionado, pero las reglas leidas de VLAN60 permiten ICMP, SNMP y
  algunos puertos Wazuh; no se observo un PASS UDP/123 para estos hosts.
- El bastion esta sincronizado pero no escucha en UDP/123; no es una fuente NTP
  disponible automaticamente para las VMs.
- Verificacion por SSH de los otros participantes: Kali `10.10.20.30`
  (`adminatacante`), `clientesadmin` `10.10.20.20` (`adminclientes`) y
  `srv-dmz` `10.10.30.10` (`adminsrvdmz`) indican `NTPSynchronized=yes`.
  Kali usa zona `America/Lima` y fuente NTP publica con offset -15.336 ms;
  cliente y servidor usan UTC, con offsets +511 us y +359 us, respectivamente,
  en la lectura realizada. La zona horaria no equivale a desfase de reloj.

## Cambio minimo a evaluar

En el par pfSense HA, una regla PASS **de entrada en VLAN60**, solo UDP, origen
`10.10.60.11` y `10.10.60.13` (hosts, no toda la VLAN), destino VIP CARP
`10.10.60.1`, puerto destino `123`, registro habilitado. Confirmar primero
orden respecto de reglas de bloqueo y comportamiento de sincronizacion HA.
Respaldar configuracion y registrar regla/ID para revertir exactamente. Esta
regla no da Internet ni acceso general entre VLANs.

Tras autorizarla: probar respuestas NTP de la VIP con `08-probar-ntp.py` en
ambos hosts; solo si responde y la fuente esta sincronizada, configurar drop-in
de `systemd-timesyncd` con `NTP=10.10.60.1`, probar `timedatectl timesync-status`
y medir offset estable durante la campaña. La correccion de Sensor1 debe
planificarse con sus servicios/experimento para evitar salto de ~3 min en sus
logs. El comparador inactivo puede configurarse primero.

Antes de medir `t_inicio_ataque`, repetir la comprobacion de Kali y, si se usa
para eventos de respuesta, del servidor DMZ el dia de la campaña. Ya estaban
sincronizados al auditar; el bloqueo actual es el par de VLAN 60. La metrica
temporal solo se habilita cuando todos los relojes relevantes tienen fuente y
offset medidos. El umbral admisible debe definirse junto con la resolucion
esperada de la latencia.
