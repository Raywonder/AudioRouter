$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$driverDll = Join-Path $scriptDir "ASIOA.Driver.dll"
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Administrator permission is required to uninstall the ASIOA native ASIO driver."
}

if (Test-Path $driverDll) {
    $regsvr = Join-Path $env:WINDIR "System32\regsvr32.exe"
    & $regsvr /s /u $driverDll
    if ($LASTEXITCODE -ne 0) {
        throw "regsvr32 failed while unregistering ASIOA.Driver.dll. Exit code: $LASTEXITCODE"
    }
}

$settingsDir = Join-Path $env:APPDATA "ASIOA Audio Router"
$marker = Join-Path $settingsDir "driver-installed.json"
Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue

Write-Host "ASIOA native ASIO driver registration removed."
