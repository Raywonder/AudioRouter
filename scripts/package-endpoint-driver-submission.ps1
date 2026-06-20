param(
    [string]$EndpointPackageDir = "E:\Builds\asioa-audio-router\endpoint-driver",
    [string]$OutputDir = "E:\Builds\asioa-audio-router\driver-submission",
    [string]$PackageName = "ASIOAEndpointDriver",
    [string]$CertificateSubject = "",
    [switch]$SignCab
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $EndpointPackageDir)) {
    throw "Endpoint package directory not found: $EndpointPackageDir"
}

$inf = Get-ChildItem -LiteralPath $EndpointPackageDir -Filter *.inf -File | Select-Object -First 1
$sys = Get-ChildItem -LiteralPath $EndpointPackageDir -Filter *.sys -File | Select-Object -First 1
if (-not $inf -or -not $sys) {
    throw "The endpoint package must contain at least one INF and one SYS file."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$workDir = Join-Path $OutputDir "$PackageName-$stamp"
$driverDir = Join-Path $workDir $PackageName
New-Item -ItemType Directory -Path $driverDir -Force | Out-Null

Copy-Item -LiteralPath $inf.FullName -Destination $driverDir -Force
Copy-Item -LiteralPath $sys.FullName -Destination $driverDir -Force
Get-ChildItem -LiteralPath $EndpointPackageDir -Filter *.cat -File -ErrorAction SilentlyContinue |
    Copy-Item -Destination $driverDir -Force
Get-ChildItem -LiteralPath $EndpointPackageDir -Filter *.pdb -File -ErrorAction SilentlyContinue |
    Copy-Item -Destination $driverDir -Force

$ddfPath = Join-Path $workDir "$PackageName.ddf"
$cabName = "$PackageName-$stamp.cab"
$cabPath = Join-Path (Join-Path $workDir "Disk1") $cabName

$driverFiles = Get-ChildItem -LiteralPath $driverDir -File | Sort-Object Name
$ddf = @(
    ".OPTION EXPLICIT",
    ".Set CabinetFileCountThreshold=0",
    ".Set FolderFileCountThreshold=0",
    ".Set FolderSizeThreshold=0",
    ".Set MaxCabinetSize=0",
    ".Set MaxDiskFileCount=0",
    ".Set MaxDiskSize=0",
    ".Set CompressionType=MSZIP",
    ".Set Cabinet=on",
    ".Set Compress=on",
    ".Set CabinetNameTemplate=$cabName",
    ".Set DestinationDir=$PackageName"
)
foreach ($file in $driverFiles) {
    $ddf += "`"$($file.FullName)`""
}
$ddf | Set-Content -LiteralPath $ddfPath -Encoding ASCII

Push-Location $workDir
try {
    makecab /f $ddfPath
    if ($LASTEXITCODE -ne 0) {
        throw "makecab failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $cabPath)) {
    throw "CAB file was not created at expected path: $cabPath"
}

if ($SignCab) {
    $signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "\\x64\\signtool.exe$" } |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if (-not $signtool) {
        throw "signtool.exe was not found. Install the Windows SDK/WDK signing tools."
    }
    if (-not $CertificateSubject) {
        throw "CertificateSubject is required when SignCab is used."
    }
    & $signtool.FullName sign /n $CertificateSubject /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /v $cabPath
    if ($LASTEXITCODE -ne 0) {
        throw "CAB signing failed with exit code $LASTEXITCODE."
    }
}

$manifest = [ordered]@{
    package = $PackageName
    createdAt = (Get-Date).ToString("s")
    endpointPackageDir = $EndpointPackageDir
    cab = $cabPath
    files = @($driverFiles | ForEach-Object { $_.Name })
    signCab = [bool]$SignCab
    notes = @(
        "Submit this CAB through Microsoft Partner Center Hardware dashboard for attestation signing or as part of the WHQL/HLK path.",
        "Microsoft regenerates the catalog during signing. Keep the original staged package for local build traceability.",
        "A Microsoft-signed returned package is required for normal Secure Boot systems to load the ASIOA Windows endpoint driver."
    )
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $workDir "submission-manifest.json") -Encoding UTF8

Write-Host "ASIOA endpoint driver submission CAB created:"
Write-Host $cabPath
Write-Host "Manifest:"
Write-Host (Join-Path $workDir "submission-manifest.json")
