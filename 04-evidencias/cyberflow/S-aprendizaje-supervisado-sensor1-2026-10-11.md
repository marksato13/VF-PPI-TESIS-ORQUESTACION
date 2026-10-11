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
