# URL pública estable del panel para la demostración

**Estado actualizado:** Mark autorizó Funnel para `tag:bastion` y se activó la URL pública en el bastión. Falta el ensayo final desde un móvil externo con Tailscale apagado y una sesión `lector` real.

## Decisión

Mark no tiene un dominio en Cloudflare. Quick Tunnel cambia su URL al reiniciar. Con autorización de Mark se eligió **Tailscale Funnel** en VM-GESTION para obtener una URL estable que no requiera correo ni cuenta de Tailscale a los visitantes:

`https://vm-gestion.tail83bf9c.ts.net/`

La URL es **pública cuando Funnel está habilitado**. El segundo control es el login propio de CyberFlow; compartir solo la cuenta `lector` con evaluadores, nunca la cuenta `admin`. Sin sesión el panel responde HTTP 401. No deshabilitar el login. El panel queda en Sensor1; Funnel se ejecuta en el bastión y solo conecta desde allí a `https://10.10.60.11:8788`.

## Comprobaciones de lectura realizadas

| Elemento | Resultado |
|---|---|
| Bastión | VM-GESTION, `100.68.234.28`, etiqueta `tag:bastion`, `tailscaled` active/enabled, Tailscale 1.102.2 |
| Serve privado existente | `https://vm-gestion.tail83bf9c.ts.net:8788` **tailnet only** → `https+insecure://10.10.60.11:8788`; no se alteró |
| Origen | pfSense/ACL del sensor permite al bastión `10.10.10.30`; panel `ppi-dashboard` y `cyberflow-panel-acceso` activos; bastión obtiene HTTP 401 sin login |
| Certificado | CN/SAN IP `10.10.60.11`; certificado autofirmado, SHA-256 `51:DA:20:59:D3:18:66:37:F8:DC:76:28:66:09:41:D0:7E:87:0A:A1:48:F8:C4:B1:1D:DC:C7:8C:BE:12:37:97` |
| Funnel | El primer intento se bloqueó por política; después de la autorización de Mark, `sudo -n tailscale funnel --bg --https=443 https+insecure://10.10.60.11:8788` inició el Funnel. `tailscale funnel status --json` confirmó `AllowFunnel` para `:443` y conservó `:8788` como Serve privado |

## Permiso del propietario de la tailnet — completado

Mark habilitó el permiso de Funnel para VM-GESTION. La URL que entregó Tailscale al primer intento fue:

`https://login.tailscale.com/f/funnel?node=nwQpY2W51Y11CNTRL`

Si la consola requiere editar la política manualmente, añadir una entrada en `nodeAttrs` **sin reemplazar entradas existentes**:

```json
{"target": ["tag:bastion"], "attr": ["funnel"]}
```

Al usar un tag, el permiso alcanza a todos los nodos con ese tag; revisar el alcance del tag en la tailnet antes de guardar. No conceder `funnel` al wildcard `*`.

## Activación y verificación después del permiso

En el bastión, luego de comprobar que Sensor1 sigue en 401 sin login y que el panel solo acepta usuarios existentes:

```bash
tailscale funnel --bg --https=443 https+insecure://10.10.60.11:8788
tailscale funnel status
tailscale serve status
```

El uso de `https+insecure` refleja el proxy Tailscale Serve **ya configurado**, porque el certificado interno es autofirmado. El salto sensor↔bastión sigue cifrado pero no verifica la identidad TLS del origen; reforzar la confianza del certificado si se quiere dejar el servicio público estable como política prolongada.

**Verificaciones realizadas tras activar:**

- `tailscale funnel status`: `Funnel on` en `https://vm-gestion.tail83bf9c.ts.net/` → `https+insecure://10.10.60.11:8788`.
- `tailscale serve status`: mantiene el acceso `:8788` **tailnet only**. `tailscaled` sigue `active` y `enabled`.
- DNS público mediante Cloudflare DNS-over-HTTPS devolvió dos IP públicas (`199.38.181.54`, `209.177.145.137`), no la IP privada de Tailscale que obtiene el portátil con MagicDNS.
- Un `curl` desde Windows forzando la primera IP pública devolvió **HTTP 401**, con `ssl_verify_result=0`; `/api/status` también devolvió 401 sin cookie. La segunda IP falló por handshake desde Windows, pero respondió con la página de login 401 desde el bastión; repetir la prueba desde móvil externo antes de la demo.
- El login de `lector` y sus restricciones todavía requieren una prueba humana autenticada. No se solicitaron ni registraron contraseñas.

**Prueba de verdad fuera de la tailnet:** abrir `https://vm-gestion.tail83bf9c.ts.net/` desde un dispositivo sin Tailscale (por ejemplo, móvil en datos celulares con Tailscale apagado). Debe mostrar login HTTPS; sin sesión, las APIs deben responder 401. Ingresar con `lector`, confirmar que se ven métricas actuales y que `/api/archivo` y secciones de desarrollador responden 403/no aparecen. No compartir contraseñas en chat. Registrar fecha, estado de Tailscale y prueba con un correo/cuenta del evaluador solo si la política de demostración lo requiere.

## Operación y reversión

- **URL estable** significa que el nombre no cambia entre activaciones; disponibilidad depende del bastión, de `tailscaled` y de Funnel. Si se deja `--bg` habilitado, seguirá público tras reinicios mientras el nodo y la política lo permitan.
- Para cerrar la exposición al terminar la sesión, detener solo el Funnel de 443 con la sintaxis `tailscale funnel --https=443 off` (verificar con `tailscale funnel status`); no ejecutar `tailscale funnel reset` porque podría afectar la configuración Serve privada.
- Mantener el panel de Sensor1, el modelo, pfSense y el CORE-STACK sin cambios. Para revocación definitiva, además retirar el atributo `funnel` de `tag:bastion` y comprobar que la URL pública deja de responder.
- Si el profesor necesita una URL que siga siempre activa, documentar responsable del bastión, monitoreo y revocación de la cuenta `lector`; no usar la contraseña admin como credencial compartida.

**Fuentes:** documentación oficial de Tailscale sobre Funnel, puertos permitidos y `nodeAttrs`; observaciones SSH de esta sesión. Se descartó Cloudflare Quick Tunnel por no ofrecer nombre estable sin dominio propio.
