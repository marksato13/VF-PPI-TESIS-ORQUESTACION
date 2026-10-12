# -*- coding: utf-8 -*-
"""Fig. 1 Metodologia por fases, con el estilo de las VI-x. Cambios respecto
del SVG: estado de cada fase; F7 separa la validacion interna de la externa
pendiente; dos lazos de vuelta distintos (recalibrar tras evaluar y
reentrenamiento supervisado desde la operacion) mas el de mejoras desde la
validacion, anidados para que no se crucen."""
from cfkit import Fig, DATOS, PREV, PERS, GRIS, AZUL, ZONA_BD, ICO
import arqkit
from arqkit import ic, IMG, TXT
arqkit.BG = "#FFFFFF"

L = Fig("FIG. 1 / METODOLOGÍA",
        "Siete fases, de la captura a la validación",
        "Cada fase deja un artefacto que usa la siguiente · las flechas de abajo son las vueltas atrás")

OK = ("#E6F4EE", "#2E8B6E", "#1F6B53")
PARC = ("#FFF4E0", "#D99A2B", "#8A5A12")
PEND = ("#F1F4F7", "#9AA9B6", "#5B6F80")

FASES = [
    ("F1", "Datos y\nlínea base", "red", "Espejo SPAN\nSensor pasivo\nPCAP + EVE", ("hecho", OK)),
    ("F2", "Preproceso\nmulticapa", "engranaje", "Extracción\n28 variables\nL3 · L4 · L7", ("hecho", OK)),
    ("F3", "Modelado\nhíbrido", "arbol", "IF recalibrado\nθ = −0,568892\n+ heurísticos", ("hecho", OK)),
    ("F4", "Experimento y\nevaluación", "lupa", "PCAP común\nReplay\nfrente a Suricata", ("parcial", PARC)),
    ("F5", "Respuesta", "candado", "PERMIT · LIMIT · BLOCK\nFeed firmado\nCaducidad finita", ("hecho", OK)),
    ("F6", "Despliegue en\noperación", "servidor", "Sensor y host\nsystemd\nEn vivo", ("hecho", OK)),
    ("F7", "Validación", "visto", "Interna: demo técnica\nExterna: TAM y expertos", ("en curso", PARC)),
]

X0, W, GAP, Y = 48, 196, 22, 170
L.box(X0, 132, 4 * W + 3 * GAP, 26, "CONSTRUIR Y EVALUAR",
      "rounded=1;arcSize=50;html=1;fillColor=#EEF3F8;strokeColor=none;fontSize=11;fontStyle=1;fontColor=%s;" % AZUL)
L.box(X0 + 4 * (W + GAP), 132, 3 * W + 2 * GAP, 26, "OPERAR Y VALIDAR",
      "rounded=1;arcSize=50;html=1;fillColor=#FFF6EA;strokeColor=none;fontSize=11;fontStyle=1;fontColor=%s;" % AZUL)

cards = []
for i, (num, tit, ico, det, (est, col)) in enumerate(FASES):
    x = X0 + i * (W + GAP)
    g = L.box(x, Y, W, 240, "", "fillColor=#FFFFFF;strokeColor=%s;rounded=1;absoluteArcSize=1;"
              "arcSize=12;html=1;strokeWidth=1.2;" % ZONA_BD)
    L.box(16, 16, 40, 24, num, "rounded=1;arcSize=40;html=1;fillColor=%s;strokeColor=none;"
          "fontSize=12;fontStyle=1;fontColor=#FFFFFF;" % AZUL, g)
    f, b, c = col
    tw = 10 + 7 * len(est)
    L.box(W - tw - 14, 18, tw, 20, est, "rounded=1;arcSize=50;html=1;fillColor=%s;strokeColor=%s;"
          "fontSize=9;fontStyle=1;fontColor=%s;" % (f, b, c), g)
    L.box(16, 58, 34, 34, "", IMG + "image=%s;" % ic(ico, ICO), g)
    L.box(16, 100, W - 28, 44, tit, TXT + "fontSize=15;fontStyle=1;fontColor=%s;" % AZUL, g)
    L.box(16, 156, W - 32, 1, "", "fillColor=%s;strokeColor=none;" % ZONA_BD, g)
    L.box(16, 168, W - 28, 64, det, TXT + "fontSize=11;fontColor=%s;" % GRIS, g)
    cards.append(g)

for a, b in zip(cards, cards[1:]):
    L.flecha(a, b, DATOS, ex=("1", "0.5"), en=("0", "0.5"))

# vueltas atras, anidadas: la mas corta arriba, la mas larga abajo
F = lambda i, fx: int(X0 + i * (W + GAP) + fx * W)
YB = Y + 240
L.flecha(cards[3], cards[2], PREV, "recalibrar", ex=("0.25", "1"), en=("0.75", "1"),
         pts=[(F(3, 0.25), YB + 34), (F(2, 0.75), YB + 34)], dash=1)
L.flecha(cards[5], cards[2], PERS, "reentrenar con aprobación humana", ex=("0.5", "1"), en=("0.35", "1"),
         pts=[(F(5, 0.5), YB + 74), (F(2, 0.35), YB + 74)], dash=1)
L.flecha(cards[6], cards[1], PREV, "observaciones → mejoras", ex=("0.5", "1"), en=("0.5", "1"),
         pts=[(F(6, 0.5), YB + 114), (F(1, 0.5), YB + 114)], dash=1)

L.pie(YB + 150, "Las fases avanzan de izquierda a derecha; ningún regreso cambia el modelo en uso sin una persona.",
      [(DATOS, 0, "Avance entre fases"), (PREV, 1, "Vuelta atrás"), (PERS, 1, "Con aprobación humana")])
L.save("Fig1_Metodologia.drawio")
