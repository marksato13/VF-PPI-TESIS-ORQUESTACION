# Diseño de enforcement — acción real (permitir / limitar / bloquear)

**Estado:** diseño acordado, **pendiente de implementar** (objetivo v1.1). Resuelve
la *decisión 1* del `ESTADO.md` ("¿el bloqueo es demostrativo o corta de verdad?").

**Principio:** el sistema **no se queda en alerta**: toma acción (PERMIT / LIMIT /
BLOCK). Pero con espejo SPAN el sensor **observa, no está en el camino**, así que la
acción se aplica **donde el tráfico pasa**, no en el kernel del sensor.

---

## 1. Dónde actúa (decisión)

Tres lugares posibles; se elige **A**:

| | A · host destino | B · gateway pfSense | C · sensor en línea |
|---|---|---|---|
| Protege | los hosts gestionados (DMZ) | toda la red | el segmento |
| Corta lateral | no | sí | sí (ese segmento) |
| Radio de daño si falla | bajo (un host) | alto (HA producción) | alto (SPOF en el camino) |
| Gobernanza | ✅ servidores propios | ⚠️ infra ajena, permiso explícito | ⚠️ re-cablear red viva |
| Cambia premisa de la tesis | no | poco | sí (deja de observar) |

**Elegido: A (host destino) + nivel LIMIT.** Es acción **real** (corta/limita en el
activo protegido), **no toca** el pfSense HA ni re-cablea, bajo radio de daño y
reversible. Eleva la afirmación de "demostrativo" a **"real, alcance host"**.

- **B (gateway)** = mejora de red-completa, **gated** a permiso explícito de Mark
  sobre el firewall + tabla `pf` dedicada + rollback probado. No para v1.x.
- **C (inline)** = trabajo futuro; cambia la premisa y mete un SPOF en producción.

---

## 2. Modelo multi-host: **un feed / N agentes (pull)**

El sensor **publica una lista firmada**; cada host la **consulta y aplica** en su
propio kernel. El sensor **no** guarda credenciales de los hosts ni un inventario.

```
   SENSOR (SPAN, observa y decide)
   motor: por entidad -> PERMIT / LIMIT / BLOCK
     │ firma y publica el FEED (solo-lectura, VLAN gestion):
     │   [{ ip, accion, hasta(epoch), alcance, motivo }, ...]
     └──── pull cada 5-10 s (el HOST inicia, verifica firma) ────┐
        ▼                     ▼                     ▼
   srv-dmz .30.10        host B .30.11        host C ...
   agente reconcilia     agente               agente
   nftables + tc         (idem)               (idem)
   aplica en SU ingress (desde la IP atacante)
```

**Agente (bucle idempotente):** pull → verifica firma → filtra por `alcance` y por la
**lista de nunca-bloquear** (gateways/DNS) → **reconcilia** su estado local con el
feed (BLOCK = set nftables con `timeout`; LIMIT = `ip saddr X limit rate … else
drop`) → las entradas caducadas se quitan solas.

**Propiedades:** alta de host = instalar agente + clave pública (cero cambios en el
sensor); host caído = se pone al día al volver; superficie mínima (sensor solo
publica; si lo comprometen no tiene escritura directa en los hosts).

### Alcance por verdicto
- **BLOCK → global** (`alcance: all`): un atacante confirmado es malo en todos los
  hosts → corta el pivote lateral.
- **LIMIT → global** también (limitar a un abusivo en todos lados es barato).
- Configurable en el `.toml` (permite dirigido `alcance:[host]` para casos dudosos).

---

## 3. Reglas transversales de seguridad

- **Compuerta de calibración:** sin `calibrado_en_esta_red=true` no se actúa (ya
  existe el interlock en `responder_iptables`). Se aplica también a publicar el feed.
- **Lista de nunca-bloquear:** gateways, DNS, el propio sensor, el bastión (ya existe).
- **Nunca `∞` automático:** timeouts escalados (p.ej. 300 s → 1800 s por reincidencia);
  `∞` solo con revisión humana.
- **Firma del feed:** ed25519, clave privada en el sensor (0600), pública en los hosts.
- **Auditoría:** cada acción a `logs/` (ip, acción, verdicto, motivo, hasta) + comando
  de desbloqueo manual documentado.

---

## 4. Qué ya existe vs qué es nuevo

| Pieza | Estado |
|---|---|
| Motor con `--enforce` + nftables `ppi_enforce` + expiración | ✅ existe (aplicaba en el sensor = demostrativo) |
| Interlock de calibración (no corta sin calibrar) | ✅ existe (`responder_iptables`) |
| Lista de nunca-bloquear (gateways/DNS) | ✅ existe |
| Heurísticos deterministas (brute-force, http-abuse, port-scan) | ⚠️ parcial (formalizar los 3 con umbrales versionados) |
| **Feed firmado + agente pull en los hosts** | ❌ nuevo (núcleo de este diseño) |
| **Nivel LIMIT (rate-limit)** | ❌ nuevo |
| **Aplicar en el host destino (no en el sensor)** | ❌ nuevo |

---

## 5. Lo que falta DECIDIR antes de implementar

1. **Score → acción (el segundo umbral).** Hoy el modelo da un solo corte
   (anómalo sí/no). Para tres acciones desde el score hacen falta **dos cortes**, y
   el del medio (PERMIT|LIMIT|BLOCK) **no está calibrado**. Decidir: ¿el score da
   solo PERMIT/anómalo y el LIMIT↔BLOCK lo deciden los **heurísticos + severidad**,
   o se **bandea el score** (y cómo se calibra esa banda)?
2. **Umbrales de los heurísticos** (la imagen: ≥100 req/30 s puerto 80; ≥15/60 s
   puerto 22; ≥20 puertos/10 s) → confirmarlos y versionarlos, y cuáles dan LIMIT
   vs BLOCK.
3. **Mecanismo de LIMIT:** nftables `limit rate` (simple, integrado) vs `tc/qdisc`
   (shaping más fino). Recomendado empezar con nftables.
4. **Transporte del feed:** ¿endpoint HTTPS de solo-lectura en el panel del sensor,
   o fichero firmado que los hosts traen por `rsync/scp` (pull)? y cómo se autentica
   el pull.
5. **Timeouts:** valores exactos y la lógica de reincidencia (escalado).
6. **Inventario de agentes:** qué hosts llevan agente (los de la DMZ) y su alta.
7. **Alcance por defecto:** confirmar global para BLOCK y para LIMIT.
8. **Rollback/operación:** desbloqueo manual, y qué pasa si el feed no se puede leer
   (fail-open vs fail-closed en el host).

---

## 6. Plan de implementación (v1.1, cuando se decida lo de §5)

1. Definir el formato del feed + firma (esquema JSON + ed25519).
2. `publicar_feed.py` en el sensor (a partir de las decisiones del motor + heurísticos).
3. `agente-enforce` (systemd timer) para los hosts: pull, verifica, reconcilia
   nftables/tc; lista de nunca-bloquear local.
4. Nivel LIMIT en el agente.
5. Pruebas: unit (reconciliación idempotente, firma, nunca-bloquear) + e2e con la
   Kali (que un BLOCK real corte el ataque en el host, medido).
6. Documentar y, si se quiere, subir a `v1.1`.

---

## 7. Alertas y notificación

**Regla de diseño:** las alertas fluyen **hacia adentro**, a un concentrador
(Wazuh), **no hacia afuera** desde el sensor. El sensor está en VLAN60 **sin salida
a Internet**, y eso **no es una limitación sino una propiedad de seguridad**: el
sensor observa pero **no puede ser un pivote de exfiltración**. Por eso **Telegram
desde el sensor queda descartado** (exigiría abrir egress y sacaría IPs internas y
scores a un tercero).

**Por capas:**

1. **Canal primario — Wazuh como concentrador** (el previsto en VLAN60): el sensor
   **emite** por **syslog/agente**, todo **intra-VLAN60 (sin egress)**. Wazuh aporta
   tablero, correlación e histórico; es el hub de alertas.
2. **Ya disponible hoy** (sin esperar a Wazuh): `motor_decision.log` /
   `predictor.log` (registro local estructurado) y el **panel de solo-lectura** que
   muestra decisiones/alertas en vivo. Visibilidad inmediata, cero egress.
3. **Push externo (al teléfono), si de verdad se quiere:** sale **desde Wazuh** (o un
   notificador dedicado con **egress estrecho y auditado**), **nunca desde el
   sensor**, y **sanitizado** (nada de IPs internas ni scores crudos; un aviso
   mínimo tipo «N alertas, severidad alta, revisa la consola»). Preferir **correo
   interno/corporativo** antes que un bot público. *(Este push queda como opcional,
   a decidir; el sistema no lo necesita para actuar.)*

En la imagen de arquitectura, la caja «2) ALERTA + LOG» pasa a ser **Wazuh + log +
panel**, no Telegram.

---

## 8. Posicionamiento: complementa, no reemplaza

CyberFlow **se enchufa en el stack de seguridad, no lo suplanta** — y la propia
arquitectura lo demuestra: **consume** Suricata (`eve.json`) y **emite** hacia Wazuh
(alertas adentro, no afuera), sin duplicar lo que esas herramientas ya hacen.

| Capa | Herramienta | Rol |
|---|---|---|
| Firmas / amenazas conocidas | **Suricata** | CyberFlow lo **consume** (`eve.json`), no lo reemplaza |
| SIEM / logs / correlación / cumplimiento / EDR | **Wazuh** | el **hub**: CyberFlow le **emite** sus veredictos |
| Detección **conductual de lo desconocido** + respuesta temprana | **CyberFlow** | el nicho: modelo *one-class* por entidad, **recalibrado a la red** (92,4 %→4,45 %), con *lead-time* y acción graduada |

**Lo que CyberFlow NO intenta ser** (y por eso complementa): gestor de logs, EDR de
host, motor de cumplimiento, tablero-para-todo → eso es Wazuh. **Lo que aporta y los
demás no:** anomalía conductual no supervisada, **calibrada a la red concreta**, con
respuesta graduada, **alimentando** al SIEM.

**Valor para la tesis:** (a) honestidad — ocupa un nicho concreto y medible, no
compite con productos maduros; (b) adopción real — un equipo con Suricata+Wazuh lo
**añade** sin arrancar nada (clave para el **TAM**: utilidad + facilidad de
integración); (c) verificable, no declarativo — la complementariedad está en la
arquitectura (consume Suricata, emite a Wazuh, aislado sin egress).

> Replicar este posicionamiento en el `README` del producto y en el **artículo**
> (sección de contribución/alcance).

---

## 9. Caducidad y escalado

**Principio:** el coste de **equivocarse** (falso positivo) debe estar **acotado en
el tiempo**; el coste de ser un **atacante reincidente** debe **crecer**. Asimétrico
a propósito.

### La escalera (por IP origen)

| Nivel | Disparador | Acción | Duración |
|---|---|---|---|
| 1 | 1ª vez anómalo (score) | **LIMIT** | 300 s |
| 2 | heurístico confirmado, o repite | **BLOCK** | 300 s |
| 3 | 2ª reincidencia (< 24 h) | BLOCK | 1800 s |
| 4 | 3ª+ reincidencia (< 24 h) | BLOCK | 3600 s (tope automático) **+ marcar para revisión humana** |
| ∞ | — | permanente | **SOLO un humano**, tras revisar la cola de candidatos |

### Reglas que la hacen segura
1. **Nunca `∞` automático.** El tope de la máquina es 3600 s; lo permanente lo
   decide una persona desde el panel/Wazuh sobre la **cola de candidatos** (nivel 4).
2. **Caducidad = fail-safe.** Toda acción automática lleva `timeout` en el set de
   nftables → se quita sola. Si el sensor o el feed mueren, los bloqueos **expiran
   igual**; nada queda colgado para siempre por un fallo.
3. **Decaimiento del contador.** Si una IP se porta bien **24 h**, su contador de
   reincidencia **se reinicia** → la próxima ofensa vuelve a 300 s. Un falso
   positivo aislado no escala a esa IP durante semanas.
4. **La lista de nunca-bloquear manda siempre** (gateways, DNS, sensor, bastión).

### Justificación (con el FPR medido)
- 4,45 % de FPR ≈ **1 de cada ~22** ventanas marcadas es falsa. Un `∞` sobre eso
  deja un host legítimo fuera **indefinidamente** → para disponibilidad, peor que el
  ataque.
- **300 s primero** acota el daño de un falso positivo a **≤ 5 min** (y con LIMIT ni
  corta: degrada).
- La escalera **sube solo con reincidencia**, que un falso positivo casual no cumple;
  un atacante persistente sí → a él le sube el coste mientras el legítimo apenas lo nota.
- El **humano** entra solo para lo irreversible (`∞`).

### Estado necesario
Un **estado por IP** (contador de reincidencia + último visto) que **persista** entre
bloqueos, para saber el nivel. Vive en el sensor (junto al feed); el `timeout` de
nftables borra en cada host.
