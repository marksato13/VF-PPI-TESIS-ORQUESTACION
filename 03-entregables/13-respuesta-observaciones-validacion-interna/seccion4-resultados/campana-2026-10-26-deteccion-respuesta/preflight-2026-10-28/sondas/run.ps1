# Ejecuta un script local en un host del laboratorio saltando por el bastion; guarda la salida en out_<nombre>.txt
param([string]$Script, [string]$Destino = "bastion")
$s = Split-Path -Parent $MyInvocation.MyCommand.Path
$hosts = @{
  "bastion"  = ""
  "sensor"   = "~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
  "srv"      = "~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"
  "kali"     = "~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
  "clientes" = "~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
}
$h = $hosts[$Destino]
if ($h -eq "") { $remoto = "tr -d '\r' | bash -s" }
else { $k, $u = $h -split " "; $remoto = "tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i $k $u 'bash -s'" }
$nombre = [IO.Path]::GetFileNameWithoutExtension($Script)
Get-Content -Raw (Join-Path $s $Script) |
  ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$env:USERPROFILE\.ssh\id_ed25519" gadmin@10.10.10.30 $remoto 2>&1 |
  Tee-Object (Join-Path $s "out_$nombre.txt")
