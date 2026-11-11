"""E1 por DESTINO (lectura literal del criterio E1 de OBJETIVOS-Y-CRITERIOS.md, fila E1):
«señal atribuible (paquetes del origen al destino del episodio dentro de la ventana y de [inicio, fin]) de la regla prevista, con t_det + eps < t_fin_eval».
El criterio habla de destino, no de puerto. El lector historico de analizar_b3.py filtraba ademas por puerto (80, 18081, 53) y para escaneos no tenia puerto -> indeterminado de herramienta.
Este modulo NO modifica analizar_b.py ni analizar_b3.py; es un lector aparte, solo offline.
Diferencia deliberada con el lector historico: sin paquetes dentro, devuelve indeterminado (el historico devolvia el resultado de la senal)."""
import bisect


def e1_por_destino(ts_origen_destino, t_inicio, t_fin, ev_ini, ev_fin, resultado_senal):
    """ts_origen_destino: instantes (epoch) de TODOS los paquetes origen->destino, ordenados. ev_*: ventana de evidencia (epoch, absolutos).
    Devuelve dict con paquetes dentro de [max(t_inicio, ev_ini), min(t_fin, ev_fin)], paquetes previos al inicio dentro de la ventana, y el resultado."""
    a, b = max(t_inicio, ev_ini), min(t_fin, ev_fin)
    dentro = (bisect.bisect_right(ts_origen_destino, b) - bisect.bisect_left(ts_origen_destino, a)) if a <= b else 0
    previos = (bisect.bisect_left(ts_origen_destino, t_inicio) - bisect.bisect_left(ts_origen_destino, ev_ini)) if ev_ini < t_inicio else 0
    if resultado_senal == "fallido":
        res = "fallido"
    elif resultado_senal == "verificado" and dentro > 0:
        res = "verificado"
    else:
        res = "indeterminado"
    return {"paquetes_en_ventana_y_episodio": dentro, "paquetes_previos_al_inicio_en_ventana": previos, "resultado": res}
