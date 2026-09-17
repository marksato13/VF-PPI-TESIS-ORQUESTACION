# Red y seguridad

## Principios

1. **Las NIC externas de VM02–VM05 permanecen desconectadas** durante campañas
   oficiales. VM01 conserva Internet y administra por PPI-MGMT.
2. **El bypass no es hipotético**: VM01 alcanzó TCP/22 del servidor sin cruzar el
   sensor. Por eso el aislamiento se verifica antes de cada campaña, no se asume.
3. **Ningún secreto en Git.** SOPS + age o systemd credentials.
4. **Escaneo de secretos antes de cada publicación.**

## Cuenta técnica

`useransible` con clave Ed25519. En VM02–VM05 solo puede ejecutar
`/usr/bin/systemctl reboot --no-wall`; en el sensor además los helpers
versionados `ppi-suricata-metrics`, `ppi-pcap-control` y `ppi-enforce`.

**No tiene sudo general.** La prueba negativa con `/usr/bin/id` falla en las
cuatro VMs, y esa prueba se repite tras cada cambio de permisos.

## Enforcement

| Elemento | Valor |
|---|---|
| Tabla | `inet ppi_enforce`, separada y **aditiva** |
| Hook | `forward`, prioridad −300 |
| Expiración | **120 s nativos** — el bloqueo se levanta solo |
| Whitelist | Interna, nunca bloquea gateway, sensor ni servidor |

## Lo que falta

| Elemento | Estado |
|---|---|
| UFW o nftables en la VM de orquestación | Pendiente |
| Tailscale | Pendiente |
| restic a almacenamiento externo | Pendiente |
| **Prueba de restauración** | Pendiente — *un backup sin restaurar no es un backup* |
| SBOM de dependencias | Pendiente |
| Rotación de logs | Pendiente |

> **El Quick Tunnel de Cloudflare no es infraestructura.** URL cambiante y sin
> garantía de disponibilidad. Para pruebas puntuales y nada más.
