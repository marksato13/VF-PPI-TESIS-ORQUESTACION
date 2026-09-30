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
