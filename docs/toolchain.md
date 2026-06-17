# Toolchain

## Current Working Tooling

- .NET SDK 8/9 is installed.
- Python 3.12 is available through the local launcher as `-V:Astral/CPython3.12.12`.
- wxPython and PyInstaller build in the release venv under `E:\Builds\asioa-audio-router\py312-venv`.
- The route model, smoke test, WPF secondary prototype, and wxPython primary control panel build successfully.

## Native Audio Tooling Still Required

The virtual ASIO driver and VST3 bridge require native Windows C++ tooling.

The current Windows host previously showed an incomplete Visual Studio C++ environment: bundled CMake and MSBuild were present, but `vcvarsall.bat`, `cl.exe`, `clang++`, `g++`, and `ninja.exe` were not available.

Required for native phases:

- Visual Studio 2022 Desktop development with C++ workload.
- Windows SDK.
- Steinberg ASIO SDK or compatible licensed ASIO driver implementation path.
- Steinberg VST3 SDK for the optional VST3 bridge.
- Driver signing certificate for public distribution of the ASIO driver.

## Build Commands

Managed and wxPython control-panel build:

```powershell
dotnet build .\asioa-audio-router.sln -c Release
dotnet run --project .\src\ASIOA.Smoke\ASIOA.Smoke.csproj -c Release
py -V:Astral/CPython3.12.12 -m venv E:\Builds\asioa-audio-router\py312-venv
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe -m pip install -r .\src\ASIOA.Wx\requirements.txt
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath E:\Builds\asioa-audio-router\wx-publish --workpath .\build\pyinstaller .\src\ASIOA.Wx\asioa_router_wx.spec
```

Native driver and VST3 builds will be added once the C++ toolchain and SDK licensing path are in place.
