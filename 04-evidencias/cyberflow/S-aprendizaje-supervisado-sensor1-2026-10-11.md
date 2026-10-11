# S — Aprendizaje supervisado activado en el Sensor1: linaje y primer lote real

**Fecha:** 11 de octubre de 2026 · **Máquina:** `cyberflow-sensor` (10.10.60.11)

**Código:**
- producto `main@c9d08bf`, rama del sensor `79549f7`;
- `scripts/modeling/cyberflow_aprendizaje.py`;
- guía `docs/APRENDIZAJE.md`.

**Qué cambia y qué no:**
- **Cambia:** el `.local.toml` gana la sección `[reentrenamiento]` (`activo = true`, con copia
  `cyberflow.local.toml.bak-20261011-050639`). También se crean el conjunto de oro y el primer lote.
- **No cambia:** el modelo en uso, el umbral y el motor.

## 1. La base y el oro tienen linaje verificable hasta el modelo desplegado

La partición de la nota L se escribió en `/tmp/recal` y ya no existía. Se reconstruyó así:
- se tomaron las primeras **337 980 filas elegibles** de `multilayer-v3.csv`, que solo crece por el final;
- sobre ellas se ejecutó `particionar_linea_base.py --solo-elegibles`, que es determinista.

| Comprobación | Resultado |
|---|---|
| Reparto | 204 148 / 65 633 / 65 421, con 2 778 descartadas por guarda (igual que la nota L) |
| sha256 obtenido | `bdf6f6419ec19e711c7add9e8b5f1440b896b32270c25d69b7e8267d4f9aba7a` |
| sha256 esperado | el mismo: `entrada_sha256` de `artifacts/preliminar/ensayo-if-v2.json`, el paquete del que salió `if_recalibrado_desplegable.joblib` |
| Veredicto | **idéntica byte a byte** |

**Base:** `artifacts/aprendizaje/base/particionado-nota-L.csv`. Sus filas de train y
validation son las que se suman a los lotes nuevos.

**Conjunto de oro:** las 65 421 ventanas de test, en `artifacts/aprendizaje/oro/oro.csv`.
- modo `0444`, sha256 `08604ae3…6ac1`;
- ventanas del 27-sep 09:13 al 29-sep 22:48;
- FPR del modelo vigente sobre el oro: **4,45 %**, la misma cifra de la nota L.

## 2. El primer lote real (10-oct) fue **rechazado**, y es lo correcto

| | Oro (27–29 sep, piloto) | Lote 10-oct |
|---|---|---|
| Filas | 65 421 | 68 920 |
| IPs | 30 | 20 |
| `http_request_rate_60s` (media) | 0,074 | **0,000** |
| `byte_rate_10s` (media) | 430,7 | **5,8** |
| `syn_completion_ratio_10s` | 0,186 | 0,000 |
| PSI máximo (`http_request_rate_60s`) | — | **2,41**, muy por encima del umbral de rechazo de 0,5 |

El motor no marcó ninguna IP ese día: 23 707 decisiones y 0 ALERT. Por eso el filtro de
contaminación no retiró nada.

El lote se rechazó por **distribución**. El 10-oct la red no tenía el tráfico de usuarios
que el piloto inyectó del 27 al 29 de septiembre (HTTP, DNS y sesiones TCP): solo había
plano de control y hosts en reposo.

**Deriva del mismo día:**
- PSI de las puntuaciones 0,41, que es una señal;
- el modelo marcaría como anómalo solo el 0,34 % del lote.

**Interpretación:**
- Aprender ese día como normal enseñaría al modelo que «normal es una red callada».
  Después marcaría como anómala la actividad legítima de los usuarios. El saneamiento lo
  impidió sin intervención.
- Mientras la red siga así, los lotes se rechazarán. No habrá candidato aunque la deriva
  se sostenga, porque el candidato pide 7 lotes aceptados.
- Hay dos salidas, y las dos son decisiones humanas:
  1. **Volver a inyectar tráfico representativo.** Los lotes volverán a parecerse al oro.
  2. **Declarar que la red cambió y recalibrar entera** (INSTALACION §8), con un oro
     nuevo. No es lo mismo que aceptar lotes a mano por encima del oro viejo.

## 2.bis Conjunto de ataques etiquetados y dos hallazgos sobre las notas L y M

Para que el veredicto de un candidato sea completo hacen falta ataques de **esta**
red. Se construyó `artifacts/aprendizaje/ataques/ataques-nota-M.csv` (solo lectura,
sha256 `4affd07f…`) con este criterio:
- ventanas de la Kali (10.10.20.30) con `packet_count_10s > 0`;
- entre las 00:00 y las 02:00 UTC del 30-sep, la campaña de la nota M.

Se apuntó `[reentrenamiento] ataques` a ese fichero.

**Hallazgo 1. El denominador de la nota M es 84, no 78.** Las **54 detectadas se
reproducen exactas** con el modelo desplegado, pero la ráfaga tiene **84** ventanas
activas (de 00:10 a 01:52). Fuera de la ráfaga, la Kali solo emite 1 o 2 ventanas por
hora de ruido de sistema.

| | Nota M / model card | Medido hoy |
|---|---|---|
| Ventanas de ataque | 78 | **84** |
| Detectadas | 54 | 54 |
| Tasa | 69 % | **64,3 %** |

Hay que corregir la cifra en la model card o justificar el criterio de las 78. No
se ha cambiado nada sin la decisión de Mark.

**Hallazgo 2. La línea base de la nota L contiene una ráfaga de la Kali.**
- El 27-sep, de 21:40 a 21:59 UTC, hubo 51 ventanas activas de la Kali.
- Esas ventanas quedaron en la partición **train** del modelo desplegado.
- El modelo marca 44 de ellas y, en total, 50 de las 549 ventanas de la Kali que hay en train.

La memoria del ensayo decía que la Kali estuvo apagada en esa ventana. Los datos dicen
que no.

**Lo que no afecta:** el conjunto de oro no tiene ventanas de ataque. Sus 74 ventanas
de la Kali son ruido de sistema, el modelo no marca ninguna y el FPR sin ellas es 4,46 %
frente a 4,45 %. **El 4,45 % se sostiene.**

**Lo que sí afecta:** la afirmación de que el modelo «se entrenó con tráfico limpio»
deja de ser exacta. Un candidato futuro volvería a aprender esa ráfaga.

**Corrección aplicada** (sin tocar el modelo desplegado):
- se añadió `excluir_ventanas = ["10.10.20.30@2026-09-27T21:35/22:05"]` a la política;
- ningún candidato entrenará con ese tramo, ni desde la base ni desde los lotes;
- cada candidato registra cuántas filas excluyó.

## 3. Temporizador

**✅ Instalado por Mark el 11-oct, 05:24 UTC.** Estado: `active`. Primer disparo el
12-oct a las 00:30 UTC.

Detalle de la instalación:

Las unidades `cyberflow-aprendizaje.service` y `.timer` están generadas en
`~/cf-deploy/unidades/`: corren como `m4rk`, a las 00:30 UTC, con `Nice=19`.

Para instalarlas, Mark ejecuta:

```bash
sudo cp ~/cf-deploy/unidades/cyberflow-aprendizaje.* /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now cyberflow-aprendizaje.timer
```

Hasta entonces, lote y deriva se pueden lanzar a mano (`cyberflow_aprendizaje.py … diario`).

**Lo que todavía no se puede afirmar:**
- No hay ningún candidato real entrenado.
- No hay un conjunto de ataques etiquetados de esta red (`ataques = ""`), así que cualquier
  candidato quedaría en `EVALUACION_INCOMPLETA`.
