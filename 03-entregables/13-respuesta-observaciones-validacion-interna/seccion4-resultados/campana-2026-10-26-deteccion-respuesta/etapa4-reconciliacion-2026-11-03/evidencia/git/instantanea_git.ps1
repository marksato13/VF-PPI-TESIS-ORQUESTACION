$ErrorActionPreference = 'Continue'
$base = 'C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW'
$out = 'C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\recon\instantanea-git.txt'
$L = New-Object System.Collections.Generic.List[string]
function A($s) { $L.Add([string]$s) }
A ("# Instantanea git " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
foreach ($repo in @("$base\producto-as-deployed", "$base\orquestacion-limpio", "$base\orquestacion")) {
  if (-not (Test-Path "$repo\.git")) { A "## $repo : sin .git"; continue }
  Push-Location $repo
  A "`n## REPO $repo"
  A ("remote: " + ((git remote get-url origin) 2>&1))
  git fetch --all --tags --quiet 2>&1 | Out-Null
  A "### ramas remotas"
  git branch -r --format='%(refname:short) %(objectname:short) %(committerdate:iso)' | % { A $_ }
  A "### etiquetas"
  git tag --format='%(refname:short) %(objectname:short) %(*objectname:short)' | % { A $_ }
  A "### worktrees"
  $wts = git worktree list --porcelain
  $wts | % { A $_ }
  $rutas = ($wts | Where-Object { $_ -like 'worktree *' }) | % { $_.Substring(9) }
  foreach ($w in $rutas) {
    if (-not (Test-Path $w)) { A "#### $w : NO EXISTE en disco"; continue }
    Push-Location $w
    A "#### WT $w"
    A ("rama: " + (git branch --show-current) + " | HEAD: " + (git rev-parse HEAD))
    A ("upstream: " + ((git rev-parse --abbrev-ref '@{u}') 2>&1))
    A "cambios (status --short, sin ignorados):"
    git status --short | % { A ("  " + $_) }
    A "stash:"
    git stash list | % { A ("  " + $_) }
    Pop-Location
  }
  Pop-Location
}
$L | Set-Content -Encoding utf8 $out
"escrito $out ($($L.Count) lineas)"
