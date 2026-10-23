# -*- coding: utf-8 -*-
"""VI-4 Respuesta y reversion, como secuencia en el tiempo. Los tres tiempos
separados y medidos desde t_inicio con la CADENA VIGENTE DE 10 s (evidencia
producto-main/docs/evidencias/tiempos-2026-10-15-cadena-10s.md: deteccion 13 s
[4-23] en la ablacion N=3, ataque->decision 26,1 s, respuesta total hasta
nftables 41,4 s, de los cuales decision->nft son 15,3 s); la cadena son tres
temporizadores escalonados de 10 s (:00 publicador, :03 relay, :06 agente); la
reversion es por caducidad (300/1800/3600 s) o retirada manual con nft delete
element; sin etiquetas encimadas."""
from cfkit import Fig, DATOS, COPIA, RED, PERS, GRIS, AZUL, BLOCK
import arqkit
arqkit.BG = "#FFFFFF"

L = Fig("VI-4 / SECUENCIA DE RESPUESTA",
        "Aplicación, caducidad y reversión en el host protegido",
        "El tiempo corre de arriba abajo · los tres tiempos se miden desde el inicio del ataque, con el reloj del sensor")

# ------------------------------------------------------- lineas de vida
COL = {"kali": 360, "sen": 620, "rel": 880, "host": 1160, "ope": 1440}
CAB = [("kali", "Kali", "portatil", "Lanza el ataque"),
       ("sen", "Sensor", "chip", "Decide y publica"),
       ("rel", "Bastión", "red", "Relay del feed"),
       ("host", "Host protegido", "servidor", "Agente + nftables"),
       ("ope", "Operador", "usuarios", "Comprueba y revierte")]
for k, t, i, n in CAB:
    L.card(COL[k] - 115, 140, 230, 56, t, "1", i, n, fondo="#EEF3F8")
    L.vida(COL[k], 196, 930)

def a(k, y):
    return L.ancla(COL[k], y)

# ------------------------------------------------------------ mensajes
T0, TDET, TDEC, TRESP = 262, 308, 408, 765

L.flecha(a("kali", 232), a("host", 232), RED, "escaneo nmap → srv-dmz")
L.flecha(a("kali", T0), a("sen", T0), COPIA, "copia SPAN", dash=1)

mot = L.card(COL["sen"] - 120, 280, 240, 56, "Motor", "1", "arbol", "Marca la ventana · tick 10 s")
pub = L.card(COL["sen"] - 120, 380, 240, 56, "Publicador", "1", "firma", "Agrega y firma · ciclo 10 s (:00)")
L.flecha(mot, pub, DATOS, ex=("0.5", "1"), en=("0.5", "0"))

L.flecha(a("sen", 470), a("rel", 470), DATOS, "feed firmado")
rel = L.card(COL["rel"] - 120, 490, 240, 56, "Relay", "1", "red", "Réplica · ciclo 10 s (:03)")
L.flecha(a("rel", 580), a("host", 580), DATOS, "pull del agente · ciclo 10 s (:06)")

ver = L.rombo(COL["host"] - 100, 610, 200, 80, "¿Firma\nválida?")
noap = L.card(COL["ope"] - 115, 622, 230, 56, "No aplica", "1", "llave", "Lo vigente caduca solo")
nft = L.card(COL["host"] - 130, 730, 260, 70, "nftables", "1", "candado", "LIMIT o BLOCK\ncon caducidad",
             fondo=BLOCK[0], borde=BLOCK[1])
cad = L.card(COL["host"] - 130, 850, 260, 56, "Caduca sola", "1", "reloj", "300 · 1800 · 3600 s")
ret = L.card(COL["ope"] - 115, 850, 230, 56, "Retirada manual", "1", "pantalla", "nft delete element")

L.flecha(ver, noap, DATOS, "No", ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(ver, nft, DATOS, "Sí", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(nft, cad, DATOS, ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(ret, nft, PERS, "retira", ex=("0.5", "0"), en=("1", "0.5"), pts=[(COL["ope"], TRESP)])

# ------------------------------------------------- regla de los tiempos
L.texto(48, 214, 200, 18, "t_inicio", tam=11, color=AZUL, extra="fontStyle=1;")
for x, y1, nom, val in [(56, TRESP, "respuesta", "41,4 s"),
                        (120, TDEC, "decisión", "26,1 s"),
                        (184, TDET, "detección", "13 s [4–23]")]:
    L.box(x, T0, 6, y1 - T0, "", "fillColor=%s;strokeColor=none;" % DATOS)
    L.texto(x + 12, y1 - 16, 64, 34, "%s\n%s" % (nom, val), tam=10, color=AZUL, extra="fontStyle=1;")
L.guia(48, COL["kali"], T0)
L.guia(260, COL["sen"] - 120, TDET)
L.guia(196, COL["sen"] - 120, TDEC)
L.guia(132, COL["host"] - 130, TRESP)

L.pie(950, "La respuesta la marcan tres temporizadores escalonados de 10 s (:00/:03/:06), no el cómputo.",
      [(RED, 0, "Tráfico del ataque"), (COPIA, 1, "Copia SPAN"),
       (DATOS, 0, "Entrega y ejecución"), (PERS, 0, "Acción de una persona")])
L.texto(48, 1020, 1520, 20, "Cadena vigente de 10 s (medición 15-oct): ataque→decisión 26,1 s · decisión→nftables 15,3 s · total 41,4 s. "
        "Una firma inválida no borra nada: lo ya aplicado caduca a su hora.")
L.h = 1060
L.save("VI-4_Respuesta_reversion.drawio")
