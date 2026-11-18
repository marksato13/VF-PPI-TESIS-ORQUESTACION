# Protocolo del replay 4.3 — CyberFlow vs Suricata ET Open (fijado ANTES de procesar)

Fijado el 2026-11-11, antes de copiar ningún PCAP al comparador y de ejecutar Suricata. El hash de este documento y de las dos listas fijas se registra en `FIJADO.txt` (mismo directorio). Alcance: **solo las capturas existentes de la cuarta corrida de la Campaña A**; ningún tráfico nuevo.

## 1. Población evaluada (aprobada por Mark)
- **Evaluación principal del 4.3:** cuarta corrida de la Campaña A (9–10-nov-2026, modo sombra, nonce `4c-20261109T215425Z-3bf15267cb93`), **21 de 25 episodios elegibles**.
- **Elegibilidad (fijada antes de comparar):** 12 requisitos de integridad «verificado» (`integridad.json`) + fuente `completa` (clase C0) + observación completa (`en_poblacion_principal`).
- **Elegibles (21):** `dns_inusual-r1…r5`, `inundacion_http-r1…r5`, `fuerza_bruta_http-r1…r5`, `escaneo_sostenido-r1…r5`, `escaneo_breve-r4` (lista con inicio/fin en `episodios-elegibles.csv`).
- **Excluidos (4), documentados, no sustituidos:** `escaneo_breve-r1`, `-r2`, `-r3`, `-r5`. Motivo único: `integridad no apta` por el requisito `cobertura_durante` («durante incompleta»: 0 anclas esperadas de la Kali en un barrido de ~5 s). Los otros 11 requisitos están verificados. Ver `ESCANEOS-BREVES-SIN-ANCLAS.md` del repositorio. No entran en ningún recuento.
- **Antecedentes separados (no evaluación principal):** la batería N=3 del 5-oct (los «nueve» del texto anterior de la Tabla 5), Nikto (6-oct) y la pasada del 23-oct. No se mezclan con esta población.
- **Fuerza bruta HTTP** (5 elegibles) se incluye por estar en la corrida y ser elegible; la Tabla 5 la trata como «ensayo adicional» y se reporta como familia aparte.

## 2. Regla de alerta válida de Suricata (atribución al episodio)
Una alerta de `eve.json` cuenta como **detección del episodio E** si cumple **todo**:
1. `event_type = alert`.
2. **Exclusiones del conteo de detección:** firma que empieza por `SURICATA STREAM ` **o** por `ET INFO `. Se cuentan e informan aparte, nunca como detección.
3. **Tiempo:** `timestamp` del evento (tiempo del paquete, UTC) ∈ [`t_inicio`, `t_fin` + 60 s] de E (marcas del generador, sha256 `5fd72ab9da47eb7fddc498debec1f4affcdb127e3636c339663d362d3e3fe1c1`). Es **durante el episodio** si ≤ `t_fin`; **posterior** si ∈ (`t_fin`, `t_fin`+60 s]. El margen de 60 s es el mismo que usa `analizar_3b.py` para las ventanas requeridas.
4. **Origen y destino:** {`src_ip`, `dest_ip`} = {10.10.20.30, destino del episodio} en cualquiera de los dos sentidos (una firma de respuesta también es atribuible). Destino: DNS → 10.10.10.20; resto → 10.10.30.10.
5. **Comportamiento (interpretación fijada):** el puerto del extremo servidor es el del servicio generado: inundación TCP/80; fuerza bruta TCP/18081; DNS UDP/53 o TCP/53; escaneos: cualquier puerto TCP del destino. No se exige que la firma «se llame» como la técnica; se exige que ocurra sobre el comportamiento generado.
- **Detección del episodio (principal)** = ≥1 alerta válida **durante el episodio** (≤ `t_fin`). Las posteriores se informan como «tardía» y no cuentan.
- **Alertas no STREAM/ET INFO con prefijo `SURICATA`** (de motor/decodificación): cuentan según la regla; se listan por SID y se reporta además la sensibilidad «excluyéndolas».
- **Control legítimo:** una alerta (no STREAM/ET INFO) cuenta como falsa alarma de la entidad-ventana a la que pertenece (ver §5); las alertas sobre extremos fuera de la población de CyberFlow se informan sin contarse.

## 3. Configuración de CyberFlow que se compara
**Principal: híbrido `HIB_0.03`** = Isolation Forest con α = 0,03 + heurísticos. Razón (previa al replay y ajena a Suricata): el artículo adopta el percentil 3 (§3.3.5, umbral −0,5898535710336618 en escala de puntuación). Se informan además, como aporte de componentes (Tabla 5, fila «por componentes»): `IF_0.03` solo y `HEUR` solo.
| Elemento | Valor |
|---|---|
| Modelo | `if_limpio_2026_10` (`if_limpio_2026_10_desplegable.joblib` sha256 `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60`) |
| Manifiesto | `manifest-if-limpio-2026-10.json` sha256 `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7` |
| Umbral α = 0,03 | −0,5898535710336618 (`score_samples < umbral`); procedencia verificada el 10-nov (cuantil 0,03 de 65 553 puntuaciones de validación sin Kali) |
| Heurísticos | `VERSION_UMBRALES = 2026-11-02.1` (`heuristicos.py` sha256 `5d30ffe6a8156c07954f39752e175becb7bfa0fd21a6119e1e6537b2a1217f68`) |
| Motor | candidato `ec78ca5` (`motor_decision.py` sha256 `b652582dd9ac8ee5754bde9fb1b9cb90bc713575320685232353033014dfc565`), motor en vivo del Sensor1 desde 2026-11-09 19:28:12Z |
| Salida analizada | `analizar_3b.py` / `s50` v2 → `analisis-4c/analisis-3b.json` sha256 `3aa77fc0f5b70694cafb260f5d6edabe54bbfa10c870fed8f8a6e7c7fb0215f1`; registro de decisiones `motor_decision.log` sha256 `733d7a0cab66ef1a6358c80cc2285a6d0da8693722c11a018c5dfb49bb9267cd` |
| Señal atribuible | la de `analizar_3b.py`: la configuración da señal en la ventana **y** hay paquetes del origen hacia el destino dentro de la ventana y de [inicio, fin] |
No se reentrena ni se recalibra nada; CyberFlow **no se vuelve a ejecutar**: se usa su salida ya registrada sobre esos mismos PCAP.

## 4. Configuración de Suricata
| Elemento | Valor |
|---|---|
| Host | comparador `suricata-comparator` 10.10.60.13 (usuario `adminsuricata`), Suricata **7.0.3 RELEASE**, servicio `inactive`/`disabled`; sin sudo, sin arrancar el servicio |
| Reglas ET Open | `/var/lib/suricata/rules/suricata.rules` sha256 `7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9` (53 012 `alert` + 1 `drop` = 53 013 habilitadas; snapshot 2-oct-2026; tarball `et-open-20261002.tar.gz` sha256 `3facf0eaed30caf56d2eba43d96ccd2b79dcc851c8d6be4c822e67b4120a7355`) |
| YAML original | `/etc/suricata/suricata.yaml` sha256 `d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650`; `HOME_NET: "[10.10.30.0/24]"`, `EXTERNAL_NET: "!$HOME_NET"` |
| **Configuración principal** | copia del YAML original con **una sola línea cambiada**: `HOME_NET: "[10.10.10.0/24,10.10.30.0/24]"` (cubre DC1 10.10.10.20 y la DMZ 10.10.30.10; la Kali 10.10.20.30 queda fuera = `EXTERNAL_NET`). El hash de la copia se registra tras crearla, antes de la primera ejecución. No se toca `/etc/suricata` |
| **Sensibilidad S1 (separada)** | YAML original sin cambios (`HOME_NET [10.10.30.0/24]`), mismas reglas y mismos PCAP |
| Comando (ambas) | `suricata -r <slice.pcap> -c <yaml> -S /var/lib/suricata/rules/suricata.rules -l <salida>/<slice> -k none --runmode single --set unix-command.enabled=no` |
| PCAP | los **mismos** PCAP crudos que consumió CyberFlow (con la duplicación del espejo). **No** se deduplica; los STREAM resultantes se excluyen del conteo por la regla §2. La sensibilidad con deduplicado queda fuera de este alcance y se declara |

## 5. PCAP y control
- **Rebanada por episodio** = los ficheros de su `pcap-manifiesto.json` (≈ 120 s previos + episodio + cola), concatenados en orden de nombre. **Control** = los 371 ficheros `live-20261109212155…212253` (21:21:55–21:52:53Z) que cubren las ventanas del control [21:23:00, 21:53:00]Z (con 60 s de historia). Control declarado antes de empezar (`control-declarado.json`): sin ataques, sin sondas, 6 perfiles a factor 1,0.
- **Hashes por fichero** (de los manifiestos / del `archivar.log` del Sensor1; coinciden con `sha256_archivador`): `pcap-lista-fija.csv` (1 634 filas, 22 rebanadas). Se verifica cada fichero **antes** de unirlo; si algún hash falla, la rebanada es **indeterminada**.
- Se registra el sha256 de cada rebanada unida (derivada determinista) en los resultados.
- Origen: Sensor1 `~/cf-e4/4c-A-completa-20261110T0951Z/archivo-pcap/` (solo lectura) → bastión → comparador por tubería ssh (sin copia intermedia).

## 6. Unidad común del control legítimo y de la comparación
- **Unidad de control A — entidad-ventana:** un par (IP iniciadora, `window_end` de la rejilla de 10 s) de la población de CyberFlow del control: **2 218 pares**, 19 entidades, 181 ventanas. CyberFlow: par con señal de la configuración (decisiones de `motor_decision.log`: `HIB_0.03` = `score < −0,5898535710336618` **o** heurístico). Suricata: par con ≥1 alerta válida (no STREAM / ET INFO) cuyo **iniciador de flujo** (`flow_id` → `src_ip` del evento `flow`; si no hay, `src_ip` de la alerta) es esa entidad y cuyo instante cae en esa ventana (`window_end` = primer múltiplo de 10 s ≥ instante).
- **Unidad de control B — ventana de 10 s:** ventana con ≥1 señal de cualquier entidad; denominador **181**.
- Alertas de Suricata sobre extremos fuera de las 19 entidades (p. ej. el bastión): se informan, no se cuentan.
- Referencia de CyberFlow (ya medida, a reproducir desde el log): `HIB_0.03` 200/2 218 = 9,02 %; `IF_0.03` 200; `HEUR` 0.

## 7. Latencia comparativa
- Solo en episodios donde **ambos** tienen detección (≥1 señal/alerta válida, durante el episodio o posterior) y con marcas equivalentes.
- **Marca equivalente = tiempo de los datos**, no de procesamiento: CyberFlow = `window_end_utc` de la primera ventana atribuible con señal de la configuración; Suricata = `timestamp` del paquete que dispara la primera alerta válida. Ambas contra el `t_inicio` del generador. Relojes Kali/Sensor1/srv-dmz/bastión: |desfase|+incertidumbre ≤ 0,023 s en las 100 mediciones del respaldo.
- Limitación declarada: la marca de CyberFlow está **cuantizada a 10 s** (rejilla); diferencias < 10 s se informan como **no concluyentes**. No se usa la «disponibilidad del registro» de `analizar_3b` (incluye retraso de procesamiento) para esta comparación; se muestra aparte.

## 8. Qué queda indeterminado (reglas previas)
- Rebanada con hash que no coincide, ejecución de Suricata fallida o incompleta, o salida de CyberFlow sin ventana atribuible por falta de observación → `indeterminado` (no se cuenta como acierto ni como fallo).
- Cualquier valor de latencia sin detección de ambos → no se reporta.
- Los resultados se reportan con n pequeño (21): sin significancia estadística; se darán intervalos de Clopper-Pearson para las proporciones.

## 9. Trazabilidad de salida
Por rebanada y configuración: sha256 de la rebanada unida, de `eve.json` y de `suricata.log`; versión y carga de reglas (`53013 rules successfully loaded, 0 failed`); conteo de eventos por tipo; lista de alertas con SID y firma. Salidas en el comparador `~/cf-4.3/` y extractos en `C:\Users\markp\cf-b4\replay-4.3\`.
