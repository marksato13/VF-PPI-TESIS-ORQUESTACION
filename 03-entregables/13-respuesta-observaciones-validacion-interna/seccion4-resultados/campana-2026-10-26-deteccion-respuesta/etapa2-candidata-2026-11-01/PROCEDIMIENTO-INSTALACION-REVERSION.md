# Procedimiento de instalación, comprobación y reversión del candidato (preparado, NO ejecutado)

> **No autorizado en esta etapa.** Nada de lo que sigue se ha ejecutado. Se ejecuta solo si Mark lo autoriza para la Etapa 3. Todos los pasos necesitan `sudo` con contraseña, así que los ejecuta Mark.
>
> **Orden obligatorio:** primero en sombra (sin `--aplicar`), con el v1 desplegado intacto. Solo después de comprobar la sombra se pasa a aplicar.
>
> En DC1, el paso 4 instala software: la restricción «No instales nada en DC1» exige una autorización explícita aparte.

Ficheros (rama `candidato/etapa2-20261101`; hashes en [REFERENCIAS.md](REFERENCIAS.md)):

- `scripts/engine/{motor_decision,heuristicos,feed,publicar_feed_v2}.py`;
- `scripts/enforce/{agente_enforce_v2,cf_nft_helper}.py`;
- `deploy/enforcement/relay_eventos.py`;
- `deploy/enforcement/candidato-etapa2/`, con estos ficheros:
  - `ppi-publicar-feed-v2.service`;
  - `ppi-relay-eventos.service`;
  - `ppi-enforce-agent-v2-{dmz,dns}.service`;
  - `cf-nft-helper.sudoers`;
  - `cf-feed-ssh.sh`.

## 0. Respaldo previo (todos los hosts)

Bloque para `[SENSOR1 m4rk]`, `[BASTIÓN gadmin]`, `[SRV-DMZ adminsrvdmz]` y `[DC1 dcadmin]` → **lo ejecutas tú**: necesita sudo con contraseña.

```bash
D=~/respaldo-etapa2-$(date -u +%Y%m%dT%H%MZ); mkdir -p "$D"
sudo nft list ruleset > "$D/ruleset.nft"; sudo cp -a /etc/sudoers.d "$D/"; systemctl list-units 'ppi-*' > "$D/unidades.txt"
sha256sum "$D"/* > "$D/SHA256SUMS"
```

## 1. Sensor1: motor candidato y publicador v2 (en sombra)

Bloque para `[SENSOR1 m4rk]` → **lo ejecutas tú**: reinicia `ppi-motor` y necesita sudo.

```bash
cd ~/cyberflow && git fetch && git switch --detach <HASH-CANDIDATO>   # ver REFERENCIAS.md
mkdir -p ~/feed-v2 && chmod 700 ~/feed-v2
sudo cp deploy/enforcement/candidato-etapa2/ppi-publicar-feed-v2.service /etc/systemd/system/
# Motor: añadir '--disparo eventos' solo si se ha aprobado; sin esa opcion es periodico (como hoy).
sudo systemctl daemon-reload && sudo systemctl restart ppi-motor && sudo systemctl enable --now ppi-publicar-feed-v2
```

**Comprobación:**

- `systemctl is-active ppi-motor ppi-publicar-feed-v2`;
- `tail -1 ~/feed-v2/traza.jsonl` (secuencia creciente);
- `python3 -c "import json;print(json.load(open('/home/m4rk/feed-v2/feed.json'))['version'])"` → 2;
- `~/feed/feed.json` (v1) sigue actualizándose.

## 2. Bastión: relé por eventos

Bloque para `[BASTIÓN gadmin]` → **lo ejecutas tú**: necesita sudo y llaves nuevas.

```bash
mkdir -p ~/relay-v2 && cp relay_eventos.py ~/relay-v2/
ssh-keygen -t ed25519 -N '' -f ~/.ssh/cyberflow-to-dc1      # solo si se autoriza DC1
sudo cp ppi-relay-eventos.service /etc/systemd/system/ && sudo systemctl daemon-reload
sudo systemctl enable --now ppi-relay-eventos
```

En los hosts de destino y en el sensor, la llave del relé se registra **con comando forzado**:

```
command="/usr/local/bin/cf-feed-ssh.sh recibir <dir>",restrict ssh-ed25519 …
```

**Comprobación:** `tail -3 ~/relay-v2/traza.jsonl` (cada destino con `entregado_en` y sin `error`).

## 3. srv-dmz: helper y agente v2 (sombra → aplicar)

Bloque para `[SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**: instala en `/usr/local/sbin` y en `sudoers`.

```bash
sudo install -o root -g root -m 0755 cf_nft_helper.py /usr/local/sbin/cf-nft-helper
sudo install -o root -g root -m 0755 cf-feed-ssh.sh /usr/local/bin/cf-feed-ssh.sh
sudo install -o root -g root -m 0440 cf-nft-helper.sudoers /etc/sudoers.d/cf-nft-helper && sudo visudo -c
mkdir -p ~/enforce-v2 && cp agente_enforce_v2.py feed.py ~/enforce-v2/ && cp ~/enforce/pub.pem ~/enforce-v2/
sudo cp ppi-enforce-agent-v2-dmz.service /etc/systemd/system/
# SOMBRA: quitar '--aplicar' del ExecStart (la unidad candidata no lo lleva) y arrancar
sudo systemctl daemon-reload && sudo systemctl enable --now ppi-enforce-agent-v2-dmz
```

**Comprobación en sombra:**

- `tail ~/enforce-v2/traza.jsonl` → `recepcion` con `estado: aceptado` y `ajenas` > 0 cuando haya entradas de DC1;
- `sudo nft list table inet cyberflow` sigue siendo la del v1.

**Para aplicar** (requiere autorización):

1. Detener el agente v1: `sudo systemctl disable --now ppi-enforce-agent.timer`.
2. Retirar su regla `NOPASSWD: /usr/sbin/nft`.
3. Añadir `--aplicar` a la unidad v2.

Comprobación: `echo '{"perfil":"dmz","operaciones":[{"op":"listar"}]}' | sudo -n /usr/local/sbin/cf-nft-helper`.

**Tablas.** El v2 usa su propia tabla, `inet cyberflow_dmz`, y no toca `inet cyberflow` del v1 (prueba `test_helper_dmz_no_toca_la_tabla_del_v1`). Aun así, no deben aplicar los dos a la vez. Al pasar a aplicar se desactiva el agente v1; su tabla se vacía sola por caducidad o con `sudo nft destroy table inet cyberflow` dentro de la ventana autorizada.

## 4. DC1: helper y agente v2 perfil dns (requiere autorización explícita para instalar en DC1)

Bloque para `[DC1 dcadmin]` → **lo ejecutas tú**: crea un usuario, instala el helper y sudoers.

```bash
sudo useradd -m -s /usr/sbin/nologin cfagente
sudo install -o root -g root -m 0755 cf_nft_helper.py /usr/local/sbin/cf-nft-helper
sudo install -o root -g root -m 0755 cf-feed-ssh.sh /usr/local/bin/cf-feed-ssh.sh
# en cf-nft-helper.sudoers, descomentar la linea de cfagente
sudo install -o root -g root -m 0440 cf-nft-helper.sudoers /etc/sudoers.d/cf-nft-helper && sudo visudo -c
sudo -u cfagente mkdir -p /home/cfagente/enforce-v2   # + agente_enforce_v2.py, feed.py, pub.pem
sudo cp ppi-enforce-agent-v2-dns.service /etc/systemd/system/ && sudo systemctl daemon-reload
sudo systemctl enable --now ppi-enforce-agent-v2-dns      # sombra: sin --aplicar
```

**Comprobación:**

- `sudo nft list tables` → con `--aplicar`, solo aparece `inet cyberflow_dns`;
- `samba-tool dns query 127.0.0.1 <zona> @ ALL -P` sigue respondiendo;
- `ss -lunpt | grep ':53 '` sin cambios.

## 5. Reversión (en orden inverso; cada paso es independiente)

| Host | Acción | Bloque |
|---|---|---|
| DC1 | Quitar agente, tabla, helper y usuario | `[DC1 dcadmin]` → lo ejecutas tú (sudo): `sudo systemctl disable --now ppi-enforce-agent-v2-dns; echo '{"perfil":"dns","operaciones":[{"op":"desinstalar"}]}' \| sudo /usr/local/sbin/cf-nft-helper; sudo rm -f /etc/sudoers.d/cf-nft-helper /usr/local/sbin/cf-nft-helper /usr/local/bin/cf-feed-ssh.sh /etc/systemd/system/ppi-enforce-agent-v2-dns.service; sudo userdel -r cfagente; sudo systemctl daemon-reload` |
| srv-dmz | Volver al v1 | `[SRV-DMZ adminsrvdmz]` → lo ejecutas tú (sudo): `sudo systemctl disable --now ppi-enforce-agent-v2-dmz; echo '{"perfil":"dmz","operaciones":[{"op":"desinstalar"}]}' \| sudo /usr/local/sbin/cf-nft-helper; sudo cp -a <RESPALDO>/sudoers.d/. /etc/sudoers.d/ && sudo visudo -c; sudo systemctl enable --now ppi-enforce-agent.timer` |
| Bastión | Parar el relé v2 | `[BASTIÓN gadmin]` → lo ejecutas tú (sudo): `sudo systemctl disable --now ppi-relay-eventos` (el `ppi-relay-feed.timer` del v1 no se tocó) |
| Sensor1 | Volver al motor y publicador desplegados | `[SENSOR1 m4rk]` → lo ejecutas tú (sudo): `sudo systemctl disable --now ppi-publicar-feed-v2; cd ~/cyberflow && git switch --detach 24f8a80 && sudo systemctl restart ppi-motor` (o el hash desplegado de ese momento) |

**Comprobación de la reversión:**

- `sudo nft list ruleset | diff - <RESPALDO>/ruleset.nft` (solo deben variar los elementos con caducidad);
- `systemctl list-units 'ppi-*'` igual que `unidades.txt`.

## 6. Limpieza D5 de un origen de ensayo (tras cada episodio de la campaña B)

Bloque para `[SENSOR1 m4rk]` → lo ejecuto yo si se autoriza: no necesita sudo y, en seco, no toca el estado.

```bash
python3 scripts/enforce/limpiar_origen.py --ip 10.10.20.30 --estado-publicador ~/feed-v2/estado.json \
  --respaldo ~/limpieza-$(date -u +%H%M%S) --informe ~/limpieza-$(date -u +%H%M%S)/informe.json   # en seco
```

En los agentes, la retirada es la petición `retirar_origen` del helper (perfiles dmz y dns). En la Etapa 2 solo se ha ensayado en el banco: `test_limpieza_con_helper_real`.
