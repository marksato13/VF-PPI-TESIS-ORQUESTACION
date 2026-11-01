"""Comprobación reproducible del contrato de características del IF (solo lectura).

Compara, nombre a nombre y en orden:
  - el esquema que usa el motor (multilayer-v2.json, ordenado por "order");
  - la lista ``features`` del manifiesto del modelo desplegado;
  - ``FEATURE_NAMES`` del extractor (leído con ``ast``, sin importarlo);
  - el esquema ampliado (multilayer-v3.json).

Cuenta por capa y por procedencia (pcap / eve). Las columnas de ``METADATA_COLUMNS`` del extractor
(contadores auxiliares como ``dns_query_count_60s``) NO son entradas del modelo y se listan aparte.

Uso:
  python -I -B herramientas/contrato_caracteristicas.py --esquema contrato/multilayer-v2.json \
      --ampliado contrato/multilayer-v3.json --manifiesto contrato/manifest-if-limpio-2026-10.json \
      --extractor contrato/extract_multilayer_v2.py --salida resultados/contrato-caracteristicas.json
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

ESPERADO = {"L3": 9, "L4": 8, "L7": 11}
L2_AMPLIADO = ("arp_request_rate_10s", "unique_src_mac_30s", "mac_ip_binding_changes_60s")


def nombres_extractor(src: str) -> dict[str, tuple[str, ...]]:
    """Evalúa las tuplas literales de nombres del extractor sin ejecutar el módulo."""
    arbol = ast.parse(src)
    tuplas: dict[str, tuple[str, ...]] = {}
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name):
            nombre = nodo.targets[0].id
            v = nodo.value
            if isinstance(v, ast.Tuple):
                tuplas[nombre] = tuple(ast.literal_eval(v))
            elif isinstance(v, ast.BinOp) and isinstance(v.op, ast.Add) and \
                    isinstance(v.left, ast.Name) and isinstance(v.right, ast.Name):
                tuplas[nombre] = tuplas[v.left.id] + tuplas[v.right.id]
    return tuplas


def ordenadas(esquema: dict) -> list[dict]:
    return sorted(esquema["features"], key=lambda f: f["order"])


def comprobar(esquema: dict, ampliado: dict, manifiesto: dict, extractor_src: str) -> dict:
    v2 = ordenadas(esquema)
    v3 = ordenadas(ampliado)
    n2 = [f["name"] for f in v2]
    det = next(iter(manifiesto["detectors"].values()))
    ext = nombres_extractor(extractor_src)
    por_capa = Counter(f["layer"] for f in v2)
    por_fuente = Counter(f["source"] for f in v2)
    capa_fuente = Counter((f["layer"], f["source"]) for f in v2)
    extra = [f for f in v3 if f["name"] not in set(n2)]
    meta = list(ext.get("METADATA_COLUMNS", ()))
    checks = {
        "esquema_28": len(n2) == 28,
        "orden_contiguo_1_28": [f["order"] for f in v2] == list(range(1, 29)),
        "nombres_unicos": len(set(n2)) == len(n2),
        "manifiesto_igual_al_esquema_en_orden": list(det["features"]) == n2,
        "manifiesto_n_features_28": det.get("n_features") == 28,
        "manifiesto_schema_v2": det.get("schema") == "multilayer-v2.json",
        "extractor_igual_al_esquema_en_orden": list(ext.get("FEATURE_NAMES", ())) == n2,
        "capas_L3_9_L4_8_L7_11": dict(por_capa) == ESPERADO,
        "L7_todas_eve_y_resto_pcap": all((f["layer"] == "L7") == (f["source"] == "eve") for f in v2),
        "ampliado_31": len(v3) == 31,
        "ampliado_conserva_las_28_en_orden": [f["name"] for f in v3[:28]] == n2,
        "ampliado_anade_3_L2_pcap": [f["name"] for f in extra] == list(L2_AMPLIADO)
                                     and all(f["layer"] == "L2" and f["source"] == "pcap" for f in extra),
        "metadatos_no_son_caracteristicas": not (set(meta) & set(n2)),
    }
    return {
        "herramienta": "contrato_caracteristicas.py", "solo_lectura": True,
        "modelo": {"detector": next(iter(manifiesto["detectors"])), "model_sha256": det.get("model_sha256"),
                   "schema": det.get("schema"), "n_features": det.get("n_features")},
        "por_capa": dict(sorted(por_capa.items())), "por_fuente": dict(sorted(por_fuente.items())),
        "por_capa_y_fuente": {"%s/%s" % k: v for k, v in sorted(capa_fuente.items())},
        "caracteristicas": [{"orden": f["order"], "nombre": f["name"], "capa": f["layer"], "fuente": f["source"]}
                            for f in v2],
        "ampliado_solo": [{"orden": f["order"], "nombre": f["name"], "capa": f["layer"], "fuente": f["source"]}
                          for f in extra],
        "metadatos_del_extractor_no_entradas": meta,
        "comprobaciones": checks, "todo_ok": all(checks.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for n in ("esquema", "ampliado", "manifiesto", "extractor", "salida"):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    r = comprobar(json.loads(a.esquema.read_text(encoding="utf-8")),
                  json.loads(a.ampliado.read_text(encoding="utf-8")),
                  json.loads(a.manifiesto.read_text(encoding="utf-8")),
                  a.extractor.read_text(encoding="utf-8"))
    a.salida.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("por capa:", r["por_capa"], "| por fuente:", r["por_fuente"], "| ampliado añade:",
          [x["nombre"] for x in r["ampliado_solo"]])
    for k, v in r["comprobaciones"].items():
        print("OK  " if v else "FALLO", k)
    return 0 if r["todo_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
