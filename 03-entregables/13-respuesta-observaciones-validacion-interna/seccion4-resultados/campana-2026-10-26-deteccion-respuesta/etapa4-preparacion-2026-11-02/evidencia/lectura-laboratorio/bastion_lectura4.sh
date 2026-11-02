#!/usr/bin/env bash
# Cuarta tanda (sin sudo): curva horaria de los perfiles y DC1 en 10.10.10.20.
set +e
echo "== cliente: ficheros del laboratorio"
ssh -o BatchMode=yes admin 'cd ~/laboratorio && ls -la && sha256sum *.py 2>/dev/null; grep -nE "hora|curva|laborable|forzar|tasa|intensidad|factor|UTC|zona|tz|weekday|isoweekday|PERFILES|def " clientes_lab.py | head -80'
echo "== cliente: config (lineas relevantes)"
ssh -o BatchMode=yes admin 'cd ~/laboratorio && for f in clientes_config.py config*.json perfiles*.json; do [ -f "$f" ] && { echo "# $f"; grep -nE "hora|curva|laborable|tasa|factor|intens|pausa|media|perfil" "$f" | head -60; }; done; echo fin'
echo "== DC1 10.10.10.20"
for d in dcadmin@10.10.10.20; do ssh -o BatchMode=yes -o ConnectTimeout=5 "$d" 'hostname; date -u +%FT%TZ; systemctl list-units --all --no-legend --plain "ppi-*" | cat; ls /etc/cyberflow /opt/cyberflow 2>&1 | head -3' 2>&1 | head -8; done
