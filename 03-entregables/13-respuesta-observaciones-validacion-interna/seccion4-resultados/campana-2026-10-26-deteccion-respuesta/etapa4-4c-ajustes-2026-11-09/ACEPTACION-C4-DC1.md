# C4: referencia del ruleset de DC1 — para aceptación de Mark (09-nov-2026)

**Estado: tomada, reverificada en solo lectura y ACEPTADA por Mark. No se cambió nada en DC1.**

## Qué se hizo
Desde el bastión como `dcadmin@10.10.10.20` (VM-AD-DC, Debian 13; `sudo -n` sin contraseña), con el comando del PROCEDIMIENTO-ETAPA4 §3:
`sudo nft list ruleset > ~/dc1-ruleset-$(date -u +%Y%m%dT%H%M%SZ).nft && sha256sum ~/dc1-ruleset-*.nft | tail -1`

| Dato | Valor |
|---|---|
| Fichero | `/home/dcadmin/dc1-ruleset-20261109T060309Z.nft` (09-nov 06:03:09Z = 01:03:09 Perú) |
| Tamaño / sha256 | **0 bytes** / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (el de un fichero vacío) |
| rc del comando | **0**, y 0 bytes de errores |
| Reverificación (07:12Z = 02:12 Perú) | `nft list ruleset` rc 0, 0 líneas, 0 bytes de error; `diff` contra la referencia: **SIN_CAMBIOS**; `nft list tables`: 0 |

## Qué significa (y qué no)
- **DC1 no tiene ninguna tabla ni regla nft** en este momento; no es un fallo de lectura (rc 0, sin errores, `nft` 1.1.3 en `/usr/sbin/nft`).
- No usa otro filtro de paquetes: `iptables` e `ip6tables` no están instalados, `nftables`, `ufw` y `firewalld` están inactivos. Escucha servicios de dominio (22, 53, 88, 135, 139, 389, 445, 464, 636, 3268, 3269 y 49152–49154).
- Sirve como referencia de «DC1 sin cambios»: si algún día aparece una tabla `cyberflow` o cualquier regla, `sudo nft list ruleset | diff - <fichero>` lo mostrará. La Etapa 4 no instala nada en DC1 y el agente DNS no se aplica (no hay agente DNS).
- **No demuestra** que DC1 esté protegido por otro medio fuera del propio host (por ejemplo, el firewall de red); eso no se midió.

## Aceptación
- ☑ **Aceptada por Mark (chat, 09-nov-2026, 07:17Z = 02:17 Perú):** referencia vacía de nftables de DC1 para C4, con la lectura privilegiada documentada en rc 0 y sin errores.

Evidencia: `evidencia/dc1-referencia-c4.txt` (toma) y `evidencia/dc1-reverificacion.txt` (reverificación).
