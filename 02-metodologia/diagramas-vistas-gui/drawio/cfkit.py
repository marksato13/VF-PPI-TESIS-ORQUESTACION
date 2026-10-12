# -*- coding: utf-8 -*-
"""Kit comun de las figuras VI-x de CyberFlow, sobre arqkit (skill diagramas-arquitectura).

Estilo pizarra como los SVG originales: cabecera 'VI-x / SECCION', zonas numeradas
con fondo claro, tarjetas con icono, limites de maquina discontinuos y un pie con
la idea principal y la leyenda de conectores.
"""
import os, sys
sys.path.insert(0, os.path.expanduser(r"~\.claude\skills\diagramas-arquitectura\scripts"))
import arqkit
from arqkit import Lamina, TXT, IMG, ic, esc

arqkit.OUT = os.environ.get("ARQKIT_OUT") or os.path.dirname(os.path.abspath(__file__))

AZUL = "#1E3A52"      # titulos
GRIS = "#5B6F80"      # notas
TENUE = "#8A9BA8"     # previsto
ICO = "#3E5466"       # iconos
ZONA_BG, ZONA_BD = "#F7F9FB", "#C9D3DD"

# conectores por naturaleza
DATOS = "#2A6FA8"     # datos o ejecucion
COPIA = "#D3852B"     # copia SPAN o control (discontinuo)
RED = "#6B7F8E"       # recorrido normal del trafico
PREV = "#9AA9B6"      # previsto o no ejecutado (discontinuo)
PERS = "#2E8B6E"      # hacia la persona

# acciones
PERMIT = ("#F1F4F7", "#9AA9B6")
LIMIT = ("#FFF4E0", "#D99A2B")
BLOCK = ("#FDECEC", "#C0392B")

# iconos extra, mismo trazo que arqkit
arqkit.ICON.update({
    "chip": '<rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/>'
            '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "documento": '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v4h4"/><path d="M9 12h6M9 16h6"/>',
    "arbol": '<rect x="9" y="2.5" width="6" height="5" rx="1"/><rect x="2.5" y="16.5" width="6" height="5" rx="1"/>'
             '<rect x="15.5" y="16.5" width="6" height="5" rx="1"/><path d="M12 7.5v4.5M5.5 16.5V12h13v4.5"/>',
    "permitir": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.2l2.4 2.4 4.6-4.9"/>',
    "limitar": '<path d="M3 12h11"/><path d="M3 7h7"/><path d="M3 17h7"/><path d="M15 6v12"/><path d="M18 9l3 3-3 3"/>',
    "bloquear": '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
    "embudo": '<path d="M3 4h18l-7 8v6l-4 2v-8z"/>',
    "deriva": '<path d="M3 17c3-6 6-6 9 0s6 6 9 0"/><path d="M3 9h18" stroke-dasharray="2 2"/>',
})


class Fig(Lamina):
    """Lamina con la cabecera de las figuras VI-x."""

    def __init__(s, seccion, titulo, bajada, ancho=1600):
        s.c, s.n, s.w, s.h = [], 0, ancho, 1000
        s.y = 130
        s.box(48, 26, 900, 18, seccion, TXT + "fontSize=11;fontColor=%s;fontStyle=1;" % GRIS)
        s.box(48, 44, 1200, 36, titulo, TXT + "fontSize=24;fontColor=%s;fontStyle=1;" % AZUL)
        s.box(48, 82, 1200, 20, bajada, TXT + "fontSize=12;fontColor=%s;" % GRIS)

    def zona(s, nro, nombre, x, y, w, h, fondo=ZONA_BG):
        g = s.box(x, y, w, h, "", "fillColor=%s;strokeColor=%s;rounded=1;arcSize=2;"
                  "html=1;absoluteArcSize=1;arcSize=10;" % (fondo, ZONA_BD))
        s.box(16, 12, w - 32, 22, ("%s  %s" % (nro, nombre)) if nro else nombre,
              TXT + "fontSize=13;fontColor=%s;fontStyle=1;" % AZUL, g)
        return g

    def maquina(s, nombre, x, y, w, h, parent):
        """Limite de maquina: contorno discontinuo con su nombre arriba."""
        g = s.box(x, y, w, h, "", "fillColor=none;strokeColor=%s;dashed=1;dashPattern=5 4;"
                  "rounded=1;absoluteArcSize=1;arcSize=10;html=1;" % TENUE, parent)
        s.box(12, 8, w - 24, 16, nombre, TXT + "fontSize=9;fontColor=%s;fontStyle=1;" % GRIS, g)
        return g

    def card(s, x, y, w, h, tit, parent, icono="servidor", nota="", fondo="#FFFFFF",
             borde="#C9D3DD", prev=False, color_ico=ICO):
        st = ("fillColor=%s;strokeColor=%s;rounded=1;absoluteArcSize=1;arcSize=10;html=1;"
              % (fondo, borde))
        if prev:
            st += "dashed=1;dashPattern=5 4;"
        g = s.box(x, y, w, h, "", st, parent)
        s.box(14, (h - 26) // 2, 26, 26, "", IMG + "image=%s;" % ic(icono, color_ico), g)
        tc = TENUE if prev else AZUL
        if nota:
            ty = max(8, (h - 40) // 2)
            s.box(50, ty, w - 60, 20, tit, TXT + "fontSize=13;fontColor=%s;fontStyle=1;" % tc, g)
            s.box(50, ty + 20, w - 60, h - ty - 22, nota, TXT + "fontSize=10;fontColor=%s;" % GRIS, g)
        else:
            s.box(50, (h - 20) // 2, w - 60, 20, tit,
                  TXT + "fontSize=13;fontColor=%s;fontStyle=1;" % tc, g)
        return g

    def accion(s, x, y, w, h, tipo, nota, parent):
        fondo, borde = {"PERMIT": PERMIT, "LIMIT": LIMIT, "BLOCK": BLOCK}[tipo]
        ico = {"PERMIT": "permitir", "LIMIT": "limitar", "BLOCK": "bloquear"}[tipo]
        return s.card(x, y, w, h, tipo, parent, ico, nota, fondo, borde, color_ico=borde)

    def vida(s, cx, y0, y1):
        """Linea de vida de un diagrama de secuencia."""
        return s.box(cx - 5, y0, 10, y1 - y0, "", "shape=line;direction=south;html=1;dashed=1;"
                     "dashPattern=4 4;strokeColor=#B8C4CE;strokeWidth=1.2;")

    def ancla(s, x, y):
        """Punto invisible para colgar un mensaje de una linea de vida."""
        return s.box(x - 1, y - 1, 2, 2, "", "fillColor=none;strokeColor=none;html=1;")

    def guia(s, x0, x1, y):
        return s.box(x0, y, x1 - x0, 1, "", "shape=line;html=1;dashed=1;dashPattern=2 3;"
                     "strokeColor=#C9D3DD;strokeWidth=1;")

    def rombo(s, x, y, w, h, txt, parent="1"):
        return s.box(x, y, w, h, txt, "rhombus;html=1;whiteSpace=wrap;fillColor=#FFFFFF;"
                     "strokeColor=%s;strokeWidth=1.4;fontSize=12;fontStyle=1;fontColor=%s;"
                     % (AZUL, AZUL), parent)

    def pastilla(s, x, y, w, h, txt, parent="1", fondo="#F1F4F7", borde="#C9D3DD", color=GRIS):
        return s.box(x, y, w, h, txt, "rounded=1;arcSize=50;html=1;fillColor=%s;strokeColor=%s;"
                     "fontSize=10;fontColor=%s;fontStyle=1;" % (fondo, borde, color), parent)

    def punto(s, x, y, n, txt, parent="1", w=320):
        """Punto de comprobacion numerado: circulo con el numero y su texto."""
        s.box(x, y, 22, 22, str(n), "ellipse;html=1;fillColor=#FFFFFF;strokeColor=%s;"
              "strokeWidth=1.4;fontSize=11;fontStyle=1;fontColor=%s;" % (AZUL, AZUL), parent)
        s.box(x + 30, y + 2, w, 20, txt, TXT + "fontSize=11;fontColor=%s;fontStyle=1;" % AZUL, parent)

    def texto(s, x, y, w, h, v, parent="1", tam=10, color=GRIS, extra=""):
        return s.box(x, y, w, h, v, TXT + "fontSize=%d;fontColor=%s;%s" % (tam, color, extra), parent)

    def flecha(s, a, b, color=DATOS, etiqueta="", ex=None, en=None, pts=None, dash=0,
               doble=False, w="1.6"):
        st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=%s;strokeWidth=%s;"
              "endArrow=block;endFill=1;endSize=5;fontSize=10;fontColor=%s;"
              "labelBackgroundColor=#FFFFFF;" % (color, w, GRIS))
        if dash:
            st += "dashed=1;dashPattern=6 4;"
        if doble:
            st += "startArrow=block;startFill=1;startSize=5;"
        if ex:
            st += "exitX=%s;exitY=%s;exitDx=0;exitDy=0;" % ex
        if en:
            st += "entryX=%s;entryY=%s;entryDx=0;entryDy=0;" % en
        return s.edge(a, b, st, etiqueta, pts)

    def pie(s, y, idea, leyenda, w=1504):
        s.box(48, y, w, 1, "", "fillColor=%s;strokeColor=none;" % ZONA_BD)
        s.box(48, y + 14, w, 24, idea, TXT + "fontSize=15;fontColor=%s;fontStyle=1;" % AZUL)
        fx = 48
        for col, dash, txt in leyenda:
            st = "endArrow=block;endFill=1;endSize=5;html=1;strokeColor=%s;strokeWidth=1.6;" % col
            if dash == 2:
                st += "endArrow=none;"
            elif dash:
                st += "dashed=1;dashPattern=6 4;"
            i = s._i()
            s.c.append('<mxCell id="%s" style="%s" edge="1" parent="1"><mxGeometry relative="1" '
                       'as="geometry"><mxPoint x="%d" y="%d" as="sourcePoint"/><mxPoint x="%d" '
                       'y="%d" as="targetPoint"/></mxGeometry></mxCell>'
                       % (i, st, fx, y + 58, fx + 40, y + 58))
            s.box(fx + 48, y + 50, 260, 18, txt, TXT + "fontSize=10;fontColor=%s;" % GRIS)
            fx += 48 + 10 + 7 * len(txt) + 30
        s.h = y + 90
