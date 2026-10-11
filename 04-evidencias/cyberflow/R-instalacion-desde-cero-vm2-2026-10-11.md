# R — Instalación desde cero en la VM2 (cyberflow-sensor2)

**Fecha:** 10–11 de octubre de 2026 (instalación: 11-oct, 03:28–03:35 UTC) ·
**Versión instalada:** `main@b9245ed` (`cyberflow-main.tgz`, SHA-256 `8ce8d60f…7e608a`,
idéntico en origen y destino) · **Máquina:** `cyberflow-sensor2` (10.10.60.12),
Ubuntu 24.04.2, sin salida a Internet · **Plan:**
[`PLAN-PRUEBA-INSTALACION-VM2.md`](../../02-metodologia/validacion-interna-profesor/PLAN-PRUEBA-INSTALACION-VM2.md)

Sustituye a la nota `K` del 29-sep (`main@99d5005`) como evidencia de replicabilidad.

## Quién hizo qué

- **Claude** (por el bastión, sin sudo): B0, B2, B3, B6, B7 y la conversión de las salidas
  en capturas.
- **Mark**: B1, B4, B5 y las cuentas del panel, con `~/prueba_sudo.sh`. La VM2 no tiene
  sudo sin contraseña, y las contraseñas (sudo y panel) solo las tecleó él.

Cada comando corrió dentro de `script`, así que las salidas están completas en
`~/capturas/*.log` de la VM2. Las capturas de las guías se generaron de esos registros
(`main@bba15b6`).

## Resultado por criterio

| # | Criterio | Resultado | Evidencia |
|---|---|---|---|
| R1 | Instala en otra máquina, sin Internet | **Cumple** | Paso 7 del instalador: «instalando sin red desde ruedas/». Entorno con CPython 3.14.4 (fig. 6.3) |
| R2 | Solo con lo publicado | **Cumple** | Solo se ejecutaron los comandos de README e INSTALACION §6–7 |
| R3 | El asistente configura sin editar a mano | **Cumple** | `configurar.sh` detectó `ens37`, la MAC `00:0c:29:ea:45:d3`, el tráfico entrante y la red `10.10.0.0/16`. `.local.toml` validado (fig. 6.1) |
| R4 | El comprobador previo diagnostica antes de tocar | **Cumple** | `instalar.sh --comprobar`: 5 bloques OK, «642 paquetes en 5 s», «Todo listo para instalar» (fig. 6.2) |
| R5 | `doctor.sh` refleja el estado real | **Cumple** | 7 servicios OK y 3 avisos, los tres ciertos (ver abajo) (fig. 7.1) |
| R6 | Se desinstala limpio y se reinstala | **Cumple** | `desinstalar.sh`: «Limpio». No quedó ninguna unidad `ppi-*`/`cyberflow-*`. Reinstalación sin restos (fig. R.2) |
| R7 | Artefactos íntegros | **Cumple** | `sha256sum -c`: 13/13 OK (fig. 6.5) |
| R8 | Sin credenciales expuestas | **Cumple** | Contraseñas sin eco (fig. 6.7). 0 líneas en `.bash_history`. `/etc/cyberflow/{usuarios.json,clave-sesion,panel.key}` en modo `0600` |
| R9 | Funciona: capta, decide, muestra | **Cumple, salvo el login por roles** | Decisiones en el log (fig. 7.3), anillo rotando (32 ficheros a los 13 min, fig. 7.2), `kernel_drops = 0`. Panel en `https://127.0.0.1:8788`: 401 sin sesión, sin HTTP en claro. Falta entrar como `admin` y `lector` desde el navegador |

**Modo demo en la misma VM:** `PUERTO=8790 bash scripts/demo.sh` sirve el panel (200,
134 KB) con 224 decisiones de ejemplo.

## Los tres avisos de `doctor.sh` (esperados)

1. **«pcaps ilegibles: 1».** Es el primer fichero del anillo tras arrancar
   (`live-20261011033223.pcap`), creado como `tcpdump:tcpdump` antes de que el grupo pase a
   `m4rk`. Los demás son legibles. Es el mismo caso del Sensor1, que el panel ya muestra en
   ámbar.
2. **«Aún no hay dataset».** El temporizador `cyberflow-acumular` aún no había corrido.
3. **«Modelo SIN calibrar en esta red».** Es el perfil genérico, opción (a) del plan, y
   aplica INSTALACION §8.

## Desviaciones y correcciones

| Desviación | Corrección |
|---|---|
| `instalar.sh` y `doctor.sh` mostraban «0» y en otra línea «0 decisiones» cuando aún no había decisiones (`grep -c … \|\| echo 0`) | `main@bba15b6`. **La fig. 6.4 muestra la salida anterior a la corrección** |
| El instalador imprimía «Ahora: sudo systemctl enable --now …» y luego lo hacía él mismo | `cyberflow_config.py` solo lo imprime en una terminal (`main@bba15b6`). Sigue visible en la fig. 6.3 |
| `demo.sh` usaba siempre el puerto 8788, que en un sensor instalado ocupa el panel real | Variable `PUERTO`, documentada en el README (`main@1a83ad9`) |

No se encontró ningún paso del manual que no funcionara tal como está escrito.

## Pendiente

- **Mark:** entrar al panel con `admin` y `lector` (túnel `ssh -L 8788:127.0.0.1:8788`) y
  comprobar que el `lector` no ve la parte de desarrollador. Así R9 queda completo, y salen
  las capturas 7.4 y G.x del navegador.
- `doctor.sh` a los 30 min: la segunda pasada fue a los 9 min (ver abajo). Conviene
  repetirla antes de la sesión con el profesor.
- Faltan 18 de 30 capturas. Las de navegador, switch e hipervisor son de Mark (índice en
  `docs/img/CAPTURAS.md`).
