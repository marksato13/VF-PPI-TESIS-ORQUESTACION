param([string]$script)
# Ejecuta un script bash local en Sensor1 (via bastion) y devuelve la salida
function b64($t) { [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($t -replace "`r", ""))) }
$sen = b64 (Get-Content -Raw $script)
$bas = "ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 `"timeout 500 bash -c 'echo $sen|base64 -d|bash'`" 2>&1"
ssh -o BatchMode=yes -o ConnectTimeout=15 gadmin@10.10.10.30 "echo $(b64 $bas)|base64 -d|timeout 520 bash" 2>&1
