# Estado

**Actualizado:** 9 de octubre de 2026 (verificación por SSH en Sensor1 y publicación de
la documentación del producto en `main`).

Fuente de verdad del despliegue:
[ficha técnica](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md)
(producto, `main@01b6f3f`). Afirmaciones con estado y fuente:
[`02-metodologia/trazabilidad/afirmaciones-cientificas.md`](02-metodologia/trazabilidad/afirmaciones-cientificas.md).
Estado por bloques de la validación interna:
[`02-metodologia/validacion-interna-profesor/ESTADO-IMPLEMENTACION-20261009.md`](02-metodologia/validacion-interna-profesor/ESTADO-IMPLEMENTACION-20261009.md).

---

## En una frase

El sistema está **desplegado sobre tráfico real** en Sensor1 por **espejo SPAN**: el
motor ejecuta un **Isolation Forest recalibrado** en esa red (`if_recalibrado_2026_09`,
umbral `score_samples < −0,568892`) junto con cuatro heurísticos, y la respuesta
**PERMIT / LIMIT / BLOCK** la aplica un **agente en el host protegido** a partir de un
feed firmado. Está **validado en vivo un LIMIT automático** de punta a punta (nota `O`);
falta demostrar un **BLOCK automático** originado por la detección.

## Cuatro estados — no son lo mismo

*Implementado en Git* (existe en un commit) · *Publicado* (en el remoto, rama indicada) ·
*Desplegado* (corriendo en Sensor1 / hosts) · *Validado* (con evidencia de que funciona).

| Componente | Implementado | Publicado | Desplegado | Validado | Evidencia |
|---|---|---|---|---|---|
| Espejo SPAN → sensor (`ens37`, sin IP) | ✅ | ✅ `main` | ✅ | ✅ | notas `B`, `D` (17-sep) |
| Suricata + `eve.json` | ✅ | ✅ `main` | ✅ | ✅ | nota `G` (17-sep) |
| Motor con **IF recalibrado** | ✅ código | ✅ código en `main`; el joblib **no** se publica (solo su hash) | ✅ | FPR 4,45 % en test normal (nota `L`); 54/78 Kali (nota `M`) | reconciliación por SSH (9-oct) |
| Equivalencia de escalas del umbral | ✅ `verificar_equivalencia_umbral.py` | ✅ `main@33549a1` | — | ⏳ falta correrlo sobre el joblib vivo y publicar su salida | ficha técnica §2 |
| Heurísticos `2026-10-06.2` | ✅ | ✅ `main@9425373` y rama del sensor | ✅ | port_scan 3/3 tras la rama OR; dns_entropy → LIMIT en vivo (6-oct) | notas 26, 31 |
| Etiqueta de versión en el feed | ✅ ahora sale del código | ✅ `main@9425373` | ❌ la unidad del publicador en Sensor1 aún pasa `--umbrales 2026-10-06.1` | — | ver «Instrucciones vigentes» |
| LIMIT automático (modelo → feed → relay → agente → nft) | ✅ | ✅ | ✅ | ✅ en vivo | nota `O` (1-oct) |
| BLOCK aislado con regla explícita en el host | ✅ | ✅ | ✅ | ✅ en banco | nota `N` (30-sep) |
| BLOCK automático de punta a punta | ✅ | ✅ | ✅ | ❌ **pendiente** | — |
| Timers systemd (publicar / relay / agente) | ✅ | ✅ | ✅ (reemplazaron los crons el 6-oct) | ✅ | `OnCalendar=minutely` |
| Panel con TLS + login + roles | ✅ | ✅ | ✅ (30-sep) | ⏳ QA por rol con capturas | — |
| Panel: 3 vistas, visor de código, «Pruebas previas», detector real | ✅ | ✅ rama del sensor `8d696e5`; la tarjeta Detector también en `main@308fc97` | ✅ (9-oct) | ⏳ QA autenticada por rol | contenido idéntico a `8d696e5` salvo finales de línea |
| Documentación pública alineada al despliegue | ✅ | ✅ `main@01b6f3f` | — | — | CI de `main` |
| Suite de pruebas en Linux | ✅ | ✅ | — | ✅ 328 pruebas OK en CPython 3.14.4 (WSL) y CI de GitHub | 9-oct |
| Validación interna con el profesor | — | — | — | ❌ pendiente | bloque B6 |
| Validación externa (TAM + expertos) | instrumentos listos | — | — | ❌ sin respuestas | bloque B7 |

## Instrucciones vigentes (operación en Sensor1 y hosts)

**Comprobar que corre.** En el sensor: `systemctl is-active ppi-motor ppi-dashboard
ppi-publicar-feed.timer`. En el host protegido: `systemctl is-active
ppi-enforce-agent.timer` y `sudo nft list table inet cyberflow`.

**Corregir la etiqueta de versión del feed** (cosmético: no cambia las reglas aplicadas).
En el sensor:

```bash
systemctl cat ppi-publicar-feed.service | grep -n -- --umbrales
sudo systemctl edit --full ppi-publicar-feed.service   # cambiar 2026-10-06.1 por 2026-10-06.2
sudo systemctl daemon-reload
```

Con el publicador de `main` la etiqueta ya sale de `heuristicos.VERSION_UMBRALES`; al
desplegarlo, el argumento sobra.

**Verificar la equivalencia del umbral sobre el artefacto vivo** (publicar la salida
como evidencia en `04-evidencias/cyberflow/`):

```bash
python3 scripts/modeling/verificar_equivalencia_umbral.py \
  --modelo artifacts/preliminar/if_recalibrado_desplegable.joblib \
  --manifiesto artifacts/preliminar/manifest-if-recalibrado.json \
  --detector if_recalibrado_2026_09 --umbral-decision -0.06889178778834089 \
  --salida /tmp/equivalencia-umbral.json
```

**Rollback del enforcement** (antes se hacía quitando opciones del cron; ya no hay cron):

```bash
# 1) dejar el agente en modo sombra (decide y registra, no aplica): en el HOST
sudo systemctl edit --full ppi-enforce-agent.service   # quitar --aplicar de ExecStart
sudo systemctl daemon-reload
# 2) o pararlo del todo y retirar sus reglas: en el HOST
sudo systemctl disable --now ppi-enforce-agent.timer
sudo nft delete table inet cyberflow
# 3) opcional, dejar de publicar el feed: en el SENSOR
sudo systemctl disable --now ppi-publicar-feed.timer
```

La tabla `inet cyberflow` es propia y aislada: borrarla no toca el cortafuegos del host.

**Rollback del panel** (si una versión nueva falla): restaurar el respaldo y reiniciar
solo el panel —`cp dashboard.py.bak-AAAAMMDD-HHMM dashboard.py && sudo systemctl restart
ppi-dashboard`—; no reiniciar motor ni Suricata.

**No hacer:** regenerar las unidades de Sensor1 con `configs/cyberflow.toml` (es el
perfil genérico histórico: OCSVM, `1,8126`, `calibrado=false`); Sensor1 usa
`configs/cyberflow.local.toml`.

## Decisiones pendientes

| # | Decisión | Por qué importa |
|---|---|---|
| 1 | **Demostrar un BLOCK automático** | Solo con un endpoint autorizado (401/403) y fuerza bruta sostenida; hoy el BLOCK está validado en banco, no originado por la detección en vivo |
| 2 | **DNS** | El 0/8 del piloto apuntó a un host que no era el resolver: verificar consultas en PCAP, EVE, atribución y variables antes de concluir que el modelo falla |
| 3 | **Visibilidad de port-scan** | El cortafuegos descarta antes del troncal espejado casi todos los puertos (998/1000 en una campaña): separar tráfico generado, descartado y visto |
| 4 | **Perfil de configuración** | Publicar o no un perfil reproducible del despliegue real en lugar del genérico histórico |
| 5 | **Lista nunca-bloquear** | Hoy fijada en el código del publicador y del agente; pasarla a configuración por despliegue |
| 6 | **`tls_handshake_failure_ratio_60s`** | Hacerla observable, retirarla o mantenerla documentada como no observable |
| 7 | **Despliegue de `main` en Sensor1** | `main` tiene el publicador corregido y la documentación canónica; el sensor corre el snapshot de la rama `as-deployed-sensor-20261006` |

## Lo siguiente, por orden

1. Correr la verificación de equivalencia sobre el joblib vivo y publicar su salida.
2. Corregir la etiqueta `--umbrales` del publicador en Sensor1.
3. QA autenticada del panel por rol (capturas fechadas).
4. Demostrar el BLOCK automático contra un endpoint autorizado.
5. Ensayo y sesión de validación interna (B6); después TAM y juicio de expertos (B7).

---

## Histórico (antes del 9 de octubre)

> Lo que sigue se conserva como registro. Donde contradiga lo anterior, manda lo de
> arriba.

**Corte del 1 de octubre.** Recalibración congelada en Sensor1, `v1.0.0` etiquetada, Kali
con TPR 69 % global (HTTP 27/27, escaneo 27/43, DNS 0/8) y primer LIMIT automático en
vivo. Entonces el enforcement corría por **crons de usuario** y el panel con la columna
Acción aún no estaba desplegado. En ese corte se escribió «motor (OCSVM)» en la tabla de
componentes: era texto heredado; el motor ya ejecutaba el IF recalibrado.

**Tráfico de usuarios (17-sep → 29-sep).** El 17-sep, en 95 s, el 87 % de las tramas
eran plano de control (STP/PVST+, VRRP/CARP, pfsync) y solo 13 % tráfico IP real. Tras la
campaña `piloto-con-dns` (29-sep), sobre 336 964 filas y 45 entidades, el 44,2 % de las
ventanas tenían L7 y las entidades principales eran hosts de usuario: la línea base sirvió
para recalibrar.

**El modelo de laboratorio no era trasladable (medido).** En los primeros minutos sobre
tráfico real y sin ataques, el OCSVM dio **92,4 % de ALERT** (85 de 92 decisiones en 7
ventanas), casi todo sobre interfaces del cortafuegos emitiendo CARP. Después, el IF
recalibrado dio **4,45 %** sobre test normal retenido (337 980 filas elegibles, sin fuga
temporal; train 204 148 / validation 65 633 / test 65 421; umbral desde validación con
`alpha = 0,05`). **Esa diferencia no aísla el efecto de recalibrar:** cambiaron a la vez el
modelo (OCSVM → IF), los datos (minutos iniciales → ~70 h de línea base) y el alcance (se
excluyó el plano de control y se deduplicó el espejo). Para atribuir la mejora a la
recalibración habría que puntuar ambos modelos sobre el mismo conjunto retenido.

**Entorno congelado (17-sep).** El sensor tenía Python 3.12.3; con scikit-learn 1.7.2,
`IsolationForest.fit` acepta `sample_weight` y lo ignora en silencio (`if_primary_weighted`
pasaba de 97/179 a 103/179). Se compiló CPython 3.14.4 en el sensor. Evidencia: nota `J`.

**Manifiesto frente a motor.** El manifiesto de laboratorio declaraba `if_primary_weighted`
como principal, el `.toml` genérico apunta a `ocsvm_scaled` y el motor vivo ejecuta un
tercer modelo, `if_recalibrado_2026_09`: reconciliado el 9-oct (ver la reconciliación en
el producto). No se intercambian umbrales entre ellos.

**Correcciones al material anterior (17-sep).** La VLAN 60 es `/24`; pfSense-B sí emite;
el volumen lógico del sensor se amplió de 18,5 GB a 36,9 GB; la interfaz de captura pedía
DHCP y había una `ens38` inexistente; el espejo pasó a `startup-config`; la VLAN 40 es
SERVICIOS y la 70 TRANSIT_FORTIGATE.

**Producto (hasta el 30-sep).** Segunda VM instalada 100 % offline con el ciclo
desinstalar → reinstalar sano (nota `K`); `v1.0.0` etiquetada con CI verde (265 pruebas en
aquel momento); instalador para observación por SPAN, bloqueo en línea o personalizado,
online u offline; `doctor.sh`; timers con `OnCalendar`; panel con KPIs, topología y modo
demo; instrumentos TAM y de juicio de expertos preparados.
