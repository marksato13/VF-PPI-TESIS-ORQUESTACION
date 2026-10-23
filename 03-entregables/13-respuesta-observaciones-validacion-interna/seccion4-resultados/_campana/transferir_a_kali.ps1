# Transfiere orquestar_campana.sh a la Kali (10.10.20.30) via el bastion, por el mismo
# patron de relay doble-base64. Lo ejecutas TU desde tu terminal (usa tus claves ssh).
# Deja el script en /tmp/orquestar_campana.sh con permiso de ejecucion.
#
# Uso:  pwsh transferir_a_kali.ps1
#   (opcional) -Script "ruta\orquestar_campana.sh"
param(
  [string]$Script = "$PSScriptRoot\orquestar_campana.sh"
)
if (-not (Test-Path -LiteralPath $Script)) { Write-Error "No existe: $Script"; exit 1 }
$bytes = [IO.File]::ReadAllBytes($Script)
$b64   = [Convert]::ToBase64String($bytes)
$inner = "echo $b64 | base64 -d > /tmp/orquestar_campana.sh && chmod +x /tmp/orquestar_campana.sh && wc -l /tmp/orquestar_campana.sh"
$b1    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($inner))
$kali  = "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 `"echo $b1|base64 -d|bash`""
$b2    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($kali))
Write-Host "Transfiriendo a la Kali via bastion..."
ssh gadmin@10.10.10.30 "echo $b2|base64 -d|bash"
Write-Host "`nListo. Para lanzar la campana:"
Write-Host 'ssh -t gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 ''N=3 NB=1 bash /tmp/orquestar_campana.sh''"'
