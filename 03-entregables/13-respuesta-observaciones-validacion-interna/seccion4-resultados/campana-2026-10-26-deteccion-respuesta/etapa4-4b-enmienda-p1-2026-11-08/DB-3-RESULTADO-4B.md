# DB-3 sobre la 4B (09-nov-2026): resultado por perfil

**Estado: ejecutado en el portátil sobre las copias verificadas del Sensor1; sin publicar.** Herramientas idénticas a las publicadas (`analisis_db3.py` `618c355d…`, `limites_db3.py` `e9b500b6…`) y a las que usó `s50` en el Sensor1 (`salud_captura.py` `274b4d61…`, `config-campana-4c.json` `f177d9bb…`).
Reglas aprobadas por Mark: L1 ≤ 1.0 aviso/entidad·hora, L2 ≤ 10 % de ventanas en ALERT, separación de aviso 60 s, mínimo 2.0 h C0 por perfil, seis perfiles obligatorios. Intervalo: 2026-11-08T18:00:00+00:00 → 2026-11-09T02:00:00+00:00.

## Entradas (hashes completos)

| Fichero | sha256 |
|---|---|
| `copias/motor_decision.log` | `c56b79cba981570687485fabdc14f4905be740a398ba46e22375a77e70660c48` |
| `replay/motor_decision.log (inventario)` | `d7332d97ee0834fcc5f938bbc5c8be120b24642f0b48d9fa6e7b8c33d63372be` |
| `copias/eve-segmento.json` | `6844e36c675e3e0a97fb163bc4cfb7a837b118660a7750cb55564c39cf8456f4` |
| `analisis/incrementos.jsonl` | `1ebaf0c28815fbee659a8e285b1fe37b42f22d9b424e35e90a77a1b11d985938` |
| `salud/tcpdump-anillo.log` | `b64cf99fb81a2712b2b97c6321e358765059decbec65cfcaf51ea1a2847da74e` |

Las dos primeras figuran en `copias/SHA256SUMS` del Sensor1 (el inventario y los incrementos, comparados byte a byte contra el Sensor1); `tcpdump-anillo.log` en `salud/SHA256SUMS-tcpdump`. `--ahora` = 1794195057.59889, el mismo instante con que `s50` midió Suricata.

## α = 0.05: **no_cumple** (elegible: no)

| Perfil | IP | Ventanas requeridas | Decididas C0 | Faltantes | Horas C0 | L1 avisos/h (obs.) | L1 | L2 % en ALERT (obs.) | L2 | Resultado |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|
| ofimática | `10.10.20.21` | 2881 | 2881 | 0 | 8.003 | 14.870 | no_cumple | 9.72 % | cumple | **no_cumple** |
| navegación | `10.10.20.22` | 2881 | 2881 | 0 | 8.003 | 1.250 | no_cumple | 78.72 % | no_cumple | **no_cumple** |
| descargas | `10.10.20.23` | 2879 | 2879 | 0 | 7.997 | 4.752 | no_cumple | 1.63 % | cumple | **no_cumple** |
| aplicación | `10.10.20.24` | 2881 | 2881 | 0 | 8.003 | 6.373 | no_cumple | 60.43 % | no_cumple | **no_cumple** |
| ligero | `10.10.20.25` | 2846 | 2846 | 0 | 7.906 | 0.000 | cumple | 0.00 % | cumple | **cumple** |
| errático | `10.10.20.26` | 2881 | 2881 | 0 | 8.003 | 10.871 | no_cumple | 22.28 % | no_cumple | **no_cumple** |

Reportadas aparte (no deciden): `10.10.10.20` no_cumple, `10.10.10.21` no_cumple, `10.10.40.10` no_cumple, `10.10.50.51` no_cumple, `10.10.50.52` no_cumple, `10.10.60.42` cumple. Las demás IP tienen menos de 1 000 ventanas.

## α = 0.03: **no_cumple** (elegible: no)

| Perfil | IP | Ventanas requeridas | Decididas C0 | Faltantes | Horas C0 | L1 avisos/h (obs.) | L1 | L2 % en ALERT (obs.) | L2 | Resultado |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|
| ofimática | `10.10.20.21` | 2881 | 2881 | 0 | 8.003 | 7.622 | no_cumple | 3.23 % | cumple | **no_cumple** |
| navegación | `10.10.20.22` | 2881 | 2881 | 0 | 8.003 | 6.248 | no_cumple | 57.69 % | no_cumple | **no_cumple** |
| descargas | `10.10.20.23` | 2879 | 2879 | 0 | 7.997 | 0.375 | cumple | 0.10 % | cumple | **cumple** |
| aplicación | `10.10.20.24` | 2881 | 2881 | 0 | 8.003 | 15.245 | no_cumple | 34.81 % | no_cumple | **no_cumple** |
| ligero | `10.10.20.25` | 2846 | 2846 | 0 | 7.906 | 0.000 | cumple | 0.00 % | cumple | **cumple** |
| errático | `10.10.20.26` | 2881 | 2881 | 0 | 8.003 | 10.621 | no_cumple | 17.42 % | no_cumple | **no_cumple** |

Reportadas aparte (no deciden): `10.10.10.20` no_cumple, `10.10.10.21` cumple, `10.10.40.10` no_cumple, `10.10.50.51` no_cumple, `10.10.50.52` no_cumple, `10.10.60.42` cumple. Las demás IP tienen menos de 1 000 ventanas.

## α = 0.01: **no_cumple** (elegible: no)

| Perfil | IP | Ventanas requeridas | Decididas C0 | Faltantes | Horas C0 | L1 avisos/h (obs.) | L1 | L2 % en ALERT (obs.) | L2 | Resultado |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|
| ofimática | `10.10.20.21` | 2881 | 2881 | 0 | 8.003 | 0.375 | cumple | 0.10 % | cumple | **cumple** |
| navegación | `10.10.20.22` | 2881 | 2881 | 0 | 8.003 | 19.868 | no_cumple | 20.90 % | no_cumple | **no_cumple** |
| descargas | `10.10.20.23` | 2879 | 2879 | 0 | 7.997 | 0.000 | cumple | 0.00 % | cumple | **cumple** |
| aplicación | `10.10.20.24` | 2881 | 2881 | 0 | 8.003 | 12.496 | no_cumple | 5.97 % | cumple | **no_cumple** |
| ligero | `10.10.20.25` | 2846 | 2846 | 0 | 7.906 | 0.000 | cumple | 0.00 % | cumple | **cumple** |
| errático | `10.10.20.26` | 2881 | 2881 | 0 | 8.003 | 9.997 | no_cumple | 10.07 % | no_cumple | **no_cumple** |

Reportadas aparte (no deciden): `10.10.10.20` cumple, `10.10.10.21` cumple, `10.10.40.10` cumple, `10.10.50.51` cumple, `10.10.50.52` cumple, `10.10.60.42` cumple. Las demás IP tienen menos de 1 000 ventanas.


## Aclaración de la discrepancia sobre `.21`, `.23` y `.25`

**Qué decía mi informe de `s50`:** «cinco tienen las 2881 ventanas posibles, y `.25` 2846; `.23` 2879 y `.21` 2878 (en la IP 10.10.10.21)». Era **inexacto en dos cosas** y confundía dos hosts distintos.

| IP | Qué es | Ventanas (motor en vivo = inventario del replay) | Posibles en la rejilla de 10 s (2881) |
|---|---|---:|---|
| `10.10.20.21` | perfil **ofimática** | **2881** | todas |
| `10.10.10.21` | **otro host** (infraestructura; no es el perfil `.21`) | 2878 | faltan 3 (19:34:30Z; 22:06:40–22:06:50Z) |
| `10.10.20.23` | perfil **descargas** | 2879 | faltan 2 (20:08:40Z; 21:22:00Z) |
| `10.10.20.25` | perfil **ligero** | 2846 | faltan 35 (en 21 tramos de 1 a 2 ventanas, repartidos en las 8 h) |

- **`.21` no tiene ventanas ausentes:** el 2878 que cité era de `10.10.10.21`. Corrijo el informe.
- **Las ausencias no son pérdida del detector.** Son idénticas en el motor en vivo y en el inventario del replay (0 «solo en vivo», 0 «solo en inventario»); por eso para DB-3 las ventanas **requeridas** de `.23` y `.25` son 2879 y 2846, no 2881, y sus faltantes son 0 (requeridas = decididas). `s50` también da `cobertura_total` 1,0, 0 no evaluadas y 0 ausentes. La Suricata de todas las ventanas decididas es `cero_descartes`.
- **Lo que NO está demostrado:** que en esas ventanas el perfil no generara tráfico. Contrasté con el EVE de la corrida (`evidencia-pendiente/4b-db3/discrepancia2.py`): `.23` tiene 18 697 eventos EVE y `.25` 12 695; en las 2 ventanas ausentes de `.23` hay eventos EVE en 1 de ellas dentro de (w−10, w] y en las 2 dentro de (w−60, w]; en las 35 de `.25`, en 28 dentro de (w−10, w] y en las 35 dentro de (w−60, w]. Por tanto **la causa de que el motor no construyera esas filas queda sin determinar** (por ejemplo, ventanas sin flujo nuevo cuyas filas se atribuyen a otra ventana); no es atribuible al detector ni descartable por falta de tráfico. Se declara como límite.
- **Efecto en DB-3:** ninguno en el veredicto. Las horas requeridas del denominador de L1 son 7,997 h (`.23`) y 7,906 h (`.25`) en lugar de 8,003 h; `.25` no tiene ninguna ALERT con ningún α y `.23` cumple con α 0,03 y 0,01, y no cumple con α 0,05 por L1 (4,75 avisos/h), con 0,0163 de L2. Con 8,003 h el resultado de ninguno cambiaría de lado (4,75 → 4,75; 0 → 0).
