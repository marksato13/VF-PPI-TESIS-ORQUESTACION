# Sube ficheros locales (normalizados a LF) a un host del laboratorio via el bastion: subir.ps1 <alias> <dir_remoto> <ficheros...>
param([string]$Alias, [string]$Dir, [Parameter(ValueFromRemainingArguments=$true)][string[]]$Ficheros)
$s = Split-Path -Parent $MyInvocation.MyCommand.Path
$tmp = Join-Path $s "_lf"; New-Item -ItemType Directory -Force $tmp | Out-Null
$nombres = @()
foreach ($f in $Ficheros) {
  $src = if ([IO.Path]::IsPathRooted($f)) { $f } else { Join-Path $s $f }
  $n = Split-Path -Leaf $src; $nombres += $n
  $b = [IO.File]::ReadAllBytes($src); $t = [Text.Encoding]::UTF8.GetString($b) -replace "`r`n", "`n"
  [IO.File]::WriteAllBytes((Join-Path $tmp $n), [Text.Encoding]::UTF8.GetBytes($t))
}
$B = "gadmin@10.10.10.30"
ssh -o BatchMode=yes $B "mkdir -p ~/cf-stage/paso2/$Alias"
scp -q -o BatchMode=yes ($nombres | ForEach-Object { Join-Path $tmp $_ }) "${B}:cf-stage/paso2/$Alias/"
$n = $nombres -join " "
ssh -o BatchMode=yes $B "cd ~/cf-stage/paso2/$Alias && ssh -n $Alias 'mkdir -p $Dir' && scp -q $n ${Alias}:$Dir/ && ssh -n $Alias 'cd $Dir && sha256sum $n'"
