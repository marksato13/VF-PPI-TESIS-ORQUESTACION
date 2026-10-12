# -*- coding: utf-8 -*-
"""VI-3 Decision hibrida. Correcciones respecto del SVG:
dos niveles (el motor decide por ventana; el publicador combina por IP cada
60 s sobre los ultimos 120 s); filtro 'nunca bloquear'; las IP excluidas se
cuentan; la version de umbrales va en el feed; las cuatro reglas con su accion
en un solo bloque, sin cruces; PERMIT/LIMIT/BLOCK con icono propio.
Fuentes: motor_decision.py, heuristicos.py, publicar_feed.py, escalada.py."""
from cfkit import Fig, DATOS, PREV, GRIS, LIMIT, BLOCK
import arqkit
arqkit.BG = "#FFFFFF"

L = Fig("VI-3 / FLUJO DE DECISIÓN HÍBRIDA",
        "De una ventana por IP a una acción explicable",
        "El motor decide cada ventana; el publicador combina por IP y fija la caducidad")

# --------------------------------------------------------------- entrada
ent = L.card(48, 140, 280, 64, "eve.json + anillo PCAP", "1", "documento", "Eventos y paquetes")
ext = L.card(372, 140, 300, 64, "Extractor", "1", "engranaje", "28 variables por IP y ventana")
exc = L.rombo(716, 132, 220, 80, "¿IP excluida?")
fue = L.card(1000, 140, 300, 64, "Excluida", "1", "lupa", "Se contabiliza; no se puntúa")

# ------------------------------------------------- nivel 1: motor
n1 = L.zona("01", "NIVEL 1 · MOTOR — decide cada ventana", 48, 250, 1504, 325)
r1 = L.rombo(16, 65, 180, 90, "¿Paquetes\nen 10 s?", n1)
ifo = L.card(240, 80, 240, 60, "Isolation Forest", n1, "arbol", "s(x) = score_samples(x)")
r2 = L.rombo(524, 65, 180, 90, "s(x) < θ ?", n1)
alm = L.card(748, 80, 220, 60, "ALERT del modelo", n1, "campana", "θ = −0,568892",
             fondo=LIMIT[0], borde=LIMIT[1])
p1 = L.pastilla(46, 172, 120, 26, "sin puntuar", n1)
p2 = L.pastilla(554, 172, 120, 26, "PERMIT", n1)

heu = L.box(240, 205, 776, 100, "", "fillColor=#FFFFFF;strokeColor=#C9D3DD;rounded=1;"
            "absoluteArcSize=1;arcSize=10;html=1;", n1)
L.texto(16, 10, 744, 20, "Heurísticos versionados · 2026-10-06.2 · también sin paquetes (L7)", heu,
        tam=12, color="#1E3A52", extra="fontStyle=1;")
for i, (nom, tipo) in enumerate([("Fuerza bruta", "BLOCK"), ("Escaneo", "BLOCK"),
                                 ("Abuso HTTP", "LIMIT"), ("DNS entropía", "LIMIT")]):
    f, b = BLOCK if tipo == "BLOCK" else LIMIT
    L.pastilla(16 + i * 190, 44, 176, 40, "%s → %s" % (nom, tipo), heu, fondo=f, borde=b,
               color="#1E3A52")

reg = L.card(1180, 62, 308, 242, "Registro de decisión", n1, "tabla",
             "IP · ventana · score · regla\nmotor_decision.log")

# ------------------------------------------------- nivel 2: publicador
n2 = L.zona("02", "NIVEL 2 · PUBLICADOR — cada 60 s, sobre los últimos 120 s, por IP", 48, 600, 1504, 150)
fil = L.card(16, 56, 316, 64, "Nunca bloquear", n2, "embudo", "Bastión · sensor · gateways · DNS")
com = L.card(400, 56, 316, 64, "La más severa por IP", n2, "visto", "Modelo → LIMIT · regla → su acción")
esc = L.card(784, 56, 316, 64, "Escalera de caducidad", n2, "reloj", "Reincidencia en 24 h")
fee = L.card(1168, 56, 316, 64, "Feed firmado", n2, "firma", "Lleva la versión de umbrales",
             fondo="#EEF3F8")

# ------------------------------------------------- acciones
per = L.accion(64, 790, 460, 64, "PERMIT", "Sin entrada en el feed", "1")
lim = L.accion(570, 790, 460, 64, "LIMIT", "Limitación de tasa · 300 s", "1")
blo = L.accion(1076, 790, 460, 64, "BLOCK", "300 → 1800 → 3600 s · revisión humana desde el 3.º", "1")

# ------------------------------------------------------------ conectores
L.flecha(ent, ext, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(ext, exc, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(exc, fue, DATOS, "Sí", ex=("1", "0.5"), en=("0", "0.5"))
# No: se abre hacia el modelo y hacia los heuristicos
L.flecha(exc, r1, DATOS, "No", ex=("0.5", "1"), en=("0", "0.5"), pts=[(826, 232), (58, 232), (58, 365)])
L.flecha(exc, heu, DATOS, ex=("0.5", "1"), en=("0", "0.5"), pts=[(826, 232), (58, 232), (58, 505)])

L.flecha(r1, ifo, DATOS, "Sí", ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(r1, p1, PREV, "No", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(ifo, r2, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(r2, alm, DATOS, "Sí", ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(r2, p2, PREV, "No", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(alm, reg, DATOS, ex=("1", "0.5"), en=("0", "0.2"))
L.flecha(heu, reg, DATOS, ex=("1", "0.5"), en=("0", "0.8"))

L.flecha(reg, fil, DATOS, "decisiones por ventana", ex=("0.5", "1"), en=("0", "0.5"),
         pts=[(1382, 588), (58, 588), (58, 688)])
L.flecha(fil, com, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(com, esc, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(esc, fee, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
# abanico del feed a las tres acciones
for d in (per, lim, blo):
    L.flecha(fee, d, DATOS, ex=("0.5", "1"), en=("0.5", "0"), pts=[(1374, 770)])

L.pie(880, "Caducidad finita: ningún bloqueo automático es indefinido.",
      [(DATOS, 0, "Flujo de la decisión"), (PREV, 1, "Sin acción")])
L.save("VI-3_Decision_hibrida.drawio")
