# Runbook — corrida de la Kali para medir detección (TPR)

**Objetivo:** medir cuántos ataques detecta el modelo **recalibrado** con su
**umbral congelado**, sobre la **misma red** que su tráfico normal de
entrenamiento. Es la mitad que le falta al FPR de 4,45 % (ver nota `L`).

> **Preparado, NO disparado.** El encendido físico de la Kali (`10.10.20.30`) lo
> hace **Mark**, no el agente. No lanzar durante una ventana de piloto legítimo.
> Ver [[cyberflow-prueba-funcional]].

## Precondiciones
1. La ventana de piloto legítimo ha terminado (era «hasta el lunes por la tarde»).
2. Existe el modelo preliminar: `artifacts/preliminar/ensayo-if-v2.joblib`
   (entrenado 29-sep sobre la base de sensor1; umbral `alpha=0,05`).
3. Mark **enciende** la Kali (`10.10.20.30`) y confirma que la DMZ objetivo es la
   autorizada.
4. Campaña con nombre y timestamps propios (p.ej. `prueba-ataque-2026xxxx`), NO
   mezclada con `piloto-con-dns`.

## Los seis perfiles de ataque (`scripts/dataset/run_v2_anomaly_kali.py`)

| Perfil | Señales que deberían encenderse |
|---|---|
| `ANOM-KALI-SYN-RATE-50` | `syn_rate_10s`, `rst_ratio_10s`, `unique_dst_port_ratio_30s` |
| `ANOM-KALI-PORT-SCAN` | `unique_dst_port_ratio_30s`, `syn_completion_ratio_10s` |
| `ANOM-KALI-PORT-SCAN-WIDE` | `unique_dst_port_ratio_30s`, `syn_rate_10s` |
| `ANOM-KALI-UDP-PROBE-50` | `packet_rate_10s`, `protocol_diversity_30s` |
| `ANOM-KALI-PASSWORD-SPRAY-50` | `http_auth_failure_ratio_60s`, `http_request_rate_60s` |
| `ANOM-KALI-DNS-ENTROPY-50` | `dns_nxdomain_ratio_60s`, `unique_dns_name_ratio_60s` |

Disparar cada uno (desde el host que orquesta las campañas F, el mismo que corrió
F6; el script llama a `scripts/campaign/run-f1-kali.sh` y extrae features v2):

```bash
for P in ANOM-KALI-SYN-RATE-50 ANOM-KALI-PORT-SCAN ANOM-KALI-PORT-SCAN-WIDE \
         ANOM-KALI-UDP-PROBE-50 ANOM-KALI-PASSWORD-SPRAY-50 ANOM-KALI-DNS-ENTROPY-50; do
    python3 scripts/dataset/run_v2_anomaly_kali.py --profile "$P" --episode 1
done
```

Cada corrida escribe features en `$PPI_ARTIFACTS_ROOT/features-v2/<campaign_id>/`
(por omisión `/srv/ppi-evidence/artifacts`).

## Medir la detección (agente, tras la corrida)
Para cada CSV de features de ataque generado:

```bash
.venv/bin/python scripts/modeling/puntuar_deteccion.py \
    --modelo artifacts/preliminar/ensayo-if-v2.joblib \
    --csv <features-v2/CAMPAIGN/features.csv>
```

`tasa_deteccion` = fracción de ventanas de ataque con `score < umbral` = **TPR**
por perfil. Se agrega el TPR global y se compara: se espera **muy por encima** del
45 % cross-dataset preliminar, porque aquí el normal de entrenamiento y el ataque
son de la **misma red**.

## Cerrar
- TPR (Kali, esta red) + FPR (4,45 %) → afirmación de detección completa.
- Entonces **congelar** el modelo → `calibrado_en_esta_red=true` (toca el modelo
  vivo; coordinar) → desbloquea `v1.0.0` (P2).

## Lo que NO hacer
- No encender la Kali por cuenta del agente (lo hace Mark).
- No lanzar ataques contra nada fuera de la DMZ autorizada.
- No mezclar la campaña de ataque con la línea base normal (partición
  `evaluation_only`, ya forzada por el script).
