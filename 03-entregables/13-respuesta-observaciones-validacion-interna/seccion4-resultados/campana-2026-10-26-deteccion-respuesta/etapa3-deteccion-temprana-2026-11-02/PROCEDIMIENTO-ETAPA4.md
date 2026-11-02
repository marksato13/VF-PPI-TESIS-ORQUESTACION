# Procedimiento de instalación, comprobación y reversión de la candidata de la Etapa 3 (para la Etapa 4; NO ejecutado)

> **No autorizado.** En la Etapa 3 no se ha ejecutado nada de este procedimiento: ni instalación, ni reinicios, ni reglas, ni campañas. Solo se ejecutará si Mark autoriza la Etapa 4. Los pasos con `sudo` llevan contraseña, así que los ejecuta Mark.
>
> **Base:** este procedimiento **amplía** `../etapa2-cierre-tecnico-2026-11-01/PROCEDIMIENTO-INSTALACION-REVERSION.md`, que tampoco se ha ejecutado. Sus pasos 0 (respaldo), 2 (relé), 3 (srv-dmz) y 4 (DC1) siguen siendo válidos y se ejecutan en ese orden. Aquí solo se describe lo que **cambia o se añade**.
>
> **Orden obligatorio:**
> 1. Respaldo.
> 2. Instalación en **sombra**: agentes sin `--aplicar` y ninguna regla nueva.
> 3. Comprobación sin ataques.
> 4. Solo con una autorización aparte, paso a aplicar y campaña B.

Hashes de la rama `candidato/etapa3-20261102`: ver [DEPENDENCIAS-Y-COMANDOS.md](DEPENDENCIAS-Y-COMANDOS.md).

## Qué cambia respecto a la Etapa 2

| Componente | Host | Cambio | Efecto en sombra |
|---|---|---|---|
| Motor (`motor_decision.py`, `heuristicos.py`, `dns_heuristica.py`, `http_heuristica.py`) | Sensor1 | vistas DNS y HTTP de los heurísticos, `dns_entropy` ≥ 30, `http_abuse` 600, `port_scan` ráfaga con puertos distintos; `VERSION_UMBRALES = 2026-11-02.1` | ninguno sobre el IF (mismas 28 entradas, mismo modelo y α); cambian las decisiones heurísticas registradas |
| Vía rápida (`detector_rapido.py`, `escaneo_temprano.py`) | Sensor1 | **proceso nuevo**: `ppi-via-rapida@<ifaz>.service` (alternativa C) | escribe `senales-rapidas.jsonl`; una captura más de la interfaz del espejo |
| Publicador v2 (`publicar_feed_v2.py`) | Sensor1 | `--senales-rapidas`, política de renovación por evidencia | lo publica al feed v2; los agentes en sombra no aplican |
| Helper (`cf_nft_helper.py`) | srv-dmz, DC1 | LIMIT DNS 30/minuto, ráfaga 18, solo UDP/53 | ninguno en sombra (el helper no se llama con `--aplicar` ausente) |

Unidades nuevas en `deploy/enforcement/candidato-etapa3/`:

- `ppi-via-rapida@.service`: plantilla; la instancia es la interfaz de captura del espejo.
- `ppi-publicar-feed-v2.service`: igual que la de la Etapa 2, más `--senales-rapidas /home/m4rk/feed-v2/senales-rapidas.jsonl`.

## 0. Comprobaciones previas adicionales

Bloque `[SENSOR1 m4rk]` → **lo ejecuto yo**: lecturas sin sudo por SSH desde el bastión, sin cambios.

```bash
grep -n -A3 'af-packet:' /etc/suricata/suricata.yaml | grep interface      # interfaz del espejo: <IFAZ>
command -v tcpdump; tcpdump --version | head -1
nproc; free -m; uptime
```

- `<IFAZ>` es la instancia de `ppi-via-rapida@`. Si `suricata.yaml` no es legible sin sudo, la lectura la haces tú.
- Se anota la carga (`uptime`, `free`) **antes** de instalar: es la referencia para comprobar que el proceso nuevo no la cambia de forma apreciable.

## 1. Sensor1: código, publicador y vía rápida (sombra)

Bloque `[SENSOR1 m4rk]` → **lo ejecutas tú**: reinicia `ppi-motor` e instala unidades en `/etc/systemd/system` (sudo con contraseña).

```bash
cd ~/cyberflow && git fetch && git switch --detach 585da7b        # DEPENDENCIAS-Y-COMANDOS.md
install -d -m 0700 ~/feed-v2
sudo install -o root -g root -m 0644 deploy/enforcement/candidato-etapa3/ppi-publicar-feed-v2.service /etc/systemd/system/
sudo install -o root -g root -m 0644 'deploy/enforcement/candidato-etapa3/ppi-via-rapida@.service' /etc/systemd/system/
sudo systemd-analyze verify /etc/systemd/system/ppi-publicar-feed-v2.service '/etc/systemd/system/ppi-via-rapida@.service'
sudo systemctl daemon-reload
sudo systemctl restart ppi-motor
sudo systemctl enable --now ppi-publicar-feed-v2
sudo systemctl enable --now ppi-via-rapida@<IFAZ>
```

**Comprobación** `[SENSOR1 m4rk]` → lo ejecuto yo (lecturas):

- `systemctl is-active ppi-motor ppi-publicar-feed-v2 ppi-via-rapida@<IFAZ>`;
- `tail -1 ~/cyberflow/logs/motor_decision.log`: debe traer las claves `dns_vista` y `http_vista` (valen `null` si la entidad no tuvo actividad DNS o HTTP);
- `tail -2 ~/feed-v2/via-rapida-resumen.jsonl`: los paquetes procesados crecen;
- `wc -l ~/feed-v2/senales-rapidas.jsonl`: **sin ataques debe quedar vacío**. Una línea sobre un par legítimo es una falsa alarma: se registra, se para la unidad y se revisa K antes de seguir;
- `uptime`, `free -m` y `top -b -n1 -p $(pgrep -d, -f detector_rapido)`: CPU y memoria del detector frente a la referencia del paso 0.

**[pendiente en vivo]**

1. Que `tcpdump` con solo `CAP_NET_RAW` y `CAP_NET_ADMIN` (sin root) abra `<IFAZ>`. Si no, la alternativa es `-Z m4rk` arrancando como root; **no** se cambia sin revisión.
2. Que la captura adicional no haga perder paquetes a Suricata: comparar `capture.kernel_drops` en `stats.log` antes y después.
3. El retardo del espejo y del búfer de captura del sensor (desconocido; ver `VIA-RAPIDA-ESCANEO.md` §6.5).
4. Que `pipefail` reinicie la unidad si muere el detector: `systemctl status` tras `kill` del proceso Python. Es una prueba de la unidad, no un ataque.

## 2–4. Relé, srv-dmz y DC1

Igual que en la Etapa 2, con dos diferencias:

- se copia `cf_nft_helper.py` **de esta rama** (con el LIMIT DNS candidato);
- en DC1 sigue haciendo falta autorización explícita para instalar.

**El LIMIT DNS no está aprobado** (`DNS.md` §4): requiere la medida de varios días de tasas legítimas por origen y el ensayo en el banco DNS. Hasta entonces, en DC1 se instala en sombra o no se instala.

## 5. Paso a aplicar (requiere autorización aparte; no forma parte de la sombra)

Igual que el paso 3 de la Etapa 2: detener el agente v1, retirar su regla de sudoers, añadir `--aplicar` y reiniciar. La vía rápida no tiene un paso propio: su efecto llega por el mismo agente.

**Antes de aplicar**, revisar en sombra durante al menos un día laborable:

- 0 señales rápidas sobre legítimos;
- 0 `dns_entropy` sobre DC1/DC2;
- 0 `http_abuse` sobre 10.10.20.26.

## 6. Reversión

En orden inverso. La de los pasos 2–4 es la de la Etapa 2.

| Host | Etiqueta y quién | Acciones |
|---|---|---|
| Sensor1 | `[SENSOR1 m4rk]` → lo ejecutas tú (sudo) | `sudo systemctl disable --now ppi-via-rapida@<IFAZ>`; `sudo rm -f '/etc/systemd/system/ppi-via-rapida@.service'`. Para el publicador: o se reinstala la unidad de `candidato-etapa2/` (si se vuelve a la Etapa 2) o `sudo systemctl disable --now ppi-publicar-feed-v2` y se borra (si se vuelve a lo desplegado antes). `cd ~/cyberflow && git switch --detach <HASH-DESPLEGADO-ANTES>`; `sudo systemctl daemon-reload && sudo systemctl restart ppi-motor` |

**Comprobación de la reversión** `[SENSOR1 m4rk]` → lo ejecuto yo (lecturas):

- `systemctl list-units 'ppi-via-rapida@*'`: vacío;
- `git -C ~/cyberflow rev-parse HEAD` = `<HASH-DESPLEGADO-ANTES>`;
- `tail -1 ~/cyberflow/logs/motor_decision.log`: sin `dns_vista`;
- unidades frente a `unidades-estado.txt` como en la Etapa 2.

`~/feed-v2/senales-rapidas.jsonl` y `via-rapida-resumen.jsonl` **no se borran**: son evidencia.

## 7. Lo que la campaña B (no autorizada) tendría que confirmar

1. Que la restricción llega antes del último SYN en el laboratorio real (presupuesto con espejo, SSH y CPU reales).
2. Qué hace nmap ante el descarte.
3. Efecto del LIMIT DNS sobre `dns_inusual` y sobre los legítimos limitados por error.
4. Que las restricciones a legítimos sean 0 en tráfico de un día completo.
5. Episodios **nuevos**, no los 25 del 3B, para elegir α sin reutilizar los ataques de desarrollo.
