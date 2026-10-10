# Pendientes — CyberFlow

**Actualizado:** 9 de octubre de 2026. Fuente única de «qué falta». El estado de cada
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

Corre por **timers systemd** con `OnCalendar=minutely` (reemplazaron a los crons el
6-oct): `ppi-publicar-feed` en el sensor, `ppi-relay-feed` en el bastión y
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
- **Replicabilidad del despliegue**: 2.ª VM instalada sin Internet (nota `K`).
- **Recalibración**: IF con FPR 4,45 % sobre test normal retenido (nota `L`); detección
  54/78 Kali (nota `M`).
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
