# Procedimiento de instalación, comprobación y reversión (cierre técnico de la Etapa 3; NO ejecutado)

> **No autorizado.** Nada de este procedimiento se ha ejecutado. Solo se ejecutará si Mark autoriza la Etapa 4. Los pasos con `sudo` llevan contraseña, así que los ejecuta Mark.
>
> **Sustituye** a `../etapa3-deteccion-temprana-2026-11-02/PROCEDIMIENTO-ETAPA4.md`, que se conserva sin cambios. Lo que sigue igual se cita, no se repite. La base de la Etapa 2 (`../etapa2-cierre-tecnico-2026-11-01/PROCEDIMIENTO-INSTALACION-REVERSION.md`, pasos 0, 2, 3 y 4) sigue valiendo.
>
> **Orden obligatorio:**
> 1. Comprobar el estado del laboratorio.
> 2. Respaldo.
> 3. Instalación en **sombra**: agentes sin `--aplicar` y ninguna regla nueva.
> 4. Comprobación sin ataques.
> 5. Solo con una autorización aparte, paso a aplicar y campaña B.

**Commit a instalar:** `ec78ca5` de la rama `candidato/etapa3-20261102` (ver [DEPENDENCIAS-Y-COMANDOS.md](DEPENDENCIAS-Y-COMANDOS.md)). Sustituye a `585da7b`.

## Qué cambia respecto al procedimiento de la Etapa 3

| Componente | Cambio del cierre | Qué hay que comprobar además |
|---|---|---|
| `detector_rapido.py` | lectura continua con `os.read` y analizador incremental | que emite sin esperar a otro paquete (las pruebas lo cubren; en vivo solo se ve que el resumen avanza) |
| `ppi-via-rapida@.service` | filtro `"tcp or (vlan and tcp)"` | que el filtro compila con la libpcap de Sensor1 y la captura ve SYN/SYN-ACK/RST etiquetados (paso 0 y paso 1) |
| `motor_decision.py` | `auth_failure_heuristic` solo con la vista HTTP; campos `decision_if` y `auth_failure` | que el registro trae los dos campos |
| `publicar_feed_v2.py` | rechaza ALERT heurísticos sin evidencia válida (evento `rechazada`) | que la traza no muestre restricciones `auth_failure_heuristic` con `http_vista` sin peticiones válidas |

## 0. Estado del laboratorio y comprobaciones previas

`[BASTIÓN gadmin]` → **lo ejecuto yo**: lecturas por SSH sin sudo.

```bash
ssh m4rk@10.10.60.11 'systemctl is-active ppi-motor ppi-publicar-feed suricata; git -C ~/cyberflow rev-parse --short HEAD; uptime; free -m'
ssh m4rk@10.10.60.11 'tcpdump --version 2>&1 | head -2'
ssh m4rk@10.10.60.11 'tcpdump -d -y EN10MB "tcp or (vlan and tcp)" | head -5'
```

- **Estado:**
  - confirmar con Mark que **piloto-con-dns** terminó o que esta instalación no interfiere;
  - que no hay campaña en curso;
  - que lo desplegado sigue siendo `7b275b8`.

  Si algo no cuadra, se para y se consulta.
- **libpcap:** se anota la versión. Con libpcap ≥ 1.10 el banco mostró que los dos filtros entregan lo mismo en vivo. Si `tcpdump -d` falla o la versión es muy antigua, **no se instala** la vía rápida y se consulta.
- El resto del paso 0 de la Etapa 3 sigue igual: `<IFAZ>` de `suricata.yaml` y la carga de referencia.

## 1. Sensor1 en sombra

`[SENSOR1 m4rk]` → **lo ejecutas tú**: reinicia `ppi-motor` e instala unidades con sudo, que pide contraseña.

Igual que el paso 1 de la Etapa 3, cambiando el commit:

```bash
cd ~/cyberflow && git fetch && git switch --detach ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742
# ... resto idéntico (install de las dos unidades, systemd-analyze verify, daemon-reload,
#     restart ppi-motor, enable --now ppi-publicar-feed-v2 y ppi-via-rapida@<IFAZ>)
```

**Comprobación** `[SENSOR1 m4rk]` → lo ejecuto yo (lecturas):

- las del paso 1 de la Etapa 3: unidades activas, `dns_vista`/`http_vista` en el registro, el resumen de la vía rápida crece y **`senales-rapidas.jsonl` vacío sin ataques**;
- `tail -1 ~/cyberflow/logs/motor_decision.log`: trae `decision_if` y `auth_failure` (este vale `null` si no hubo señal de fallos de autenticación);
- `tail -3 ~/feed-v2/via-rapida-resumen.jsonl`:
  - `bytes_pendientes` bajo, por debajo del tamaño de un paquete;
  - `paquetes_tcp` crece al ritmo del tráfico SYN/RST del espejo;
- para comprobar que la captura ve las etiquetas, unos segundos de captura sin tocar la interfaz. Bloque `[SENSOR1 m4rk]` → **lo ejecutas tú**: tcpdump necesita privilegios, sudo con contraseña.

  ```bash
  sudo timeout 10 tcpdump -i <IFAZ> -n -e -c 20 "tcp or (vlan and tcp)" 2>/dev/null | head
  ```

  Debe mostrar `vlan` en las tramas o, si el vNIC las entrega sin etiqueta, tráfico TCP normal. Sin `-e` no se ve la etiqueta. Es una lectura breve que no cambia la interfaz.
- en la traza del publicador (`grep rechazada ~/feed-v2/traza*.jsonl | head`): los eventos `rechazada` son correctos, señal histórica sin evidencia válida. Una entrada `auth_failure_heuristic` en el feed con `http_vista` sin peticiones válidas sería un defecto, y se para.

**[pendiente en vivo]**: los cuatro puntos de la Etapa 3 (capacidades de tcpdump, `kernel_drops` de Suricata, retardo del espejo y reinicio con `pipefail`).

## 2–4. Relé, srv-dmz y DC1

Sin cambios respecto a la Etapa 3:

- `cf_nft_helper.py` de esta rama;
- DC1 con autorización explícita;
- **el LIMIT DNS sigue sin aprobar**: requiere el protocolo de [PROTOCOLO-OBSERVACION-DNS.md](PROTOCOLO-OBSERVACION-DNS.md) con P1 cumplido. Hasta entonces DC1 se instala en sombra o no se instala.

## 5. Paso a aplicar

Igual que en la Etapa 3 (autorización aparte). Antes de aplicar, además de lo anterior, al menos un día laborable en sombra con:

- 0 señales rápidas sobre legítimos;
- 0 `dns_entropy` sobre DC1/DC2;
- 0 `http_abuse` sobre 10.10.20.26;
- **0 restricciones `auth_failure_heuristic` sin evidencia válida** en la traza del publicador.

## 6. Reversión

Igual que en la Etapa 3: la vía rápida se desactiva y se borra su unidad, el publicador se vuelve a la unidad anterior, se hace `git switch --detach <HASH-DESPLEGADO-ANTES>` y se reinicia `ppi-motor`.

- Para volver a la candidata de la Etapa 3 sin el cierre: `git switch --detach 585da7b` y reinstalar su unidad de vía rápida, con el filtro `tcp`.
- **Comprobación**, además de la de la Etapa 3: `tail -1 motor_decision.log` **sin** `decision_if`.
- Los ficheros de evidencia (`senales-rapidas.jsonl`, `via-rapida-resumen.jsonl` y la traza) no se borran.
