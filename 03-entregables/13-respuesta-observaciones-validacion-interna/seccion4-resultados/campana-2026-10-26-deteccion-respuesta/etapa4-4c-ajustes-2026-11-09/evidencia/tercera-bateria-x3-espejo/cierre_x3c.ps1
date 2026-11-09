$e="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e10"
$g="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\inst4b\guiones"
$bash="C:\Program Files\Git\bin\bash.exe"
"##### b20 (primer paso) " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
$o = & $bash --noprofile --norc "$e\b20_rep.sh" 2>&1
$o | Set-Content "$e\b20_x3c_1.out"
$o | Select-String -Pattern "rc=|AVISO|marcas:|fin_ultimo|vigía terminado|campana_fin" | ForEach-Object { $_.Line.Substring(0,[Math]::Min(300,$_.Line.Length)) }
$fu = ($o | Select-String -Pattern "fin_ultimo=([0-9.]+)" | Select-Object -Last 1).Matches.Groups[1].Value
"fin_ultimo = $fu"
$ep = [double]$fu
$t = [DateTimeOffset]::FromUnixTimeSeconds([long]$ep + 306).UtcDateTime
"esperar hasta " + $t.ToString("HH:mm:ss") + "Z (fin_ultimo + 306 s)"
$s=[int](($t-[datetime]::UtcNow).TotalSeconds); if($s -gt 0){ Start-Sleep -Seconds ([Math]::Min($s, 540)) }
$s=[int](($t-[datetime]::UtcNow).TotalSeconds); if($s -gt 0){ Start-Sleep -Seconds $s }
"##### b20 (repetido) " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
$o2 = & $bash --noprofile --norc "$e\b20_rep.sh" 2>&1
$o2 | Set-Content "$e\b20_x3c_2.out"
$o2 | Select-String -Pattern "rc=|AVISO|traza|marcas:" | ForEach-Object { $_.Line.Substring(0,[Math]::Min(300,$_.Line.Length)) }
Set-Location $g
"##### s20 " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
$o3 = & $bash r4.sh s20_verificar_cierre_e4.sh sensor 4c ([long]$ep) 2>&1
$o3 | Set-Content "$e\s20_x3c.out"
$o3 | Select-Object -Last 8 | ForEach-Object { $_.Substring(0,[Math]::Min(230,$_.Length)) }
"FIN_UNIX=$ep"
