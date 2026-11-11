#!/usr/bin/env python3
"""Series por bloques de 1 s de los INTENTOS del generador (registro de `inundacion_instrumentada.sh`) y su continuidad tras `t_apl`. Solo biblioteca estándar.
Separa tres cosas: `intentos` (todas las iteraciones, por su t_inicio), `con_respuesta` (el servidor respondió: codigo_http != 000) y `sin_respuesta` (000).
Continuidad por la vía «salida» (regla en CRITERIO-E3-SPAN-O-SALIDA.md): existe una racha de K bloques consecutivos tras t_apl con intentos >= FRAC · B0_intentos,
con B0_intentos = media de los N_BASE bloques anteriores a t_apl. Mismas constantes que analizar_b (K=5 en LIMIT, N_BASE=10, FRAC=0,5)."""
import collections
import json
import math
import sys

K_LIMIT, N_BASE, FRAC = 5, 10, 0.5


def leer(ruta):
    out = []
    for l in open(ruta, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        p = l.rstrip("\n").split("\t")
        if len(p) < 6:
            continue
        out.append({"t0": float(p[0]), "t1": float(p[1]), "codigo": p[2], "tcon": p[3], "rc": int(p[4]), "lazo": p[5]})
    return out


def series(filas):
    s = collections.defaultdict(lambda: {"intentos": 0, "con_respuesta": 0, "sin_respuesta": 0})
    for f in filas:
        b = s[int(math.floor(f["t0"]))]
        b["intentos"] += 1
        b["con_respuesta" if f["codigo"] != "000" else "sin_respuesta"] += 1
    return {t: dict(v) for t, v in s.items()}


def continuidad_salida(ser, t_apl, t_fin, k=K_LIMIT):
    """Los bloques ausentes cuentan como 0 intentos (el registro es continuo y local: sin huecos de captura)."""
    previos = [ser.get(t, {"intentos": 0})["intentos"] for t in range(int(math.floor(t_apl)) - N_BASE, int(math.floor(t_apl)))]
    b0 = sum(previos) / N_BASE
    umbral = FRAC * b0
    bloques = list(range(int(math.ceil(t_apl)), int(math.floor(t_fin))))
    racha = mejor = 0
    t_ini_racha = mejor_ini = None
    for t in bloques:
        if ser.get(t, {"intentos": 0})["intentos"] >= umbral and b0 > 0:
            racha += 1
            t_ini_racha = t if racha == 1 else t_ini_racha
            if racha > mejor:
                mejor, mejor_ini = racha, t_ini_racha
        else:
            racha = 0
    post = [ser.get(t, {"intentos": 0})["intentos"] for t in bloques]
    return {"b0_intentos_por_s": round(b0, 2), "umbral_por_s": round(umbral, 2), "bloques_evaluados": len(bloques), "mejor_racha": mejor, "k_exigido": k,
            "cumple": bool(b0 > 0 and mejor >= k), "intentos_posterior_media_por_s": round(sum(post) / max(1, len(post)), 2)}


def resumen(ruta, t_apl, t_fin):
    filas = leer(ruta)
    ser = series(filas)
    cs = continuidad_salida(ser, t_apl, t_fin)
    pre = [ser.get(t, {"con_respuesta": 0})["con_respuesta"] for t in range(int(math.floor(t_apl)) - N_BASE, int(math.floor(t_apl)))]
    pos = [ser.get(t, {"con_respuesta": 0})["con_respuesta"] for t in range(int(math.ceil(t_apl)), int(math.floor(t_fin)))]
    return {"iteraciones": len(filas), "con_respuesta": sum(1 for f in filas if f["codigo"] != "000"), "sin_respuesta": sum(1 for f in filas if f["codigo"] == "000"),
            "continuidad_salida": cs, "con_respuesta_por_s": {"previo": round(sum(pre) / N_BASE, 2), "posterior": round(sum(pos) / max(1, len(pos)), 2)},
            "serie": [{"t": t, **ser[t]} for t in sorted(ser)]}


if __name__ == "__main__":
    print(json.dumps(resumen(sys.argv[1], float(sys.argv[2]), float(sys.argv[3])), indent=1))
