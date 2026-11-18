param([string]$Hop, [string]$Script, [int]$T = 70)
$sc = "C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad"
$k = "$env:USERPROFILE\.ssh\id_ed25519"
$sb = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(([IO.File]::ReadAllText("$sc\$Script") -replace "`r", "")))
$sens = "ssh -n -i ~/.ssh/cyberflow-to-sensor -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/home/gadmin/.ssh/known_hosts_d5 -o GlobalKnownHostsFile=/dev/null m4rk@10.10.60.11"
$h = switch ($Hop) { 'local' { '' } 'sensor' { $sens } default { "ssh -n -o BatchMode=yes -o ConnectTimeout=8 $Hop" } }
if ($Hop -eq 'local') { $c = "bash -c " + '"$(echo ' + $sb + ' | base64 -d)"' } else { $c = "timeout $T $h 'bash -c " + '"$(echo ' + $sb + ' | base64 -d)"' + "'" }
ssh -i $k -o BatchMode=yes -o ConnectTimeout=10 gadmin@10.10.10.30 $c 2>&1
