param(
    [string]$Configuration = "Release",
    [string]$Platform = "x64",
    [string]$SampleRoot = "E:\Builds\asioa-audio-router\windows-driver-samples\audio\simpleaudiosample",
    [string]$OutputDir = "E:\Builds\asioa-audio-router\endpoint-driver",
    [string]$DownloadDir = "E:\Downloads\asioa-audio-router",
    [string]$CertificateSubject = "Devine Creations ASIOA Test Signing",
    [switch]$NoAutoDownload
)

$ErrorActionPreference = "Stop"

function Save-FileIfMissing {
    param(
        [Parameter(Mandatory=$true)][string]$Uri,
        [Parameter(Mandatory=$true)][string]$Path
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Host "Already downloaded: $Path"
        return
    }

    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    Write-Host "Downloading: $Uri"
    Invoke-WebRequest -Uri $Uri -OutFile $Path -UseBasicParsing
}

function Ensure-SimpleAudioSample {
    param([string]$Path)

    $solutionPath = Join-Path $Path "SimpleAudioSample.sln"
    if (Test-Path -LiteralPath $solutionPath) {
        return $solutionPath
    }

    if ($NoAutoDownload) {
        throw "Microsoft SimpleAudioSample was not found at $Path, and NoAutoDownload was set."
    }

    $sampleRepo = Split-Path -Parent (Split-Path -Parent $Path)
    $repoRoot = Split-Path -Parent $sampleRepo
    New-Item -ItemType Directory -Path $repoRoot -Force | Out-Null

    if (-not (Test-Path (Join-Path $sampleRepo ".git"))) {
        git clone --filter=blob:none --sparse https://github.com/microsoft/Windows-driver-samples.git $sampleRepo
        if ($LASTEXITCODE -ne 0) { throw "Could not clone microsoft/Windows-driver-samples." }
    }

    git config --global --add safe.directory $sampleRepo | Out-Null
    git -C $sampleRepo sparse-checkout set audio/simpleaudiosample
    if ($LASTEXITCODE -ne 0) { throw "Could not sparse-checkout audio/simpleaudiosample." }

    if (-not (Test-Path -LiteralPath $solutionPath)) {
        throw "Microsoft SimpleAudioSample was not found after auto-download at $Path."
    }

    return $solutionPath
}

function Ensure-WdkNugetPackage {
    param([string]$SampleRepositoryRoot)

    $packagesConfig = Join-Path $SampleRepositoryRoot "packages.config"
    if (-not (Test-Path -LiteralPath $packagesConfig)) {
        return
    }

    $nuget = Join-Path $DownloadDir "nuget.exe"
    if (-not (Test-Path -LiteralPath $nuget)) {
        if ($NoAutoDownload) {
            throw "nuget.exe was not found at $nuget, and NoAutoDownload was set."
        }
        Save-FileIfMissing -Uri "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe" -Path $nuget
    }

    & $nuget restore $packagesConfig -PackagesDirectory (Join-Path $SampleRepositoryRoot "packages")
    if ($LASTEXITCODE -ne 0) {
        throw "NuGet restore for WDK packages failed with exit code $LASTEXITCODE."
    }
}

function Ensure-WdkTaskAlias {
    param([string]$SampleRepositoryRoot)

    $packageBins = Get-ChildItem -LiteralPath (Join-Path $SampleRepositoryRoot "packages") -Recurse -Directory -Filter bin -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "Microsoft\.Windows\.WDK\.x64" }
    foreach ($bin in $packageBins) {
        $task18 = Join-Path $bin.FullName "Microsoft.DriverKit.Build.Tasks.18.0.dll"
        $verifier18 = Join-Path $bin.FullName "Microsoft.DriverKit.Build.Tasks.PackageVerifier.18.0.dll"
        $task17 = Join-Path $bin.FullName "Microsoft.DriverKit.Build.Tasks.17.0.dll"
        $verifier17 = Join-Path $bin.FullName "Microsoft.DriverKit.Build.Tasks.PackageVerifier.17.0.dll"
        if ((Test-Path -LiteralPath $task18) -and -not (Test-Path -LiteralPath $task17)) {
            Copy-Item -LiteralPath $task18 -Destination $task17 -Force
        }
        if ((Test-Path -LiteralPath $verifier18) -and -not (Test-Path -LiteralPath $verifier17)) {
            Copy-Item -LiteralPath $verifier18 -Destination $verifier17 -Force
        }
    }
}

function Set-AsioaEndpointBranding {
    param([string]$SamplePath)

    $inx = Join-Path $SamplePath "Source\Main\SimpleAudioSample.inx"
    if (-not (Test-Path -LiteralPath $inx)) {
        return
    }
    $content = Get-Content -LiteralPath $inx -Raw -Encoding Unicode
    $content = $content -replace "ROOT\\sysvad_ComponentizedAudioSample", "ROOT\ASIOAAudioRouterBridge"
    $content = $content -replace "ROOT\\SimpleAudioSample", "ROOT\ASIOAAudioRouterBridge"
    $content = $content -replace "Simple Audio Sample Device", "ASIOA Audio Router Bridge"
    $content = $content -replace "Simple Audio Sample Driver", "ASIOA Audio Router Bridge Driver"
    $content = $content -replace "Speaker/Headphone \(Simple Audio Sample\)", "ASIOA Bridge Output 1/2"
    $content = $content -replace "Microphone \(Simple Audio Sample\)", "ASIOA Bridge Input 1/2"
    Set-Content -LiteralPath $inx -Value $content -Encoding Unicode
}

function Sign-EndpointCatalogIfPossible {
    param([string]$PackagePath)

    $cat = Get-ChildItem -LiteralPath $PackagePath -File -Filter *.cat -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cat) {
        return
    }
    $cert = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
        Where-Object { $_.Subject -like "*$CertificateSubject*" -and $_.HasPrivateKey } |
        Sort-Object NotAfter -Descending |
        Select-Object -First 1
    if (-not $cert) {
        Write-Warning "No ASIOA test-signing certificate with private key was found. Endpoint package will remain unsigned."
        return
    }
    $signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "\\x64\\signtool.exe$" } |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if (-not $signtool) {
        Write-Warning "signtool.exe was not found. Endpoint package will remain unsigned."
        return
    }
    & $signtool.FullName sign /fd SHA256 /sha1 $cert.Thumbprint /tr http://timestamp.digicert.com /td SHA256 $cat.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Catalog signing failed with exit code $LASTEXITCODE."
    }
}

$solution = Ensure-SimpleAudioSample -Path $SampleRoot
$sampleRepositoryRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $SampleRoot))
Ensure-WdkNugetPackage -SampleRepositoryRoot $sampleRepositoryRoot
Ensure-WdkTaskAlias -SampleRepositoryRoot $sampleRepositoryRoot
Set-AsioaEndpointBranding -SamplePath $SampleRoot

$vsInstallCandidates = @(
    @{ Name = "Community"; Root = "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community" },
    @{ Name = "BuildTools"; Root = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools" }
) | Where-Object { $_.Root -and (Test-Path $_.Root) }

$msbuildCandidates = foreach ($candidate in $vsInstallCandidates) {
    $msbuildPath = Join-Path $candidate.Root "MSBuild\Current\Bin\amd64\MSBuild.exe"
    if (Test-Path -LiteralPath $msbuildPath) {
        [pscustomobject]@{
            Name = $candidate.Name
            Root = $candidate.Root
            MSBuild = $msbuildPath
            Toolset = Join-Path $candidate.Root "MSBuild\Microsoft\VC\v170\Platforms\$Platform\PlatformToolsets\WindowsKernelModeDriver10.0"
        }
    }
}

if (-not $msbuildCandidates) {
    throw "MSBuild was not found. Install Visual Studio 2022 with C++ and Windows driver build tools."
}

$expectedToolsetRoots = $msbuildCandidates | ForEach-Object { $_.Toolset }

$driverBuildHost = $msbuildCandidates | Where-Object { Test-Path -LiteralPath $_.Toolset } | Select-Object -First 1
$toolsetRoots = $expectedToolsetRoots | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

if (-not $driverBuildHost) {
    $wdkSetup = Join-Path $DownloadDir "wdksetup.exe"
    if (-not $NoAutoDownload) {
        Save-FileIfMissing `
            -Uri "https://download.microsoft.com/download/302bbcbf-52ae-4e23-ba35-dce560124051/KIT_BUNDLE_WDK_MEDIACREATION/wdksetup.exe" `
            -Path $wdkSetup
    }

    $message = @"
WindowsKernelModeDriver10.0 build tools are missing.

The Microsoft Windows-driver-samples tree is present, and the WDK bootstrapper is staged at:
$wdkSetup

Install/repair the Visual Studio 2022 Windows Driver Kit individual component, then install the WDK. Microsoft documents this as the "Windows Driver Kit" Visual Studio component plus the matching WDK for VS 2022.

After installation, this folder should exist:
$($expectedToolsetRoots -join "`n")

Then rerun:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-endpoint-driver.ps1
"@
    throw $message
}

Write-Host "Using $($driverBuildHost.Name) MSBuild: $($driverBuildHost.MSBuild)"

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

& $driverBuildHost.MSBuild $solution /p:Configuration=$Configuration /p:Platform=$Platform /p:SpectreMitigation=false /p:RunCodeAnalysis=false /p:SignMode=Off /p:EnableTestSign=false /t:Rebuild /m /v:minimal
if ($LASTEXITCODE -ne 0) {
    throw "Endpoint driver build failed with exit code $LASTEXITCODE."
}

$packageDirs = Get-ChildItem -LiteralPath $SampleRoot -Recurse -Directory -Filter package -ErrorAction SilentlyContinue |
    Where-Object { Get-ChildItem -LiteralPath $_.FullName -File -Include *.inf,*.sys,*.cat -ErrorAction SilentlyContinue }

if (-not $packageDirs) {
    throw "Endpoint driver build completed but no package folder with .inf, .sys, and .cat files was found."
}

$latestPackage = $packageDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item -LiteralPath (Join-Path $latestPackage.FullName "*") -Destination $OutputDir -Recurse -Force
Sign-EndpointCatalogIfPossible -PackagePath $OutputDir

Write-Host "ASIOA endpoint driver package staged from: $($latestPackage.FullName)"
Write-Host "ASIOA endpoint driver package output: $OutputDir"
Write-Host "Secure Boot note: this local endpoint package may install but still fail to load with Code 52 until Microsoft attestation/WHQL signing is completed or the test machine is placed into a permitted test-signing environment."
