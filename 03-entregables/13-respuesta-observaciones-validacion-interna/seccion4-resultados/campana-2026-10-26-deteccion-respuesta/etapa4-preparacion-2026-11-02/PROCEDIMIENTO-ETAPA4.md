# Procedimiento de la Etapa 4: 4A (instalación en sombra), 4B, 4C y reversión

> **Estado: preparado y probado offline. NO ejecutado.** Este documento sustituye a `../etapa3-cierre-tecnico-2026-11-02/PROCEDIMIENTO-ETAPA4.md`, que partía de dos afirmaciones falsas: que el Sensor1 ejecuta `7b275b8` y que `~/cyberflow` es un checkout de git (ver [ESTADO-OBSERVADO-LABORATORIO.md](ESTADO-OBSERVADO-LABORATORIO.md)). Ejecutar cualquier paso exige que Mark **pida la Etapa 4** y que se cumplan las condiciones de [README.md §5](README.md#5-condiciones-antes-de-instalar). Este documento no autoriza la campaña B.

**Código que se instala:** `ec78ca5` (`ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742`), sin cambios.

**Herramientas:** `acc6588` de la rama `candidato/etapa3-20261102`. Solo añaden `scripts/etapa4/`, `deploy/etapa4/` y pruebas, y `paquete_candidata.sh` aborta si el código difiere de ec78ca5.

**Qué no cambia:**

- el modelo, el escalador (dentro del pipeline), las 28 características, el umbral y las reglas;
- el publicador v1, el relé v1, el panel y el acumulador;
- el agente v1 de srv-dmz, que sigue *disabled/inactive*;
- DC1;
- el LIMIT DNS, que **no se aplica en ningún sitio**.

Ningún agente lleva `--aplicar` y el motor no lleva `--enforce`.

**Convenciones:**

- Cada bloque lleva **`[MÁQUINA cuenta]`**, quién lo ejecuta y por qué.
- **Resultado esperado** y **parada** van debajo de cada bloque. Una parada detiene el procedimiento en ese punto. Si ocurre después de la fase 3 de Sensor1, se revierte (§7).
- Los comandos marcados *→ lo ejecuto yo* los lanzo desde el portátil por SSH a través del bastión (`gadmin@10.10.10.30`, llave `~/.ssh/id_ed25519`). Desde el bastión salto con sus llaves: `cyberflow-to-sensor` (m4rk@10.10.60.11) y `cyberflow-to-srv` (adminsrvdmz@10.10.30.10).
- Los comandos de Mark llevan `ssh -t` porque piden la contraseña de sudo.
- Ningún comando imprime claves privadas. `priv.pem` del feed **no se lee ni se copia**: solo se deriva la clave pública en el propio Sensor1.

## 0. Requisitos previos

Se comprueban **el mismo día de la instalación**; ninguno se da por cumplido por lo visto el 2-nov.

| # | Requisito | Cómo se demuestra |
|---|---|---|
| R0.1 | Mark pide la Etapa 4 por escrito | mensaje en el chat |
| R0.2 | **piloto-con-dns** cerrado o expresamente compatible | Mark lo confirma. La última fila con esa etiqueta es del 30-sep, pero no hay acta de cierre ([ESTADO §4](ESTADO-OBSERVADO-LABORATORIO.md#4-tráfico-legítimo-kali-y-piloto-con-dns)) |
| R0.3 | Mark acepta los dos cambios de captura: anillo `-G 5` y `--disparo eventos` | mensaje en el chat |
| R0.4 | El estado del laboratorio sigue siendo el de [ESTADO-OBSERVADO-LABORATORIO.md](ESTADO-OBSERVADO-LABORATORIO.md) | §1.1, lecturas del día |
| R0.5 | Kali sin procesos de ataque | §1.1 |

### 0.1 Lecturas del día

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo (solo lecturas).

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  systemctl show ppi-motor ppi-motor-capture -p Id -p MainPID -p NRestarts -p DropInPaths -p ActiveState;
  tr \"\\0\" \" \" < /proc/\$(systemctl show -p MainPID --value ppi-motor)/cmdline; echo;
  sha256sum ~/cyberflow/scripts/engine/motor_decision.py ~/cyberflow/scripts/engine/motor_incremental.py;
  ls -d ~/cyberflow-e4 ~/feed-v2 2>&1; timedatectl show -p NTPSynchronized'"
```

- **Esperado:**
  - el motor es `~/cyberflow/scripts/engine/motor_decision.py` sin `--enforce`;
  - `DropInPaths=` vacío;
  - `motor_decision.py` empieza por `6c274d9e3529` y `motor_incremental.py` por `a403307aa5f7`;
  - `~/cyberflow-e4` y `~/feed-v2` no existen;
  - `NTPSynchronized=yes`.
- **Parada:** cualquier diferencia. Se documenta y se vuelve a leer el estado antes de seguir.

`[LAPTOP Git Bash → BASTIÓN gadmin → KALI adminatacante]` → lo ejecuto yo (lectura; queda registrado como acceso a la Kali).

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 \
  'date -u +%FT%T.%3NZ; pgrep -af \"nmap|hping|curl|dig|hydra|generar_campana\" || echo sin-procesos-de-ataque'"
```

- **Esperado:** `sin-procesos-de-ataque`.
- **Parada:** cualquier proceso listado.

## 1. Paquete de la candidata

`[LAPTOP Git Bash]` → lo ejecuto yo.

```
cd "/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa3"
git fetch origin && git status --short && git rev-parse HEAD origin/candidato/etapa3-20261102
bash deploy/etapa4/laptop/paquete_candidata.sh /c/Users/markp/cf-e4-paquete
diff <(grep -v VERSION-ETAPA4 /c/Users/markp/cf-e4-paquete/SHA256SUMS) \
     <(grep -v VERSION-ETAPA4 "/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4-preparacion-2026-11-02/evidencia/paquete/SHA256SUMS")
```

- **Esperado:**
  - `git status` vacío y los dos hashes iguales (`acc6588…`, o un descendiente que solo toque herramientas);
  - el guion termina con `ficheros: 82`;
  - `diff` sin salida. La única línea que cambia en cada construcción es `VERSION-ETAPA4` (lleva la hora): por eso el sha256 del `.tar.gz` no se compara con el de la preparación, y sí el de cada fichero.
- **Parada:**
  - `PARADA: el código difiere de ec78ca5…`;
  - cualquier diferencia en `diff`;
  - `HEAD` distinto de `acc6588` **sin** una nota de cambios publicada que lo explique.

## 2. Traslado a los tres hosts

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo.

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'mkdir -p ~/cf-e4 && ls -la ~/cf-e4'
scp -i ~/.ssh/id_ed25519 /c/Users/markp/cf-e4-paquete/cyberflow-e4-ec78ca5.tar.gz \
    /c/Users/markp/cf-e4-paquete/cyberflow-e4-ec78ca5.tar.gz.sha256 gadmin@10.10.10.30:cf-e4/
```

`[BASTIÓN gadmin]` → lo ejecuto yo (por SSH desde el portátil). Copia el paquete al Sensor1 y a srv-dmz, y lo extrae en los tres.

```
cd ~/cf-e4 && sha256sum -c cyberflow-e4-ec78ca5.tar.gz.sha256 \
  && mkdir paquete && tar -xzf cyberflow-e4-ec78ca5.tar.gz -C paquete \
  && ( cd paquete && sha256sum -c --quiet SHA256SUMS ) && cat paquete/VERSION-ETAPA4
for d in "cyberflow-to-sensor m4rk@10.10.60.11" "cyberflow-to-srv adminsrvdmz@10.10.30.10"; do
  set -- $d
  ssh -o BatchMode=yes -i ~/.ssh/$1 $2 'mkdir -p ~/cf-e4 && [ ! -e ~/cf-e4/paquete ]' || { echo "PARADA $2"; break; }
  scp -i ~/.ssh/$1 ~/cf-e4/cyberflow-e4-ec78ca5.tar.gz ~/cf-e4/cyberflow-e4-ec78ca5.tar.gz.sha256 $2:cf-e4/
  ssh -o BatchMode=yes -i ~/.ssh/$1 $2 'cd ~/cf-e4 && sha256sum -c cyberflow-e4-ec78ca5.tar.gz.sha256 \
    && mkdir paquete && tar -xzf cyberflow-e4-ec78ca5.tar.gz -C paquete \
    && ( cd paquete && sha256sum -c --quiet SHA256SUMS ) && cat paquete/VERSION-ETAPA4'
done
```

- **Esperado:** en cada host, `cyberflow-e4-ec78ca5.tar.gz: OK`, ninguna línea de error de `sha256sum -c --quiet` y `candidato=ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742`.
- **Parada:** `PARADA <host>` (ya existe `~/cf-e4/paquete`) o cualquier verificación fallida.

## 3. Respaldos (antes de cualquier cambio)

Se hacen **justo antes** de instalar, no antes. Cada respaldo es un directorio nuevo con `SHA256SUMS`, y la reversión se hace contra él.

`[BASTIÓN gadmin → SENSOR1 m4rk]` → **lo ejecutas tú**: `CON_SUDO=1` lee el ruleset nft, `/etc/sudoers.d` y `getcap`, y m4rk necesita contraseña de sudo.

```
ssh -t -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'CON_SUDO=1 bash ~/cf-e4/paquete/deploy/etapa4/sensor1/respaldo_sensor1.sh'
```

- **Esperado:** última línea `RESPALDO OK /home/m4rk/respaldos-etapa4/sensor1-<UTC>`, con `ok    ruleset nft (sudo)`.
- **Parada:** `RESPALDO INCOMPLETO` o cualquier `FALLO`.

`[BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**. adminsrvdmz tiene NOPASSWD, pero la norma reserva sudo a Mark.

```
ssh -t -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'CON_SUDO=1 bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/respaldo_srvdmz.sh'
```

- **Esperado:** `RESPALDO OK /home/adminsrvdmz/respaldos-etapa4/srvdmz-<UTC>`.
- **Parada:** `RESPALDO INCOMPLETO`.
- **Revisar a mano** en `sudoers-defaults.txt` que no haya `requiretty`: el instalador para si lo hay.

`[BASTIÓN gadmin]` → lo ejecuto yo (sin privilegios; solo copia metadatos y huellas de llaves públicas).

```
bash ~/cf-e4/paquete/deploy/etapa4/bastion/respaldo_bastion.sh
```

- **Esperado:** `RESPALDO OK /home/gadmin/respaldos-etapa4/bastion-<UTC>`.

`[DC1 dcadmin]` → **lo ejecutas tú** (sudo en DC1; no se instala nada allí). Es la lectura de referencia del ruleset de DC1, que la Etapa 4 no toca.

```
sudo nft list ruleset > ~/dc1-ruleset-$(date -u +%Y%m%dT%H%M%SZ).nft && sha256sum ~/dc1-ruleset-*.nft | tail -1
```

- **Esperado:** un fichero no vacío y su hash, que Mark anota en el chat.

## 4. Fase 4A: instalación en sombra

### 4.1 Llaves del relé v2 (bastión)

`[BASTIÓN gadmin]` → lo ejecuto yo (sin sudo: crea dos llaves ed25519 nuevas en `~/.ssh`; la parte privada no sale del bastión).

```
bash ~/cf-e4/paquete/deploy/etapa4/bastion/instalar_bastion_sombra.sh llaves
```

- **Esperado:** dos huellas `SHA256:…` (`cyberflow-feed-v2-sensor` y `cyberflow-feed-v2-srv`) y dos líneas `OK`.
- **Parada:** `PARADA … ya existe`.

### 4.2 Sensor1, fases 0–5

`[BASTIÓN gadmin → SENSOR1 m4rk]` → **lo ejecutas tú**: la fase 3 instala unidades en `/etc` y la 4 reinicia la captura y el motor, todo con sudo.

```
ssh -t -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1); echo "respaldo: $R"
  bash ~/cf-e4/paquete/deploy/etapa4/sensor1/instalar_sensor1_sombra.sh "$R" ~/cf-e4/cyberflow-e4-ec78ca5.tar.gz'
```

**Esperado**, en orden:

| Fase | Línea esperada |
|---|---|
| 0 | `OK    fase 0: respaldo, paquete, unidades base sin cambios, filtro, disco y reloj` |
| 1 | `OK    fase 1: código de ec78ca5 en /home/m4rk/cyberflow-e4/ec78ca5 (solo lectura)` |
| 2 | `motor_decision: N módulos del candidato: …`, `publicar_feed_v2: …`, `detector_rapido: …` y `OK importaciones`, seguidas de `OK    fase 2: …` |
| 3 | `OK    fase 3: unidades instaladas y verificadas (aún sin reiniciar nada)` |
| 4 | `antes: motor=<PID 24f8a80> captura=<PID>` y `OK    fase 4: … motor <PID> = candidato sin --enforce; anillo -G 5` |
| 5 | `OK    fase 5: …` y `SIGUIENTE: …` |

- **Parada:** la primera `PARADA`.
  - En las fases 0–2 no hay nada que revertir: ninguna unidad cambió. `~/cyberflow-e4` y `~/feed-v2` pueden existir ya; se conservan.
  - En las fases 3–5 se revierte con §7.3.
- **Interrupción del servicio:** el reinicio de la fase 4 detiene la captura y el motor unos segundos. Queda anotado por la línea `antes:` y por `ExecMainStartTimestamp`.

### 4.3 Clave pública del feed y llaves públicas del relé

`[BASTIÓN gadmin]` → lo ejecuto yo. Solo mueve material **público**: `pub.pem`, derivada en el Sensor1, y las dos `.pub`.

```
scp -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cyberflow-e4/pub.pem ~/cf-e4/pub.pem
openssl pkey -pubin -in ~/cf-e4/pub.pem -noout && sha256sum ~/cf-e4/pub.pem
scp -i ~/.ssh/cyberflow-to-sensor ~/.ssh/cyberflow-feed-v2-sensor.pub m4rk@10.10.60.11:cf-e4/
scp -i ~/.ssh/cyberflow-to-srv ~/cf-e4/pub.pem ~/.ssh/cyberflow-feed-v2-srv.pub adminsrvdmz@10.10.30.10:cf-e4/
```

- **Esperado:** `openssl` sin error y un hash de `pub.pem`, que se anota.
- **Parada:** `openssl` falla, porque el fichero no es una clave pública.

### 4.4 srv-dmz: agente v2 en sombra

`[BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**: crea cuentas e instala en `/usr/local`, `/opt`, `/etc`, `/var/lib` y sudoers.

```
ssh -t -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$(ls -d ~/respaldos-etapa4/srvdmz-* | tail -1); echo "respaldo: $R"
  bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/instalar_srvdmz_sombra.sh "$R" ~/cf-e4/paquete ~/cf-e4/pub.pem ~/cf-e4/cyberflow-feed-v2-srv.pub'
```

- **Esperado:** `OK    fase 0`, `OK    fase 1: …` y `OK    fase 2: agente v2 en SOMBRA arrancado; …`.
- **Parada:** cualquier `PARADA`. Si ocurre después de crear las cuentas, se revierte con §7.2.

### 4.5 Sensor1: acceso del relé v2 (solo «servir»)

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo. Sin sudo: añade **una** línea con `command=…,restrict` al `authorized_keys` de m4rk.

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1)
  bash ~/cf-e4/paquete/deploy/etapa4/sensor1/instalar_sensor1_sombra.sh llave-rele "$R" ~/cf-e4/cyberflow-feed-v2-sensor.pub'
```

- **Esperado:** `OK    llave del relé v2 añadida con comando forzado de solo lectura`.
- **Parada:** `PARADA authorized_keys cambió en más de una línea`, entre otras.

### 4.6 Bastión: relé v2 hacia srv-dmz (sin DC1)

`[BASTIÓN gadmin]` → **lo ejecutas tú** (sudo en `/opt` y `/etc/systemd`; gadmin no tiene NOPASSWD para eso).

```
R=$(ls -d ~/respaldos-etapa4/bastion-* | tail -1); echo "respaldo: $R"
bash ~/cf-e4/paquete/deploy/etapa4/bastion/instalar_bastion_sombra.sh instalar "$R" ~/cf-e4/paquete ~/cf-e4/pub.pem
```

- **Esperado:** el instalador comprueba primero que las dos llaves nuevas están limitadas (`orden no permitida` en ambos extremos). Termina con tres líneas de la traza y `OK    relé v2 entregando a srv-dmz; relé v1 intacto`.
- **Parada:**
  - `PARADA Sensor1 no limita la llave del relé…` o `srv-dmz no limita…`: la llave daría una shell. **No se sigue.**
  - `sin entregas en la traza`: se revierte con §7.1.

## 5. Verificación de la 4A

Todas son **lecturas**. Se repiten al final del periodo de observación (§5.3).

### 5.1 Servicios, versión cargada, firma, entrega y sombra

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo.

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1)
  bash ~/cyberflow-e4/ec78ca5/deploy/etapa4/sensor1/verificar_sensor1.sh "$R"'
```

- **Esperado:** `VERIFICACIÓN SENSOR1 OK`. Cubre:
  - los 7 servicios activos;
  - el motor es el candidato con `--disparo eventos` y sin `--enforce`;
  - la captura usa `-G 5`;
  - `SHA256SUMS` del candidato verifica y `~/cyberflow` está intacto;
  - las importaciones salen del candidato;
  - las decisiones traen `decision_if`, `auth_failure`, `http_vista` y `dns_vista`;
  - `motor_startup` con `disparo: eventos` y el umbral del manifiesto;
  - la vía rápida avanza;
  - el feed v2 tiene < 60 s y su firma verifica con la clave pública;
  - hay lecturas SIGUSR1 del anillo y de la vía rápida en los últimos 2 min;
  - el reloj está sincronizado;
  - el logrotate de feed-v2 está instalado.
- **INFO a anotar:**
  - decisiones con HTTP tardío excluido de la vista. Es el **rechazo del HTTP tardío**: un registro HTTP que llega > 60 s después de su ventana no entra en la vista;
  - `auth_failure` solo histórico, sin `autoriza`;
  - menciones de `dns_entropy` en el feed v2. Son propuestas sin agente DNS: **el LIMIT DNS no se aplica**.
- **Parada:** cualquier `FALLO`. Se revierte con §7, salvo que la causa sea de lectura y se documente.

`[BASTIÓN gadmin]` → lo ejecuto yo.

```
bash ~/cf-e4/paquete/deploy/etapa4/bastion/verificar_bastion.sh
```

- **Esperado:** `VERIFICACIÓN BASTIÓN OK`. Cubre:
  - el relé v2 está activo y solo tiene destino srv-dmz;
  - el relé v1 sigue activo;
  - la última entrega es de hace < 60 s;
  - la latencia traído→entregado p50/máx queda anotada;
  - el reloj está sincronizado.

`[BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuto yo (la parte sin sudo).

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/verificar_srvdmz.sh'
```

`[BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**: la traza del agente pertenece a `cfagente` (0700) y leer las reglas efectivas requiere root.

```
ssh -t -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$(ls -d ~/respaldos-etapa4/srvdmz-* | tail -1)
  CON_SUDO=1 bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/verificar_srvdmz.sh "$R"'
```

- **Esperado:** `VERIFICACIÓN SRV-DMZ OK`. **Sombra = ausencia demostrada de restricciones aplicadas:**
  - ningún proceso de agente con `--aplicar`;
  - la unidad v2 sin `--aplicar`;
  - el agente v1 *disabled/inactive*;
  - recepciones aceptadas en la traza;
  - **ningún evento `aplicacion`**;
  - sin tabla `inet cyberflow_dmz`;
  - el ruleset efectivo igual al del respaldo (salvo contadores);
  - el helper rechaza un perfil ajeno.
- **Parada:** cualquier `FALLO` en los puntos de sombra. Es la condición X2 de [SALUD-CAPTURA §4.2](SALUD-CAPTURA.md#42-durante). Se revierte inmediatamente con §7.

`[DC1 dcadmin]` → **lo ejecutas tú** (sudo en DC1).

```
sudo nft list ruleset | diff - "$(ls ~/dc1-ruleset-*.nft | tail -1)" && echo "DC1 sin cambios"
```

- **Esperado:** `DC1 sin cambios`. Las líneas `counter` pueden variar; se revisa a mano cualquier otra diferencia.

### 5.2 Captura, VLAN, capacidades, relojes, recursos y registros

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo (solo lecturas; `journalctl` es NOPASSWD).

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  F=$(ls /var/lib/ppi-motor-capture/live-*.pcap | tail -2 | head -1)
  echo "fichero cerrado: $F  tcp=$(tcpdump -r $F -nn tcp 2>/dev/null | wc -l)  vlan_tcp=$(tcpdump -r $F -nn "vlan and tcp" 2>/dev/null | wc -l)"
  ls /var/lib/ppi-motor-capture | tail -6
  pv=$(systemctl show -p MainPID --value ppi-via-rapida@ens37); t=$(pgrep -x -P $pv tcpdump)
  echo "tcpdump vía rápida PID $t usuario $(ps -o user= -p $t)"; grep -E "^Cap(Prm|Eff|Amb)" /proc/$t/status
  sudo -n journalctl -u ppi-motor-capture --since -5min -o short-iso-precise --no-pager | grep "packets captured" | tail -3
  sudo -n journalctl -u ppi-via-rapida@ens37 --since -5min -o short-iso-precise --no-pager | grep "packets captured" | tail -3
  tail -1 ~/cyberflow/logs/_state-e4/ciclos.jsonl
  du -sh ~/cyberflow/logs/motor_decision.log ~/feed-v2; df -h /home | tail -1; free -m | grep Mem; uptime
  timedatectl show -p NTPSynchronized -p TimeUSec'
```

- **Esperado:**
  - **VLAN:** `tcp` > 0. Si la captura conserva la etiqueta, `vlan_tcp` = `tcp`. Con `rx-vlan-offload` on es posible `vlan_tcp` = 0: es informativo. El filtro `tcp or (vlan and tcp)` acepta los dos casos.
  - **Anillo:** ficheros cada 5 s.
  - **Capacidades:** el tcpdump de la vía rápida corre como `m4rk` y su `CapEff` incluye `cap_net_raw`.
  - **SIGUSR1:** tres líneas `packets captured` recientes en cada unidad, con `dropped by kernel` constante.
  - **Motor:** `retraso_pcap_s` ≤ 25 en el último ciclo.
  - **Recursos:** ≥ 2 GB libres en /home.
- **Parada:**
  - sin líneas SIGUSR1: el timer no funciona, el periodo sería C3 y se corrige antes de seguir;
  - `dropped by kernel` crece: se documenta y se diagnostica; la 4B no empieza (I4);
  - sin `cap_net_raw`: la vía rápida no captura.

**Relojes de los cinco hosts.** Se usa el guion de medida del 3B (`p10b_relojes.sh`, copia idéntica en `guiones/`), que no forma parte del paquete.

`[LAPTOP Git Bash]` → lo ejecuto yo.

```
scp -i ~/.ssh/id_ed25519 "/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4-preparacion-2026-11-02/guiones/p10b_relojes.sh" gadmin@10.10.10.30:cf-e4/
```

`[BASTIÓN gadmin]` → lo ejecuto yo.

```
echo "65fecb5ac8b109c8edf7412e5aa8cd562319417a02e92b3809562a41a41f34fa  $HOME/cf-e4/p10b_relojes.sh" | sha256sum -c && bash ~/cf-e4/p10b_relojes.sh | tee -a ~/cf-e4/relojes-4a.log
```

- **Esperado:** los cinco hosts con NTP sincronizado y desfase ≤ 0,1 s.
- **Parada:** desfase > 1 s. La sesión se excluiría (OBJETIVOS v3).

### 5.3 Periodo de observación de la 4A

La 4A se da por **cerrada** solo cuando se cumple todo esto:

1. §5.1 y §5.2 sin `FALLO`, al principio **y al final** del periodo.
2. **≥ 60 min** de `salud_captura.py` (comandos en [SALUD-CAPTURA §5](SALUD-CAPTURA.md#5-comandos-de-medida), con `<DIR>` = `/home/m4rk/cf-e4/4a`) sin tramos C2 ni C3. Los C1 se anotan.
3. **Una rotación diaria** de `eve.json` (Suricata, `copytruncate`) y de `motor_decision.log` (cyberflow, diaria) **dentro** del periodo. Después de cada rotación:
   - hay decisiones nuevas;
   - el feed v2 sigue fresco;
   - la vía rápida avanza.

   Se lee con `ls -la --time-style=full-iso /var/log/suricata/ ~/cyberflow/logs/` y repitiendo §5.1.
4. **Línea base SIGUSR1** del anillo real: `D` del tcpdump del anillo durante todo el periodo. Si crece, es el primer dato real de pérdida del socket, y se diagnostica antes de la 4B.
5. Registro del **volumen**: MB/h de `motor_decision.log` y de `~/feed-v2`. Se compara con `maxsize` del logrotate (200M) para fijar el riesgo de rotación dentro de la 4C.

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo. Directorio de la 4A, sin tocar servicios.

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '[ ! -e ~/cf-e4/4a ] && mkdir -p ~/cf-e4/4a/salud && echo listo'
```

El muestreador de la 4A es el de [SALUD-CAPTURA §5](SALUD-CAPTURA.md#5-comandos-de-medida) **sin** la línea `--archivador <DIR>/archivo-pcap`, porque en la 4A no se archiva. Las otras fuentes quedan iguales.

## 6. 4B y 4C

- **4B:** [PROTOCOLO-4B-CONTROL.md](PROTOCOLO-4B-CONTROL.md).
- **4C:** [PROTOCOLO-4C-CAMPANA-A.md](PROTOCOLO-4C-CAMPANA-A.md), con el orden publicado en [ORDEN-4C.md](ORDEN-4C.md).
- **Observación DNS de 7 días**, aparte y pasiva: [OBSERVACION-DNS-ETAPA4.md](OBSERVACION-DNS-ETAPA4.md).

Ninguno se inicia sin la 4A cerrada (§5.3) y una petición expresa de Mark para cada uno.

## 7. Reversión

**No depende de git.**

- Devuelve las unidades al contenido **copiado en el respaldo** y cada unidad a su `is-enabled`/`is-active` del respaldo.
- Devuelve el motor al `ExecStart` base: 24f8a80 en `~/cyberflow`, que la instalación no tocó.
- **No borra evidencia:**
  - `~/cyberflow-e4`, `~/feed-v2`, `logs/_state-e4` y `~/relay-v2` se conservan;
  - la traza del agente se copia antes de retirar `/var/lib/cyberflow`;
  - las llaves nuevas del bastión no se borran: quedan inútiles al retirar sus líneas de `authorized_keys`.

**Orden:** primero el relé (deja de entregar), después srv-dmz y por último Sensor1. Todos los pasos son de Mark: usan sudo.

### 7.1 Bastión

`[BASTIÓN gadmin]` → **lo ejecutas tú**.

```
R=$(ls -d ~/respaldos-etapa4/bastion-* | tail -1); bash ~/cf-e4/paquete/deploy/etapa4/bastion/revertir_bastion.sh "$R"
```

- **Esperado:** `REVERSIÓN OK (traza en ~/relay-v2 conservada)`.
- **Parada:** `DIFERENCIA …`. Se informa y no se sigue a ciegas.

### 7.2 srv-dmz

`[BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → **lo ejecutas tú**.

```
ssh -t -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$(ls -d ~/respaldos-etapa4/srvdmz-* | tail -1); bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/revertir_srvdmz.sh "$R"'
```

- **Esperado:** `REVERSIÓN OK (traza del agente copiada en /home/adminsrvdmz/respaldos-etapa4/srvdmz-evidencia-<UTC>)`.
- **Parada:** `DIFERENCIA ruleset` o `sudoers.d`. Se revisa a mano antes de seguir.

### 7.3 Sensor1

`[BASTIÓN gadmin → SENSOR1 m4rk]` → **lo ejecutas tú**.

```
ssh -t -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1); bash ~/cf-e4/paquete/deploy/etapa4/sensor1/revertir_sensor1.sh "$R"'
```

**Esperado:** `REVERSIÓN OK (evidencia conservada en ~/cyberflow-e4, ~/feed-v2 y logs/_state-e4)`. Comprueba:

- cada unidad con el estado del respaldo;
- las unidades base iguales byte a byte;
- sin drop-ins;
- la `cmdline` del motor igual a la del respaldo;
- la captura en `-G 15`;
- `~/cyberflow` igual a su hash;
- `authorized_keys` restaurado.

**Parada:** `DIFERENCIA …`.

### 7.4 Comprobación posterior

Son lecturas de §0.1 y del estado observado.

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo.

```
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  tr "\0" " " < /proc/$(systemctl show -p MainPID --value ppi-motor)/cmdline; echo
  grep "\"event\": \"motor_startup\"" ~/cyberflow/logs/motor_decision.log | tail -1 | cut -c1-300
  systemctl show ppi-motor ppi-motor-capture -p Id -p DropInPaths -p NRestarts
  ls ~/cyberflow-e4 ~/feed-v2 | head'
```

- **Esperado:**
  - el motor vuelve a `~/cyberflow/scripts/engine/motor_decision.py` sin `--disparo`;
  - `motor_startup` con `procesamiento: incremental` y **sin** `disparo: eventos`;
  - `DropInPaths=` vacío;
  - la evidencia presente.

## 8. Qué está probado y qué no

| Elemento | Estado |
|---|---|
| Paquete (82 ficheros, código = ec78ca5) | **Preparado y probado offline** (`evidencia/paquete/`) |
| Unidades: sintaxis, `ExecStart` efectivo con el drop-in sobre la unidad base observada, origen de las importaciones (positivo y negativo) | **Preparado y probado offline**, `systemd-analyze` en contenedor (`evidencia/banco/ensayo-unidades-importaciones.txt`) |
| SIGUSR1 sin interrumpir la captura (anillo `-G` + `-Z`, tubería, `R = C + D`) | **Preparado y probado offline** (`evidencia/banco/ensayo-tcpdump-estadisticas.txt`) |
| `/proc/<pid>/io` de la tubería | **Pendiente en vivo** (no existe en WSL2) |
| Guiones de respaldo, instalación, verificación y reversión | Sintaxis (`bash -n`, shellcheck) y fases sin sudo **probadas offline**; las fases con sudo **pendientes de instalación** |
| Unidades base, procesos, hashes, sudo, cadena v1 | **Verificado mediante lectura** el 2-nov (`evidencia/lectura-laboratorio/`) |
| Reglas nft de srv-dmz y DC1; `Defaults` de sudoers en srv-dmz | **Pendiente**: requieren sudo de Mark (§3) |
| Línea base SIGUSR1 del anillo real, descartes de Suricata, `rx_dropped` | **Pendiente de medición en vivo** ([SALUD-CAPTURA §6](SALUD-CAPTURA.md#6-qué-queda-pendiente-de-medir-en-vivo)) |
