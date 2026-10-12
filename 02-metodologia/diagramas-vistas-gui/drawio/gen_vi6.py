# -*- coding: utf-8 -*-
"""VI-6 Reentrenamiento supervisado. Correcciones respecto del SVG:
banda propia de deriva contra el conjunto de oro; excluir_ventanas; marcas de
ejecutado / pendiente (oro, saneamiento, lote rechazado del 10-oct, deriva
medida frente a candidato sin ejecutar); veredicto en abanico sin lineas
superpuestas; promover y revertir como accion de una persona.
Fuente: producto/docs/APRENDIZAJE.md y nota S."""
from cfkit import Fig, DATOS, PREV, PERS, GRIS, AZUL, LIMIT, BLOCK
import arqkit
arqkit.BG = "#FFFFFF"

L = Fig("VI-6 / REENTRENAMIENTO SUPERVISADO",
        "El sistema prepara candidatos; solo una persona los promueve",
        "Cada noche a las 00:30 UTC · cuatro defensas contra el envenenamiento · promoción reversible")

OK = ("#E6F4EE", "#2E8B6E", "#1F6B53")
PEND = ("#F1F4F7", "#9AA9B6", "#5B6F80")


def marca(card, w, txt, hecho=True):
    f, b, c = OK if hecho else PEND
    tw = 8 + 7 * len(txt)
    L.box(w - tw - 10, -10, tw, 20, txt, "rounded=1;arcSize=50;html=1;fillColor=%s;strokeColor=%s;"
          "fontSize=9;fontStyle=1;fontColor=%s;%s" % (f, b, c, "" if hecho else "dashed=1;"), card)


# ------------------------------------------------------- 01 datos
b1 = L.zona("01", "DATOS DEL DÍA · SANEAMIENTO Y LINAJE", 48, 140, 1504, 205)
dat = L.card(16, 56, 200, 64, "Dataset acumulado", b1, "disco", "Cada 10 min")
exv = L.card(248, 56, 220, 64, "Excluir ventanas", b1, "lupa", "Ráfaga Kali del 27-sep")
san = L.card(500, 56, 240, 64, "Saneamiento", b1, "embudo", "Contaminación · atípicos")
psi = L.rombo(772, 46, 170, 84, "¿PSI ≤ 0,5?", b1)
rec = L.card(737, 140, 240, 56, "Lote rechazado", b1, "bloquear", "10-oct · PSI 2,41",
             fondo=LIMIT[0], borde=LIMIT[1])
ace = L.card(980, 56, 220, 64, "Lote aceptado", b1, "check", "Elegible para candidato")
lin = L.card(1232, 56, 256, 64, "Linaje", b1, "candado", "sha256 encadenado")
marca(exv, 220, "aplicado")
marca(san, 240, "ejecutado")
marca(lin, 256, "ejecutado")

# ------------------------------------------------------- 02 deriva
b2 = L.zona("02", "DERIVA · EL MODELO VIGENTE FRENTE AL ORO", 48, 365, 1504, 135)
oro = L.card(16, 46, 240, 64, "Conjunto de oro", b2, "cofre", "65 421 ventanas · no entrena")
med = L.card(290, 46, 240, 64, "Medir vigente", b2, "grafico", "FPR 4,45 % · PSI")
dis = L.rombo(570, 34, 220, 88, "¿Deriva sostenida\no toca el mes?", b2)
L.texto(830, 52, 640, 40, "La deriva solo adelanta el reentrenamiento:\nnunca cambia el modelo por sí sola.", b2)
marca(oro, 240, "creado")
marca(med, 240, "medido")

# ------------------------------------------------------- 03 candidato
b3 = L.zona("03", "CANDIDATO · ENTRENAR Y EVALUAR", 48, 525, 1504, 165)
bas = L.card(16, 56, 220, 64, "Base", b3, "tabla", "Entrenamiento nota L")
lim = L.card(268, 56, 260, 64, "Límite de influencia", b3, "embudo", "≤ 30 % nuevo · ≤ 10 % por IP")
ent = L.card(560, 56, 240, 64, "Entrenar candidato", b3, "arbol", "Isolation Forest")
eva = L.card(832, 56, 260, 64, "Evaluar", b3, "visto", "Oro + ataques nota M")
marca(ent, 240, "pendiente", False)
marca(eva, 260, "pendiente", False)
v_no = L.pastilla(1120, 44, 368, 30, "NO_PROMOVER · se queda el vigente", b3,
                  fondo=BLOCK[0], borde=BLOCK[1], color=AZUL)
v_in = L.pastilla(1120, 82, 368, 30, "EVALUACION_INCOMPLETA · faltan ataques", b3,
                  fondo=LIMIT[0], borde=LIMIT[1], color=AZUL)
v_pr = L.pastilla(1120, 120, 368, 30, "PROMOVIBLE · FPR y detección no empeoran", b3,
                  fondo="#E6F4EE", borde="#2E8B6E", color=AZUL)

# ------------------------------------------------------- 04 persona
b4 = L.zona("04", "UNA PERSONA DECIDE", 48, 710, 1504, 115)
rev = L.card(280, 46, 360, 56, "revertir", b4, "flecha", "Restaura el .toml anterior")
uso = L.card(700, 46, 360, 56, "Modelo en uso", b4, "chip", "Cambia solo por estas dos vías", fondo="#EEF3F8")
pro = L.card(1120, 46, 368, 56, "promover <id>", b4, "usuarios", "Guarda copia del .toml")
marca(pro, 368, "pendiente", False)

# ------------------------------------------------------------ conectores
L.flecha(dat, exv, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(exv, san, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(san, psi, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(psi, ace, DATOS, "Sí", ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(psi, rec, DATOS, "No", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(ace, lin, DATOS, ex=("1", "0.5"), en=("0", "0.5"))

L.flecha(oro, med, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(med, dis, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(dis, ent, PREV, "Sí", ex=("0.5", "1"), en=("0.5", "0"), dash=1)
L.flecha(lin, lim, DATOS, "lotes aceptados", ex=("0.5", "1"), en=("0.5", "0"),
         pts=[(1408, 512), (446, 512)])

L.flecha(bas, lim, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(lim, ent, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(ent, eva, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
for v in (v_no, v_in, v_pr):
    L.flecha(eva, v, DATOS, ex=("1", "0.5"), en=("0", "0.5"), pts=[(1154, 613)])

L.flecha(v_pr, pro, PERS, ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(pro, uso, PERS, ex=("0", "0.5"), en=("1", "0.5"))
L.flecha(rev, uso, PERS, ex=("1", "0.5"), en=("0", "0.5"))

L.pie(855, "Isolation Forest no es supervisado; lo supervisado es el proceso: ningún modelo entra sin una persona.",
      [(DATOS, 0, "Datos y evaluación"), (PREV, 1, "Disparo pendiente"), (PERS, 0, "Acción de una persona")])
L.save("VI-6_Reentrenamiento.drawio")
