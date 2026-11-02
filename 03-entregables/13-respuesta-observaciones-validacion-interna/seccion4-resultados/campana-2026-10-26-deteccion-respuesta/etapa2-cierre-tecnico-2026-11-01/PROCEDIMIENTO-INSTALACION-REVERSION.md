# Procedimiento de instalación, comprobación y reversión del candidato de la Etapa 2 (revisado, NO ejecutado)

> **No autorizado en esta etapa.** No se ha ejecutado nada de este procedimiento en el laboratorio. Solo se ejecutará si Mark lo autoriza para la Etapa 3. Todos los pasos llevan `sudo` con contraseña, así que los ejecuta Mark.
>
> **Orden obligatorio:**
> 1. Respaldo del estado observado.
> 2. Instalación en **sombra**: agentes sin `--aplicar`, el v1 intacto y ningún cambio de reglas.
> 3. Comprobación.
> 4. Solo con una autorización aparte, paso a aplicar.
>
> **DC1:** el paso 4 instala software y crea cuentas. La restricción «No instales nada en DC1» exige una autorización explícita aparte.

Esta versión **sustituye** a `../etapa2-candidata-2026-11-01/PROCEDIMIENTO-INSTALACION-REVERSION.md`, que se conserva como antecedente. Se ha revisado contra los scripts y las unidades reales de la rama `candidato/etapa2-20261101`; los hashes están en [REFERENCIAS.md](REFERENCIAS.md).

Lo marcado como **[banco]** se ha probado en el banco aislado `cyberflow-etapa2-banco:3`, sin red, con `deploy/pruebas-aisladas/ensayo_ssh_unidades.sh`. La salida está en `resultados/ensayo-ssh-unidades.txt`. Lo marcado como **[pendiente en vivo]** solo se puede comprobar en el laboratorio.

## Cambios respecto al procedimiento anterior

| # | Problema en la versión anterior | Corrección | Prueba |
|---|---|---|---|
| P1 | La cuenta del transporte en DC1 se creaba con `nologin`, pero `sshd` ejecuta el comando forzado con la shell de la cuenta, así que el relé no podía entregar. | Se separan dos cuentas: **`cffeed`** para el transporte (`/bin/sh`, contraseña bloqueada, solo la llave del relé con `command=…,restrict`) y **`cfagente`** para el agente (`nologin`, sin llaves). | [banco] S1 (entrega real) y S2 (con `nologin` falla) |
| P2 | El feed se dejaba en `~/enforce-v2` del administrador y el agente corría como ese usuario. | Código y clave pública en `/opt/cyberflow/agente-v2` (`root:root` 0755/0644), feed en `/var/lib/cyberflow/feed` (`cffeed:cfagente` 2750, ficheros 0640) y estado en `/var/lib/cyberflow/agente` (`cfagente` 0700). | [banco] S4 |
| P3 | El perfil del helper venía en la petición. | El perfil lo fija el host en `/etc/cyberflow/nft-helper.perfil` (`root:root` 0644), con `dns` en DC1 y `dmz` en srv-dmz. El helper rechaza el fichero si no es de root o si su fichero o su directorio son escribibles por otros. | [banco] S7; unitarias `TestFicheroDePerfil` |
| P4 | El relé no verificaba la pareja feed/firma. | El relé recibe `--clave-publica` y entrega en dos fases (temporales y luego renombrado conjunto). El comando forzado admite exactamente esas órdenes. | [banco] S1 y S3; unitarias del punto 2 |
| P5 | El respaldo no guardaba el estado de las unidades, y la reversión reactivaba el v1 aunque estuviera parado. | Se guardan `is-enabled` e `is-active` de cada unidad y la reversión restaura **ese** estado, sin reactivar el enforcement antiguo si estaba en sombra o parado. | revisión del texto (sin ejecución) |
| P6 | Faltaban comprobaciones previas: `python3`, `openssl`, `nft` y la versión de systemd. | Se añade el paso 0.b. | [pendiente en vivo] |
| P7 | En la sombra se podían cambiar reglas. | Las unidades candidatas **no** llevan `--aplicar`, y en sombra el agente solo lee el feed y lista. | [banco] S5: sin `--aplicar` no aparece ninguna tabla |
| P8 | Las unidades se copiaban con `cp` y heredaban bits de ejecución. | Se usa `install -m 0644`. | [banco] S8: `systemd-analyze verify` sin avisos para el relé y los agentes |

## 0. Respaldo y comprobaciones previas (todos los hosts)

### 0.a Respaldo del estado observado

Bloque para `[SENSOR1 m4rk]`, `[BASTIÓN gadmin]`, `[SRV-DMZ adminsrvdmz]` y `[DC1 dcadmin]` → **lo ejecutas tú**, porque necesita sudo con contraseña (en DC1 `dcadmin` tiene NOPASSWD, pero solo se usa para lecturas, y esto es una lectura).

```bash
D=~/respaldo-etapa2-$(date -u +%Y%m%dT%H%MZ); mkdir -p "$D"
sudo nft list ruleset > "$D/ruleset.nft"
sudo cp -a /etc/sudoers.d "$D/sudoers.d"
for u in $(systemctl list-unit-files 'ppi-*' --no-legend | awk '{print $1}'); do
  printf '%s %s %s\n' "$u" "$(systemctl is-enabled "$u" 2>&1)" "$(systemctl is-active "$u" 2>&1)"
done > "$D/unidades-estado.txt"
getent passwd cffeed cfagente > "$D/cuentas.txt" || true
sha256sum "$D"/ruleset.nft "$D"/unidades-estado.txt > "$D/SHA256SUMS"
```

`unidades-estado.txt` es la referencia de la reversión: cada unidad vuelve **exactamente** a su `is-enabled` e `is-active`.

### 0.b Comprobaciones previas

Bloque para `[SRV-DMZ adminsrvdmz]` y `[DC1 dcadmin]` → **lo ejecuto yo**: son lecturas sin sudo, se hacen por SSH desde el bastión con las llaves existentes y no cambian nada.

```bash
command -v python3 openssl; python3 --version; openssl version; ls -l /usr/sbin/nft; systemctl --version | head -1
```

Mínimos:

- Python ≥ 3.11 (`-I` e importación del `feed.py` co-desplegado; probado con 3.13 en el banco);
- OpenSSL con Ed25519 (`pkeyutl -rawin`);
- `nft` en `/usr/sbin/nft`.

Si falta algo **en DC1**, se detiene el procedimiento y no se instala nada sin autorización.

## 1. Sensor1: motor candidato y publicador v2 (en sombra)

Bloque para `[SENSOR1 m4rk]` → **lo ejecutas tú**: reinicia `ppi-motor` y necesita sudo.

```bash
cd ~/cyberflow && git fetch && git switch --detach <HASH-CANDIDATO>          # REFERENCIAS.md
install -d -m 0700 ~/feed-v2
sudo install -o root -g root -m 0644 deploy/enforcement/candidato-etapa2/ppi-publicar-feed-v2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart ppi-motor                    # sin '--disparo eventos' salvo aprobacion: periodico como hoy
sudo systemctl enable --now ppi-publicar-feed-v2
```

**Comprobación** `[SENSOR1 m4rk]` → lo ejecuto yo (lecturas):

- `systemctl is-active ppi-motor ppi-publicar-feed-v2`;
- `grep motor_startup ~/cyberflow/logs/motor_decision.log | tail -1`. Debe mostrar `"horizonte": "por_ventana"`, `ancla_reanudada` (no null si había registro reciente) y `recuperacion_eve.completa`;
- `tail -1 ~/feed-v2/traza.jsonl` (la secuencia crece);
- el feed v1 `~/feed/feed.json` sigue actualizándose.

**[pendiente en vivo]**:

- que `/home/m4rk/cyberflow/.venv/bin/python` exista con las dependencias del modelo. `systemd-analyze` lo marcó ausente en el banco, como era de esperar;
- el tamaño de `eve.json` frente al rebobinado (como mucho 512 MB);
- la retención del anillo (`retener_minutos = 15`) frente a `--history-seconds 230 + --recuperacion-max-segundos 600`.

## 2. Bastión: relé por eventos

Bloque para `[BASTIÓN gadmin]` → **lo ejecutas tú**: necesita sudo y crear llaves.

```bash
sudo install -d -o root -g root -m 0755 /opt/cyberflow/relay-v2
sudo install -o root -g root -m 0644 relay_eventos.py feed.py /opt/cyberflow/relay-v2/
sudo install -o root -g root -m 0644 pub.pem /opt/cyberflow/relay-v2/pub.pem    # clave PUBLICA del sensor
install -d -m 0700 ~/relay-v2
ssh-keygen -t ed25519 -N '' -f ~/.ssh/cyberflow-to-srv-v2
ssh-keygen -t ed25519 -N '' -f ~/.ssh/cyberflow-to-dc1        # solo si se autoriza DC1
sudo install -o root -g root -m 0644 ppi-relay-eventos.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ppi-relay-eventos
```

En el **sensor**, la llave del relé se añade a `~m4rk/.ssh/authorized_keys` **con comando forzado de solo lectura**:

```
command="/usr/local/bin/cf-feed-ssh.sh servir /home/m4rk/feed-v2",restrict ssh-ed25519 AAAA… rele
```

Eso exige instalar `cf-feed-ssh.sh` en el sensor:

- bloque `[SENSOR1 m4rk]` → **lo ejecutas tú** (sudo): `sudo install -o root -g root -m 0755 cf-feed-ssh.sh /usr/local/bin/`.

**Comprobación** `[BASTIÓN gadmin]` → lo ejecuto yo (lectura): `tail -3 ~/relay-v2/traza.jsonl`. Cada destino debe aparecer con `entregado_en`. Una `pareja_inconsistente` aislada es normal (lectura entre los dos renombrados); repetida durante más de 2 s, no.

## 3. srv-dmz: cuentas, helper y agente v2 en sombra

Bloque para `[SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**: crea cuentas e instala en `/usr/local`, `/opt`, `/etc` y `sudoers`.

```bash
sudo useradd -r -m -d /var/lib/cyberflow/cffeed-home -s /bin/sh cffeed && sudo passwd -l cffeed
sudo useradd -r -M -d /nonexistent -s /usr/sbin/nologin cfagente
sudo usermod -aG cfagente cffeed
sudo install -d -o root -g root -m 0755 /opt/cyberflow/agente-v2 /etc/cyberflow /var/lib/cyberflow
sudo install -d -o cffeed -g cfagente -m 2750 /var/lib/cyberflow/feed
sudo install -d -o cfagente -g cfagente -m 0700 /var/lib/cyberflow/agente
sudo install -o root -g root -m 0644 agente_enforce_v2.py feed.py pub.pem /opt/cyberflow/agente-v2/
sudo install -o root -g root -m 0755 cf_nft_helper.py /usr/local/sbin/cf-nft-helper
sudo install -o root -g root -m 0755 cf-feed-ssh.sh /usr/local/bin/cf-feed-ssh.sh
echo dmz | sudo tee /etc/cyberflow/nft-helper.perfil >/dev/null && sudo chmod 0644 /etc/cyberflow/nft-helper.perfil
sudo install -o root -g root -m 0440 cf-nft-helper.sudoers /etc/sudoers.d/cf-nft-helper && sudo visudo -c
sudo install -d -o cffeed -g cffeed -m 0700 /var/lib/cyberflow/cffeed-home/.ssh
# authorized_keys de cffeed (una linea, la llave publica cyberflow-to-srv-v2 del bastion):
#   command="/usr/local/bin/cf-feed-ssh.sh recibir /var/lib/cyberflow/feed",restrict ssh-ed25519 AAAA… rele
sudo install -o root -g root -m 0644 ppi-enforce-agent-v2-dmz.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ppi-enforce-agent-v2-dmz        # SOMBRA
```

**Comprobación en sombra** `[SRV-DMZ adminsrvdmz]` → lo ejecutas tú (las rutas de `cfagente` necesitan sudo para leerse):

- `sudo tail /var/lib/cyberflow/agente/traza.jsonl`: debe haber `recepcion` con `estado: aceptado` y ninguna `aplicacion`;
- `sudo nft list tables`: debe salir **la misma lista** que en `ruleset.nft` (sin `cyberflow_dmz`);
- `echo '{"perfil":"dns","operaciones":[{"op":"listar"}]}' | sudo -u cfagente sudo -n /usr/local/sbin/cf-nft-helper` → `perfil_no_autorizado`.

**[pendiente en vivo]**:

- que la entrega del relé llegue a `/var/lib/cyberflow/feed` con 0640 `cffeed:cfagente` (probado en el banco, S1 y S4);
- que el `sudo` del host aplique el `Defaults` correcto (`requiretty` rompería el helper).

**Pasar a aplicar** (requiere una autorización aparte):

1. Detener el agente v1 según su estado en `unidades-estado.txt`: `sudo systemctl disable --now ppi-enforce-agent.timer`.
2. Retirar del sudoers su regla `NOPASSWD: /usr/sbin/nft`.
3. Añadir `--aplicar` al `ExecStart` de la unidad v2.
4. `daemon-reload` y `restart`.

El v2 usa su propia tabla, `inet cyberflow_dmz`, y no toca `inet cyberflow` del v1 (prueba `test_helper_dmz_no_toca_la_tabla_del_v1`), pero los dos no deben aplicar a la vez.

## 4. DC1: cuentas, helper y agente v2 perfil dns (requiere autorización explícita para instalar en DC1)

Bloque para `[DC1 dcadmin]` → **lo ejecutas tú**: crea cuentas e instala software. Aunque `dcadmin` tenga NOPASSWD, la norma solo lo admite para lecturas.

Son los mismos pasos que en el punto 3, con estos cambios:

- `echo dns | sudo tee /etc/cyberflow/nft-helper.perfil`;
- unidad `ppi-enforce-agent-v2-dns.service`;
- llave `cyberflow-to-dc1` en el `authorized_keys` de `cffeed`.

**Comprobación** `[DC1 dcadmin]` → lo ejecuto yo (lecturas con `dcadmin`):

- `sudo nft list tables`: sin cambios en sombra;
- `samba-tool dns query 127.0.0.1 <zona> @ ALL -P` sigue respondiendo;
- `ss -lunpt | grep ':53 '` sin cambios.

## 5. Reversión (en orden inverso; cada paso es independiente)

La reversión restaura **el estado observado** en `unidades-estado.txt`. Si el v1 estaba en sombra o parado, **no** se reactiva.

| Host | Etiqueta y quién | Acciones |
|---|---|---|
| DC1 | `[DC1 dcadmin]` → lo ejecutas tú (sudo, cambios) | `sudo systemctl disable --now ppi-enforce-agent-v2-dns`; `echo '{"perfil":"dns","operaciones":[{"op":"desinstalar"}]}' \| sudo /usr/local/sbin/cf-nft-helper`; `sudo rm -f /etc/sudoers.d/cf-nft-helper /usr/local/sbin/cf-nft-helper /usr/local/bin/cf-feed-ssh.sh /etc/systemd/system/ppi-enforce-agent-v2-dns.service /etc/cyberflow/nft-helper.perfil`; `sudo rm -rf /opt/cyberflow/agente-v2 /var/lib/cyberflow`; `sudo userdel cffeed; sudo userdel cfagente`; `sudo visudo -c && sudo systemctl daemon-reload` |
| srv-dmz | `[SRV-DMZ adminsrvdmz]` → lo ejecutas tú (sudo) | Lo mismo con el perfil `dmz`. Después `sudo cp -a <RESPALDO>/sudoers.d/. /etc/sudoers.d/ && sudo visudo -c`. Para cada línea `ppi-enforce-agent*` de `unidades-estado.txt`: si estaba `enabled`/`active`, `sudo systemctl enable --now <unidad>`; si estaba `disabled`/`inactive`, se deja así. |
| Bastión | `[BASTIÓN gadmin]` → lo ejecutas tú (sudo) | `sudo systemctl disable --now ppi-relay-eventos`; `sudo rm -f /etc/systemd/system/ppi-relay-eventos.service && sudo rm -rf /opt/cyberflow/relay-v2 && sudo systemctl daemon-reload`. El `ppi-relay-feed.timer` del v1 no se tocó. |
| Sensor1 | `[SENSOR1 m4rk]` → lo ejecutas tú (sudo) | `sudo systemctl disable --now ppi-publicar-feed-v2`; quitar de `~/.ssh/authorized_keys` la línea `cf-feed-ssh.sh servir`; `cd ~/cyberflow && git switch --detach <HASH-DESPLEGADO-ANTES>` (el de `unidades-estado`/registro previo, hoy `24f8a80`) y `sudo systemctl restart ppi-motor` |

**Comprobación de la reversión** (en cada host, `[… ]` → lo ejecutas tú, sudo de lectura del ruleset):

- `sudo nft list ruleset | diff - <RESPALDO>/ruleset.nft`: solo pueden variar los elementos con caducidad y los contadores;
- `for u in $(awk '{print $1}' <RESPALDO>/unidades-estado.txt); do printf '%s %s %s\n' $u $(systemctl is-enabled $u) $(systemctl is-active $u); done | diff - <RESPALDO>/unidades-estado.txt`: sin diferencias.

## 6. Lo que queda pendiente de comprobar en el laboratorio

1. Existencia del venv de Sensor1 y sus versiones (scikit-learn 1.9.0, numpy 2.5.1).
2. `Defaults` de sudo en srv-dmz y DC1 (`requiretty`, `secure_path`).
3. Tamaño y rotación de `eve.json` frente al rebobinado del motor.
4. La entrega SSH real bastión → srv-dmz / DC1, con el `known_hosts` existente.
5. En DC1: que Samba siga resolviendo tras instalar (en sombra no hay reglas).
6. Endurecimiento de las unidades (`ProtectSystem`, `PrivateTmp`). `NoNewPrivileges` es incompatible con `sudo` y no se ha ensayado con systemd real, porque en el banco systemd no está arrancado.
