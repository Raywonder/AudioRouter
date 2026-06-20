$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageDir = Join-Path $scriptDir "endpoint"
$hardwareId = "ROOT\ASIOAAudioRouterBridge"
$driverNamePattern = "ASIOA Audio Router Bridge"

if (-not (Test-Path $packageDir)) {
    Write-Host "ASIOA endpoint driver package was not bundled with this installer."
    exit 0
}

$inf = Get-ChildItem -LiteralPath $packageDir -Filter "*.inf" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $inf) {
    Write-Host "ASIOA endpoint driver INF was not found in the bundled endpoint package."
    exit 0
}

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Administrator permission is required to install the ASIOA Windows audio endpoint driver."
}

$cert = Get-ChildItem Cert:\CurrentUser\My,Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -match "ASIOA|Devine Creations ASIOA" -and $_.HasPrivateKey } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if ($cert) {
    $certPath = Join-Path $env:TEMP "asioa-endpoint-driver.cer"
    Export-Certificate -Cert $cert -FilePath $certPath -Force | Out-Null
    Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
    Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\TrustedPublisher | Out-Null
}

$pnputil = Join-Path $env:WINDIR "System32\pnputil.exe"
if (-not (Test-Path $pnputil)) {
    throw "pnputil.exe was not found."
}

& $pnputil /add-driver $inf.FullName /install
if ($LASTEXITCODE -ne 0) {
    throw "pnputil failed while installing the ASIOA Windows audio endpoint driver. Exit code: $LASTEXITCODE"
}

$existingDevice = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -match "ASIOAAudioRouterBridge" -or $_.FriendlyName -like "*$driverNamePattern*" } |
    Select-Object -First 1

if (-not $existingDevice) {
    $devconCandidates = @(
        Join-Path $packageDir "devcon.exe"
        "C:\Program Files (x86)\Windows Kits\10\Tools\10.0.28000.0\x64\devcon.exe"
        "C:\Program Files (x86)\Windows Kits\10\Tools\10.0.26100.0\x64\devcon.exe"
        "C:\Program Files (x86)\Windows Kits\10\Tools\10.0.22621.0\x64\devcon.exe"
    )
    $devcon = $devconCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($devcon) {
        & $devcon install $inf.FullName $hardwareId
        if ($LASTEXITCODE -ne 0) {
            throw "devcon failed while creating the ASIOA Windows audio endpoint. Exit code: $LASTEXITCODE"
        }
    } else {
        throw "ASIOA driver was added to the Driver Store, but no root endpoint exists yet and devcon.exe was not found to create $hardwareId."
    }
}

$settingsDir = Join-Path $env:APPDATA "ASIOA Audio Router"
New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
@{
    driver = "ASIOA Windows audio endpoint"
    inf = $inf.FullName
    hardwareId = $hardwareId
    installedAt = (Get-Date).ToString("o")
    endpointLayer = "wdm-wasapi-directsound"
} | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $settingsDir "endpoint-driver-installed.json") -Encoding UTF8

Write-Host "ASIOA Windows audio endpoint driver installation completed or refreshed. Restart audio applications to refresh device lists."
