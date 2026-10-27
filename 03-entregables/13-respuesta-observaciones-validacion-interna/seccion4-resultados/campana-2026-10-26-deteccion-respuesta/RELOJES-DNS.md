# Relojes y DNS — estado medido y pasos administrativos pendientes

**Fecha:** 26–27-oct-2026. Comprobaciones benignas de solo lectura. **No se cambió ningún reloj ni el DNS.**

## Relojes (mecanismo, estado, desfase e incertidumbre)

No se concluye «sin sincronización» por ausencia de `chrony`: se comprobó el mecanismo real de cada host.

| Host | Mecanismo | NTP | NTPSynchronized | Desfase vs bastión | Fuente |
|---|---|---|---|---|---|
| Bastión 10.10.10.30 | chrony | sí | **sí** | referencia (System time 0,0007 s de NTP, root dispersion 0,02 s) | `chronyc tracking` |
| Sensor 10.10.60.11 | **systemd-timesyncd** (activo) | sí | **no** | **−47,55 s** (±0,18 s, 3 muestras) | `timedatectl`, 3 mediciones con RTT |
| srv-dmz 10.10.30.10 | systemd-timesyncd | sí | **sí** | — | `timedatectl` |
| Kali 10.10.20.30 | sin medir (es el generador; sin llave) | — | — | — | medir con su propio reloj en la campaña |

**Hallazgo preciso del sensor:** `timesyncd` está **activo y ya apuntando al bastión** (`Server: 10.10.10.30`),
pero `NTPSynchronized=no` y el reloj va **−47,55 s**. Es decir, la configuración es correcta; timesyncd no corrige
por sí solo un salto tan grande (desliza, no escalona). No hay que instalar nada.

### Paso administrativo pendiente (antes de la campaña)

- `[SENSOR root] → lo ejecutas tú` (sudo con contraseña; m4rk tiene `(ALL:ALL) ALL`):
  forzar el escalón una vez y dejar que timesyncd mantenga:
  ```bash
  sudo systemctl restart systemd-timesyncd      # reintenta el paso; si no converge:
  sudo timedatectl set-ntp false && sudo timedatectl set-ntp true   # fuerza un nuevo ciclo
  # verificación:
  timedatectl timesync-status   # Offset debe caer a milisegundos
  ```
  Medir y guardar el desfase **antes y después** (con `comprobar_relojes.sh` en cada host). Si no converge,
  alternativa: un escalón único con `chronyd -q 'server 10.10.10.30 iburst'` (requiere chrony) o corregir el desfase
  conocido (−47,55 s) en el análisis, documentándolo.
- Todas las marcas de 4.2/4.4 son del reloj del sensor; mientras no sincronice, el análisis usará `logged_at` del
  propio sensor (coherente consigo mismo) y el desfase medido para cruzar con la Kali.

## DNS

**Una respuesta pública no prueba por sí sola el reenvío**, por eso se comprobó con una consulta **única no
cacheable**:

- `dig @10.10.10.20 probe-<epoch>-<rand>.example.com` → respondió con el **SOA de `example.com`**
  (`elliott.ns.cloudflare.com`), con `ra` (recursion available). Un nombre que nunca pudo estar en caché solo se
  resuelve así si la consulta **salió al exterior** (recursión/forwarding a Internet).
- Conclusión: el resolutor 10.10.10.20 **reenvía/recursa a Internet**. El escenario DNS **no debe** usar nombres que
  salgan a terceros.

### Zona local reservada — preparación y comprobación (pendiente, requiere el DNS/AD)

- `[DNS/AD 10.10.10.20] → lo ejecutas tú` (sin mis llaves): crear una **zona local reservada** que resuelva dentro
  del laboratorio y **no** recurse. Opciones:
  - Windows AD DNS: nueva zona de búsqueda directa `lab-ppi` (o `lab.test`), con un registro comodín `*` → una IP de
    laboratorio; marcar la zona para no reenviar.
  - o un sinkhole: responder localmente a `*.lab-ppi` sin salida.
- **Respuesta esperada** del escenario: cada `dig @10.10.10.20 <rand>.lab-ppi` debe resolver **local** (o dar
  NXDOMAIN de la zona local), nunca tocar Internet.
- **Comprobación de no-egress** (antes de la campaña): mientras se lanza una consulta de prueba a `<rand>.lab-ppi`,
  capturar en el borde/pfSense el tráfico saliente a 53/udp hacia Internet y confirmar **cero** paquetes de esa
  consulta. Registrar el dominio elegido en `escenarios.json` (`params.zona_dns`) y poner `habilitado: true`.
