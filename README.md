# ASIOA Audio Router

ASIOA Audio Router is a planned accessible Windows virtual ASIO mixer and application audio router for DAW users.

Goal: route individual application audio into a DAW without manually chaining virtual audio cables, while also letting selected apps hear the DAW master output and other chosen inputs.

The implementation source of truth is the revised design bible under `ASIO_Audio_Router_Design_Bible_v1_0`. New work should follow its phase documents, accessibility standard, architecture volumes, schemas, and examples before adding or changing app behavior.

## Product Shape

ASIOA is not just one plug-in. It is a small audio system:

- ASIOA Router app: accessible wxPython control surface, tray app, startup manager, route matrix, meters, mute/volume controls, and smart buffer settings. The older WPF control app remains as a secondary prototype.
- ASIOA audio engine: captures per-application audio, physical inputs, and DAW return audio, then mixes/routes them.
- ASIOA virtual ASIO driver: exposes up to 68 input and 68 output channels to DAWs.
- ASIOA VST3 bridge plug-in: optional DAW insert/control plug-in for hosts that should connect through a plug-in instead of selecting the ASIO driver.

## First Channel Layout

- ASIOA input 1/2 to DAW: first stereo capture pair.
- ASIOA output 1/2 from DAW: DAW master return.
- Feedback guard: ASIOA output 1/2 is never routed back into ASIOA input 1/2 by default.
- Additional input/output pairs are allocated to apps, physical devices, and monitoring buses.
- Initial maximum: 68 channels each direction.

See [docs/channel-map.md](docs/channel-map.md).

## Accessibility Baseline

The app must be usable with NVDA, Narrator, and keyboard only:

- Every input, output, route, mute, solo, monitor, bypass, and buffer setting exposes Name, Role, Value, and State through UI Automation.
- Route matrix must have list/table alternatives, not only a visual grid.
- Volume uses 1 dB or 5 percent steps with exact speech feedback.
- Mute/unmute and bypass state must be clear from focus alone.
- Tray menu must use classic keyboard-navigable menu behavior.

See [docs/accessibility.md](docs/accessibility.md).
See [docs/toolchain.md](docs/toolchain.md) for the current build status and native driver requirements.
See [docs/dependencies.md](docs/dependencies.md) for local dependency paths.

## Current Build Status

This build currently contains the route model, feedback-guard smoke test, wxPython control panel, native ASIO driver package, and updater path. The wxPython UI includes a readable Overview web view, quiet background device refresh, screen-reader routing settings, startup update-check settings, driver capability reporting, and a local diagnostics inbox for agent-readable reports. The WPF control app is retained as a secondary reference app. The native ASIO driver exposes the ASIOA 68-in and 68-out ASIO surface for ASIO-capable hosts when registered. A true Windows-visible speaker or microphone endpoint for WDM, WASAPI, DirectSound, and non-ASIO apps is the next native-driver milestone, along with production signing, per-application capture, the real-time effects host, and the VST3/CLAP bridge.

User documentation:

- [App user guide](docs/user-guide.md)
- [DAW and plug-in guide](docs/plugin-guide.md)

```powershell
dotnet build .\asioa-audio-router.sln
dotnet run --project .\src\ASIOA.Smoke\ASIOA.Smoke.csproj
py -V:Astral/CPython3.12.12 -m venv E:\Builds\asioa-audio-router\py312-venv
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe -m pip install -r .\src\ASIOA.Wx\requirements.txt
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe .\src\ASIOA.Wx\asioa_router_wx.py
```

## Primary Technical References

- Microsoft application loopback capture sample: https://learn.microsoft.com/en-us/samples/microsoft/windows-classic-samples/applicationloopbackaudio-sample/
- Microsoft WASAPI loopback recording: https://learn.microsoft.com/windows/win32/coreaudio/loopback-recording
- Steinberg VST3 SDK: https://github.com/steinbergmedia/vst3sdk
- VST3 developer portal: https://steinbergmedia.github.io/vst3_dev_portal/
