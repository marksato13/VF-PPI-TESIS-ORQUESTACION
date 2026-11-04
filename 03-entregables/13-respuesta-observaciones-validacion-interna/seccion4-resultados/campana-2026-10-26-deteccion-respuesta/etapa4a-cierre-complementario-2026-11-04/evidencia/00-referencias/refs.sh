set -u
C="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW"
for d in orquestacion-limpio producto-recuperacion producto-panel-v2; do
  cd "$C/$d"; echo "===== $d"; git remote -v | head -2; git branch --show-current; git fetch -q origin 2>&1 | tail -2
  git log --oneline -1 HEAD; git status --short | grep -v '^??' | head -5
done
cd "$C/orquestacion-limpio"; echo "== docs origin/main:"; git log --oneline -3 origin/main
cd "$C/producto-recuperacion"
for b in recuperacion/etapa4a-instalacion-20261104 panel/cadena-v2-20261104 main recuperacion/etapa4a-20261103; do echo "== $b: $(git log --oneline -1 origin/$b)"; done
git branch -r --sort=-committerdate | head -8
git cat-file -t ec78ca5
