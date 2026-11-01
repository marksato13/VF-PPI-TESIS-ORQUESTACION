#!/usr/bin/env python3
"""Comprobaciones de presupuesto_e2e.py (solo lectura). Uso: python -I pruebas/test_presupuesto_e2e.py

La más importante valida el simulador contra la realidad: el publicador SÍ corrió en sombra durante el 3B y dejó
su feed y su estado de escalada finales. El simulador, con el mismo código desplegado y el mismo registro, debe
producir el mismo feed (IPs, acciones, caducidades) y el mismo estado del origen.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI / "herramientas"))
import presupuesto_e2e as p  # noqa: E402

CAMP = AQUI.parent
EV = CAMP / "ejecucion-3b-2026-11-01" / "evidencia" / "sensor" / "copias"
FALLOS: list[str] = []


def ok(cond: bool, txt: str) -> None:
    print(("OK   " if cond else "FALLO") + "  " + txt)
    if not cond:
        FALLOS.append(txt)


def main() -> int:
    verdicto, sev, nunca = p.extraer_publicador(AQUI / "codigo-desplegado" / "publicar_feed.py")
    esc = p.cargar_escalada(AQUI / "codigo-desplegado" / "escalada.py")
    ok(nunca == {"10.10.10.30", "10.10.60.11", "10.10.30.1", "10.10.40.1", "10.10.60.1", "10.10.20.1",
                 "10.10.10.20"}, "NUNCA_BLOQUEAR extraído del publicador desplegado (7 IPs, DNS incluido)")
    ok(p.sha(AQUI / "codigo-desplegado" / "publicar_feed.py").startswith("f7bc4c7d"), "publicador = f7bc4c7d")
    ok(p.sha(AQUI / "codigo-desplegado" / "escalada.py").startswith("7d80ab4a"), "escalada = 7d80ab4a")
    ok(p.sha(AQUI / "codigo-desplegado" / "agente_enforce.py").startswith("2985c123"), "agente = 2985c123")

    dec = []
    with gzip.open(EV / "motor_decision.log.gz", "rt", encoding="utf-8") as fh:
        for l in fh:
            if '"event": "decision"' in l:
                dec.append(json.loads(l))
    dec.sort(key=lambda d: float(d["logged_at"]))

    # 1. Con umbral None, verdicto_alfa es exactamente el desplegado
    ok(all(p.verdicto_alfa(d, None, verdicto, sev) == verdicto(d) for d in dec[:20000]),
       "verdicto_alfa(umbral=None) == _verdicto_de desplegado (20 000 decisiones)")
    # 2. Con el umbral desplegado, la parte del modelo reproduce decision==ALERT del motor
    umbral = dec[0]["threshold"]
    difer = sum(1 for d in dec if (p.verdicto_alfa(d, umbral, verdicto, sev) or ("",))[0]
                != (verdicto(d) or ("",))[0])
    ok(difer == 0, "umbral desplegado: misma acción que el código desplegado en las %d decisiones (difieren %d)"
       % (len(dec), difer))

    # 3. Validación contra la realidad: feed y estado finales del publicador en sombra
    feed = json.loads((EV / "feed.json").read_text(encoding="utf-8"))
    estado_real = json.loads((EV / "estado.json").read_text(encoding="utf-8"))
    T_final = (feed["generado"] // 10) * 10
    cad = p.Cadena(esc, verdicto, sev, nunca)
    entradas_sim = {}
    orig_tick = cad.tick

    def tick_capturando(T, decs):
        if abs(T - T_final) < 1e-6:
            ahora = T + p.P["pub_inicio_offset_s"]
            por_ip = {}
            for d in decs:
                la = float(d["logged_at"])
                if la > ahora:
                    break
                if la < ahora - 120 or d["entity_ip"] in nunca:
                    continue
                v = verdicto(d)
                if v and (d["entity_ip"] not in por_ip or sev[v[0]] > sev[por_ip[d["entity_ip"]]]):
                    por_ip[d["entity_ip"]] = v[0]
            entradas_sim.update(por_ip)
        orig_tick(T, decs)

    cad.tick = tick_capturando
    p.correr(cad, dec, float(dec[0]["logged_at"]), T_final)
    reales = {e["ip"]: e["accion"] for e in feed["entradas"]}
    ok(entradas_sim == reales, "feed final simulado == feed real (%s)" % sorted(reales))
    ok(all(abs(e["hasta"] - (T_final + p.P["pub_inicio_offset_s"] + 300)) <= 1 for e in feed["entradas"]),
       "caducidad real = tick + 0,29 + 300 s (fase medida del publicador)")
    kali_sim, kali_real = cad.estado.get(p.ORIGEN, {}), estado_real.get(p.ORIGEN, {})
    ok(kali_sim.get("bloqueos") == kali_real.get("bloqueos") == 3, "nivel de escalada del origen: 3 (sim y real)")
    ok(abs(kali_sim.get("ultimo_evento_block", 0) - kali_real.get("ultimo_evento_block", 1)) < 1e-3,
       "último evento BLOCK del origen idéntico (sim %.3f / real %.3f)"
       % (kali_sim.get("ultimo_evento_block", 0), kali_real.get("ultimo_evento_block", 0)))

    # 4. Reglas del tick y de la clasificación
    ok(p.tick_publicador(100.10) == (100.0, 100.0), "t_det antes de :x0,29 -> ese tick (inf y sup)")
    ok(p.tick_publicador(100.50) == (100.0, 110.0), "t_det entre :x0,29 y :x1,06 -> tick ambiguo (inf/sup)")
    ok(p.tick_publicador(101.50) == (110.0, 110.0), "t_det después de la ejecución -> tick siguiente")
    ok(p.clasificar(50, 40, 45) == "antes_del_fin" and p.clasificar(50, 48, 52) == "indeterminado"
       and p.clasificar(50, 51, 53) == "despues_del_fin", "clasificación antes / indeterminado / después")

    # 5. Resultado publicado coherente
    r = json.loads((AQUI / "resultados" / "presupuesto-e2e.json").read_text(encoding="utf-8"))
    ok(len(r["episodios"]) == 25 and sum(e["en_poblacion_principal_v2"] for e in r["episodios"]) == 15,
       "25 episodios, 15 en la población v2")
    breves = [e for e in r["episodios"] if e["escenario"] == "escaneo_breve"]
    ok(all(e["primera_cualquiera"]["V0"]["clase"] == "despues_del_fin" for e in breves),
       "escaneo breve: 0/5 aplicaciones antes del fin con la cadena actual")
    ok(all(e["t_apl_real"].startswith("no aplica") for e in r["episodios"]), "t_apl real = no aplica en sombra")
    print("\n%d fallos" % len(FALLOS))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
