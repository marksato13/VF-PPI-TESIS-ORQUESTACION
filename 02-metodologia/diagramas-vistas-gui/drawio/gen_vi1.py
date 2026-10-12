# -*- coding: utf-8 -*-
"""VI-1 Arquitectura operativa. Correcciones respecto del SVG:
pfSense en la ruta, la copia SPAN sale del conmutador, el recorrido no pasa por
srv-dmz, cadencia de 60 s en publicador/relay/agente, Wazuh como previsto,
srv-dmz identificado como el host protegido de la zona 03."""
import cfkit, arqkit
from cfkit import Fig, DATOS, COPIA, RED, PREV, GRIS
arqkit.BG = "#FFFFFF"

L = Fig("VI-1 / ARQUITECTURA OPERATIVA",
        "CyberFlow: captura, decisión y respuesta distribuida",
        "Observación pasiva en el sensor · decisión por ventana · aplicación en el host protegido")

# ---------------------------------------------------------------- zonas
Z1x, Z2x, Z3x, ZY, ZH = 48, 432, 1096, 130, 640
z1 = L.zona("01", "CAPTURA DE TRÁFICO", Z1x, ZY, 360, ZH)
z2 = L.zona("02", "ANÁLISIS EN EL SENSOR", Z2x, ZY, 640, ZH)
z3 = L.zona("03", "RESPUESTA DISTRIBUIDA", Z3x, ZY, 456, ZH)

# 01: hosts arriba, conmutador en medio, pfSense y servidor abajo
cli = L.card(16, 60, 156, 64, "Clientes", z1, "escritorio", "6 perfiles")
kali = L.card(188, 60, 156, 64, "Kali", z1, "portatil", "atacante")
sw = L.card(16, 170, 328, 70, "Conmutador CORE-STACK", z1, "conmutador", "Espejo de puertos (SPAN)")
pf = L.card(16, 290, 156, 64, "pfSense", z1, "enrutador", "ruteo entre VLAN")
dmz = L.card(188, 290, 156, 64, "srv-dmz", z1, "servidor", "10.10.30.10")
L.texto(16, 400, 328, 60, "El sensor recibe una copia del tráfico.\nNo reenvía ni filtra nada.",
        z1, extra="align=center;")

# 02: dos columnas de tarjetas
IZ, DE, CW = 16, 328, 296
sen = L.card(16, 60, 608, 60, "Sensor pasivo", z2, "chip", "Interfaz de captura sin IP · modo promiscuo")
sur = L.card(IZ, 170, CW, 64, "Suricata", z2, "documento", "Eventos → eve.json")
pcap = L.card(DE, 170, CW, 64, "Anillo PCAP", z2, "disco", "Captura rotativa")
ext = L.card(IZ, 290, CW, 64, "Extractor", z2, "engranaje", "28 variables por ventana")
mot = L.card(DE, 290, CW, 64, "Motor híbrido", z2, "arbol", "Isolation Forest + heurísticos",
             fondo="#EEF3F8")
obs = L.card(IZ, 410, CW, 64, "Observación", z2, "pantalla", "Registro de decisiones · panel")
pub = L.card(DE, 410, CW, 64, "Publicador", z2, "firma", "Feed firmado Ed25519 · cada 60 s",
             fondo="#EEF3F8")
waz = L.card(IZ, 530, CW, 56, "Wazuh", z2, "campana", "previsto", prev=True)
L.texto(DE, 540, CW, 40, "Sin enforcement local:\nel sensor no toca la red.", z2)

# 03: bastion y host protegido como limites de maquina
mb = L.maquina("BASTIÓN", 16, 60, 424, 120, z3)
rel = L.card(16, 36, 392, 64, "Relay del feed", mb, "red", "Réplica en la red interna · cada 60 s")
mh = L.maquina("HOST PROTEGIDO · srv-dmz", 16, 210, 424, 400, z3)
age = L.card(16, 36, 392, 64, "Agente", mh, "engranaje", "Pull del feed · cada 60 s")
ver = L.card(16, 150, 392, 64, "Verificación de firma", mh, "llave", "Firma inválida: no aplica cambios")
nft = L.card(16, 264, 392, 80, "nftables", mh, "candado", "LIMIT: limitación de tasa\nBLOCK: conjunto con expiración",
             fondo="#EEF3F8")

# ------------------------------------------------------------ conectores
# recorrido normal: hosts -> conmutador -> pfSense / servidor
L.flecha(cli, sw, RED, ex=("0.5", "1"), en=("0.2378", "0"))
L.flecha(kali, sw, RED, ex=("0.5", "1"), en=("0.7622", "0"))
L.flecha(sw, pf, RED, ex=("0.2378", "1"), en=("0.5", "0"), doble=True)
L.flecha(sw, dmz, RED, ex=("0.7622", "1"), en=("0.5", "0"), doble=True)

# copia SPAN: del conmutador al sensor, por el pasillo entre zonas
L.flecha(sw, sen, COPIA, "copia SPAN", ex=("1", "0.5"), en=("0", "0.5"),
         pts=[(420, 335), (420, 220)], dash=1)

# dentro del sensor
L.flecha(sen, sur, DATOS, ex=("0.2434", "1"), en=("0.5", "0"))
L.flecha(sen, pcap, DATOS, ex=("0.7566", "1"), en=("0.5", "0"))
L.flecha(sur, ext, DATOS, ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(pcap, ext, DATOS, ex=("0.5", "1"), en=("0.8", "0"), pts=[(908, 392), (685, 392)])
L.flecha(ext, mot, DATOS, ex=("1", "0.5"), en=("0", "0.5"))
L.flecha(mot, pub, DATOS, "decisión", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(mot, obs, DATOS, ex=("0.2", "1"), en=("0.8", "0"), pts=[(819, 512), (685, 512)])
L.flecha(obs, waz, PREV, ex=("0.5", "1"), en=("0.5", "0"), dash=1)

# feed firmado: sale del sensor y cruza al bastion por el pasillo
L.flecha(pub, rel, DATOS, "feed firmado", ex=("1", "0.5"), en=("0", "0.5"),
         pts=[(1084, 572), (1084, 258)])
L.flecha(rel, age, DATOS, "pull", ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(age, ver, DATOS, ex=("0.5", "1"), en=("0.5", "0"))
L.flecha(ver, nft, DATOS, "firma válida", ex=("0.5", "1"), en=("0.5", "0"))

L.pie(800, "El sensor observa; nftables actúa en el núcleo del host protegido.",
      [(RED, 0, "Tráfico de la red"), (COPIA, 1, "Copia SPAN"),
       (DATOS, 0, "Datos y ejecución"), (PREV, 1, "Previsto")])
L.save("VI-1_Arquitectura_operativa.drawio")
