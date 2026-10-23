# Figuras VI-1 a VI-7 en draw.io — plan por bloques

**Origen:** los SVG de `PPI/.../DIAGRAMAS/digramas` (12-oct), con las correcciones del
análisis del mismo día. **Destino:** `.drawio` editable + PNG para revisar, y después las
vistas del «Mapa del sistema» del panel.

**Método.** Cada figura la genera un script de Python con el sistema de diseño de la
skill (`arqkit`). Para corregir, se cambian unas líneas y se vuelve a generar, sin
rehacer el dibujo a mano. Después, en este orden: `auditar.py` (conectores sueltos,
numeración, solapes), exportación a PNG y **revisión mirando el PNG**.

**Reglas comunes:**
- La misma cabecera que los SVG («VI-x / SECCIÓN», título, una línea de bajada).
- Zonas numeradas.
- Tarjetas con icono, título y como máximo una línea de nota.
- Conectores ortogonales anclados.
- Poco texto: lo que sobre va a la leyenda o a la nota del panel, no al dibujo.

**Colores de los conectores**, por naturaleza:

| Color | Significado |
|---|---|
| Azul | Datos o ejecución |
| Naranja discontinuo | Copia SPAN o control |
| Gris discontinuo | Previsto o no ejecutado |
| Verde | Hacia la persona |

**Colores de las acciones:** PERMIT neutro, LIMIT ámbar, BLOCK rojo, cada uno con su
propio icono. Nunca el mismo escudo para los tres.

| Bloque | Figura | Correcciones respecto del SVG | Estado |
|---|---|---|---|
| B0 | Kit común | Paleta pizarra como en los SVG, iconos por acción, cabecera VI-x | — |
| B1 | **VI-1 Arquitectura operativa** | pfSense en la ruta; la copia SPAN sale del conmutador (no de la Kali); el recorrido de hosts no pasa por srv-dmz; cadena escalonada de 10 s en publicador, relay y agente (:00/:03/:06); Wazuh marcado como previsto si no está activo | act. 17-oct (cadena 10 s) |
| B2 | **VI-2 Topología experimental** | Capa ESXi y grupo de puertos promiscuo bajo Gi2/0/19; el Sensor2 también recibe la copia (ens37); DNS/AD 10.10.10.20 en la VLAN 10; leyenda con estilos distintos para el recorrido y la copia SPAN; puntos 1–4 | hecho 12-oct |
| B3 | **VI-3 Decisión híbrida** | Dos niveles: el motor decide por ventana y el publicador combina por IP en 120 s; filtro «nunca bloquear»; las exclusiones se contabilizan; la versión de umbrales está en el feed; sin cruces en la salida de los heurísticos | hecho 12-oct |
| B4 | **VI-4 Respuesta y reversión** | Los tres tiempos con su medición (detección 13 s [4–23] · decisión 26,1 s · respuesta total 41,4 s, de los cuales decisión→nftables 15,3 s); t_ataque como origen; cadena escalonada de 10 s (:00/:03/:06); retirada manual = `nft delete element` | act. 17-oct (cadena 10 s) |
| B5 | **VI-5 Comparación y ablación** | Unidad = episodio y falsos positivos aparte (no «episodio o ventana»); tramo normal y control con firma (Nikto); panel de resultados de la batería N=3 (0/9 · 6/9 · 7/9 · 9/9; 3,4 s frente a 12,0 s); C3 marcada como propuesta | hecho 12-oct |
| B6 | **VI-6 Reentrenamiento** | Nodo de deriva (oro → medición → disparo); `excluir_ventanas`; marcas de ejecutado o pendiente (oro, lotes, primer lote rechazado frente a candidato sin ejecutar); salida del veredicto en abanico, sin seis líneas superpuestas | hecho 12-oct |
| B7 | **VI-7 Matriz de validación** | Estados rellenos con su nota; filas nuevas: comparación con Suricata y tres tiempos | hecho 12-oct |
| B8 | Fig. 1 Metodología (opcional) | Mismo estilo; F7 con interna hecha y externa pendiente | hecho 12-oct |
| B9 | Revisión conjunta | Misma retícula en todas, exportación PNG y SVG, entrega en la carpeta del PPI | |
| B10 | Panel | Las aprobadas pasan a las vistas del «Mapa del sistema» | hecho 12-oct: «Mapa del sistema», siete vistas (rama del sensor `b7fa23e`, `da7e2cc`) |

**Entrega:**
- cada `.drawio` + `.png` en la carpeta de su figura, `PPI/.../DIAGRAMAS/digramas/Figura VI-x …/` (y `Metodológica/` para la Fig. 1);
- los generadores en esta carpeta (`gen_vi*.py`), versionados.
