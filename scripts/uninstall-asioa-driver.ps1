$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$driverDll = Join-Path $scriptDir "ASIOA.Driver.dll"
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Administrator permission is required to uninstall the ASIOA native ASIO driver."
}

if (Test-Path $driverDll) {
    $regsvr = Join-Path $env:WINDIR "System32\regsvr32.exe"
    $unregister = Start-Process -FilePath $regsvr -ArgumentList @("/s", "/u", $driverDll) -Wait -PassThru
    if ($unregister.ExitCode -ne 0) {
        Write-Warning "regsvr32 did not fully unregister ASIOA.Driver.dll. Exit code: $($unregister.ExitCode)"
    }
}

$driverName = "ASIOA Audio Router"
$clsid = "{4B6B66F3-0182-4E8B-9B7C-0C545022110A}"
Remove-Item -Path "HKLM:\SOFTWARE\ASIO\$driverName" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "HKLM:\SOFTWARE\Classes\CLSID\$clsid" -Recurse -Force -ErrorAction SilentlyContinue

$settingsDir = Join-Path $env:APPDATA "ASIOA Audio Router"
$marker = Join-Path $settingsDir "driver-installed.json"
Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue

Write-Host "ASIOA native ASIO driver registration removed."
