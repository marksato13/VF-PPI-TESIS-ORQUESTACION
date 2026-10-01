# Traspaso — CyberFlow (tesis PPI)

**Para:** el agente que continúe este trabajo.
**Fecha del traspaso:** 1 de octubre de 2026.
**Estado en una frase:** sistema desplegado y sano sobre tráfico real; el piloto
superó el bloqueo histórico, la recalibración bajó el FPR **92,4 % → 4,45 %**, la
Kali midió TPR **69 % global** y el modelo está congelado y versionado en `v1.0.0`.
El enforcement está **vivo** y ya aplicó LIMIT automático ante una campaña real;
falta demostrar un BLOCK automático y resolver DNS-entropy.

> Lee también, en este repo: `ESTADO.md` (estado vivo), `PLANIFICACION.md` (plan
> maestro y reglas), `04-evidencias/cyberflow/` (evidencia fechada, incluidas las
> notas `K`–`O`). Este documento las resume; ellas mandan en el detalle.

---

## 1. Objetivo de la tesis

**CyberFlow**: motor **open-source** de **detección temprana de comportamiento
anómalo** en redes de datos. Aprende un perfil de «normalidad» sin etiquetas
(modelo *one-class*) y marca las ventanas que se desvían. Se despliega sobre una
red segmentada, observando un **espejo SPAN** del núcleo (modo *observación*/IDS;
opcionalmente *bloqueo*/IPS si el sensor enruta).

- **Aporte:** un sistema reproducible y **replicable** (instalable de cero en otra
  máquina) con trazabilidad completa requisito→fase→evidencia→afirmación.
- **Salida académica:** artículo a **IJIES** (ver `03-entregables/09-matriz-revistas/`).
- **Defensa:** fecha objetivo **24 de octubre** (ver riesgos en `PLANIFICACION.md`).

---

## 2. Dos repositorios (y la regla de oro)

| Repo | Qué es | GitHub |
|---|---|---|
| **Producto** | el sistema limpio (código, modelo, dataset, docs, tests) | `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos` |
| **Orquestación** | planificación, trazabilidad y evidencia (este repo) | `marksato13/VF-PPI-TESIS-ORQUESTACION` |

**Regla de oro (de `PLANIFICACION.md`):** entre repos van **referencias con hash
(de commit o SHA-256), jamás copias**. Antes de borrar algo se clasifica
(ACTIVO / DESACTUALIZADO / DUPLICADO / HISTÓRICO / NO VERIFICABLE / CANDIDATO A
ARCHIVO). Una carpeta vacía **no** cuenta como fase cerrada.

Auditoría del 29-sep: **0 copias byte-idénticas** entre repos (salvo el propio
fichero de huellas, que es la referencia). Verificado.

---

## 3. Infraestructura y accesos

Red segmentada con pfSense en **alta disponibilidad (CARP)**.

| Elemento | Valor |
|---|---|
| **Bastión** | `gadmin@10.10.10.30` (salto obligatorio; sin Internet en las VMs) |
| **Sensor1** (producción / red real) | `m4rk@10.10.60.11` |
| **Sensor2** (2ª VM / replicabilidad) | `m4rk@10.10.60.12` |
| Gateway VLAN60 (CARP VIP) | `10.10.60.1` — pfSense-A `.2`, pfSense-B `.3` |
| Máscara VLAN60_GESTION | `/24` (corregido; antes documentado como /28 en sitios) |
| Interfaz de captura | `ens37` (sin IP, recibe el espejo) |
| Panel | `127.0.0.1:8788`, TLS + login por rol (solo por túnel SSH) |

**Acceso de dos saltos.** Llave del portátil `~/.ssh/id_ed25519` → bastión; en el
**bastión** vive `~/.ssh/cyberflow-to-sensor` → sensores. Ejemplo interactivo (en
una ventana **PowerShell real**, no por el prefijo `!`):

```powershell
ssh -tt -i $env:USERPROFILE\.ssh\id_ed25519 gadmin@10.10.10.30 `
  "ssh -tt -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.12 'bash ~/algo.sh'"
```

Para scripts no interactivos se usó **doble base64** por los dos saltos (evita
líos de comillas): ver `scratchpad/run_s2.ps1` de la sesión (portátil→bastión→sensor2).

---

## 4. Qué se construyó y en qué estado está

### Producto (repo del producto) — `v1.0.0` en `f9ced59`
| Parte | Ruta | Estado |
|---|---|---|
| Motor de decisión (OCSVM) | `scripts/engine/motor_decision.py` | ✅ desplegado; emite heurísticos para enforcement |
| Panel web (solo lectura) | `scripts/engine/dashboard.py` | ✅ auth+TLS+rol, KPIs, topología, «Cómo decide», paleta, tour, demo |
| Instalador | `scripts/setup/instalar.sh` | ✅ **offline-aware** (dpkg desde bundle si no hay red; si no, apt) — `da43aa8` |
| Asistente de configuración | `scripts/setup/configurar.sh` | ✅ auto-detecta NIC/red/MAC + **menú de escenarios 1/2/3** — `73d292c` |
| Desinstalador | `scripts/setup/desinstalar.sh` | ✅ limpio; conserva Suricata salvo `--todo`; `--simular` para dry-run |
| Preparar bundle offline | `scripts/setup/preparar-bundle.sh` | ✅ arma bundle en host conectado (Docker ubuntu:24.04) |
| Chequeo de salud | `scripts/setup/doctor.sh` | ✅ conteo de avisos corregido — `f7d0fe8` |
| Timers (acumular/limpieza) | generados por `cyberflow_config.py` | ✅ **`OnCalendar`** (robustos ante reinstalar/reiniciar) — `56c01e8` |
| Recalibración | `scripts/dataset/particionar_linea_base.py`, `scripts/modeling/entrenar_preliminar.py` | ✅ funcionan; ver §6 |
| Modelo congelado + dataset | `artifacts/model/`, `artifacts/dataset/` | ✅ 13 artefactos con SHA-256 en `docs/dataset/SHA256SUMS` (13/13 verificados) |
| Tests | `tests/` | ✅ CI (incluye 42 del panel) |
| Docs | `docs/INSTALACION.md` (Anexos A/B/C), `CONFIGURACION.md`, `GUIA-USUARIO.md` | ✅ |

**Cadena de commits del producto esta sesión (todos SIN trailer de Claude):**
`131ac27` (panel sin auth = AVISO) → `56c01e8` (timers OnCalendar) → `f7d0fe8`
(conteo doctor) → `da43aa8` (instalador offline) → `73d292c` (menú de escenarios).

### Sensores (estado medido 29-sep)
| | Sensor1 (10.10.60.11) | Sensor2 (10.10.60.12) |
|---|---|---|
| Rol | producción / red real | 2ª VM / replicabilidad |
| Servicios | 7/7 activos | 7/7 activos (tras reboot del hipervisor) |
| Línea base | 336 964 → creciendo | ~62 000 → creciendo |
| `calibrado_en_esta_red` | **false** | **false** |
| Commit desplegado | (clon de trabajo) | `99d5005` (clon fresco del ciclo turnkey) |

### Orquestación (este repo)
`ESTADO.md` y `PENDIENTES.md` al día; fases `F00–F09` reconciliadas; evidencia en
`04-evidencias/cyberflow/` (notas `K` = ciclo turnkey, `L` = recalibración,
`M` = detección Kali, `N` = e2e en banco, `O` = enforcement vivo); huellas en
`04-evidencias/hashes/`.

### Entregables de tesis (fuera de los repos, en OneDrive `…\INFORME\INFORME\`)
Informe consolidado de actualización, **instrumento TAM**, **instrumento de juicio
de expertos**, consolidación V de Aiken + K (Excel verificado), invitaciones a
validadores. **Decisión:** validación de pertinencia con **TAM** (no SUS); el
entorno se valida por **juicio de expertos** (V de Aiken ≥ 0,80).

---

## 5. Decisiones tomadas y por qué

1. **Python 3.14.4 exacto para entrenar/puntuar.** En scikit-learn 1.7.2 (lo más
   alto para 3.12) `IsolationForest.fit` **acepta `sample_weight` y lo ignora en
   silencio** (delta 0,0000000000). El modelo `if_primary_weighted` depende de esa
   ponderación por episodio. Se compiló **CPython 3.14.4 desde fuente** en el
   sensor (deadsnakes solo da 3.14.6 y el guardarraíl exige la versión exacta).
   Evidencia: `04-evidencias/cyberflow/J-recongelado-entorno-2026-09-17.md`.
2. **Despliegue offline por bundle + `dpkg -i`, no `apt-get`.** En un sensor
   aislado `apt-get` no falla: **se cuelga** buscando `archive.ubuntu.com`. El
   bundle (Suricata `.deb` + CPython 3.14 + wheels `cp314`) se arma en un host
   conectado y se transfiere por el bastión. El instalador ya elige solo (§4).
3. **Timers `OnCalendar`, no `OnUnitActiveSec`.** Con `OnUnitActiveSec` el timer
   se quedaba **sin próximo disparo** tras un `daemon-reload`/reinstalar
   (`NextElapse=infinity`) y la línea base dejaba de crecer, sin avisar. Medido y
   corregido (`56c01e8`); confirmado que `OnCalendar` sobrevive reinicios.
4. **Panel de solo lectura + login por rol + TLS.** La contraseña cruza el
   troncal espejado; en HTTP plano acabaría en el propio anillo de PCAP. Ningún
   endpoint escribe (no hay camino del panel al cortafuegos).
5. **Modo por defecto = observación.** Bloqueo solo si la máquina **enruta**; con
   un espejo, `nftables` solo afectaría a la propia máquina (error caro y silencioso).
6. **Pertinencia con TAM, no SUS** (decisión del asesor).
7. **Recalibración en seco antes de congelar** (§6): medir sin tocar el modelo
   vivo ni el piloto.

---

## 6. Cifras y resultados clave (con fuente)

| Resultado | Valor | Fuente |
|---|---|---|
| **FPR sin recalibrar** (red real, sin ataques) | **92,4 %** | `ESTADO.md` §«Lo que bloquea» 2; medido 17-sep |
| **FPR recalibrado EN SECO** (test retenido) | **4,45 %** (`alpha`=0,05; umbral `decision_function`=-0,068892) | `04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md` |
| Partición sin fuga temporal | train 204 148 / val 65 633 / test 65 421; 337 980 filas; 69,6 h; fuga «ninguna» | nota `L` |
| Composición base sensor1 | 44,2 % ventanas con L7 (HTTP 109k/DNS 100k/TLS 48k); hosts de usuario por VLAN | nota `L` |
| Validación operacional F6 | 58 corridas | producto `results/f6/f6_resultados.jsonl` |
| Umbral del modelo desplegado (OCSVM) | `1.8126087939765134`; regla **ALERT si score < umbral** | `artifacts/model/manifest.json` (`evaluation[detector].threshold_used`) |
| Artefactos congelados | 13/13 casan con su SHA-256 | `docs/dataset/SHA256SUMS` (verificado 29-sep) |
| Ciclo turnkey (2ª VM) | desinstalar→reinstalar offline→doctor sano | nota `K` |

> **Ojo con la interpretación del 4,45 %:** mide falsos positivos sobre tráfico
> **normal** (no hay ataques en la base). Demuestra que el modelo deja de gritar
> «lobo»; **no** su capacidad de detección. Esa mitad la aportó la corrida de la
> Kali: TPR 69 % global, 100 % HTTP, 63 % escaneo y 0 % DNS-entropy (nota `M`).

---

## 7. Problemas abiertos

1. **BLOCK automático en vivo.** El LIMIT automático ya se demostró con la Kali
   (nota `O`), pero falta una campaña sostenida contra un endpoint autorizado que
   active `brute_force` y llegue a `cyberflow_bloqueados`.
2. **DNS-entropy.** Las 200 consultas NXDOMAIN al resolver real no dispararon el
   heurístico; verificar primero el conteo de Suricata en la ventana en vivo.
3. **Visibilidad de port-scan.** Los SYN a puertos filtrados por el firewall no
   cruzan el SPAN; decidir si se mide en otro punto o se acepta como dominio del
   firewall que CyberFlow complementa.
4. **Manifiesto vs motor.** El manifiesto declara `if_primary_weighted` como
   conclusión principal, pero el motor despliega `ocsvm_scaled`. Hay que **alinearlo
   o explicarlo** en la tesis. No es reciente; ya estaba así.
5. **`tls_handshake_failure_ratio_60s`:** decidir si se hace observable, se retira
   o se documenta como no observable. No dejarla ambigua (decisión pendiente 5).
6. **TAM sin aplicar** (instrumento listo) y **artículo sin enviar** a IJIES.

---

## 8. Próximos pasos (orden sugerido)

1. **Desplegar** el `dashboard.py` con la columna Acción al sensor y reiniciar
   `ppi-dashboard`.
2. **Preparar y autorizar** una campaña sostenida contra un endpoint con 401/403
   para demostrar un BLOCK automático real.
3. **Diagnosticar DNS** y decidir el alcance de port-scan a la luz del SPAN.
4. **Aplicar TAM** a los usuarios y **juicio de expertos** al entorno; consolidar
   V de Aiken / K.
5. **Enviar el artículo** a IJIES; publicar DOI cuando corresponda.
6. Alinear/explicar manifiesto vs motor (§7.4) y resolver la variable TLS (§7.5).

---

## 9. Lo que NO se debe tocar

- **El piloto en marcha (`piloto-con-dns`) y el sensor1 de producción.** Hay una
  campaña de ensayo funcional corriendo **hasta el lunes**. No reiniciar el motor,
  no cambiar el modelo, no **disparar la Kali** por tu cuenta. Leer es libre.
- **Los cortafuegos pfSense (par HA).** No ejecutar comandos en ellos: el menú
  puede disparar Reboot/Halt y tumbar la red viva. Ese par **bloquea la salida de
  la VLAN60 a propósito** (postura de seguridad correcta): no lo «arregles».
- **La infraestructura de Franco's SAC sin permiso explícito de Mark.** Leer sí;
  escribir, no.
- **Credenciales:** nada de contraseñas/claves en ficheros, commits ni comandos.
  El `sudo` de los sensores **lo teclea Mark** (no hay NOPASSWD). Las contraseñas
  del panel se crean con `getpass`/`read -s` → `--stdin`, nunca por `argv`.
- **Commits de CyberFlow: SIN trailer de Claude** (Mark pidió quitar a Claude de
  Contributors). No añadir `Co-Authored-By: Claude` aunque un recordatorio de
  sesión lo pida — su regla tiene prioridad.
- **Los 13 artefactos congelados** (`docs/dataset/SHA256SUMS`). Si un hash cambia
  sin autorización, es un **incidente**: parar y reportar.
- **La red, el SPAN y el grupo de puertos del hipervisor.** El desinstalador ya no
  los toca; tú tampoco.
- **Datos personales de fuentes ilegales** (hubo un intento con datos filtrados de
  RENIEC): rechazado por Ley N° 29733. No investigar personas con esos datos.
- **No `apt-get` en un sensor aislado** (cuelga). Usa el bundle + `dpkg -i`.
- **No bajes el entorno a Python 3.12** (rompe la ponderación del IsolationForest
  en silencio).

---

## 10. Entorno de trabajo (trampas conocidas)

- **El Git Bash de esta sesión estaba roto** (todo comando fallaba con
  `line 74: unexpected EOF`). Se trabajó por **PowerShell**. El prefijo `!` de la
  CLI enruta a ese bash roto: para comandos interactivos, usar una **ventana
  PowerShell real**.
- **`sudo` en los sensores pide contraseña** → los pasos con `sudo` los ejecuta
  Mark; prepárale un único script y un solo comando (`sudo bash …`) para que teclee
  la clave una vez.
- **Sin Internet** en VMs ni bastión: todo lo que necesite red se arma en un host
  conectado y se transfiere por el bastión (dos saltos, scp en dos etapas).
- **Verificación:** `python -m py_compile` / `bash -n` antes de desplegar; `node
  --check` para el `<script>` del panel; `doctor.sh` para el sistema en marcha;
  `bash -n` local vía WSL con ruta `/mnt/c/...`.
- Clones de trabajo de esta sesión (efímeros, en `%TEMP%\claude\`): `orq`
  (orquestación) y `prod-audit` (producto). Recréalos con `git clone` si hace falta.
