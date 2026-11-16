# Builds the Windows installer of OPTiBAR: dist\installer\OPTiBAR-<version>-Setup.exe
#
#     powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
#
# Needs uv and Inno Setup 6 (winget install JRSoftware.InnoSetup). The version is the one of pyproject.toml.
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Push-Location $root
try {
    $version = (uv run --group build python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])").Trim()
    if ($LASTEXITCODE -ne 0) { throw 'could not read the version of pyproject.toml' }
    Write-Host "Building OPTiBAR $version"

    # 1. the app, frozen into dist\OPTiBAR
    uv run --group build pyinstaller packaging\windows\OPTiBAR.spec --noconfirm --clean --distpath dist --workpath build\pyinstaller
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }

    # 2. the installer, from dist\OPTiBAR
    $iscc = @(
        (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source,
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $iscc) { throw 'Inno Setup 6 not found, install it with: winget install JRSoftware.InnoSetup' }
    & $iscc /Qp "/DAppVersion=$version" packaging\windows\optibar.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }

    Write-Host "Done: $(Join-Path $root "dist\installer\OPTiBAR-$version-Setup.exe")"
}
finally {
    Pop-Location
}
