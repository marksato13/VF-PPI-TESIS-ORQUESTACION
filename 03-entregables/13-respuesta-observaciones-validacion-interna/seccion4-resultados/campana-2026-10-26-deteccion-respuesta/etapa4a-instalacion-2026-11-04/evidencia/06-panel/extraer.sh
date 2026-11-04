set -eu
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-panel-v2"
ST="/c/Users/markp/AppData/Local/Temp/claude/f17b3819211dc686/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad/panel/stage-e0dc71d"
mkdir -p "$ST"
cd "$R"
git cat-file blob e0dc71d:scripts/engine/dashboard.py > "$ST/dashboard.py"
git cat-file blob e0dc71d:scripts/engine/cadena_v2.py > "$ST/cadena_v2.py"
cd "$ST" && sha256sum dashboard.py cadena_v2.py | tee SHA256SUMS
scp -q -i ~/.ssh/id_ed25519 -o BatchMode=yes dashboard.py cadena_v2.py SHA256SUMS gadmin@10.10.10.30:cf-stage/ && echo "en el bastion"
ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes gadmin@10.10.10.30 'cd cf-stage && sha256sum -c SHA256SUMS && ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "mkdir -p ~/cf-e4/panel-e0dc71d" && scp -q -i ~/.ssh/cyberflow-to-sensor dashboard.py cadena_v2.py SHA256SUMS m4rk@10.10.60.11:cf-e4/panel-e0dc71d/ && ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "cd ~/cf-e4/panel-e0dc71d && sha256sum -c SHA256SUMS"'
