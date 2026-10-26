echo "== ficheros con marcas 2026-10-05T20:3 (excluye piloto)"
find ~ /var/log -xdev -type f \( -name '*.jsonl' -o -name '*.log' -o -name '*.json' -o -name '*.csv' \) 2>/dev/null | grep -v '/piloto/' | grep -v '/.venv/' | while read f; do
  n=$(grep -c '2026-10-05T20:3' "$f" 2>/dev/null); [ "${n:-0}" -gt 0 ] && echo "$n $f $(stat -c '%y' "$f" | cut -c1-19)"
done
find ~ /var/log -xdev -type f -name '*.gz' 2>/dev/null | grep -v '/piloto/' | head -300 | while read f; do
  n=$(zgrep -c '2026-10-05T20:3' "$f" 2>/dev/null); [ "${n:-0}" -gt 0 ] && echo "GZ $n $f"
done
echo "== motor"; systemctl cat ppi-motor 2>/dev/null | grep -E 'ExecStart' | head -3
