set -eu
P="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-panel-v2"
S="/c/Users/markp/AppData/Local/Temp/claude/f17b3819211dc686/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad/cc"
B="$S/base-a27889d"
if [ ! -d "$B" ]; then mkdir -p "$B"; (cd "$P" && git archive a27889d) | tar x -C "$B"; fi
MSYS_NO_PATHCONV=1 docker run --rm -e PYTHONDONTWRITEBYTECODE=1 -v "$(cygpath -w "$P"):/rama:ro" -v "$(cygpath -w "$B"):/base" -v "$(cygpath -w "$S"):/s:ro" debian:trixie-slim bash /s/docker_panel.sh
