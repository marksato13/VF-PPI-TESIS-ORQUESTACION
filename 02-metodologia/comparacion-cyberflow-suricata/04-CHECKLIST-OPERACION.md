# Checklist operativo

## Antes de tocar infraestructura

- [ ] Aprobar el plan P0.
- [ ] Respaldar configuracion de pfSense si se necesitara cambiarla.
- [x] Confirmar la sesion SPAN en la salida aportada del CORE-STACK: dos fuentes, destino `Gi2/0/19`.
- [x] Confirmar mismo host y PG de captura en ambas VMs mediante capturas ESXi.
- [ ] Verificar VLAN ID, promiscuo efectivos y uplink de `PG-CYBERFLOW-SPAN`.
- [ ] Contrastar MAC `00:0c:29:c8:ad:ec` con el adaptador 2 del comparador.
- [ ] Confirmar que `10.10.60.13` no esta duplicada.
- [ ] Confirmar que no existe DHCP sobre la IP estatica.

## Antes del piloto

- [ ] `ens34` tiene solo gestion.
- [x] `ens37` sin IPv4 ni IPv6 tras configurar `systemd-networkd` y deshabilitar IPv6 solo en captura.
- [ ] Verificar persistencia tras un reinicio programado de la VM comparadora.
- [x] Mark levanto `ens37`; salida confirma UP/LOWER_UP.
- [x] `tcpdump` ve trafico en `ens37` (20 paquetes en la prueba aportada).
- [x] Se observan etiquetas VLAN 10, 60 y 100.
- [ ] Verificar visibilidad del trafico de prueba VLAN 20/30.
- [ ] Comparar recepcion, duplicados y drops de ambos receptores en un intervalo comun.
- [x] Mantener PROMISC en `ens37` del comparador sin `tcpdump`; ejecutado por Mark y RX creciente.
- [ ] Investigar incremento de `rx_dropped` en Sensor1 y drops de Suricata.
- [x] `suricata -T` termina correctamente en directorio de prueba, 53013 reglas y 0 fallidas.
- [x] Aplicar archivos definitivos con respaldo y repetir `suricata -T` antes de iniciar servicio.
- [x] Ejecutar piloto pasivo 75 s con parada automatica; EVE y stats revisados.
- [x] Verificar `suricata.service` inactive/disabled tras el piloto.
- [ ] CyberFlow esta en observacion.
- [ ] Relojes sincronizados: ambos indican `NTPSynchronized=no`, con ~180 s de diferencia.
- [ ] Versiones y hashes registrados.
- [ ] No hay campana de Kali activa.

## Durante la ejecucion

- [ ] Registrar `episode_id`.
- [ ] Registrar hora exacta de inicio y fin.
- [ ] No cambiar reglas, modelo ni configuracion.
- [ ] Guardar logs y PCAP sin sobrescribir.
- [ ] Registrar drops y recursos.

## Cierre

- [ ] Apagar la Kali si corresponde.
- [ ] Verificar que Sensor1 sigue sano.
- [ ] Hash de todos los artefactos.
- [ ] Analisis reproducible desde scripts.
- [ ] Documentar limitaciones y resultados negativos.
- [ ] No dejar reglas temporales ni cambios de firewall sin registrar.
