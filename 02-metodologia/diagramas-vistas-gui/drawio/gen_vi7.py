# -*- coding: utf-8 -*-
"""VI-7 Matriz de validacion interna. Correcciones respecto del SVG: estados
rellenos con la nota que los respalda; filas nuevas 'Comparacion con Suricata'
y 'Tres tiempos'; el estado parcial dice que falta."""
from cfkit import Fig, DATOS, GRIS, AZUL, LIMIT
import arqkit
arqkit.ICON["medio"] = '<circle cx="12" cy="12" r="9"/><path d="M12 3v18"/><path d="M12 3a9 9 0 0 0 0 18z" fill="#D99A2B" stroke="none"/>'
arqkit.ICON["vacio"] = '<circle cx="12" cy="12" r="9"/>'
arqkit.BG = "#FFFFFF"

L = Fig("VI-7 / VALIDACIÓN INTERNA Y EVIDENCIAS",
        "De cada requisito a una prueba y su evidencia",
        "Estado al 12-oct · cada estado cita la nota que lo respalda · TAM y expertos van en la validación externa")

ESTADO = {"C": ("Cumplido", "permitir", "#E6F4EE", "#2E8B6E"),
          "P": ("Parcial", "medio", LIMIT[0], LIMIT[1]),
          "N": ("Pendiente", "vacio", "#F1F4F7", "#9AA9B6")}

FILAS = [
    ("Instalación offline", "engranaje", "Desde cero en una VM limpia", "doctor.sh OK a los 30 min · nota R", "C", ""),
    ("Captura y extracción", "disco", "PCAP + EVE → 28 variables", "Espejo sin descartes · notas B y D", "C", ""),
    ("Decisión híbrida", "arbol", "Score, regla y motivo por ventana", "Registro de decisiones · nota 31", "C", ""),
    ("Respuesta distribuida", "candado", "Feed firmado → nftables", "Escaneo bloqueado · notas O y 26", "P", "falta fuerza bruta"),
    ("Acceso por roles", "usuarios", "admin y lector", "401 sin sesión, sin HTTP en claro · nota R", "P", "falta ingreso por navegador"),
    ("Reentrenamiento", "arbol", "Lote → candidato → evaluación", "Oro, linaje, lote rechazado · nota S", "P", "sin candidato real"),
    ("Reversión", "flecha", "Caducidad y retirada manual", "Escalera en pruebas unitarias", "P", "falta registro en vivo"),
    ("Comparación con Suricata", "lupa", "Mismo PCAP, cuatro condiciones", "Batería N=3 · notas 26, 28 y 31", "P", "C3 propuesta · nota 33"),
    ("Tres tiempos", "reloj", "Detección, decisión, respuesta", "Mediciones del 06-oct (N=3 y N=2)", "C", "N pequeño"),
]

CX = [(48, 340), (412, 360), (796, 420), (1240, 312)]
for (x, w), t in zip(CX, ["REQUISITO", "PRUEBA", "EVIDENCIA", "ESTADO"]):
    c = L.box(x, 140, w, 40, "", "fillColor=#E7EDF3;strokeColor=#C9D3DD;rounded=1;absoluteArcSize=1;arcSize=8;html=1;")
    L.texto(18, 10, w - 30, 20, t, c, tam=12, color=AZUL, extra="fontStyle=1;")

CELDA = "fillColor=#FFFFFF;strokeColor=#C9D3DD;rounded=1;absoluteArcSize=1;arcSize=8;html=1;"
y = 196
for req, ico, pru, evi, est, falta in FILAS:
    r = L.card(CX[0][0], y, CX[0][1], 56, req, "1", ico, "")
    p = L.box(CX[1][0], y, CX[1][1], 56, "", CELDA)
    L.texto(18, 18, CX[1][1] - 30, 20, pru, p, tam=12, color="#1E3A52")
    e = L.box(CX[2][0], y, CX[2][1], 56, "", CELDA)
    L.texto(18, 18, CX[2][1] - 30, 20, evi, e, tam=12, color="#1E3A52")
    nom, ic_, f, b = ESTADO[est]
    s = L.card(CX[3][0], y, CX[3][1], 56, nom, "1", ic_, falta, fondo=f, borde=b, color_ico=b)
    for a, z in ((r, p), (p, e), (e, s)):
        L.flecha(a, z, "#9AA9B6", ex=("1", "0.5"), en=("0", "0.5"), w="1.2")
    y += 66

# leyenda de estados
L.texto(48, y + 22, 300, 20, "ESTADOS", tam=11, color=GRIS, extra="fontStyle=1;")
for i, k in enumerate("CPN"):
    nom, ic_, f, b = ESTADO[k]
    L.card(412 + i * 240, y + 10, 220, 44, nom, "1", ic_, fondo=f, borde=b, color_ico=b)
cuenta = {k: sum(1 for x in FILAS if x[4] == k) for k in "CPN"}
L.texto(1140, y + 14, 412, 40, "%d cumplidos · %d parciales · %d pendientes.\n"
        "Parcial dice siempre qué falta." % (cuenta["C"], cuenta["P"], cuenta["N"]))

L.pie(y + 80, "Ningún estado sin su evidencia: lo que falta queda escrito, no se rellena.",
      [("#9AA9B6", 0, "De requisito a evidencia")])
L.save("VI-7_Matriz_validacion.drawio")
