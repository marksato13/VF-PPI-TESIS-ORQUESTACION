# Pendientes — CyberFlow

**Actualizado:** 1 de octubre de 2026.
Fuente única de "qué falta". Lo **hecho** está al final para contexto; el detalle
vive en `04-evidencias/cyberflow/` (notas K–O), `01-arquitectura/DISENO-ENFORCEMENT.md`
y `TRASPASO.md`.

---

## 🟥 Prioridad para la validación (sesiones del 7-oct)

### 1. GUI / Dashboard — ✅ HECHO Y EN VIVO
- ✅ **Contadores por detector activo** (no `ocsvm_scaled` fijo) — ya no salen en 0
  tras congelar. `compute_counters(detector_modelo=args.detector_name)` + 5 tests.
- ✅ **Etiquetas** del detector recalibrado y los 4 heurísticos.
- ✅ **Topología rehecha:** modelo recalibrado (no "OCSVM congelado"), cadena de
  enforcement (heurísticos → decisión LIMIT/BLOCK → feed firmado → agente en host),
  Wazuh en observabilidad, fases y conectores nuevos, archivos por nodo.
- ✅ Desplegado al repo del sensor; **CI verde**.
- ✅ **Panel reiniciado (30-sep):** `ppi-dashboard` corre el código nuevo.
- ⚠️ **Bug corregido (30-sep):** una etiqueta de arista con `<` pegado a una letra
  (`score<umbral`) rompía el parseo del SVG y ocultaba TODAS las cajas de nodos.
  Escapado a `&lt;` (commit `921f0b1`). El sensor se parcheó en vivo (`sed`) y se
  reinició; las cajas ya se ven.
- ✅ **Topología HORIZONTAL (30-sep, commit `594b197`):** vista Completa rediseñada,
  flujo izquierda→derecha con las fases en columnas y más espacio. Validado sin
  solapes / fuera de banda. Con `b2900e8`: panel de detalle plegable (diagrama a
  todo el ancho), letras más gruesas, iconos más adecuados, fases numeradas y zoom
  por sección (`d29f7f4`). El número "31 variables" de una arista sigue **por
  reconciliar** con `/api/variables` (¿28?).
- ✅ **Panel derecho enriquecido (30-sep, commit `d1be279`):** flujo interno paso a
  paso del **Motor** (atribución→filtrado→ventaneo→puntuación) y de la **Decisión**
  (modelo+heurístico→acción más severa→escalada→nunca-bloquear); cada flujo con su
  título propio (se corrigió el bug del título fijo "reentrenamiento").
- ⏳ **Falta:** copiar al sensor el `dashboard.py` que añade la columna **Acción**
  (PERMIT/LIMIT/BLOCK) y ejecutar `sudo systemctl restart ppi-dashboard`. El sensor
  no tiene egress, por lo que el despliegue debe ir por el bastión; la visualización
  de topología ya está desplegada y en vivo.

### 2. Validación con usuarios y expertos
- **TAM** (utilidad/aceptación, Likert 1–7) + **Alfa de Cronbach** (≥0,70).
- **Juicio de expertos** del entorno + **V de Aiken** (≥0,80).
- Instrumentos ya preparados (carpeta de informes / entregable de orquestación).

---

## 🟦 Enforcement — EN VIVO (go-live 1-oct)
El pipeline completo corre **autónomo y aplicando** decisiones en el host DMZ, vía
crons de usuario:
- **Sensor** (`crontab` de m4rk): `publicar_feed.py` → `~/feed/feed.json`+`.sig`.
- **Bastión** (`crontab` de gadmin): `~/relay-feed.sh` (pull del sensor → push al host).
- **Host DMZ** (`crontab` de adminsrvdmz): `agente_enforce.py --aplicar --sudo` →
  `~/enforce/shadow.log` y reglas `nftables`.

**Verificado en el host:** tabla `inet cyberflow`, cadena `entrada` (hook input,
policy accept), set de bloqueados y set de limitados (100/s, ráfaga 5). `sudo -n nft`
es NOPASSWD, por lo que el agente eleva solo `nft`, no todo el proceso. El arreglo
`5368613` incorporó `--sudo` y reporte de errores; antes el agente podía reportar
"aplicado" aun si `nft` fallaba.

La campaña real `prueba-ataque-20261001-031730` desde Kali `10.10.20.30` demostró la
cadena automática: el modelo detectó la anomalía → emitió LIMIT en el feed firmado →
relay → el agente aplicó `nft` (`errores:0`). El rate-limit fue específico para la
Kali y se retiró al cesar el ataque. Además se observó un LIMIT de 3 min sobre
`10.10.20.24`, un falso positivo legítimo: el coste de un LIMIT es reversible, pero
debe seguir midiéndose durante el piloto. Evidencia completa: nota `O`.

**Rollback:** quitar `--aplicar --sudo` del cron y ejecutar
`sudo nft delete table inet cyberflow`.

## ✅ Código del panel: acción PERMIT/LIMIT/BLOCK (30-sep, commit `27a96a7`)
La tabla de Decisiones y el CSV tienen columna **Acción** (verde/ámbar/rojo),
derivada del veredicto + `heurístico` (misma lógica que `publicar_feed.py`).
El motor ya emite `heurístico`; falta desplegar este `dashboard.py` al sensor,
como se indica arriba, para que el panel vivo lo muestre.

## ✅ Autenticación del panel: HABILITADA (30-sep)
El código ya existía (login scrypt, TLS, roles, cerrojo, auditoría). Mark creó
cuentas/clave/cert con `cyberflow_usuarios.py` y regeneró la unidad. Panel ahora
en `https://10.10.60.11:8788`.

## ⏳ Enforcement — pendientes de validación
- **Demostrar un BLOCK automático real:** realizar fuerza bruta **sostenida**
  (`hydra`) únicamente contra un endpoint autorizado del DMZ que responda 401/403.
  Debe disparar `brute_force` y poblar `cyberflow_bloqueados`. El BLOCK aislado con
  regla explícita ya se probó en banco (nota `N`); falta la evidencia end-to-end
  originada por la detección en vivo.
- **DNS-entropy:** diagnosticar por qué 200 consultas NXDOMAIN únicas al resolver
  real `10.10.10.20` no elevaron `dns_query_count_60s`. Es consistente con el hueco
  histórico de DNS (0 % en nota `M`): primero confirmar si Suricata las registra en
  la ventana en vivo.
- **Port scan:** revisar umbrales o el punto de captura. En la campaña, 998 de 1000
  puertos fueron filtrados por el firewall antes del troncal espejado: el sensor solo
  vio los puertos 80/443, insuficientes para `port_scan` (≥20). CyberFlow complementa
  al firewall; no debe atribuirse la visibilidad del tráfico que este ya descartó.
- **Panel:** desplegar la columna Acción descrita arriba.
- **Seguridad (higiene, no urgente):** conservar la llave `cyberflow-to-srv` mientras
  se necesiten despliegues; revocarla al cierre del proyecto o al detenerlos.

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
