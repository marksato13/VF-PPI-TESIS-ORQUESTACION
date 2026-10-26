# Pendientes — CyberFlow

## Corte vigente — 23 de octubre de 2026 (actualizado el 25-oct)

Este corte sustituye los estados del registro histórico que se conserva más abajo.

### Cerrado y verificado

- **Publicación y convergencia Git:** ambas líneas de producto están integradas; `main`, `master` y `as-deployed-sensor-20261006` publicadas. No equivale a desplegar en las VMs.
- **Regresiones del merge:** corregidas conservación de sets/caducidad del agente, agrupación de reincidencia, exclusión por intervalos, interfaz del puntuador y pruebas del panel. Suite Linux congelada: **443 pruebas, cero fallos y errores, una omitida**. CI completo verde en `b204f59` ([ejecución](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/actions/runs/40023068513)), incluida la última corrección del panel.
- **Sesión interna:** realizada el 15-oct; el plan de observaciones ya existe. No seguir listándola como una sesión aún no celebrada.
- **BLOCK automático:** la campaña principal del 23-oct registra `brute_force → BLOCK` y corte real. Queda abierta la batería final y sus tiempos, no la existencia de toda evidencia de BLOCK.
- **4.1:** respaldo de scores completo publicado, métricas y figura verificadas. No es test ciego independiente.
- **4.1, calibración α (24-oct):** sensibilidad α con y sin las 80 ventanas Kali de validación (65 633 / 65 553); α = 0,03 es selección posterior. Evidencia: [calibracion-alfa-2026-10-24](03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/calibracion-alfa-2026-10-24/NOTA-CALIBRACION-ALFA.md).
- **4.1, comparación de detectores (25-oct):** IF congelado frente a OCSVM, LOF, Elliptic Envelope y PCA con los mismos datos, escalador y criterio de umbral (α 0,03 y 0,05). PCA, LOF y OCSVM detectan más ataques; el IF tiene la menor FPR de prueba. Evidencia: [comparacion-metodos-2026-10-25](03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25/NOTA-COMPARACION.md).
- **4.2, aporte de componentes (26-oct):** el histórico 6/9 · 7/9 · 9/9 era del modelo contaminado `if_recalibrado_2026_09` y se reproduce 9/9 desde `~/piloto/` (los PCAP sí se conservaron). Recalculado offline con el IF limpio: IF 6/9 (α 0,05 y 0,03), heurísticos 9/9, híbrido 9/9; por ventana el híbrido no añade TP y sube la FPR a 5,22 % / 3,35 %. Los heurísticos actuales se ajustaron con esta batería. Evidencia: [aporte-componentes-2026-10-26](03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.2-ablacion/aporte-componentes-2026-10-26/NOTA-APORTE-COMPONENTES.md).
- **VLAN 60, perfil de egreso (24-oct):** .2, .3, .10, .20, .21, .30, .40, .41 y .50 excluidos de la puntuación en Sensor1 y en el repo del producto. Desde el 25-oct, `configs/cyberflow.local.toml` del repo es copia exacta del de Sensor1 (detector `if_limpio_2026_10`).
- **Word:** copia editorial revisada en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/Articulo-IJIES-espanol_MARK_4.1-revisado.docx`, con PDF de revisión. Validación OOXML aprobada y revisión visual de 4.1; sigue siendo borrador de artículo.
- **Sensor1, comprobación SSH de este corte:** motor, panel y publicador activos. Los units del motor y panel declaran `if_limpio_2026_10`. No se cambió modelo ni despliegue durante esta comprobación.
- **Replay ET Open:** ejecutado en comparadora 10.10.60.13 sobre el PCAP archivado de 9 470 paquetes, con 53 013 reglas cargadas y cero fallidas. **55 alertas: 54 STREAM y una ET INFO por curl**. Evidencia: [replay y hashes](03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/_campana/resultados-2026-10-23/replay43/etopen-20261023/README.md). No afirmar cero alertas.

### Pendientes reales, por prioridad

| Prioridad | Pendiente | Criterio de cierre |
|---|---|---|
| Alta | Campaña final 4.2 | Batería N≥3 consistente: escaneo con camino abierto, HTTP con volumen suficiente y sin solape; atribución por episodio. Las dos corridas existentes son parciales. Episodios nuevos (no los del 5-oct, con los que se ajustaron los heurísticos) y fuerza bruta HTTP, que no tiene ninguno. |
| Alta | Tabla 9 final 4.3 | Mismo PCAP para ambos motores, control Nikto dentro de captura y criterio explícito para alertas informativas/STREAM; declarar HOME_NET. El replay archivado ya está ejecutado. |
| Alta | Tiempos 4.4 | Marcas t0–t5, desfase entre relojes, caducidad/reversión y figura de evidencia. No reutilizar 8 s del laboratorio como respuesta del modelo limpio. |
| Alta | Artículo completo | Revisar título/alcance, secciones 4.2–4.4, conclusiones y referencias duplicadas. El Word publicado incorpora 4.1; no es versión final para enviar. Sustituir la Tabla 7 antigua (7 candidatos históricos) por la comparación del 25-oct y decidir α (0,05 sin Kali recomendado; 0,03 = selección posterior). |
| Alta | QA del panel en Sensor1 por rol | Capturas fechadas admin/lector y comprobación de 403; las pruebas automatizadas de autenticación pasan, pero no sustituyen esa evidencia en la VM. |
| Alta | Desplegar correcciones recientes de código | Comparar hashes y preparar rollback antes de aplicar solo los componentes aprobados; un push no actualiza procesos remotos. |
| Media | F6, bibliografía | Referencias verificadas de los cinco detectores en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25/REFERENCIAS-VERIFICADAS.md`; quedan P1–P4 (DOI de Lakhina, Lazarevic sin leer, aplicación a redes de OCSVM y EE, taxonomía de Pimentel). |
| Media | Comparación de detectores | Prueba independiente, evaluación por episodio, intervalos y McNemar entre métodos, variante sin ventanas sin paquetes declarada antes de mirar. Ver §8 de `NOTA-COMPARACION.md`. |
| Media | F7, duplicados | Cuantificar paquetes SPAN y vectores/ventanas por separado; ejemplo reproducible y criterio que preserve tráfico legítimo repetido. |
| Media | Reentrenamiento antes/después | Evaluación con datos nuevos reservados, decisión documentada y sin promoción automática. |
| Media | Validación externa | Respuestas TAM y expertos reales, cálculo de fiabilidad/validez; no se cierra con instrumentos vacíos. |
| Media | Trabajo futuro | IPv6 y pfSense perimetral declarados con alcance consistente; no presentarlos como implementados. |
| Baja | Cierre operativo/publicación | Argumento viejo `--umbrales` del unit, configuración nunca-bloquear, credenciales al cierre y DOI Zenodo. |
| Baja | logrotate en Sensor1 | La entrada duplicada para `eve.json` hace fallar logrotate; requiere sudo de Mark. |

**Límite de este corte:** no se ejecutó una nueva campaña de ataques de 90–110 min. Sí se verificó acceso SSH y se ejecutó replay offline del PCAP archivado. La validación externa requiere respuestas de personas; no se fabrican.

---

## Registro histórico — no usar como lista vigente

**Actualizado originalmente:** 9 de octubre de 2026. Fuente única de «qué falta». El estado de cada
componente, con sus cuatro estados (implementado · publicado · desplegado · validado), está
en [`ESTADO.md`](ESTADO.md); el detalle, en `04-evidencias/cyberflow/` (notas K–O) y en la
[ficha técnica del producto](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md).

---

## 🟥 Para cerrar la validación interna

| # | Pendiente | Quién | Criterio de cierre |
|---|---|---|---|
| 0 | ~~Panel con el detector del motor~~ | — | ✅ **Cerrado el 10-oct**: el panel toma `if_recalibrado_2026_09` de la configuración local (sin tocar la unidad); umbral −0,568892. Abierto: decidir si se muestran FPR y detección del IF (hoy «—») |
| 1 | ~~Equivalencia del umbral sobre el artefacto vivo~~ | — | ✅ **Cerrado el 10-oct**: `EQUIVALENTE` ([nota `P`](04-evidencias/cyberflow/P-equivalencia-umbral-sensor1-2026-10-10.md)) |
| 1b | ~~Promoción ejecutable y manifiesto operativo publicados~~ | — | ✅ **Cerrado el 10-oct**: `promover_preliminar.py` reproduce el modelo vivo desde su paquete (scores idénticos; no byte a byte) y se publican manifiesto e informe ([nota `Q`](04-evidencias/cyberflow/Q-promocion-reproducible-sensor1-2026-10-10/README.md)) |
| 2 | ~~Etiqueta de versión del feed~~ | — | ✅ **Cerrado el 10-oct**: publicador de `main` desplegado; feed vivo y copia del host DMZ en `2026-10-06.2`, agente con `errores: 0`. Limpieza opcional: quitar `--umbrales` de la unidad |
| 2b | ~~Desplegar en Sensor1 las vistas nuevas y «Datos en vivo» (captura continua)~~ | — | ✅ **Cerrado el 10-oct 16:13 UTC**: `326e873` activo en `ppi-dashboard` (respaldo `dashboard.py.bak-20261010-161354`), 401 sin sesión, `flujo` leyendo tramas y eventos reales. La captura con `admin` queda dentro del punto 3 |
| 3 | **QA autenticada del panel por rol** | Mark | Capturas fechadas con `admin` y `lector`: tarjeta Detector, tres vistas, visor de código, «Pruebas previas»; el `lector` recibe 403 en lo de desarrollador |
| 4 | **Reentrenamiento ANTES/DESPUÉS con datos reales reservados** (bloque B3) | Mark + apoyo | Tabla `comparacion-*.md` sobre normal y ataques nuevos no vistos; decisión justificada; **sin desplegar** |
| 5 | **Sesión interna con el profesor** (bloque B6) | Mark | Acta o vídeo, observaciones y trazabilidad requisito → demo → evidencia |

## 🟧 Enforcement — pendientes de validación

- **BLOCK automático de punta a punta.** Fuerza bruta **sostenida** solo contra un endpoint
  autorizado del DMZ que responda 401/403: debe disparar `brute_force` y poblar
  `cyberflow_bloqueados`. Hoy el BLOCK está validado en banco (nota `N`), no originado por
  la detección en vivo. El puerto 8081 está filtrado entre la Kali y el DMZ: abrirlo o
  servir el endpoint en `:80` durante la prueba.
- **DNS.** Confirmar en PCAP y EVE que las consultas al resolver real (`10.10.10.20`)
  llegan, se atribuyen a la entidad y elevan `dns_query_count_60s`, antes de concluir nada
  sobre el modelo. El 0/8 del piloto apuntó a otro host.
- **Port scan.** Separar tráfico generado, descartado por el cortafuegos y visto por el
  sensor (en una campaña el sensor solo vio 80/443 de 1000 puertos).
- **Lista nunca-bloquear** fijada en el código del publicador y del agente: llevarla a
  configuración por despliegue y comprobar que ambos aplican la misma.
- **Tiempo de punta a punta** del pipeline distribuido (detección → feed → relay → agente
  → `nftables`), medido sobre esta cadena; la mediana de 8,0 s es de F6.

## 🟦 Enforcement vigente — cómo opera y cómo se revierte

Corre por **timers systemd** escalonados cada 10 s (`OnCalendar=*:*:00/10`, en
:00/:03/:06; reemplazaron a los crons el 6-oct y pasaron de `minutely` a 10 s el
15-oct): `ppi-publicar-feed` en el sensor, `ppi-relay-feed` en el bastión y
`ppi-enforce-agent` en el host DMZ. En el host, tabla `inet cyberflow` (cadena `entrada`,
hook input, política accept), set de bloqueados y set de limitados (100/s, ráfaga 5). El
agente eleva solo `nft` con `sudo -n` (NOPASSWD acotado).

**Rollback:**

```bash
# en el HOST: modo sombra (quitar --aplicar del ExecStart) o parada completa
sudo systemctl edit --full ppi-enforce-agent.service && sudo systemctl daemon-reload
sudo systemctl disable --now ppi-enforce-agent.timer && sudo nft delete table inet cyberflow
# en el SENSOR (opcional): dejar de publicar
sudo systemctl disable --now ppi-publicar-feed.timer
```

## 🟨 Producto

- **Unificar `main` y el panel desplegado.** Las tres vistas, el visor de código y
  «Pruebas previas» están en la rama del sensor (`as-deployed-sensor-20261006`); `main`
  tiene la documentación canónica, los heurísticos `.2`, el publicador corregido y la
  tarjeta Detector real, pero no esas vistas. Decidir cómo converger sin perder ninguna de
  las dos.
- **Perfil de configuración real**: hoy `configs/cyberflow.toml` es el perfil genérico
  histórico (OCSVM, `1,8126`); Sensor1 usa `cyberflow.local.toml`.
- **Descripción de la unidad `ppi-motor`**: aún dice «OCSVM»; corregir al planificar un
  despliegue.
- **Higiene:** revocar la llave `cyberflow-to-srv` al cerrar el proyecto.

## 🟩 Publicación (tesis)

- **Artículo a IJIES**: el cambio OCSVM → IF lo lleva el compañero con
  [`02-metodologia/trazabilidad/FICHA-CAMBIO-ARTICULO-OCSVM-A-IF.md`](02-metodologia/trazabilidad/FICHA-CAMBIO-ARTICULO-OCSVM-A-IF.md).
- **Validación externa**: aplicar TAM y juicio de expertos; Alfa de Cronbach ≥ 0,70 y V de
  Aiken ≥ 0,80 con respuestas reales. Tener los instrumentos no la cierra.
- **DOI Zenodo**: `.zenodo.json` ya describe el despliegue vigente; publicar cuando toque.
- **Versionado**: una sola versión principal, `v1.0.0` sobre `main` (decisión del 30-sep);
  el tag es foto inmutable y `main` la versión viva.

---

## ✅ Hecho (contexto)

- **Documentación pública alineada al despliegue** en `main@01b6f3f`, con CI verde
  (incluye 328 pruebas en CPython 3.14.4 y la reproducción del modelo publicado) — 9-oct.
- **Panel desplegado** en Sensor1 con TLS + login + roles (30-sep) y con tres vistas,
  visor y «Pruebas previas» (9-oct).
- **Reentrenamiento supervisado** (11-oct, `main@7ca06d1`): saneamiento, linaje, límite
  de influencia y deriva contra el conjunto de oro. El candidato es nocturno y lo promueve
  una persona. Tiene sección «Aprendizaje» en el panel y aparece en la Vista 3 del diagrama.
  **Activado en el Sensor1** (nota `S`):
  - base y oro reconstruidos desde la nota L, verificados por sha256;
  - el primer lote real (10-oct) fue rechazado porque la red estaba sin tráfico de usuarios.

  **Pendiente:** Mark instala el temporizador con sudo (2 comandos en la nota S) y decide
  entre reinyectar tráfico representativo o recalibrar con un oro nuevo.
- **Replicabilidad del despliegue**: 2.ª VM instalada sin Internet (nota `K`);
  reinstalada desde cero con `main@b9245ed` siguiendo solo los manuales: R1–R8 cumplen, R9
  salvo el login por roles en el navegador (nota `R`, 11-oct).
- **Recalibración**: IF con FPR 4,45 % sobre test normal retenido (nota `L`); detección
  54/84 Kali, 64,3 % (notas `M` y `S`).
- **Enforcement**: LIMIT automático en vivo (nota `O`); BLOCK en banco (nota `N`);
  heurísticos `2026-10-06.2`; timers systemd.
- **v1.0.0** etiquetada con Release en GitHub.

## Histórico (registro del go-live del 1-oct)

El enforcement se puso en vivo el 1-oct con **crons de usuario**: `publicar_feed.py` en el
crontab del sensor, `relay-feed.sh` en el del bastión y `agente_enforce.py --aplicar
--sudo` en el del host DMZ; entonces el rollback era quitar `--aplicar --sudo` del cron y
borrar la tabla. La campaña `prueba-ataque-20261001-031730` demostró la cadena automática
(LIMIT específico a la Kali, `errores:0`) y registró un LIMIT de 3 min sobre `10.10.20.24`,
falso positivo legítimo y reversible. El arreglo `5368613` añadió `--sudo` y el reporte de
errores del agente.
