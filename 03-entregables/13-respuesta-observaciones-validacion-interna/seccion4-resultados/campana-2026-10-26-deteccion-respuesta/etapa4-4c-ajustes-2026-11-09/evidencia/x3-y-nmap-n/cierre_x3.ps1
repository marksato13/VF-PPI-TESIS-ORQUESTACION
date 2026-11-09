$e="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e10"
$g="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\inst4b\guiones"
$bash="C:\Program Files\Git\bin\bash.exe"
$t=[datetime]::Parse("2026-11-09T12:55:35Z").ToUniversalTime(); $s=[int](($t-[datetime]::UtcNow).TotalSeconds); if($s -gt 0){Start-Sleep -Seconds $s}
"##### b20 repetido " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
& $bash --noprofile --norc "$e\b20_rep.sh" 2>&1 | Tee-Object "$e\b20_rep2.out" | Select-String -Pattern "AVISO|rc=|marcas:|copia|relé|fin_ultimo" | ForEach-Object { $_.Line.Substring(0,[Math]::Min(250,$_.Line.Length)) }
Set-Location $g
"##### s20 " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
& $bash r4.sh s20_verificar_cierre_e4.sh sensor 4c 1794228594 2>&1 | Tee-Object "$e\s20_x3.out" | Select-Object -Last 25 | ForEach-Object { $_.Substring(0,[Math]::Min(230,$_.Length)) }
