$e="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e10"
$g="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\inst4b\guiones"
$b="C:\Program Files\Git\bin\bash.exe"
Set-Location $g
"##### hora " + [datetime]::UtcNow.ToString("HH:mm:ss") + "Z"
$s = & $b r4.sh i1_i8_sensor_4c_rep.sh sensor 2>&1
$s | Select-String -Pattern "ventana|\[anillo\]|\[via\]|I5=|rc_i5|FALLO|PID y|ciclos|vía rápida|libres|archivador:|active NR" | ForEach-Object {$_.Line}
$ok = ($s -join "`n")
$c0 = ([regex]::Matches($ok, "clase=C0")).Count
"##### BASTION I8"; $i = & $b r4.sh i8_bastion.sh bastion 2>&1; $i | Select-Object -Last 6
"##### SRV-DMZ sudo"; $d = & $b r4.sh i8_srvdmz_sudo.sh bastion 2>&1; $d | Select-Object -Last 4
"##### vigilancia del control"; & $b r4.sh vigilancia_control2.sh bastion 2>&1 | Select-Object -First 6
$bien = ($c0 -eq 2) -and ($ok -match "rc_i5=0") -and ($ok -match "PID y NRestarts iguales") -and (($i -join "`n") -match "VERIFICACIÓN BASTIÓN OK") -and (($i -join "`n") -match "VERIFICACIÓN SENSOR1 OK") -and (($d -join "`n") -match "VERIFICACIÓN SRV-DMZ OK") -and ($ok -notmatch "FALLO ")
"RESULTADO_FINALES=" + $(if($bien){"CONFORME"}else{"NO CONFORME"})
