# Propuesta y plan de validación — revisión 3B

**Revisión posterior a conocer los resultados.** Nada de esto se ha desplegado. No se ha tocado el motor, ni los
servicios, ni la configuración de Suricata o tcpdump, ni el modelo, el escalador, las características, los umbrales,
los heurísticos o los escenarios. Datos en `diagnosticos/demora.json` y `diagnosticos/suricata-descartes.json`.

## 1. De dónde sale la demora (medido)

La primera emisión real de cada episodio se descompone en cuatro tramos, que suman exactamente la disponibilidad
medida (comprobado en 25/25 episodios):

| Tramo | Qué es | Mediana | Rango |
|---|---|---|---|
| A acumulación | cierre de la ventana que emite − inicio del ataque | 7,9 s | 0,9 – 23,1 s |
| B espera PCAP | cierre del fichero de 15 s que contiene el cierre de la ventana − cierre de la ventana | 12,0 s | 2 – 14 s |
| C espera de ciclo | inicio del ciclo que decide − cierre del PCAP | 1,5 s | 0,5 – 10,5 s |
| D proceso | escritura del registro − inicio del ciclo | 2,6 s | 1,2 – 7,0 s |
| **Total** | disponibilidad − inicio | **24,9 s** | 16,4 – 39,6 s |

**Incertidumbre no registrada:**

- B sale del nombre del siguiente fichero, con resolución de 1 s. No se archivó el mtime ni el instante exacto en que
  tcpdump rota (con `-G` rota al llegar el primer paquete pasados los 15 s).
- C es una cota superior del momento en que el motor vio el fichero: solo se sabe que lo vio en ese ciclo.

**Los 4 escaneos breves no oportunos** (ataques de 17,6–18,0 s):

| Episodio | Duración | A | A + D | Margen que quedaría para B + C |
|---|---|---|---|---|
| escaneo_breve-r5 | 18,0 s | 23,1 s | 25,1 s | −7,1 s (imposible) |
| escaneo_breve-r4 | 18,0 s | 23,0 s | 24,3 s | −6,3 s (imposible) |
| escaneo_breve-r2 | 18,0 s | 18,0 s | 20,6 s | −2,6 s (imposible) |
| escaneo_breve-r3 | 17,6 s | 15,0 s | 16,3 s | +1,3 s (solo si B + C ≤ 1,3 s) |

En tres de los cuatro, la primera ventana que da señal **cierra después de que el ataque haya terminado**. Ningún
cambio en la cadena PCAP → ciclo → registro puede hacerlos oportunos. El límite está en la rejilla de 10 s y en
cuánta actividad necesita la ventana para dar señal, es decir, en las características y los umbrales, que están
congelados. En el cuarto (r3) haría falta B + C ≤ 1,3 s.

**Las ventanas «tardías».** Las 49 de los episodios son todas ventanas con 0 paquetes de la Kali, y lo mismo pasa con
las 655 del inventario. Las ventanas sin paquetes de una entidad solo se construyen cuando esa entidad vuelve a enviar
tráfico. En los episodios, la disponibilidad coincide, a ±7 s, con la siguiente ventana de la Kali con paquetes (por
ejemplo, `escaneo_breve-r3`: decididas a las 09:42:15, cuando la siguiente ventana con paquetes es la de las
09:42:20). No afectan a la primera señal. Se informan, no se corrigen.

**Ciclos de más de 10 s.**

- Hay 2 de 2655:
  - el de las 08:34:33 dura 10,06 s, durante `inundacion_http-r3`;
  - el de las 09:53:34 dura 10,61 s, durante `inundacion_http-r5`.
- En ambos el anillo tenía unos 445 000 paquetes. Las etapas que más pesan son `filas` (4,0–4,2 s), `pcap_parseo`
  (2,1 s), `atribucion` (1,3–2,1 s) y `deduplicacion` (1,5 s).
- **Duración del cálculo ≠ latencia de detección.**
  - El ciclo largo retrasa el siguiente: el latido máximo es de 11,11 s, frente a 10,00 s de mediana.
  - Alarga D de las ventanas que decide (D ≈ 6,8–7,0 s en las inundaciones).
  - No cambia ninguna categoría: los episodios de inundación tienen su primera emisión a los 24,2–29,3 s, oportuna.
  - Lo que cuenta para la detección es A + B + C + D, no la duración del ciclo.

## 2. ¿Hay que modificar el producto?

**No para la validez de lo medido.**

- Las 9 reconstrucciones no exactas eran un defecto de la herramienta de recálculo, no del motor (véase el informe).
- El replay reproduce el vivo clave a clave.
- La contradicción de los 20 s estaba en la cadena de evaluación.

Para reducir la latencia hay dos cambios mínimos posibles. Se proponen como **candidatos opcionales**, no como
requisito:

| | P1 · rotación PCAP de 5 s | P2 · ciclo disparado por la rotación |
|---|---|---|
| Qué cambia | `tcpdump -G 15` → `-G 5`, con `-W` triplicado para conservar ≥ 230 s de anillo; el archivador, igual | el motor empieza el ciclo al aparecer un PCAP nuevo (inotify), con el ciclo de 10 s como máximo |
| Qué demora reduce | B: mediana de 12 s a ≤ 5 s (unos −7 s) | C: mediana de 1,5 s a ≈ 0; elimina los casos de 5–10 s |
| Lo que no arregla | A (escaneos breves), D (carga) | A, B, D |
| Riesgos | 3× ficheros: más aperturas, más entradas en `parsed_pcaps` y en el filtro por mtime; el archivador copia 3× más ficheros; más rotaciones en vacío | más ciclos bajo carga (hasta uno por PCAP); con ciclos de 10,6 s se encadenarían sin pausa; modifica el código del motor |
| Efecto sobre las características | ninguno esperado: la ventana se decide con `marca_pcap ≥ window_end`, con los mismos paquetes | ninguno esperado, por la misma regla |
| Calibración y comparabilidad | sin cambios esperados; **se verifica, no se supone**: replay de la campaña 3B con la versión candidata e igualdad de las 12 667 claves (puntuación, decisión y paquetes) | igual que P1 |
| Prueba | replay offline del 3B (P2) / reanillado sintético a 5 s de los mismos PCAP (P1) → igualdad de claves y nueva tabla A–D; prueba de carga con tráfico de clientes sin ataques | igual |
| Reversión | volver a `-G 15` en la unidad de captura (un parámetro) | volver al commit anterior del motor; bandera de configuración para el modo de disparo |

**Recomendación.**

- No aplicar P1 ni P2 antes de la campaña B, salvo que el tiempo de respuesta sea un objetivo declarado. Todos los
  episodios que hoy no son oportunos lo seguirían siendo (r2, r4, r5) o dependerían de 1,3 s (r3).
- Si se decide aplicarlos: versión candidata, criterios congelados, replay de igualdad y validación con tráfico
  independiente antes de la campaña B.

**Suricata.** Los descartes sacan 9 de 25 episodios (8 con ±60 s). La causa no está demostrada (§3 del informe).
Cualquier ajuste del `af-packet` (ring-size, tpacket-v3, threads) es un cambio de infraestructura que corresponde
decidir a Mark. Antes de la campaña B exigiría:

1. medir con tráfico normal y una carga equivalente;
2. demostrar 0 descartes en un periodo de control;
3. no cambiar nada más a la vez.

## 3. Plan de validación

1. **Validación acotada de las herramientas (hecha en esta revisión).**
   - Las 6 pruebas obligatorias, más las de formato v1 y recálculo: `pruebas/test_revision_3b.py`.
   - Pruebas existentes sin cambios: `test_analizar_3b` 90, `test_herramientas` 222 y `regresion_alfa` sin
     diferencias.
   - Reproducción local del análisis original idéntica, salvo la ruta del inventario.
2. **Congelar los criterios v2** en este commit. Desde aquí, `generar_respaldos_v2`, `verificar_integridad_v2` y
   `recalcular_caracteristicas_v2` (con sus hashes en `REFERENCIAS.md`) son las herramientas de la campaña B. No se
   ajustan después de verla.
3. **Antes de la campaña B, con datos que no se usaron para diseñar los criterios.** Aplicar la cadena v2 a una
   captura nueva de tráfico normal sin ataques (al menos 30 min, clientes a factor 1,0).
   - Criterio de aceptación: inventario sin ausentes, continuidad v2 verificada en todo el tramo, recálculo exacto en
     todas las ventanas recalculadas y 0 descartes de Suricata, o bien su cifra informada.
   - Si falla, se corrige la herramienta y se repite este paso, **no** la campaña.
4. **Campaña B** con los mismos escenarios y criterios congelados. Es la única que puede confirmar las tasas: lo de
   esta revisión es un reanálisis posterior a los resultados, no una confirmación independiente.
5. **No se cierra** por el aumento de la población (1 → 15). La población revisada es la que resulta de corregir un
   defecto de medida, no un objetivo.
