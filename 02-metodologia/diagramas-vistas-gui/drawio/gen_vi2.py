# -*- coding: utf-8 -*-
"""VI-2 Topologia experimental. Correcciones respecto del SVG:
capa ESXi con el grupo de puertos PG-CYBERFLOW-SPAN bajo Gi2/0/19; el Sensor2
tambien cuelga del grupo; DNS/AD 10.10.10.20 en la VLAN 10; el comparador
VM-SURICATA como recepcion por comprobar; leyenda que distingue enlace,
recorrido de prueba y copia SPAN; puntos de comprobacion 1-4."""
from cfkit import Fig, DATOS, COPIA, RED, PREV, GRIS
import arqkit
arqkit.BG = "#FFFFFF"

L = Fig("VI-2 / TOPOLOGÍA EXPERIMENTAL",
        "Recorrido del tráfico y observación pasiva por SPAN",
        "Segmentación por VLAN sobre hardware físico · el ruteo entre VLAN lo hace pfSense, no el conmutador")

ENLACE = "#A9B6C1"

# ------------------------------------------------------- VLAN (izquierda)
v20 = L.zona("", "VLAN 20 · USUARIOS Y ATAQUES", 48, 150, 380, 160)
L.texto(16, 34, 340, 18, "10.10.20.0/24", v20)
L.card(16, 62, 170, 64, "Clientes", v20, "escritorio", ".21 – .26")
L.card(194, 62, 170, 64, "Kali", v20, "portatil", ".30")
L.punto(16, 132, 1, "Generado: registro del emisor", v20)

v30 = L.zona("", "VLAN 30 · DMZ", 48, 330, 380, 160)
L.texto(16, 34, 340, 18, "10.10.30.0/24", v30)
dmz = L.card(16, 62, 348, 64, "srv-dmz", v30, "servidor", "10.10.30.10 · servidor objetivo")
L.punto(16, 132, 3, "Recibido: log del servidor", v30)

v10 = L.zona("", "VLAN 10 · GESTIÓN", 48, 510, 380, 140)
L.texto(16, 34, 340, 18, "10.10.10.0/24", v10)
L.card(16, 62, 170, 64, "VM-GESTION", v10, "servidor", ".30 · bastión")
L.card(194, 62, 170, 64, "DNS / AD", v10, "red", ".20")

# ------------------------------------------------------------ centro
L.punto(470, 140, 2, "Encaminado / filtrado")
pf = L.card(470, 170, 400, 76, "pfSense A/B", "1", "enrutador",
            "Gateway y firewall · ruteo entre VLAN", fondo="#EEF3F8")
sw = L.card(470, 380, 400, 90, "CORE-STACK", "1", "conmutador",
            "Conmutador físico · VLAN y troncales\nNo enruta entre VLAN")
L.texto(470, 296, 400, 36, "Troncales\nGi1/0/23 · Gi2/0/23", extra="align=center;")

# ----------------------------------------------------- ESXi (derecha)
ex = L.maquina("HOST ESXi · 172.17.25.2", 960, 150, 592, 500, "1")
pg = L.card(20, 40, 552, 64, "PG-CYBERFLOW-SPAN", ex, "red",
            "Grupo de puertos · modo promiscuo", fondo="#FFF6EA", borde="#E3B577")
s1 = L.card(20, 150, 266, 120, "Sensor1", ex, "chip",
            "ens37 · captura sin IP\nens34 · 10.10.60.11\nSolo observa", fondo="#EEF3F8")
s2 = L.card(306, 150, 266, 120, "Sensor2", ex, "chip",
            "ens37 · captura sin IP\nens34 · 10.10.60.12\nRéplica")
cmp_ = L.card(20, 300, 530, 64, "VM-SURICATA", ex, "documento",
              "10.10.60.13 · comparador · recepción por comprobar", prev=True)
L.punto(20, 390, 4, "Observado: PCAP + eventos EVE", ex)
L.texto(20, 424, 560, 36, "Gestión de los sensores por VLAN 60 · 10.10.60.0/24", ex)

# --------------------------------------------------------- conectores
# enlaces fisicos sin flecha
st_enl = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=%s;strokeWidth=1.4;"
          "endArrow=none;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.15;entryY=1;entryDx=0;entryDy=0;"
          % ENLACE)
L.edge(v10, sw, st_enl, "", [(530, 580)])

# recorrido de prueba: VLAN 20 -> conmutador -> pfSense -> conmutador -> srv-dmz
L.flecha(v20, sw, RED, ex=("1", "0.5"), en=("0", "0.2"),
         pts=[(446, 230), (446, 398)], w="2")
L.flecha(sw, pf, RED, ex=("0.3", "0"), en=("0.3", "1"), w="2")
L.flecha(pf, sw, RED, ex=("0.7", "1"), en=("0.7", "0"), w="2")
L.flecha(sw, dmz, RED, ex=("0", "0.4889"), en=("1", "0.5"), w="2")

# copia SPAN hacia el grupo de puertos y de ahi a las VM
L.flecha(sw, pg, COPIA, "copia SPAN\nGi2/0/19", ex=("1", "0.5"), en=("0", "0.5"),
         pts=[(915, 425), (915, 222)], dash=1, w="2")
L.flecha(pg, s1, COPIA, ex=("0.2409", "1"), en=("0.5", "0"), dash=1)
L.flecha(pg, s2, COPIA, ex=("0.7591", "1"), en=("0.5", "0"), dash=1)
L.flecha(pg, cmp_, PREV, ex=("1", "0.5"), en=("1", "0.5"), pts=[(1544, 222), (1544, 482)], dash=1)

L.pie(690, "Segmentación lógica por VLAN; el sensor recibe una copia y no forma parte del recorrido.",
      [(ENLACE, 2, "Enlace de red"), (RED, 0, "Recorrido de prueba"),
       (COPIA, 1, "Copia SPAN"), (PREV, 1, "Por comprobar")])
L.texto(48, 760, 1500, 20, "Puntos 1–4: dónde se comprueba que el tráfico existió, no resultados.")
L.h = 800
L.save("VI-2_Topologia_experimental.drawio")
