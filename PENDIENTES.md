# Pendientes — CyberFlow

**Actualizado:** 30 de septiembre de 2026.
Fuente única de "qué falta". Lo **hecho** está al final para contexto; el detalle
vive en `04-evidencias/cyberflow/` (notas K–N), `01-arquitectura/DISENO-ENFORCEMENT.md`
y `TRASPASO.md`.

---

## 🟥 Prioridad para la validación (sesiones del 7-oct)

### 1. GUI / Dashboard — ✅ HECHO (falta solo reiniciar el panel)
- ✅ **Contadores por detector activo** (no `ocsvm_scaled` fijo) — ya no salen en 0
  tras congelar. `compute_counters(detector_modelo=args.detector_name)` + 5 tests.
- ✅ **Etiquetas** del detector recalibrado y los 4 heurísticos.
- ✅ **Topología rehecha:** modelo recalibrado (no "OCSVM congelado"), cadena de
  enforcement (heurísticos → decisión LIMIT/BLOCK → feed firmado → agente en host),
  Wazuh en observabilidad, fases y conectores nuevos, archivos por nodo.
- ✅ Desplegado al repo del sensor; **CI verde**.
- ⏳ **Falta:** `sudo systemctl restart ppi-dashboard` (sudo de Mark) para que el
  panel vivo cargue el código nuevo.

### 2. Validación con usuarios y expertos
- **TAM** (utilidad/aceptación, Likert 1–7) + **Alfa de Cronbach** (≥0,70).
- **Juicio de expertos** del entorno + **V de Aiken** (≥0,80).
- Instrumentos ya preparados (carpeta de informes / entregable de orquestación).

---

## 🟦 Enforcement — MODO SOMBRA ya corriendo (observe-only)
El pipeline completo corre **autónomo cada minuto, en dry-run** (no aplica nada, cero
impacto en el piloto), vía **crons de usuario**:
- **Sensor** (`crontab` de m4rk): `publicar_feed.py` → `~/feed/feed.json`+`.sig`.
- **Bastión** (`crontab` de gadmin): `~/relay-feed.sh` (pull del sensor → push al host).
- **Host DMZ** (`crontab` de adminsrvdmz): `agente_enforce.py` (dry-run) → `~/enforce/shadow.log`.

Sirve para **medir los falsos positivos antes de ir en vivo** (ahora mismo registra
`LIMIT 10.10.20.24`, un cliente legítimo). **Para pararlo:** `crontab -e` (quitar la
línea) en cada host, o `crontab -r`.

## 🟧 Enforcement — pasar a VIVO (desde el modo sombra)
Código completo en `main`. **Pipeline entero PROBADO** (nota `N`): un BLOCK real
corta el ataque en el host, y la automatización sensor→bastión→agente funciona sola
(en **dry-run**). Infra ya montada en el sensor: claves ed25519 persistentes
(`artifacts/feed-keys/`), `publicar_feed.py` produce el feed en `~/feed/`; el bastión
relaya al host; el agente verifica y planea. Falta para dejarlo **vivo y recurrente**:
- **Recurrencia:** cron/timer en sensor (publicar), bastión (relay) y host (agente).
  Se puede con **crons de usuario** (sin sudo con clave) + el `sudo` sin clave del
  host DMZ para el `nft`.
- **Decisión de Mark — pasar el agente a `--aplicar`:** hoy en dry-run. En vivo
  **rate-limitaría ocasionalmente a clientes legítimos** por los falsos positivos del
  modelo (visto: `10.10.20.24` → LIMIT). Es suave/reversible (LIMIT 300 s), pero toca
  el piloto. Decidir cuándo (¿tras el piloto? ¿aceptando el coste del LIMIT?).
- **Motor con heurísticos en vivo:** desplegado en el repo del sensor; **falta
  reiniciar `ppi-motor`** (sudo con clave de Mark) para que emita el campo
  `heuristico` → así el feed llevaría BLOCK de port-scan/brute-force, no solo LIMIT.
- **DNS-entropy 0 %:** re-probar contra el **resolver real `10.10.10.20`** (nota `M`/`N`).
- **Panel:** mostrar las acciones **LIMIT/BLOCK** (hoy ALERT/PERMIT).
- **Seguridad (higiene, NO urgente):** la llave `cyberflow-to-srv` **se queda**
  mientras se construye/despliega el enforcement (hace falta para desplegar en el
  host DMZ). Revocarla es opcional, al **cierre del proyecto** o cuando ya no se
  quieran despliegues (`~/.ssh/authorized_keys` de `adminsrvdmz@10.10.30.10`).

---

## 🟨 Publicación (tesis)
- **Artículo a IJIES** (enviar).
- **DOI Zenodo** (`.zenodo.json` ya está; publicar cuando toque).
- Alinear cifras y limitaciones en todos los documentos.

---

## 🟩 Versionado (decidido)
- **Una sola versión principal: `v1.0.0` sobre `main`.** No se crea `v1.1.0`; las
  mejoras se actualizan sobre `main`. El tag `v1.0.0` es foto inmutable; `main` es la
  versión viva.

---

## ✅ Hecho (contexto)
- **v1.0.0** tag + Release GitHub; CI verde.
- **Replicabilidad**: 2ª VM turnkey offline (nota `K`).
- **Recalibración**: FPR **92,4 % → 4,45 %** (nota `L`).
- **Detección (Kali)**: TPR **100 % HTTP**, 63 % escaneo, 69 % global (nota `M`).
- **Congelado + calibrado** en sensor1 (`if_recalibrado_2026_09`, `calibrado=true`).
- **Enforcement**: diseño cerrado (`DISENO-ENFORCEMENT.md` + `flujo-decision.md`);
  código en `main` (heurísticos, feed firmado ed25519, escalera, publicador,
  integración aditiva en el motor, agente); 47 tests, CI verde; **e2e: un BLOCK
  corta el ataque en el host** (nota `N`).
- **Posicionamiento** "complementa, no reemplaza" en README + diseño.
