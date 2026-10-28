# Sube ficheros locales al sensor (~/cf-prep-20261028/herramientas/) via el bastion, con scp (bytes exactos).
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Ficheros)
$k = "$env:USERPROFILE\.ssh\id_ed25519"; $B = "gadmin@10.10.10.30"
ssh -o BatchMode=yes -i $k $B "mkdir -p ~/cf-prep-subida"
foreach ($f in $Ficheros) { scp -q -o BatchMode=yes -i $k $f "${B}:cf-prep-subida/" }
$n = ($Ficheros | ForEach-Object { Split-Path -Leaf $_ }) -join " "
ssh -o BatchMode=yes -i $k $B "cd ~/cf-prep-subida && ssh -n -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'mkdir -p ~/cf-prep-20261028/herramientas' && scp -q -i ~/.ssh/cyberflow-to-sensor $n m4rk@10.10.60.11:cf-prep-20261028/herramientas/ && ssh -n -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd ~/cf-prep-20261028/herramientas && sha256sum $n'"
