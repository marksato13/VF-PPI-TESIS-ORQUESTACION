# Contexto del proyecto

Lo que un agente necesita saber antes de tocar nada. **Toda cifra aquí tiene
fuente primaria citada**; ninguna se escribe de memoria.

## El producto en una frase

Un sistema que **detecta comportamiento anómalo en red y bloquea la IP ofensora
en el propio router**, validado sobre tráfico real de laboratorio. La mayoría de
sistemas de detección solo avisan; este actúa.

## Topología del laboratorio

| VM | Función | PPI-MGMT | PPI-LAN | PPI-DMZ |
|---|---|---|---|---|
| VM01 | Administración y agentes | `10.10.10.10` | — | — |
| **VM02** | **Sensor, router, Suricata y motor** | `10.10.10.20` | `10.20.0.1` | `10.30.0.1` |
| VM03 | Servidor protegido | `10.10.10.30` | — | `10.30.0.10` |
| VM04 | Kali, ataques controlados | `10.10.10.40` | `10.20.0.100` | — |
| VM05 | Cliente legítimo y carga | `10.10.10.50` | `10.20.0.20` | — |

**VM02 es sensor y router a la vez.** Todo el tráfico LAN↔DMZ pasa por ella, así
que el bloqueo no necesita SSH a otra máquina: escribe una regla `nftables` en su
propia tabla (`inet ppi_enforce`, hook *forward*, prioridad −300) con expiración
nativa de 120 s.

## Estado congelado

| Artefacto | SHA-256 (prefijo) |
|---|---|
| `artifacts/dataset/multilayer-v2-normal.csv` | `3846d44c…28ab` |
| `artifacts/dataset/multilayer-v2-anomalies.csv` | `d115ef98…78c3` |
| `artifacts/model/manifest.json` | `0a1e8c52…5b1b` |
| `artifacts/model/ocsvm_scaled.joblib` | `af9b50c2…7236` |

Verificación: `sha256sum -c docs/dataset/SHA256SUMS` (13 archivos).

**«Modelo congelado» significa** un archivo guardado en disco con su hash
publicado, que **nunca se reentrena**: se carga tal cual y se le pasan los datos.

## Dataset

| | |
|---|---|
| Episodios normales | **220** → 1 373 ventanas |
| Particiones | 824 entrenamiento · 273 validación · **276 prueba** |
| Ventanas de anomalía | **179** (161 de Kali real + 18 heredadas) |
| Variables | **28 definidas, 27 con variación observable** |
| Partición | **por episodio completo**, `no_episode_split = true` |

Un **episodio** es una corrida de captura: se enciende, se genera un tipo de
tráfico, se apaga. Cada corrida se parte en ventanas y cada ventana es una fila.
Las ventanas de una misma corrida se parecen mucho entre sí, así que repartirlas
al azar haría que el modelo reconociera la corrida en vez del ataque.

## Modelo y resultados

| Métrica | Valor | Fuente primaria |
|---|---|---|
| Modelo | `ocsvm_scaled`, ν = 0,05 | `artifacts/model/manifest.json` |
| Umbral | `1.8126087939765134`, regla `score < threshold` | ídem |
| ROC-AUC | **0,9741** | `fase04-modelado/07-metricas-clasificacion-*.md` |
| Detección Kali real | **88,8 %** (143/161) | `fase04-modelado/06-modelo-final-congelado-ocsvm.md` |
| Detección global | **88,3 %** (158/179) | ídem |
| FPR laboratorio | **4,71 %** (13/276) · IC [2,8 – 7,9] | `fase04-modelado/09-validacion-cruzada-*.md` |
| **FPR operación, pase 1** | **25,81 %** (16/62) · IC [16,6 – 37,9] | `fase07-validacion-final/02-resultados-f6.md` |
| **FPR operación, pase 2** | **22,97 %** (17/74) · IC [14,9 – 33,7] | ídem |
| Lead time de bloqueo | mediana **8,0 s** (6,1 – 13,7) | ídem |
| Estabilidad del umbral | CV **4,10 %**, banda [1,6496 – 1,8132] | `fase04-modelado/09-validacion-cruzada-*.md` |

## Las cinco debilidades abiertas

| ID | Qué falta | Gravedad |
|---|---|---|
| **P-1** | El sistema bloquea tráfico legítimo pesado | Crítica |
| **P-2** | El modelo se eligió mirando el conjunto de prueba | Crítica |
| **P-3** | Nadie ha usado el panel salvo el equipo (SUS con 0 respuestas) | Alta |
| **P-4** | No se sabe si funciona en otra jornada | Alta |
| **P-5** | Faltan 4 escenarios legítimos del jurado | Media |

**P-2 y P-4 se cierran con la misma campaña**: una jornada nueva que el modelo no
haya visto.

## Lo que se tiene y lo que no

| | Estado |
|---|---|
| **Reproducibilidad** | ✅ Mismos datos y código → mismas cifras (13/276 y 158/179) |
| **Replicabilidad** | ❌ Exige datos nuevos. **No la hay** |
| **Confiabilidad** | ✅ 10 ajustes → mismo hash y umbral; dos pases equivalentes |
| **Pertinencia** | ❌ Ninguna medición con usuarios |

## Las dos objeciones que el jurado hará

1. **«Su sistema falla el 25 % de las veces.»** Falla sobre tráfico legítimo muy
   pesado, condición medida y declarada por el propio equipo. En condiciones
   normales, 4,71 %.
2. **«¿Eligieron el modelo después de ver los resultados?»** Sí, y está declarado
   en la *model card* antes de cualquier métrica. Se corrige con evaluación
   nueva, no escribiendo.

Decirlo antes de que lo encuentren es lo que da credibilidad al resto.
