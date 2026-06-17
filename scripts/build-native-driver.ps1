param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    [string]$DriverDllPath,
    [string]$PublishDriverDir = "E:\Builds\asioa-audio-router\publish\driver"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ($DriverDllPath) {
    $dll = (Resolve-Path -LiteralPath $DriverDllPath).Path
} else {
    $vsRoots = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"
    )
    $msvcRoot = $vsRoots |
        Where-Object { Test-Path $_ } |
        ForEach-Object { Get-ChildItem $_ -Directory -ErrorAction SilentlyContinue } |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $msvcRoot) {
        throw "MSVC tools were not found. Install Visual Studio 2022 Desktop development with C++."
    }
    $cl = Join-Path $msvcRoot.FullName "bin\Hostx64\x64\cl.exe"
    $link = Join-Path $msvcRoot.FullName "bin\Hostx64\x64\link.exe"
    if (-not (Test-Path $cl) -or -not (Test-Path $link)) {
        throw "cl.exe or link.exe was not found under $($msvcRoot.FullName)."
    }
    $sdkRoot = "${env:ProgramFiles(x86)}\Windows Kits\10"
    $sdkVersion = Get-ChildItem (Join-Path $sdkRoot "Include") -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $sdkVersion) {
        throw "Windows 10 SDK include files were not found."
    }
    $sdkInclude = Join-Path $sdkRoot "Include\$($sdkVersion.Name)"
    $sdkLib = Join-Path $sdkRoot "Lib\$($sdkVersion.Name)"
    $includePaths = @(
        (Join-Path $repo "src\ASIOA.Driver"),
        (Join-Path $msvcRoot.FullName "include"),
        (Join-Path $sdkInclude "shared"),
        (Join-Path $sdkInclude "um"),
        (Join-Path $sdkInclude "ucrt"),
        (Join-Path $sdkInclude "winrt"),
        (Join-Path $sdkInclude "cppwinrt")
    )
    $libPaths = @(
        (Join-Path $msvcRoot.FullName "lib\onecore\x64"),
        (Join-Path $sdkLib "um\x64"),
        (Join-Path $sdkLib "ucrt\x64")
    )
    $outDir = Join-Path $repo "build\native\$Configuration"
    $objDir = Join-Path $repo "build\native\obj\$Configuration\ASIOA.Driver"
    New-Item -ItemType Directory -Force -Path $outDir, $objDir | Out-Null
    $env:PATH = "$(Split-Path $cl);$env:PATH"
    $env:INCLUDE = ($includePaths | Where-Object { Test-Path $_ }) -join ";"
    $env:LIB = ($libPaths | Where-Object { Test-Path $_ }) -join ";"
    $sources = @(
        (Join-Path $repo "src\ASIOA.Driver\asioa_driver.cpp"),
        (Join-Path $repo "src\ASIOA.Driver\dllmain.cpp")
    )
    $objects = @()
    foreach ($source in $sources) {
        $object = Join-Path $objDir ([IO.Path]::GetFileNameWithoutExtension($source) + ".obj")
        & $cl /nologo /std:c++17 /EHsc /LD /MD /O2 /W4 /DWIN32 /D_WINDOWS /D_USRDLL /DASIOA_DRIVER_EXPORTS /D_UNICODE /DUNICODE /Fo$object /c $source
        if ($LASTEXITCODE -ne 0) {
            throw "Native driver compile failed for $source with exit code $LASTEXITCODE."
        }
        $objects += $object
    }
    $dll = Join-Path $outDir "ASIOA.Driver.dll"
    & $link /NOLOGO /DLL /OUT:$dll $objects advapi32.lib ole32.lib uuid.lib shell32.lib
    if ($LASTEXITCODE -ne 0) {
        throw "Native driver link failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path $dll)) {
    throw "Expected driver DLL was not produced: $dll"
}

$signature = Get-AuthenticodeSignature -LiteralPath $dll
New-Item -ItemType Directory -Force -Path $PublishDriverDir | Out-Null
Copy-Item -LiteralPath $dll -Destination (Join-Path $PublishDriverDir "ASIOA.Driver.dll") -Force
Copy-Item -LiteralPath (Join-Path $repo "scripts\install-asioa-driver.ps1") -Destination (Join-Path $PublishDriverDir "install-asioa-driver.ps1") -Force
Copy-Item -LiteralPath (Join-Path $repo "scripts\uninstall-asioa-driver.ps1") -Destination (Join-Path $PublishDriverDir "uninstall-asioa-driver.ps1") -Force

Write-Host "ASIOA native driver DLL: $dll"
Write-Host "Published driver package to: $PublishDriverDir"
Write-Host "Driver Authenticode status: $($signature.Status)"
if ($signature.Status -ne "Valid") {
    Write-Warning "The packaged ASIOA.Driver.dll is not signed with a valid Authenticode signature. Treat this as a local/dev driver package, not a public signed driver."
}
