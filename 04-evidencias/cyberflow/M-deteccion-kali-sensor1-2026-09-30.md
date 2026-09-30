# M · Detección de ataques reales (Kali) con el modelo recalibrado — sensor1

**Fecha:** 30 de septiembre de 2026
**Máquina:** `cyberflow-sensor1` (10.10.60.11), red real; atacante Kali `10.10.20.30` → DMZ `10.10.30.10`.
**Objetivo:** cerrar la otra mitad del FPR de la nota `L`: medir la **detección (TPR)**
con el **modelo recalibrado** y su **umbral congelado** (`alpha=0,05`, el mismo que
da 4,45 % de falsos positivos), sobre ataques reales en la **misma red** que su
tráfico normal de entrenamiento.

## Método

- Ataques lanzados desde la Kali con `~/atacar2.sh` (nmap `-sT -p-`, nikto, flood
  de login, password-spray, dns-entropy), todos con `timeout` para no colgarse.
- El sensor los capturó por el espejo SPAN. La Kali **solo genera tráfico cuando
  ataca** (apagada durante toda la línea base), así que sus ventanas activas =
  ventanas de ataque; no hace falta un timestamp exacto.
- Se puntuaron las **78 ventanas activas** de `10.10.20.30` del 30-sep con
  `artifacts/preliminar/ensayo-if-v2.joblib` (harness `scripts/modeling/puntuar_deteccion.py`).
  Detección = `decision_function(x) < umbral (-0,068892)`.

## Resultado

| Ataque | Ventanas | Detectadas | TPR |
|---|---|---|---|
| HTTP (web-scan / fuerza bruta / flood) | 27 | 27 | **100 %** |
| Escaneo / sondeo de puertos | 43 | 27 | **63 %** |
| DNS-entropy | 8 | 0 | **0 %** |
| **TOTAL** | **78** | **54** | **69 %** |

Emparejado con la nota `L`: **FPR 4,45 % · TPR 69 % global (100 % en ataques HTTP)**
al mismo punto de operación. Contraste: sin recalibrar, el modelo desplegado
alertaba al **92,4 %** de *todo* (ruido), no detección útil.

## Interpretación honesta

- **Fuerte donde importa:** los ataques volumétricos y de credenciales —los más
  frecuentes según DBIR/OWASP (ver entregable 11)— se detectan al **100 %**.
- **Escaneo 63 %:** las ráfagas se detectan; el escaneo lento/bajo se diluye.
- **DNS-entropy 0 %:** limitación real (esas ventanas tienen ~3 paquetes y parecen
  normales), **pero** el ataque apuntó al DMZ `10.10.30.10`, que no es un resolver,
  así que la señal `dns_nxdomain_ratio_60s` no se disparó. El 0 % mezcla un hueco
  del modelo con un montaje de prueba imperfecto. **Repetir apuntando al DNS real
  (`10.10.10.20`)** antes de concluir. Junto con el ARP spoofing (nota escenarios),
  son los casos que piden una regla determinista, no ML de una sola clase.

## Comparación con la detección preliminar

La nota `L` estimó 45 % (cross-dataset, piso pesimista). En la **misma red**, sube a
**69 % global / 100 % HTTP**, como se predijo: el normal de entrenamiento y el
ataque comparten distribución.

## Pendiente para cerrar (P2 → `v1.0.0`)

1. (Opcional) repetir DNS-entropy contra `10.10.10.20` para separar hueco de modelo
   de artefacto de prueba.
2. **Congelar** `ensayo-if-v2` como modelo desplegado → `calibrado_en_esta_red=true`
   (toca el modelo vivo; coordinar con el fin del piloto).
3. Etiquetar `v1.0.0`.
