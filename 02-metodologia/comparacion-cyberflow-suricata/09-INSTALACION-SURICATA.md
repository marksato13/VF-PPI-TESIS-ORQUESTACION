# Preparacion de Suricata comparador: paquete offline

Estado: bundle transferido directamente por Mark mediante Tailscale al
comparador, SHA-256 verificado, 70 `.deb` extraidos y repositorio local
simulado. **Suricata todavia no esta instalado.** Sensor1 y Sensor2 no se
modificaron.

## Versiones y procedencia

- Sensor1: Suricata `7.0.3 RELEASE` activo.
- Comparador Ubuntu 24.04 x86_64: `apt-cache policy` ofrece
  `1:7.0.3-1build3`; Suricata no esta instalado.
- Un contenedor `ubuntu:24.04` con repositorios Ubuntu descargo Suricata
  `1:7.0.3-1build3`, `suricata-update` y dependencias mediante
  `apt-get install --download-only --no-install-recommends`. El comparador no
  tuvo acceso a Internet para esta preparacion.
- Bundle en el portatil:
  `C:\Users\markp\AppData\Local\Temp\opencode\suricata-offline-20261002.tar.gz`.
- SHA-256 del bundle:
  `4841dbd20a9c0b797095e40c593f7fd74e55639587ad1b77544c92f2b340187c`.
- Copia integra en el bastion:
  `/home/gadmin/suricata-offline-20261002.tar.gz`, con el mismo hash.

La instalacion local no se debe iniciar solo por tener la misma version: falta
comparar reglas, modos de captura, HOME_NET y configuracion de EVE. Antes de
instalar, revisar paquetes con `dpkg-deb -I`, version y dependencias; hacer
simulacion offline de apt/dpkg en la VM. No instalar indiscriminadamente todos
los `.deb`: el bundle incluye actualizaciones de paquetes base del contenedor.

## Problema de transporte y ruta disponible

La transferencia de muchos `.deb` desde Sensor2 al bastion se estanco y se
retiro la copia parcial. La transferencia del bundle del bastion al comparador
quedo en cero bytes y tambien se detuvo; se retiro el archivo incompleto.
Estas pruebas no demuestran una causa unica; no atribuirlo a MTU sin evidencia.
Un ping con DF y 1400 bytes de payload respondio por el camino bastion ->
comparador. Ningun proceso de copia iniciado en esas pruebas debe quedar activo.

Desde el portatil, `Test-NetConnection 10.10.60.13 -Port 22` dio
`TcpTestSucceeded=True` por Tailscale. La clave del portatil **no** esta
autorizada en la VM y no se agrego. Para transferir sin cambiar la politica de
claves, Mark ejecuto desde su PowerShell con su propia contrasena:

```powershell
scp 'C:\Users\markp\AppData\Local\Temp\opencode\suricata-offline-20261002.tar.gz' adminsuricata@10.10.60.13:/home/adminsuricata/
```

Se valido en la VM (sin privilegios):

```bash
sha256sum /home/adminsuricata/suricata-offline-20261002.tar.gz
tar -tzf /home/adminsuricata/suricata-offline-20261002.tar.gz
```

El SHA-256 coincidio exactamente. Los 70 paquetes quedaron en
`/home/adminsuricata/suricata-debs-20261002/`.

## Simulacion local y proximo paso

`10-simular-apt-offline.sh` creo un indice con `apt-ftparchive`. La fuente APT
usada fue **solo** `file:` dentro del comparador; no se modificaron los
origenes globales. La simulacion quedo en
`/home/adminsuricata/suricata-apt-state-20261002/simulation.txt`.

Resultado: **34 paquetes nuevos, una actualizacion de
`libevent-core-2.1-7t64`, cero eliminaciones**. La version elegida de
Suricata es `1:7.0.3-1build3`. El bundle requiere esa actualizacion de
libevent-core para mantener versiones coherentes de la familia libevent; no
se instalara todo el contenido del bundle indiscriminadamente.

Se preparo `/home/adminsuricata/11-instalar-suricata-offline.sh` (validado con
`bash -n`; SHA-256
`b6f89efc9c657b2670b64122934e498e99a537b79a9c949d23591dbb6052c8ca`).
Antes de instalar vuelve a simular con root y aborta si aparece otra
actualizacion o una eliminacion. Usa solo la fuente local, bloquea el inicio
automatico del servicio durante la instalacion y lo deja deshabilitado hasta
configurar `ens37`, HOME_NET y reglas. Mark debe ejecutarlo con su sudo en la
VM comparadora.

## Instalacion ejecutada y verificada

Mark ejecuto `sudo bash /home/adminsuricata/11-instalar-suricata-offline.sh`.
La nueva simulacion repitio 34 paquetes nuevos, una actualizacion de
`libevent-core-2.1-7t64` y cero eliminaciones. APT indico `0 B` a descargar
desde Internet y uso exclusivamente el repositorio local `file:`. Durante
el postinst se impidio el arranque del servicio; se limpio `policy-rc.d` y
se deshabilito `suricata.service`.

Consulta SSH posterior:

```text
suricata -V: This is Suricata version 7.0.3 RELEASE
suricata.service: disabled / inactive
suricata: 1:7.0.3-1build3
suricata-update: 1.3.0-2
libevent-core-2.1-7t64: 2.1.12-stable-9ubuntu2.2
policy-rc.d: retirado
ens34: 10.10.60.13/24
ens37: UP, PROMISC, sin IP
default via 10.10.60.1 dev ens34
```

Las advertencias `SyntaxWarning` de Python en `suricata-update` aparecieron
durante la instalacion; el paquete se configuro y el servicio quedo detenido.
Las reglas de deteccion no estan todavia configuradas; ver
`12-REGLAS-ET-OPEN.md`.
