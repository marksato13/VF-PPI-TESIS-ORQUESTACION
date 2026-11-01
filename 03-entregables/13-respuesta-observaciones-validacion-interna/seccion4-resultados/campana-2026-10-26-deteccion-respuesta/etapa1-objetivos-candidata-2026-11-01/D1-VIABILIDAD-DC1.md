# D1 · Viabilidad de la respuesta DNS en DC1 (versión 3, 1-nov-2026)

**Alcance acordado (usuario):** el escenario DNS sigue dirigido a **DC1, 10.10.10.20**. La respuesta se aplica **en DC1**, limitada al **servicio DNS** y al **origen señalado**. No se cambia el destino ni se reduce a solo detección.

**Qué se hizo en este encargo:**

- consultas de **solo lectura** en DC1 con la cuenta documentada `dcadmin`, a través del bastión;
- consultas anónimas de solo lectura desde el bastión (LDAP rootDSE, banner SSH y consultas DNS normales);
- lectura de documentación oficial.

No se instaló nada, no se modificó DC1, no se creó ninguna regla y el agente no existe todavía. La salida literal y los scripts usados están en [`d1-dc1/`](d1-dc1/).

> **Estado:** D1 queda **resuelta en cuanto al punto de aplicación (DC1) y al mecanismo propuesto (nftables en DC1, limitado a UDP/TCP 53 y al origen)**. **No está lista para desplegar:** faltan las comprobaciones técnicas de §6 y la autorización de Mark para instalar un agente en el controlador de dominio.

## 1. Hallazgo que cambia la comparación anterior

La versión 2 suponía que DC1 era un Windows Server y recomendaba una política de resolución de consultas DNS o una regla del Firewall de Windows. **Esa suposición era falsa.**

| Comprobación (1-nov-2026, solo lectura) | Resultado | Evidencia |
|---|---|---|
| Sistema operativo de DC1 | **Debian GNU/Linux 13 (trixie)**, kernel 6.12.96 | `d1-dc1/lectura-dc1-salida.txt` |
| Controlador de dominio | **Samba 4.22.10** (`samba-ad-dc` activo), rootDSE `vendorName: Samba Team`, `server role = active directory domain controller` | ídem; `d1-dc1/lectura-desde-bastion.txt` |
| Servidor DNS | **DNS interno de Samba** (`server services` incluye `dns`; BIND9 no instalado). Escucha en 10.10.10.20:53 UDP/TCP y en loopback. | ídem |
| Reenviador | `dns forwarder = 10.10.10.1` | ídem |
| Parámetros DNS de Samba | `testparm -sv` solo expone `allow dns updates`, `dns forwarder`, `dns port`, `dns proxy`, `dns update command`, `dns zone scavenging` y `dns zone transfer clients allow/deny`. **Ninguno restringe consultas por cliente.** | ídem |
| nftables | **nftables 1.1.3** instalado; módulo `nf_tables` cargado; **conjunto de reglas vacío** (0 líneas); `nftables.service` deshabilitado e inactivo | ídem |
| Dependencias de un agente | Python 3.13.5, OpenSSL 3.5.6 y NTP sincronizado | ídem |
| Segundo DC | **10.10.10.21 (vm-ad-dc2)**, también Samba 4.22.10/Debian. Los clientes, incluida la Kali, tienen `nameserver 10.10.10.20` y `10.10.10.21`. | `d1-dc1/lectura-desde-bastion.txt`; `/etc/resolv.conf` de la Kali |
| Generador del escenario | consulta **explícitamente** `@10.10.10.20` (`dig @10.10.10.20 …`) | scripts de la campaña |

**Consecuencia:** las opciones Windows no son aplicables en este laboratorio. Pasa a recomendarse la tercera vía que permitía el encargo: «otra alternativa justificada que conserve el alcance».

## 2. Comparación de mecanismos en DC1

| Opción | Aplicable aquí | Acción posible | Valoración |
|---|---|---|---|
| A1. Política de resolución de consultas de Windows DNS | **No**: DC1 no es Windows | — | descartada por incompatibilidad |
| A2. Regla del Firewall de Windows | **No**: DC1 no es Windows | — | descartada por incompatibilidad |
| **A3. nftables en DC1, tabla propia, solo `udp/tcp dport 53` y solo el origen señalado** | **Sí**: nft 1.1.3 instalado, módulo cargado y reglas vacías (comprobado) | denegar (drop) o limitar la tasa por origen; caducidad nativa del kernel | **recomendada** |
| A4. Configuración del DNS interno de Samba | No hay parámetro de ACL de consultas por cliente (comprobado con `testparm`; la documentación de Samba no lo describe). Cambiar `smb.conf` exige reiniciar el DC. | — | descartada |
| A5. Pasar el DC a BIND9_DLZ (ACL o `blackhole`) | Técnicamente posible, pero cambia el backend DNS del dominio | denegar por ACL | descartada: cambio de infraestructura desproporcionado |
| B. pfSense | Fuera de la norma (no se toca el cortafuegos central) | — | no recomendada |
| C. Resolver propio como destino | Cambia el escenario | — | descartada por el usuario |
| D. Solo detección | No cumple el objetivo | — | descartada por el usuario |

## 3. Propuesta A3 (diseño; no implementado)

### 3.1 Recepción y verificación del feed firmado

- El relé del bastión (`relay-feed.sh`, hoy: sensor → bastión → srv-dmz) añade **un segundo destino**: `feed.json` y `feed.sig` se copian por `scp` a DC1, a una cuenta **dedicada sin privilegios** (propuesta: `cfdns`), con una llave propia del bastión (propuesta: `cyberflow-to-dc1`).
- El agente de DC1 verifica la firma **ed25519** con la clave pública del sensor, igual que el agente actual (`feed.verificar` → `openssl pkeyutl -verify`; OpenSSL 3.5.6 está presente).
- **Fail-safe:** si la firma no verifica o el feed no se puede leer, el agente no cambia nada. Las entradas ya aplicadas siguen caducando solas (§3.5).

### 3.2 Identificación del origen y del servicio

- El agente solo aplica entradas vigentes (`hasta > ahora`) cuyo **alcance** sea DNS.
- Hoy el publicador escribe `alcance = "all"` en todas las entradas. La candidata debe publicar `alcance = "dns"` para las acciones de `dns_entropy` (cambio del contrato del feed, Etapa 3). Así, un BLOCK por `brute_force` contra la Kali **no** deniega su DNS en DC1, y un LIMIT por `dns_entropy` no se traduce en un bloqueo total en srv-dmz.
- **Nunca se restringe** a: DC1 y DC2 (10.10.10.20 y .21), bastión, sensores, pfSense ni las pasarelas de VLAN. La lista NUNCA_BLOQUEAR actual **no incluye 10.10.10.21**: hay que añadirlo en la candidata.
- Solo IPv4: el escenario y el feed son IPv4. IPv6 queda fuera y se declara.

### 3.3 Acción y diferencia con LIMIT y BLOCK en srv-dmz

| | srv-dmz hoy (`agente_enforce.py`, 2985c123) | DC1 propuesto |
|---|---|---|
| BLOCK | `ip saddr @cyberflow_bloqueados drop`: **todo** el tráfico del origen | **DNS-DENEGAR:** `ip saddr @cf_dns_denegar meta l4proto {udp, tcp} th dport 53 drop`. Solo el DNS del origen; Kerberos, LDAP y SMB no se tocan. |
| LIMIT | `ip saddr @cyberflow_limitados limit rate over 100/second drop`: un **único cubo compartido** por todas las IPs limitadas | **DNS-LIMITAR:** límite **por origen** con un set dinámico (`update @cf_dns_tasa { ip saddr limit rate over N/second }`), solo en el puerto 53. N está **por fijar**. |
| Caducidad | elementos con `timeout` nativo | igual: elementos con `timeout` nativo |

Notas:

- **nftables sí permite limitar la tasa**, así que en DC1 un LIMIT es técnicamente posible: no hace falta convertirlo en denegación. Pero un LIMIT **solo es eficaz si N separa el generador del uso legítimo**. En el 3B, `dns_entropy` disparó con entre 24 y 52 consultas por ventana: a ese ritmo, un límite de unas pocas consultas por segundo podría no frenar nada.
- **N se fija antes de congelar**, a partir de la tasa DNS por cliente medida en el control normal. Si ningún N separa ambos tráficos, el episodio **falla E3** y se publica así. No se cambia en silencio a denegar.
- La **asignación de acción** (que `dns_entropy` produzca DNS-LIMITAR o DNS-DENEGAR) es un parámetro de la candidata que se fija antes de congelar.
- **drop** (descarte silencioso) en lugar de **reject**: el cliente agota su espera y su resolver pasa a DC2. Esto protege la resolución de un cliente señalado por error, pero el generador, que consulta `@10.10.10.20` de forma explícita, sí queda afectado. El efecto se mide en el generador y en el SPAN, no por un código REFUSED.

### 3.4 Registro de la aplicación y verificación de que la regla existe

- Por cada ciclo, una línea JSON con: la hora del commit `nft -f -` y su código de retorno, el lote aplicado y la **relectura** `nft -j list set inet cyberflow_dns …` que demuestra que el elemento existe y con qué `timeout`.
- Contadores (`counter`) en las dos reglas: paquetes y bytes descartados por origen.
- Estos campos son la t_apl real (D7). Sin ellos, E2 es indeterminado.

### 3.5 Caducidad y retirada, incluidos fallos y reinicios

- **Caducidad nativa:** cada elemento entra con `timeout` = `hasta − ahora`. El kernel lo retira aunque el agente falle (documentación de *sets* de nftables: «elements can be added with a timeout»).
- **Nunca se alarga ni se acorta** un `timeout` aplicado, salvo por un feed firmado posterior (misma regla que el agente actual).
- **Reinicio de DC1:** `nftables.service` está deshabilitado (comprobado), así que la tabla **no persiste**: tras un reinicio no queda ninguna restricción (fallo abierto). Al volver, el agente reaplica solo las entradas aún vigentes del feed, con su resto de tiempo.
- **Agente caído o feed obsoleto:** las entradas existentes caducan solas; no se añaden nuevas.
- **Retirada manual (Mark):** `sudo nft delete table inet cyberflow_dns`, que borra solo la tabla del agente.

### 3.6 Cómo se evita afectar al DNS legítimo y a los demás servicios de DC1

- Las reglas solo coinciden con `ip saddr ∈ set` **y** con el puerto de destino 53.
- El resto de servicios del DC no se tocan: 88, 135, 389, 445, 464, 636, 3268 y los demás.
- Las consultas salientes de DC1 a su reenviador 10.10.10.1 no coinciden: entran como respuesta, con puerto de origen 53.
- Tabla propia (`inet cyberflow_dns`) en el gancho `input`, con una sola cadena. No se vacían ni se modifican otras tablas, y hoy no hay ninguna.
- La replicación entre DC1 y DC2 y la gestión (bastión y sensor) están en NUNCA_BLOQUEAR.
- **E4:** clientes de control resuelven contra DC1 durante toda la campaña B, y sus fallos se comparan con una línea base sin agente.

### 3.7 Cómo se comprueban el efecto y la recuperación (campaña B, cuando se autorice)

- **Efecto (E3):** después de t_apl, el generador registra tiempos de espera o caída de la tasa de respuesta de `@10.10.10.20` **mientras sigue consultando**. El SPAN muestra consultas del origen a DC1 sin respuesta y los contadores nft suben.
- **Recuperación (E5):** al caducar el elemento, la relectura del set ya no contiene el origen y una consulta de control del origen vuelve a resolverse antes del episodio siguiente (D5).

### 3.8 Permisos, dependencias y reversión

| Necesidad | Detalle |
|---|---|
| Permisos | Cuenta `cfdns` sin shell interactiva. `sudoers` limitado a `/usr/sbin/nft -f -` y `/usr/sbin/nft -j list table inet cyberflow_dns` (el mismo patrón «se eleva nft, no el proceso» del agente de srv-dmz). **No se usa `dcadmin`**, que tiene `sudo` NOPASSWD sobre todo (comprobado): DC1 es un activo de nivel 0. |
| Dependencias | Python 3, nft y OpenSSL, ya presentes; un timer systemd del agente; la clave pública del feed; el destino adicional en el relé del bastión y la llave `cyberflow-to-dc1`. |
| Instalación | Prepararla le corresponde a Claude; ejecutarla con sudo, a Mark. Solo antes de la campaña B y con su autorización. |
| Reversión | `systemctl disable --now` del timer; `nft delete table inet cyberflow_dns`; borrar la cuenta, sudoers y la llave; quitar el destino del relé. Ningún cambio en Samba ni en `smb.conf`. |

## 4. Respaldado por documentación frente a comprobado en este laboratorio

| Afirmación | Documentación oficial | Comprobado aquí |
|---|---|---|
| DC1 es Samba 4.22.10 sobre Debian 13 con DNS interno | — | **sí** (lectura) |
| El DNS interno de Samba no tiene ACL de consultas por cliente | la sección *Limitations* de la wiki y `smb.conf(5)` no la describen | **sí** para los parámetros expuestos (`testparm -sv`) |
| nft admite elementos con `timeout` que el kernel retira | **sí** (wiki de nftables, *Sets*) | nft 1.1.3 presente; **no ensayado** |
| nft admite limitar la tasa por origen con un set dinámico | **sí** (wiki de nftables, *Meters*: `update @set { ip saddr limit rate … }`) | **no ensayado** |
| Una regla `input` de nft con puerto 53 descarta las consultas antes de llegar al proceso de Samba | comportamiento general de netfilter | **no ensayado** |
| La tabla no persiste tras reiniciar | — | `nftables.service` deshabilitado: **sí**; reinicio **no ensayado** |
| Los clientes legítimos pasan a DC2 cuando DC1 no responde | comportamiento del resolver con dos `nameserver` | resolv.conf con dos servidores: **sí**; tiempo de conmutación **no medido** |

## 5. Conclusión para la matriz

- **D1 · punto de aplicación:** DC1. **Resuelta.**
- **D1 · mecanismo propuesto:** nftables en DC1, limitado a UDP/TCP 53 y al origen, con caducidad nativa. **Recomendado; viabilidad documental y de inventario confirmada.**
- **D1 · compatibilidad técnica concreta:** **pendiente** (§6).
- **D1 · despliegue:** **autorización futura** de Mark. No está listo para desplegar.

## 6. Qué falta comprobar exactamente (Etapa 2, offline o en sombra, sin tocar DC1 hasta que se autorice)

1. Ensayar el conjunto de reglas propuesto con nft 1.1.3 **fuera de DC1**, en un espacio de nombres de red o una VM Debian 13: sintaxis, `timeout`, límite por origen, contadores y relectura `-j`.
2. Comprobar en ese ensayo que un servidor DNS escuchando en :53 deja de responder **solo** al origen del set, y que los demás orígenes y puertos siguen respondiendo.
3. Fijar N (DNS-LIMITAR) a partir de la tasa DNS por cliente del control normal, o decidir que `dns_entropy` → DNS-DENEGAR. Debe quedar escrito antes de congelar.
4. Cambio del contrato del feed: `alcance = "dns"` para `dns_entropy`, y añadir 10.10.10.21 a NUNCA_BLOQUEAR. Rama candidata, con pruebas.
5. Agente de DC1 en la rama candidata: el agente actual con las reglas de §3.3, filtrado por alcance y registro D7, con pruebas unitarias del plan nft (sin ejecutarlo).
6. Medir el tiempo que tardan los clientes en pasar a DC2 (solo con la autorización de la campaña B o de un control).
7. En DC1, y solo cuando Mark lo autorice: instalar la cuenta, sudoers, la llave y el timer; hacer una **prueba en seco** (`nft -c -f`, que comprueba sin aplicar); y después el control sin ataques.

## Referencias oficiales

- Samba Wiki, *Samba Internal DNS Back End*, sección *Limitations*: https://wiki.samba.org/index.php/Samba_Internal_DNS_Back_End
- Samba Wiki, *The Samba AD DNS Back Ends*: https://wiki.samba.org/index.php/The_Samba_AD_DNS_Back_Ends
- Samba, `smb.conf(5)`: https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html
- nftables wiki, *Sets* (flag `timeout`, `timeout` por elemento): https://wiki.nftables.org/wiki-nftables/index.php/Sets
- nftables wiki, *Meters* (límite por origen con set dinámico `update @set { ip saddr limit rate … }`): https://wiki.nftables.org/wiki-nftables/index.php/Meters
