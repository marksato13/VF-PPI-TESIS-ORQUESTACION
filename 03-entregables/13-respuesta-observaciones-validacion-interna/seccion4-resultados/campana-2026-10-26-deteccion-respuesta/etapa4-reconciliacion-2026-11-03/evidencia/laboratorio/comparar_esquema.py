"""Compara multilayer-v2.json del sensor con el de cada commit (semantico)."""
import json
import subprocess
import sys

REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-etapa3"
lab = json.loads(open(sys.argv[1], encoding="utf-8-sig").read())


def norm(d):
    feats = d.get("features") if isinstance(d, dict) else d
    return [(f["order"], f["name"], f.get("layer"), f.get("window_seconds"), f.get("unit"), f.get("source")) for f in feats]


L = norm(lab)
print("sensor:", len(L), "caracteristicas; claves raiz:", list(lab.keys()) if isinstance(lab, dict) else "lista")
for c in ["7b275b8", "24f8a80", "6b6ef82", "ec78ca5", "3a9f26b", "f57ca00", "ca66db5"]:
    r = subprocess.run(["git", "-C", REPO, "show", f"{c}:configs/features/multilayer-v2.json"], capture_output=True)
    if r.returncode:
        print(c, "sin fichero")
        continue
    d = json.loads(r.stdout.decode("utf-8-sig"))
    C = norm(d)
    extra = {k: v for k, v in d.items() if k != "features"} if isinstance(d, dict) else {}
    extra_lab = {k: v for k, v in lab.items() if k != "features"} if isinstance(lab, dict) else {}
    print(c, "| features iguales (orden,nombre,capa,ventana,unidad,fuente):", C == L,
          "| metadatos iguales:", extra == extra_lab)
    if C != L:
        for a, b in zip(L, C):
            if a != b:
                print("   sensor", a, "\n   commit", b)
    if extra != extra_lab:
        for k in sorted(set(extra) | set(extra_lab)):
            if extra.get(k) != extra_lab.get(k):
                print("   meta", k, "| sensor:", json.dumps(extra_lab.get(k), ensure_ascii=False)[:160],
                      "| commit:", json.dumps(extra.get(k), ensure_ascii=False)[:160])
print("orden sensor:", [n for _, n, *_ in L])
