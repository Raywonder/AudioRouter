# Toolchain

## Current Working Tooling

- .NET SDK 8/9 is installed.
- Python 3.12 is available through the local launcher as `-V:Astral/CPython3.12.12`.
- wxPython and PyInstaller build in the release venv under `E:\Builds\asioa-audio-router\py312-venv`.
- The route model, smoke test, WPF secondary prototype, and wxPython primary control panel build successfully.

## Native Audio Tooling And Signing

The virtual ASIO driver, Windows endpoint driver, and VST3/CLAP bridge require native Windows C++ tooling.

The current Windows host can build the ASIO COM driver DLL and can stage a WDM endpoint package from the Microsoft SimpleAudioSample driver. The ASIO driver can be registered with `regsvr32` and appears under `HKLM\SOFTWARE\ASIO\ASIOA Audio Router`.

The Windows WDM/WASAPI/DirectSound endpoint package is different. On Secure Boot systems, Windows will not load a locally test-signed kernel driver. The local package may install into the driver store, but Device Manager/PnP can show Code 52 until the driver is Microsoft signed or the machine is placed into a proper test-signing environment.

Required for native phases:

- Visual Studio 2022 Desktop development with C++ workload.
- Windows SDK.
- Windows Driver Kit or WDK NuGet packages.
- Steinberg ASIO SDK or compatible licensed ASIO driver implementation path.
- Steinberg VST3 SDK for the optional VST3 bridge.
- Microsoft driver signing path for public distribution of kernel endpoint components. Use Partner Center attestation or HLK/WHQL signing for production. A local test certificate is only for development and will not load on normal Secure Boot systems.

## Build Commands

Managed and wxPython control-panel build:

```powershell
dotnet build .\asioa-audio-router.sln -c Release
dotnet run --project .\src\ASIOA.Smoke\ASIOA.Smoke.csproj -c Release
py -V:Astral/CPython3.12.12 -m venv E:\Builds\asioa-audio-router\py312-venv
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe -m pip install -r .\src\ASIOA.Wx\requirements.txt
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath E:\Builds\asioa-audio-router\wx-publish --workpath .\build\pyinstaller .\src\ASIOA.Wx\asioa_router_wx.spec
```

Native driver staging, when a built DLL is available:

```powershell
.\scripts\build-native-driver.ps1 -Configuration Release
```

If another build task already produced the DLL, stage that exact artifact without rebuilding:

```powershell
.\scripts\build-native-driver.ps1 -DriverDllPath E:\path\to\ASIOA.Driver.dll
```

Both commands copy `ASIOA.Driver.dll`, `install-asioa-driver.ps1`, and `uninstall-asioa-driver.ps1` to `E:\Builds\asioa-audio-router\publish\driver`. The script prints the DLL Authenticode status so release packaging can decide whether Windows signing requirements have been satisfied.

The endpoint-driver staging script is:

```powershell
.\scripts\build-endpoint-driver.ps1
```

It uses the Microsoft Windows driver sample package as the current endpoint base, brands the package as ASIOA, disables Spectre mitigation for this local build when the matching libraries are absent, stages the INF/SYS/CAT files, and signs the catalog with the local ASIOA test certificate when available. The resulting endpoint package is not production-signed. If Secure Boot blocks TESTSIGNING, Windows will keep the device in Code 52 until the package is Microsoft signed.

To inspect the current machine and installed endpoint state:

```powershell
.\scripts\check-driver-signing-state.ps1
```

To create a Microsoft Partner Center submission CAB from the staged endpoint package:

```powershell
.\scripts\package-endpoint-driver-submission.ps1
```

For production distribution, use Microsoft Partner Center attestation signing or WHQL/HLK signing. Attestation requires Hardware Developer Program access and an EV code-signing certificate, and Microsoft regenerates the signed catalog during the process. HLK/WHQL signing remains the stronger release path when full Windows certification and Windows Update distribution are needed.

For development-only loading, Windows can load test-signed code when TESTSIGNING is enabled, but Microsoft documents that Secure Boot can prevent changing that option until Secure Boot is disabled. Microsoft also supports a preproduction signing path for partners that need Secure Boot enabled during early validation, but that requires Hardware Dev Center preproduction signing and explicit test-machine provisioning. Do not present either development path as a public end-user workaround.

The current driver source is in `src\ASIOA.Driver`. It exposes the ASIO COM registration hooks, ASIO registry registration, channel names, sample-rate/buffer metadata, and safe silence until the engine/shared-memory transport is connected. The staged endpoint package is the first WDM/WASAPI/DirectSound visibility track, but it must pass Microsoft signing before ordinary Windows apps can rely on it on Secure Boot machines. VST3 builds, the native audio-policy helper for per-app output moves, and production driver signing remain separate hardening tracks.
