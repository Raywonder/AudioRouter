$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$driverDll = Join-Path $scriptDir "ASIOA.Driver.dll"
if (-not (Test-Path $driverDll)) {
    throw "ASIOA.Driver.dll was not found beside this installer script."
}

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Administrator permission is required to install the ASIOA system audio driver."
}

$signature = Get-AuthenticodeSignature -LiteralPath $driverDll
if ($signature.Status -ne "Valid") {
    Write-Warning "ASIOA.Driver.dll does not have a valid Authenticode signature ($($signature.Status)). Registering the local packaged DLL only; do not treat this as a public signed driver."
}

$regsvr = Join-Path $env:WINDIR "System32\regsvr32.exe"
& $regsvr /s $driverDll
if ($LASTEXITCODE -ne 0) {
    throw "regsvr32 failed while registering ASIOA.Driver.dll. Exit code: $LASTEXITCODE"
}

$settingsDir = Join-Path $env:APPDATA "ASIOA Audio Router"
New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
$marker = Join-Path $settingsDir "driver-installed.json"
@{
    driver = "ASIOA.Driver.dll"
    installedAt = (Get-Date).ToString("s")
    path = $driverDll
    registration = "HKLM Software\\ASIO\\ASIOA Audio Router"
    authenticodeStatus = $signature.Status.ToString()
    signedForPublicDistribution = ($signature.Status -eq "Valid")
} | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding UTF8

Write-Host "ASIOA system audio driver registered."
