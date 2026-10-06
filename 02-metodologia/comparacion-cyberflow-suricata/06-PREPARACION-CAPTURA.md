# Preparacion de configuracion persistente

Estado: aplicado por Mark en `suricata-comparator` y comprobado posteriormente
por SSH en modo lectura. El comando ejecutado fue:

```bash
sudo bash /home/adminsuricata/06-configurar-captura.sh
```

Comprobaciones previas: systemd-networkd activo, ens37 unmanaged, directorio
`/etc/systemd/network` vacio, gestion `10.10.60.13/24` en ens34 y ruta por defecto
via `10.10.60.1`. Netplan contiene `50-cloud-init.yaml` protegido; no se leyo ni
se modifico su contenido.

Se usa un archivo nativo de systemd-networkd dedicado a la MAC de captura, sin
reescribir Netplan de gestion. Deshabilita DHCP, link-local y anuncios IPv6;
sysctl deshabilita IPv6 solo en ens37. Recarga networkd y reconfigura ens37,
sin ejecutar netplan apply ni reiniciar el servicio de red.

El script respaldo Netplan y los archivos networkd, rechazo host/MAC incorrectos
y archivos de destino preexistentes, y verifica que gestion y ruta por defecto
no cambien. Ante error retira sus archivos; la restauracion completa del estado
runtime debe verificarse en consola. La persistencia tras reboot sigue pendiente
de un reinicio programado, que no se ejecuto automaticamente.

## Resultado aportado por Mark y comprobacion remota posterior

- Se crearon `/etc/systemd/network/10-suricata-capture.network` y
  `/etc/sysctl.d/90-suricata-capture.conf`; `networkctl` confirma que el primer
  archivo gobierna `ens37` y `systemd-networkd` permanece activo.
- `ens37` quedo `UP,LOWER_UP`, sin IPv4 ni IPv6; `IPv6 Address Generation Mode:
  none`; `net.ipv6.conf.ens37.disable_ipv6 = 1`.
- `ens34` conserva `10.10.60.13/24` y la unica ruta por defecto sigue siendo
  `via 10.10.60.1 dev ens34`.
- Al terminar, la interfaz mostro RX 98 paquetes / 16072 bytes, sin errores ni
  descartes de interfaz. TX 12 paquetes / 936 bytes son contadores acumulados:
  no prueban que haya transmitido despues de aplicar la configuracion. Si la
  pasividad estricta es criterio experimental, medir el delta TX en una ventana.
- Respaldo creado: `/root/suricata-capture-backup.AjYbubPy`.

El archivo y la opcion sysctl sobreviven como configuracion en disco; la prueba
de que la interfaz vuelve a subir sin IP tras reboot queda **sin verificar**.

Archivo remoto: `/home/adminsuricata/06-configurar-captura.sh`.
Copia de transferencia: `/home/gadmin/06-configurar-captura.sh` en el bastion.
Validacion remota `bash -n`: correcta.
SHA-256 remoto: `8aa9828b9aa431292a25d0f1bdfa649766547a42a0661bf14220f2d2a67c9d55`.
