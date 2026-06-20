$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$driverDll = Join-Path $scriptDir "ASIOA.Driver.dll"
if (-not (Test-Path $driverDll)) {
    throw "ASIOA.Driver.dll was not found beside this installer script."
}

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Administrator permission is required to install the ASIOA native ASIO driver."
}

$signature = Get-AuthenticodeSignature -LiteralPath $driverDll
if ($signature.Status -ne "Valid") {
    Write-Warning "ASIOA.Driver.dll does not have a valid Authenticode signature ($($signature.Status)). Registering the local packaged DLL only; do not treat this as a public signed driver."
}

$driverName = "ASIOA Audio Router"
$clsid = "{4B6B66F3-0182-4E8B-9B7C-0C545022110A}"
$asioKey = "HKLM:\SOFTWARE\ASIO\$driverName"
$clsidKey = "HKLM:\SOFTWARE\Classes\CLSID\$clsid"
$inprocKey = Join-Path $clsidKey "InprocServer32"

function Set-AsioaRegistryRegistration {
    New-Item -Path $asioKey -Force | Out-Null
    New-ItemProperty -Path $asioKey -Name "CLSID" -Value $clsid -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $asioKey -Name "Description" -Value $driverName -PropertyType String -Force | Out-Null

    New-Item -Path $inprocKey -Force | Out-Null
    Set-Item -Path $inprocKey -Value $driverDll
    New-ItemProperty -Path $inprocKey -Name "ThreadingModel" -Value "Both" -PropertyType String -Force | Out-Null
}

function Test-AsioaRegistryRegistration {
    if (-not (Test-Path $asioKey) -or -not (Test-Path $inprocKey)) {
        return $false
    }

    $asio = Get-ItemProperty -Path $asioKey
    $inprocDefault = (Get-Item -Path $inprocKey).GetValue("")
    $threadingModel = (Get-Item -Path $inprocKey).GetValue("ThreadingModel")

    return (
        $asio.CLSID -eq $clsid -and
        $inprocDefault -eq $driverDll -and
        $threadingModel -eq "Both"
    )
}

$regsvr = Join-Path $env:WINDIR "System32\regsvr32.exe"
$unregister = Start-Process -FilePath $regsvr -ArgumentList @("/s", "/u", $driverDll) -Wait -PassThru
if ($unregister.ExitCode -ne 0) {
    Write-Warning "Previous ASIOA.Driver.dll registration was not removed cleanly. Continuing with fresh registration. Exit code: $($unregister.ExitCode)"
}
$register = Start-Process -FilePath $regsvr -ArgumentList @("/s", $driverDll) -Wait -PassThru
if ($register.ExitCode -ne 0) {
    Write-Warning "regsvr32 did not complete cleanly while registering ASIOA.Driver.dll. Exit code: $($register.ExitCode). Repairing the ASIO registry entries directly."
}

Set-AsioaRegistryRegistration
if (-not (Test-AsioaRegistryRegistration)) {
    throw "ASIOA.Driver.dll registry registration could not be verified."
}

$settingsDir = Join-Path $env:APPDATA "ASIOA Audio Router"
New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
$marker = Join-Path $settingsDir "driver-installed.json"
@{
    driver = "ASIOA.Driver.dll"
    installedAt = (Get-Date).ToString("s")
    path = $driverDll
    registration = "HKLM Software\\ASIO\\ASIOA Audio Router"
    windowsEndpointLayer = "packaged-separately"
    notes = "This package enables the native ASIO driver. WDM/WASAPI/DirectSound speaker and microphone endpoints use the packaged endpoint driver and require Microsoft signing or a permitted test-signing environment before Windows will load them on Secure Boot systems."
    authenticodeStatus = $signature.Status.ToString()
    signedForPublicDistribution = ($signature.Status -eq "Valid")
} | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding UTF8

Write-Host "ASIOA native ASIO driver registered. Restart ASIO-capable hosts to see the updated driver."
