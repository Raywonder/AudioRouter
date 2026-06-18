param(
    [string]$Configuration = "Release",
    [string]$PublishDir = "E:\Builds\asioa-audio-router\publish",
    [string]$WxPublishDir = "E:\Builds\asioa-audio-router\wx-publish",
    [string]$PyInstallerWorkDir = "E:\Builds\asioa-audio-router\pyinstaller-work",
    [string]$PythonVenv = "E:\Builds\asioa-audio-router\py312-venv",
    [string]$OutputDir = "E:\Downloads\asioa-audio-router"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$solution = Join-Path $root "asioa-audio-router.sln"
$appProject = Join-Path $root "src\ASIOA.App\ASIOA.App.csproj"
$wxProject = Join-Path $root "src\ASIOA.Wx"
$installerScript = Join-Path $root "installer\ASIOA-Audio-Router.iss"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
$python = "py"
$pythonSelector = "-V:Astral/CPython3.12.12"
$venvPython = Join-Path $PythonVenv "Scripts\python.exe"

if (!(Test-Path $iscc)) {
    throw "Inno Setup compiler was not found at $iscc"
}

New-Item -ItemType Directory -Path $PublishDir -Force | Out-Null
New-Item -ItemType Directory -Path $WxPublishDir -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $PythonVenv) -Force | Out-Null

Get-ChildItem $OutputDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "ASIOA-Audio-Router-Setup-*.exe" -or $_.Name -like "ASIOA-Audio-Router-win-x64-portable-*.zip" } |
    Remove-Item -Force

dotnet build $solution -c $Configuration
dotnet publish $appProject -c $Configuration -r win-x64 --self-contained true -o (Join-Path $PublishDir "wpf-secondary")

Push-Location $wxProject
try {
    if (!(Test-Path $venvPython)) {
        & $python $pythonSelector -m venv $PythonVenv
    }
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
    & $venvPython -m PyInstaller --noconfirm --clean --distpath $WxPublishDir --workpath $PyInstallerWorkDir asioa_router_wx.spec
}
finally {
    Pop-Location
}

$wxAppDir = Join-Path $WxPublishDir "ASIOA Audio Router"
if (!(Test-Path $wxAppDir)) {
    throw "wxPython build output was not created at $wxAppDir"
}

if (Test-Path $PublishDir) {
    Get-ChildItem $PublishDir -Force | Where-Object { $_.Name -notin @("wpf-secondary", "driver") } | Remove-Item -Recurse -Force
}
Copy-Item -Path (Join-Path $wxAppDir "*") -Destination $PublishDir -Recurse -Force
& $iscc $installerScript

$portableZip = Join-Path $OutputDir "ASIOA-Audio-Router-win-x64-portable-0.2.4.zip"
Compress-Archive -Path (Join-Path $PublishDir "*") -DestinationPath $portableZip -Force

$checksumsPath = Join-Path $OutputDir "SHA256SUMS.txt"
$artifacts = Get-ChildItem $OutputDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | Sort-Object Name
$lines = foreach ($artifact in $artifacts) {
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $artifact.FullName
    "$($hash.Hash.ToLowerInvariant())  $($artifact.Name)"
}
$lines | Set-Content -Path $checksumsPath -Encoding ASCII

Write-Host "ASIOA release artifacts:"
$artifacts | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize
Write-Host "Checksums: $checksumsPath"
