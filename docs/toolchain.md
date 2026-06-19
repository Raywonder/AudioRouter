# Toolchain

## Current Working Tooling

- .NET SDK 8/9 is installed.
- Python 3.12 is available through the local launcher as `-V:Astral/CPython3.12.12`.
- wxPython and PyInstaller build in the release venv under `E:\Builds\asioa-audio-router\py312-venv`.
- The route model, smoke test, WPF secondary prototype, and wxPython primary control panel build successfully.

## Native Audio Tooling Still Required

The virtual ASIO driver and VST3 bridge require native Windows C++ tooling.

The current Windows host still has an incomplete Visual Studio C++ environment. `cl.exe` exists under the Visual Studio Community install, but the MSVC include directory is empty and `vcvarsall.bat` is missing. Direct native compilation currently fails at `windows.h` -> `excpt.h`, which means the Desktop development with C++ workload or its MSVC headers need repair/reinstall before this machine can produce the native DLL.

Required for native phases:

- Visual Studio 2022 Desktop development with C++ workload.
- Windows SDK.
- Steinberg ASIO SDK or compatible licensed ASIO driver implementation path.
- Steinberg VST3 SDK for the optional VST3 bridge.
- Driver signing certificate for public distribution of the ASIO driver. A local unsigned DLL may be staged for development testing, but it is not a signed release driver.

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

Both commands copy `ASIOA.Driver.dll`, `install-asioa-driver.ps1`, and `uninstall-asioa-driver.ps1` to `E:\Builds\asioa-audio-router\publish\driver`. The script prints the DLL Authenticode status. If the status is not `Valid`, treat the package as a local/dev driver package only.

The current driver source is in `src\ASIOA.Driver`. It exposes the 68 input/68 output ASIO surface, COM registration hooks, ASIO registry registration, channel names, sample-rate/buffer metadata, and safe silence until the engine/shared-memory transport is connected. It does not yet expose a Windows WDM, WASAPI, or DirectSound speaker/microphone endpoint. VST3 builds and the Windows-visible endpoint layer will be added once the C++ toolchain, SDK licensing path, and signing path are fully repaired.
