# Etapa 2 — Cierre técnico (2026-11-01)

**Estado: entregado para revisión. No desplegado.** No se instaló, desplegó ni reinició nada en el laboratorio. No se activó enforcement, no se lanzaron ataques ni campañas y no se editó el Word. La Etapa 3 no se ha iniciado.

| | |
|---|---|
| Código | rama `candidato/etapa2-20261101`, commits `3083f60` y `953a436` (base `2be5335`) |
| Antecedente | `../etapa2-candidata-2026-11-01/` (documentación `c90c689`), conservado sin cambios |
| Modelo | `if_limpio_2026_10` sin cambios: escalador, contrato de 28 características (9 L3, 8 L4, 11 L7), umbrales α 0,05 / 0,03 / 0,01 sin elegir uno. No se reentrenó ni recalibró |

## 1. Documentos

| Documento | Contenido |
|---|---|
| `MATRIZ.md` | Observación → corrección → prueba → evidencia → estado |
| `DIAGNOSTICO-CARACTERISTICAS-Y-REINICIO.md` | Causa exacta de las diferencias de características (punto 4) y del reinicio (punto 5); replays; justificación de `flow_duration_mean_30s` |
| `VALIDACION-3B-25-EPISODIOS.md` | Los 25 episodios con 3 α y 7 configuraciones; control; alarmas sobre otras entidades; 5 escaneos breves; rendimiento en la inundación HTTP |
| `CONCLUSIONES-CORREGIDAS.md` | C1–C11, alternativas del escaneo breve, vocabulario (señal, restricción, aplicación, efecto) y preparación de la Etapa 3 |
| `PROCEDIMIENTO-INSTALACION-REVERSION.md` | Instalación y reversión P1–P8, revisadas contra los scripts reales y probadas en el banco donde se puede; no ejecutadas |
| `DEPENDENCIAS-Y-COMANDOS.md` | Entornos, versiones y cada comando con su etiqueta |
| `REFERENCIAS.md` | Hashes del código y de todas las entradas |
| `resultados/` | Pruebas, ensayos, replays (gzip), comparaciones y análisis |
| `herramientas/`, `guiones/` | Lo necesario para regenerar `resultados/` |

## 2. Qué se corrigió y con qué evidencia

| Punto | Corrección | Evidencia principal | Alcance de la prueba |
|---|---|---|---|
| 2. Coherencia feed/firma y reintento | El relé entrega solo una pareja estable, de forma atómica, y reintenta. El agente reintenta tras un fallo del helper y un feed repetido no amplía la caducidad | `test_etapa2_correcciones.py`; S1–S5 con SSH real en el banco | Banco |
| 3. Perfil fijo por host | El helper lee el perfil de un fichero de root (DC1 `dns`, srv-dmz `dmz`), rechaza perfiles cruzados y operaciones fuera del contrato y nunca toca `ruleset`. Sin `sudo nft -f -` arbitrario | Pruebas del helper, C9 y S7 | Banco |
| 4. Características y scores | Horizonte de entrada fijado por ventana | 7 configuraciones del tramo: 0 de 1400 vectores distintos (antes hasta 198 y 4 reglas). Completo: 0 de 9244 | Replay sobre el 3B |
| 5. Reinicio | Reanudación desde la última ventana, rebobinado de `eve.json`, relectura del anillo y `historial_completo` | r8 con 6 reinicios durante tráfico normal, escaneo, fuerza bruta, DNS e inundación HTTP: 2378/2378 claves, 0 vectores distintos, 0 duplicados, 0 pérdidas | Replay |
| 6. 25 episodios | `analizar_3b.py` sin modificar sobre los replays completos | 0 diferencias de categoría con el 3B en vivo revisado (25 × 7); población principal 15/25 con las mismas exclusiones; mismas falsas alarmas en el control | Replay |
| 7. LIMIT | Coincidencias (contador del elemento) separadas de los descartes por origen (set `descartes_limite`) y del efecto medido | C8: con 3 consultas/s, 12 coincidencias y 0 descartes. Por encima del límite, en cada uno de los dos orígenes: 47 coincidencias = 13 descartes + 34 respondidas. Renovación con id nuevo y contadores a 0; caducidad correcta | Banco (netns con nft real) |
| 8. Instalación y reversión | Procedimiento revisado contra los scripts reales | S6 (sudoers), S8 (`systemd-analyze` limpio salvo el venv de Sensor1) | Banco; nada ejecutado en el laboratorio |
| 9. Conclusiones | C1–C11 | `CONCLUSIONES-CORREGIDAS.md` | — |

**Pruebas:**

- banco :2 con `953a436`: **575 pasadas y 1 omitida** (falta node para comprobar el JS del panel), en `resultados/pruebas/pytest-completo-v.txt`, con el resultado de cada prueba por su nombre;
- pruebas del motor en Windows: 17 pasadas.

Ninguna de estas pruebas sustituye a una comprobación en el laboratorio.

## 3. Cambios del motor que hay que conocer

1. **Horizonte por ventana.** La ventana A se calcula siempre con la entrada [A − 230 s, …]. La fila deja de depender de la rotación, del disparo, del retraso y de los reinicios.
2. **Conjunto de registros.** Se registra (E, A) si E tiene paquetes o L7 en (A − 60, A]. Las ventanas vacías dentro de huecos de más de 60 s ya no se registran: son 22 en el control del 3B, todo ceros, PERMIT y sin score.
3. **Coste.** Atribuir por ancla es más caro que en `2be5335`. En las inundaciones hay ciclos de hasta 23 s en el portátil, y la continuidad ≤ 20 s no queda resuelta (`VALIDACION…` §6).

## 4. Señal, restricción, aplicación y efecto

| Eslabón | Qué hay en este cierre |
|---|---|
| **Señal** (decisión del motor) | Medida en replay sobre los 25 episodios: categorías, tiempos de disponibilidad (reloj simulado) y alarmas sobre otras entidades |
| **Restricción** (feed v2 firmado) | Probada en el banco (contrato, firma, coherencia de la pareja) |
| **Entrega y aceptación** | Banco: relé por SSH real (S1–S5) y cadena por eventos con p50 de 1,02 s hasta aplicado (`ensayo-cadena-eventos.json`) |
| **Aplicación confirmada** | Banco: elemento con id en nft (netns), en `dns` y `dmz` |
| **Coincidencias y descartes** | Banco: C8 |
| **Efecto sobre el tráfico real** | **No medido en el laboratorio.** Solo C8 en netns |

Ninguna señal se cuenta como mitigación, ni una coincidencia como descarte.

## 5. Resultados clave

**Determinismo:**

- 7 configuraciones de captura y disparo dan el mismo contenido: 0 vectores, scores, reglas o clases distintos.
- El completo candidato (5 s, eventos) es idéntico al de referencia (15 s, periódico) en 12 226 claves.

**25 episodios** (candidata, población principal 15):

| Resultado | Episodios |
|---|---|
| Detección durante el ataque con IF 0,05 | 10, uno de ellos `escaneo_breve-r1` (ver abajo) |
| Detección durante el ataque solo con HEUR | 2: `dns_inusual-r2` y `r4` (`dns_entropy`) |
| Solo después del ataque | 3 escaneos breves |

`escaneo_breve-r1` aparece como «oportuna» por criterio, pero la señal no es del escaneo (C10).

**Escaneo breve.** En los 5 episodios, la primera señal `port_scan` llega después del fin, entre +0,2 y +8,2 s en el replay. La conclusión se limita a esta candidata y a estos 5 episodios.

**Control.** Las mismas falsas alarmas que en vivo: 395, 254 y 83 a α 0,05, 0,03 y 0,01, y 92 en HEUR. Las tasas son altas (IF 0,05: 15,1 %), y eso **no cambia** con esta etapa.

**`flow_duration_mean_30s`.** Hay una diferencia de contrato real con el entrenamiento: horizonte de 230 s en el motor frente a hasta unos 15–20 min en el entrenamiento. Afecta al 19 % de las ventanas con contenido del tramo, y el bosque tiene 498 cortes por encima de 230 s. Aun así, **no se concluye que haya que reentrenar**:

- con 900 s solo aparecen 54 PERMIT → ALERT sobre entidades legítimas (α 0,05, 676 ventanas) y ningún cambio en el origen de ensayo;
- la memoria se multiplica por 4 y la latencia se hace inviable.

La decisión necesita la distribución del dataset de entrenamiento (Etapa 3). Detalle en `DIAGNOSTICO…` §5.4.

## 6. Limitaciones

1. **Replay no es laboratorio.** Las latencias son del portátil, con hasta 5 replays en paralelo. Ni la entrega por SSH ni el efecto en los destinos se miden en un replay.
2. **Un solo día de datos.** 25 episodios, sin extrapolar.
3. **14 `ventana_no_regenerada` en el completo.**
   - Son iguales en ref y cand, ninguna es del origen y ninguna cae en el control.
   - En los 2 casos verificados, la entidad no tiene observaciones en su propio horizonte: sus paquetes se atribuyen al otro extremo. Con el horizonte del ancla anterior sí las tenía.
   - Lo que las convierte en no evaluadas es la contabilidad de pendientes, no una pérdida.
   - No se corrigió para no invalidar los replays: queda para la Etapa 3.
4. **Atribución del propietario.** Sigue dependiendo del inicio del horizonte. Ahora es determinista, pero sigue siendo la regla congelada del contrato.
5. **Integridad v2.** Incluye la continuidad del motor en vivo. Se conservó tal cual, como pedía el encargo.

## 7. Estado final

### Cerrado (con evidencia en este cierre)

- Coherencia feed/firma, reintento del relé y del agente, y perfil fijo por host (banco).
- Instrumentación del LIMIT: regla confirmada, coincidencias, descartes por origen, renovación, caducidad y reinicio del agente (banco, netns).
- Determinismo de características y scores frente a la rotación, el disparo, el retraso y los reinicios (replay).
- Reinicio sin duplicados, pérdidas ni información futura (replay, 6 reinicios y 5 tipos de tráfico).
- Validación offline de los 25 episodios con los criterios congelados (replay).
- Procedimiento de instalación y reversión revisado (sin ejecutar).
- Conclusiones corregidas C1–C11.

### Pendiente en vivo (requiere autorización y sudo de Mark)

- Venv del motor en el Sensor1 (único fallo de `systemd-analyze` en el banco).
- sudo `Defaults` y ficheros de perfil en DC1 y srv-dmz.
- Rotación real de `eve.json` con el motor reanudando.
- Relé SSH real Sensor1 → destinos y su latencia (P-2).
- Samba en DC1, solo lectura, sin instalar nada.
- Endurecimiento de las cuentas `cffeed` y `cfagente`.
- Coste y continuidad del motor nuevo en el Sensor1 durante una inundación.
- Efecto de LIMIT y BLOCK en los destinos reales.

### Etapa 3 (no iniciada)

- Detección del escaneo breve durante el ataque: medir A2 y A5 en replay (C1, §2).
- Atribución DNS al cliente original (R-E2).
- Renovaciones sin tráfico (R-E3.1).
- Separar HTTP legítimo de abuso (R-E3.4).
- DNS a 5/s: pendiente, sin convertirlo en BLOCK.
- `flow_duration_mean_30s`: medir el dataset de entrenamiento y decidir el contrato.
- Contabilidad de pendientes (`ventana_no_regenerada`).
- Tasa de falsas alarmas del control.

## 8. Manifiesto

`MANIFIESTO.sha256` cubre todos los ficheros de esta carpeta (en LF). Tras el push se descargó cada fichero de GitHub y se comprobó contra el manifiesto. El resultado se da en el mensaje de entrega; no se puede incluir aquí sin cambiar el propio manifiesto.
