$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Install Python 3.12 from python.org first."
}

py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install ".[dev]"
& .\.venv\Scripts\pytest.exe
& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name YandexMusicRPC `
    --icon assets\icon.ico `
    --collect-all winsdk `
    --collect-all pystray `
    main.py

Write-Host ""
Write-Host ("Done: " + (Join-Path $PSScriptRoot "dist\YandexMusicRPC.exe")) -ForegroundColor Green

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $defaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultIscc) {
        $iscc = $defaultIscc
    }
}
if (-not $iscc) {
    $userIscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    if (Test-Path $userIscc) {
        $iscc = $userIscc
    }
}
if ($iscc) {
    & $iscc installer\YandexMusicRPC.iss
    Write-Host ("Installer: " + (Join-Path $PSScriptRoot "dist\YandexMusicRPC-Setup.exe")) -ForegroundColor Green
} else {
    Write-Host "Inno Setup not found; portable EXE was built successfully." -ForegroundColor Yellow
}
