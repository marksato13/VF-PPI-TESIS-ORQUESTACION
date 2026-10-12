# -*- coding: utf-8 -*-
"""VI-5 Comparacion con Suricata y ablacion. Correcciones respecto del SVG:
unidad = episodio y falsos positivos aparte (no 'episodio o ventana'); tramo
normal y control con firma (Nikto) como entradas; panel con los resultados de
la bateria N=3 (docs/evaluacion/comparacion-suricata.json); C3 marcada como
propuesta; CyberFlow usa eventos EVE, no alertas de Suricata."""
from cfkit import Fig, DATOS, COPIA, PREV, GRIS, AZUL, ZONA_BD
import arqkit
arqkit.BG = "#FFFFFF"

L = Fig("VI-5 / COMPARACIÓN Y ABLACIÓN",
        "El aporte de cada componente, con el mismo PCAP y la misma referencia",
        "Suricata entrega eventos a CyberFlow; sus alertas no son la verdad de referencia")

# ----------------------------------------------------------- entradas
cfg = L.card(48, 140, 300, 64, "Configuración congelada", "1", "engranaje", "θ · heurísticos · ruleset")
pc = L.card(372, 140, 624, 96, "PCAP común · SHA-256", "1", "disco", " ")
for i, (t, f, b) in enumerate([("Episodios sin firma", "#EEF3F8", "#9AB6CF"),
                               ("Control con firma · Nikto", "#FFF6EA", "#E3B577"),
                               ("Tramo normal · 527 ventanas", "#F1F4F7", "#C9D3DD")]):
    L.pastilla(50 + i * 188, 56, 178, 28, t, pc, fondo=f, borde=b, color=AZUL)

sur = L.card(48, 260, 380, 64, "Suricata", "1", "lupa", "IDS · ET Open, 53 013 reglas")
ext = L.card(580, 260, 416, 64, "Extractor de CyberFlow", "1", "engranaje", "28 variables · eventos y tramas")

# --------------------------------------------------- cuatro condiciones
zc = L.zona("", "", 48, 370, 948, 120)
L.texto(140, 12, 200, 22, "CUATRO CONDICIONES", zc, tam=13, color=AZUL, extra="fontStyle=1;")
c_s = L.card(16, 44, 214, 64, "Suricata solo", zc, "lupa", "Alertas por firma")
c_m = L.card(244, 44, 214, 64, "Modelo solo", zc, "arbol", "Isolation Forest")
c_h = L.card(472, 44, 214, 64, "Heurísticos solos", zc, "embudo", "Cuatro reglas")
c_c = L.card(700, 44, 214, 64, "Combinado", zc, "visto", "Modelo + reglas", fondo="#EEF3F8")

# ------------------------------------------------------- evaluacion
ref = L.card(48, 530, 300, 64, "Referencia independiente", "1", "documento", "Inicio y fin según el orquestador")
det = L.card(372, 530, 300, 64, "Detección por episodio", "1", "reloj", "Latencia desde el lanzamiento")
fpo = L.card(696, 530, 300, 64, "Falsos positivos aparte", "1", "grafico", "Sobre el tramo normal")

# ------------------------------------------------------------ conectores
L.flecha(cfg, sur, COPIA, ex=("0.5", "1"), en=("0.2", "0"), dash=1)
L.flecha(pc, sur, DATOS, ex=("0.1", "1"), en=("0.75", "0"), pts=[(434, 244), (333, 244)])
L.flecha(pc, ext, DATOS, ex=("0.75", "1"), en=("0.6154", "0"))
L.flecha(sur, ext, DATOS, "eventos EVE", ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(sur, c_s, DATOS, ex=("0.3237", "1"), en=("0.5", "0"))
for c in (c_m, c_h, c_c):
    L.flecha(ext, c, DATOS, ex=("0.5", "1"), en=("0.5", "0"), pts=[(788, 350)])
L.flecha(zc, det, DATOS, ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(zc, fpo, DATOS, ex=("0.8418", "1"), en=("0.5", "0"))
L.flecha(ref, det, DATOS, "etiquetas", ex=("1", "0.5"), en=("0", "0.5"))

# ------------------------------------------------- panel de resultados
zr = L.zona("", "RESULTADOS · BATERÍA N=3 (EJECUTADA)", 1040, 140, 512, 454)
ANCH = [150, 110, 100, 120]
FIL = [("Condición", "Sin firma\n9 episodios", "Nikto\ncon firma", "Falsos +\n527 ventanas"),
       ("Suricata", "0/9", "3,4 s", "no medido"),
       ("Modelo", "6/9", "12,0 s", "0"),
       ("Heurísticos", "7/9", "no medido", "0"),
       ("Combinado", "9/9", "≤ 12,0 s", "0")]
y = 48
for r, fila in enumerate(FIL):
    h = 44 if r == 0 else 38
    x = 16
    for cidx, (w, v) in enumerate(zip(ANCH, fila)):
        if r == 0:
            st = "fillColor=#E7EDF3;fontStyle=1;fontColor=%s;" % AZUL
        elif r == 4:
            st = "fillColor=#EEF3F8;fontStyle=1;fontColor=%s;" % AZUL
        else:
            st = "fillColor=#FFFFFF;fontColor=%s;" % ("#1E3A52" if cidx else AZUL)
            if cidx == 0:
                st += "fontStyle=1;"
        al = "align=left;spacingLeft=10;" if cidx == 0 else "align=center;"
        L.box(x, y, w, h, v, "html=1;whiteSpace=wrap;strokeColor=%s;fontSize=11;%s%s"
              % (ZONA_BD, al, st), zr)
        x += w
    y += h
L.texto(16, y + 10, 480, 36, "Latencia del combinado: mediana 13 s, rango 4–23 s.\n"
        "Nikto: N=1; el heurístico HTTP no se midió en ese episodio.", zr)
L.card(16, 350, 480, 80, "C3 · propuesta", zr, "reloj",
       "N=5 por familia + fuerza bruta + legítimo intenso\n2 h de tráfico normal · Suricata con FP medidos", prev=True)

L.pie(630, "Se compara detección por episodio; los falsos positivos se cuentan aparte, en su unidad.",
      [(DATOS, 0, "Datos de la evaluación"), (COPIA, 1, "Configuración fija"), (PREV, 1, "Propuesto")])
L.save("VI-5_Comparacion_ablacion.drawio")
