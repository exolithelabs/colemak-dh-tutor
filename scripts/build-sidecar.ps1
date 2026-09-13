$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$binaryDir = Join-Path $repoRoot 'src-tauri\binaries'
$targetTriple = (rustc --print host-tuple).Trim()

if (-not $targetTriple) {
    throw 'Unable to determine the Rust host target triple.'
}

Push-Location $backendDir
try {
    python -m PyInstaller --clean --noconfirm colemak-backend.spec
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Path $binaryDir -Force | Out-Null
$source = Join-Path $backendDir 'dist\colemak-backend.exe'
$destination = Join-Path $binaryDir "colemak-backend-$targetTriple.exe"
Copy-Item -LiteralPath $source -Destination $destination -Force
Write-Output "Sidecar ready: $destination"
