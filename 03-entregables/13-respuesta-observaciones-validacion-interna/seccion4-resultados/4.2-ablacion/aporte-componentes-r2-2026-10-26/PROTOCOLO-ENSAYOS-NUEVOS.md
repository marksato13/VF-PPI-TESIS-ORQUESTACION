# Protocolo para ensayos controlados nuevos (no ejecutado)

**Fecha:** 26-oct-2026. **Estado:** propuesta. **No se ha ejecutado nada de este protocolo.**

## Por qué hace falta

La batería del 5-oct no permite una Tabla 8 evaluable (`NOTA-R2.md` §1 y §4):

- el PCAP empieza 7–21 s antes de cada ataque;
- no existe el registro del motor;
- los heurísticos se ajustaron con esos mismos episodios.

El protocolo separa dos cosas:

- **A.** Evaluación de componentes sobre tráfico común, sin respuesta activa.
- **B.** Ensayos de respuesta activa.

Mezclarlas fue lo que confundió el 5-oct (feed activo durante la batería) y el 23-oct (BLOCK residual).

---

## Requisitos comunes

### 1. Configuración congelada y registrada antes de empezar

Se registran en un `config-ensayo.json` y se versionan antes de lanzar ningún ataque:

- sha256 del joblib y del escalador (`df547da0…`);
- umbrales α 0,05 y 0,03;
- `VERSION_UMBRALES` de los heurísticos;
- commit de `producto-main`;
- hashes de `extract_multilayer_v2.py`, `motor_decision.py` y `publicar_feed.py`.

**No se cambia nada durante la campaña.**

### 2. Relojes comparables

- NTP activo y verificado en sensor, bastión, Kali y srv-dmz: `chronyc tracking`, desfase < 50 ms guardado antes y
  después.
- Hoy el sensor va unos 47 s por detrás. **Hay que corregirlo antes de cualquier ensayo.**

### 3. Captura continua con historia suficiente

- PCAP continuo durante toda la campaña: el anillo copiado entero, o `tcpdump -w` rotado sin huecos.
- EVE completo de esa franja.
- `motor_decision.log` íntegro.
- Antes de cada ataque, **≥ 120 s** de captura: 60 s de horizonte más 60 s de margen para la propiedad de los flujos.
- Al final, **≥ 90 s** tras el fin: 60 s de horizonte más 30 s de cierre de ficheros.
- Sin concatenar capturas sueltas.

### 4. Registro del generador

En la Kali, `marcas.jsonl` con:

- inicio y fin del comando, en reloj de pared y monotónico;
- comando exacto;
- código de salida;
- recuento de peticiones emitidas.

Además, la sesión de control debe ser identificable en el PCAP (puerto origen anotado).

### 5. Duración y repeticiones fijadas de antemano

| Parámetro | Valor |
|---|---|
| Repeticiones | ≥ 5 por familia, con orden aleatorizado y semilla registrada |
| Duración | 90 s en DNS y flood; escaneo con rango fijo y `--max-rate` fijo para que dure ≥ 30 s |
| Separación entre episodios | ≥ 180 s en la parte A; ≥ duración del BLOCK escalado + 60 s en la parte B |

Nada de esto se ajusta a la vista de los resultados.

### 6. Control normal

Antes de la campaña, 30 min de tráfico normal con la misma configuración, para estimar la FPR de cada componente en
esas condiciones.

### 7. Familias

- DNS inusual.
- Inundación HTTP.
- Escaneo de puertos.
- **Fuerza bruta HTTP**, con un endpoint instrumentado que devuelva 401.

### 8. Heurísticos independientes

Estos episodios no se usan para modificar umbrales. Si hiciera falta cambiarlos, la versión nueva se evalúa en otra
campaña.

---

## A. Evaluación de componentes sobre tráfico común (sin respuesta activa)

- **Enforcement en sombra** (dry-run) en srv-dmz: el agente registra lo que haría y no lo aplica. El tráfico de todos
  los episodios llega intacto y los componentes se comparan sobre las mismas ventanas.
- **Una sola fuente:** el `motor_decision.log` en vivo, con el IF y los heurísticos anotados por ventana. El replay
  del PCAP continuo se usa como comprobación.
- **Métricas:**
  - categorías D / P / N / NE por episodio y configuración (`config-r2.json`);
  - instante de emisión real, desde la marca de escritura del registro, y `window_end`;
  - señales compartidas y exclusivas;
  - FPR en el control.
- **Salida:** la Tabla 8 con columnas «Familia · Episodios evaluables · IF 0,05 · IF 0,03 · Heurísticos ·
  Híbrido 0,05 · Híbrido 0,03».

## B. Ensayos de respuesta activa (separados)

- **Agente en modo aplicar.** Una familia por bloque. Empezar por las que no producen BLOCK, o reiniciar el estado de
  la escalera entre bloques (con registro de que se hizo).
- **Registro obligatorio de cada eslabón, con su hora:**

| Eslabón | Qué se registra |
|---|---|
| Señal | Línea del motor |
| Feed | Cada `feed.json` publicado (copia con sello de tiempo y firma) |
| Relay | Hora de entrega |
| Agente | Journal del agente en srv-dmz |
| nft | `nft -j list set` cada 2 s durante el ataque y hasta la caducidad |
| Efecto | Respuestas del destino en el PCAP; códigos HTTP y tiempos en la Kali |
| Retirada | Instante en que la IP sale del set |

- **Contraste del fin:** el fin del generador se toma de `marcas.jsonl`, no del último paquete. Con BLOCK el último
  paquete observado no prueba que el atacante parara.
- **Cliente legítimo de control** durante cada bloque, para medir el daño colateral del LIMIT o BLOCK.

---

## Antes de ejecutar

**Requiere la decisión de Mark**, porque cambia el entorno en vivo:

- corregir NTP del sensor y del bastión (ufw);
- ventana de campaña;
- encender la Kali;
- endpoint de fuerza bruta;
- modo sombra del agente en la parte A.
