# Planificación de las sesiones de validación

> **Estado: planificado, sin ejecutar.** Dos sesiones: la **validación interna**
> (expertos, revisan producto y resultados) y la **validación externa** (usuarios,
> TAM). Sale de la asesoría del 28/29-sep: producto listo el **lunes 5-oct** y
> validación **desde el 6/7-oct**.
>
> Los nombres de los validadores **no** se publican aquí: viven en
> `PERSONAL-VALIDACION-CyberFlow.xlsx` (OneDrive, carpeta `VALIDACION`), junto a
> los instrumentos y la presentación.

---

## 1. Las dos sesiones de un vistazo

| | **Sesión 1 · Validación interna** | **Sesión 2 · Validación externa** |
|---|---|---|
| Qué valida | Que lo hecho está bien: **entorno y producto** (código y resultados) | Que el sistema **sirve** y lo adoptarían |
| Quién | 3 expertos, **juntos**; firman los tres | 5–8 usuarios (analistas SOC, admins de red), **de uno en uno** |
| Instrumento | Juicio de expertos: Parte A entorno (C1–C7) + Parte B producto (C8–C14), escala 1–4 | TAM: PU (4), PEOU (4), IU (3), Likert 1–7 |
| Estadístico | V de Aiken por criterio ≥ 0,80 · coeficiente K | Media, DE, IC 95 % por constructo · Alfa si n ≥ 5 |
| Duración | **45 min** | **20 min** por persona |
| Qué ve | Diapositivas + panel + **repo y terminal** | Diapositivas + **usa él mismo el panel** |
| Qué NO ve | — | Código, metodología, métricas del modelo |
| Asesor | Presente, **no valida** | No hace falta |
| Cuándo | Desde el 7-oct, en la franja en que coincidan los tres | Desde el 6/7-oct; **primero el externo** |
| Modalidad | Presencial o virtual (el panel se comparte por pantalla) | Presencial, o virtual con control remoto |

---

## 2. Cifras que se presentan (una sola fuente)

Toda cifra de las diapositivas sale de esta tabla. Si cambia la fuente, cambia
aquí primero.

| Cifra | Valor | Fuente |
|---|---|---|
| Falsos positivos sin recalibrar | **92,4 %** | `ESTADO.md` §2 (17-sep) |
| Falsos positivos recalibrado (test retenido) | **4,45 %** | nota `L` (29-sep) |
| Detección global (Kali, misma red) | **69 %** (54/78 ventanas) | nota `M` (30-sep) |
| Detección HTTP (web-scan, fuerza bruta, flood) | **100 %** (27/27) | nota `M` |
| Detección escaneo de puertos | **63 %** (27/43) | nota `M` |
| DNS de alta entropía · ARP spoofing | **0 %** · **0 %** — límite declarado | nota `M` · entregable 11 §4 |
| Modelo desplegado | `if_recalibrado_2026_09`, congelado, `calibrado_en_esta_red=true` | `ESTADO.md` (30-sep) |
| Versión | `v1.0.0` (producto `f9ced59`), CI verde, 265 pruebas | `ESTADO.md` P2 |
| Replicabilidad | Instalación offline de cero en una 2.ª VM | nota `K` (29-sep) |
| Por qué esos ataques | MITRE ATT&CK + OWASP/DBIR/Fortinet/ESET | [`11-justificacion-ataques`](../11-justificacion-ataques/README.md) |

---

## 3. Sesión 1 · Validación interna (45 min)

### Agenda

| Min | Bloque |
|---|---|
| 0–2 | Bienvenida, objetivo de la sesión, cómo se evalúa |
| 2–17 | Diapositivas 1–10 (con saltos al panel, ver abajo) |
| 17–25 | **Demo en vivo**: ataque → alerta en el panel |
| 25–35 | Preguntas y recorrido libre por el repo |
| 35–45 | Los validadores llenan el formulario (Parte A, Parte B, ficha, K, dictamen) |

### Diapositivas y su evidencia en el panel

| # | Diapositiva | Se abre en vivo | Criterio |
|---|---|---|---|
| 1 | Título (**detección**, no predicción) · autores · asesores | — | — |
| 2 | Problema y justificación: por qué por comportamiento y no por firmas | — | — |
| 3 | Objetivo general y específicos | — | — |
| 4 | **Alcance**: qué ataques y por qué (entregable 11); qué no hace | Panel · *Alcance del análisis* | C14 |
| 5 | Metodología (fases, una línea de tiempo) | — | — |
| 6 | Arquitectura: SPAN → Suricata → variables → modelo → decisión → panel | Panel · *Salud* + *Topología y flujo* | C5, C8 |
| 7 | Entorno: VLAN, pfSense HA, 6 perfiles de tráfico, Kali aislada | Panel · *Topología* + *Simulación → Tráfico normal* | C1–C4, C7 |
| 8 | **Resultados**: FPR 92,4 → 4,45 % · TPR 69 % / 100 % HTTP | Panel · *Modelo congelado* → **demo** | C12 |
| 9 | Reproducible y replicable: SHA-256, entorno congelado, 2.ª VM, CI | **Terminal**: `doctor.sh`, `SHA256SUMS`, tag `v1.0.0` | C9–C11, C13 |
| 10 | Limitaciones y trabajo futuro: DNS y ARP, simulado → real | Panel · *IPs bloqueadas* (modo observación) | — |

### Guion de la demo (8 min)

1. *Actividad* y *Distribución de scores* con tráfico normal: todo en PERMIT.
2. *Simulación → Tráfico anómalo*: se copia el comando de un ataque **HTTP**
   (el que detecta al 100 %) y se lanza desde la terminal de la Kali.
3. *Actividad* → *Decisiones recientes*: filtrar por `10.10.20.30`, mostrar el
   ALERT y su score frente al umbral.
4. *Exportar CSV*: la evidencia sale del panel.

**Respaldo obligatorio:** video grabado de los pasos 1–4, por si la red o el
bastión fallan ese día.

### Material que se envía un día antes

- Enlace al Canva.
- Enlace al repositorio del producto (tag `v1.0.0`) y a este repositorio.
- Enlace al formulario (se llena al final de la sesión, no antes).

---

## 4. Sesión 2 · Validación externa — TAM (20 min por persona)

El instrumento TAM se aplica **después de que el participante opere el panel**.
Mostrárselo no basta: si no lo usa, las respuestas de facilidad de uso no valen.

### Agenda

| Min | Bloque |
|---|---|
| 0–4 | 4 diapositivas: qué es · qué detecta y qué no · cómo se lee el panel · instrucciones |
| 4–12 | **El participante usa el panel** con las tareas de abajo (nosotros solo observamos) |
| 12–17 | Formulario TAM |
| 17–20 | Comentario abierto y cierre |

### Tareas en el panel

| # | Tarea que se le da | Sección | Ítems TAM |
|---|---|---|---|
| 1 | «¿El sistema está funcionando?» | Banner + *Salud* | PE1, PE2 |
| 2 | «Sigue el camino de un paquete» | *Topología* (vista Esencial) | PE2 |
| 3 | «Hay una alerta: encuéntrala. ¿Qué IP es y por qué?» | *Actividad* → *Decisiones* → filtrar por IP | PU1, PU2 |
| 4 | «¿Qué no analiza el sistema?» | *Alcance del análisis* | PU3 |
| 5 | «Descarga la evidencia» | *Exportar CSV* | PU3, PE4 |

Antes de cada sesión tiene que haber **al menos una alerta visible** en la
última hora (lanzar un ataque HTTP corto unos minutos antes).

No se muestran *Variables por capa* ni *Modelo congelado*: son material de
experto y suben el esfuerzo percibido (PE3).

---

## 5. Antes de las sesiones

| Fecha límite | Tarea |
|---|---|
| 2-oct | Cerrar la lista de validadores (3 internos, 5–8 externos) y confirmar nombres |
| 2-oct | Pedir 2–3 horarios a cada uno y anotarlos en la hoja *Disponibilidad* |
| 3-oct | Instrumento interno ampliado con la Parte B (C8–C14); TAM con IU3 |
| 3-oct | Formularios en Google Forms (interno y TAM) con su hoja de respuestas |
| 4-oct | **Panel coherente con el modelo desplegado** (ver abajo) |
| 4-oct | Canva: 10 diapositivas (interna) y 4 (externa) |
| 5-oct | Producto listo; video de respaldo de la demo grabado |
| 5-oct | Ensayo completo de las dos sesiones, cronometrado |
| 6-oct | Enviar el material previo a los validadores internos |

### Panel: revisar antes de mostrarlo

La captura del 29-sep mostraba datos que no cuadran con el modelo congelado el
30-sep. Verificar en el panel actual:

- [ ] La tarjeta *Modelo congelado* muestra el detector desplegado
      (`if_recalibrado_2026_09`) y su umbral, no `OCSVM` / `1.8126`.
- [ ] La *Distribución de scores* compara contra el umbral del modelo desplegado
      (la captura decía «100 % por debajo del umbral», en rojo, con todo en PERMIT).
- [ ] Las tasas de detección de la tarjeta coinciden con la nota `M`
      (69 % / 100 % HTTP), o indican de qué dataset salen.
- [ ] El aviso de *punto débil* habla de DNS y ARP (nota `M`), no de la fuerza
      bruta, que ahora se detecta al 100 %.
- [ ] El botón *Modo desarrollo* no aparece en la demo.

---

## 6. Después de las sesiones

1. Exportar las respuestas de Google Forms a Excel.
2. Calcular la V de Aiken y el K (`CONSOLIDACION-JUICIO-EXPERTOS.xlsx`) y las
   medias y el Alfa del TAM.
3. Generar una **constancia por validador** (ficha, puntajes, dictamen) y la
   **constancia consolidada** que firman los tres internos.
4. **Periodo de mejora (días, no semanas):** atender las observaciones de la
   validación interna y registrar cada cambio con su commit.
5. Registrar la evidencia en `04-evidencias/` y actualizar `ESTADO.md`.

---

## 7. Qué se dice y qué no

| Decir | No decir |
|---|---|
| «Detecta y alerta; en modo observación no bloquea. El bloqueo es opcional si el sensor está en línea» | «Bloquea las IPs» |
| «Se recalibra por lotes con la línea base y luego se congela con un umbral fijo» | «Aprende en tiempo real» |
| «Detecta el 100 % de los ataques HTTP y el 69 % en global» | Solo el 100 %, sin el global |
| «DNS de alta entropía y ARP no se detectan: piden una regla determinista, es trabajo futuro» | Ocultar los 0 % |
| «Datos reales capturados en un entorno de simulación con parámetros controlados» | «Probado en una empresa real» |

---

## 8. Por confirmar

- [ ] Nombres completos de los validadores mencionados en la reunión.
- [ ] Composición final del grupo interno (en la reunión quedó en dos versiones).
- [ ] Fecha de la sesión interna (lunes 5 o martes 6 como producto listo; validación desde el 7).
- [ ] Repetir DNS-entropy contra el resolver real (`10.10.10.20`) antes de presentar el 0 % como definitivo (nota `M`, pendiente 1).
