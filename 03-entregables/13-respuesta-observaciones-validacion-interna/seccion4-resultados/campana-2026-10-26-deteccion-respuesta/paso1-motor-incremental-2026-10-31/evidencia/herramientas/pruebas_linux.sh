#!/bin/bash
# Suite completa (unittest) en el sensor para referencia (7b275b8) y candidato. Solo lee ~/cyberflow.
cd ~/cf-p1 || exit 1
for d in referencia candidato; do
  echo "== $d"
  (cd "$d" && nice -n 15 ~/cyberflow/.venv/bin/python -m unittest discover -s tests 2>&1 | grep -E "^(Ran|OK|FAILED|FAIL:|ERROR:)" | tail -15)
done
