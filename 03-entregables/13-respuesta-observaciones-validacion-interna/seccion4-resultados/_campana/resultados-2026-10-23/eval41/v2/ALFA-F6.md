# F6 — Sensibilidad a α (CORREGIDO: validación original 65 633)

**Corrección (2026-10-23):** la versión previa calculó los cuantiles sobre 65 553 ventanas
(validación **sin** la entidad Kali). El **umbral operativo** `−0,5693969936322356` se reproduce
**exacto** con el cuantil α=0,05 sobre la **validación ORIGINAL de 65 633** (la que usó la calibración),
no sobre las 65 553. Esta tabla usa la validación original; la depurada queda como complementaria
(ver `CIERRE-4.1-REAUDIT-2026-10-23.md`, Punto 1).

Cuantil numpy (interpolación lineal); alerta = `score_samples < umbral`. Cortes calculados en
validación y aplicados al test (65 421 normal + 84 ataque). **α=0,05 es la configuración CONGELADA**
(reproduce el operativo); los demás α son sensibilidad, no una re-selección.

| α | Umbral (score_samples) | FPR observado (test) | Recall | Precisión | F1 |
|---:|---:|---:|---:|---:|---:|
| 0,01 | −0,6223738394125686 | 0,87 % | 59,52 % | 8,10 % | 0,1427 |
| 0,025 | −0,5952528323894616 | 2,18 % | 63,10 % | 3,59 % | 0,0679 |
| **0,05** | **−0,5693969936322356** | **4,53 %** | **64,29 %** | 1,79 % | 0,0348 |
| 0,10 | −0,5369318991910549 | 9,33 % | 70,24 % | 0,96 % | 0,0189 |

- El α=0,05 da el **umbral operativo exacto** y FPR 4,53 %. Se describe el **compromiso observado**:
  bajar α recorta FPR **y** recall; subirlo gana poco recall a gran costo de FPR. **No** se afirma que
  0,05 sea "óptimo" ni "punto de equilibrio" (no había meta de aceptación definida de antemano más allá
  del objetivo de ~5 % de FPR fijado en validación). La literatura puede sustentar el **procedimiento**
  de calibración por percentil, no que 0,05 sea óptimo para esta red.
- **Complementario (validación depurada, 65 553 sin entidad Kali):** α=0,05 → umbral
  −0,5694578968203694 (Δ −6,1e-5 vs operativo). Composición distinta; no reemplaza al operativo.
- Precisión baja en toda la tabla por el desbalance (prevalencia 0,13 %); ver Punto 4.D del cierre.
</content>
