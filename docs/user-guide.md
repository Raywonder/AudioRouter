# ASIOA Audio Router App User Guide

## What This App Does

ASIOA Audio Router is the control application for the ASIOA routing system. It manages DAW channels, application feeds, monitoring, buffering, startup behavior, and diagnostics.

The current build contains the stable routing model, accessible wxPython control surface, and a packaged native ASIO driver. If the installer package includes `ASIOA.Driver.dll`, the installer can register that packaged ASIO driver for ASIO-capable hosts. Windows may block unsigned driver binaries until an approved signing path is used. The driver capability map in the Overview shows what is installed, what is only modeled, and whether any ASIOA Windows speaker or microphone endpoint is actually visible to Windows.

Important: the ASIO driver is not the same as a Windows WDM, WASAPI, or DirectSound endpoint. Regular Windows apps will not see a new ASIOA microphone or speaker until the endpoint driver is installed and Windows loads it successfully. On Secure Boot machines, local test-signed endpoint drivers can be blocked with Code 52 until a Microsoft signing path is used.

## Starting The App

Run:

```powershell
E:\Builds\asioa-audio-router\py312-venv\Scripts\python.exe .\src\ASIOA.Wx\asioa_router_wx.py
```

Or launch the built executable:

```text
ASIOA Audio Router.exe
```

## Main Tabs

### Overview

Use this tab to review the current system state, selected driver mode, Smart Buffer state, protected accessibility buses, configured routes, device summary, update settings, diagnostics location, and feedback guard behavior. The Overview tab is one readable HTML status view instead of several separate read-only fields.

### Routing

Use this tab to review DAW input channels, DAW output channels, and configured routes.

- DAW Inputs are channels ASIOA sends into the DAW.
- DAW Outputs are channels the DAW sends back into ASIOA.
- Routes show source, destination, enabled state, mute state, monitoring state, and gain.

The `Test feedback guard` button verifies that DAW Master 1/2 cannot be routed back into Capture A 1/2 unless unsafe routing is explicitly enabled in a future advanced mode.

### Application Audio

Use this tab to see running Windows audio sessions. ASIOA shows the application name, process ID, current output label, volume, mute state, ASIOA route target, and state.

The volume and mute buttons act immediately on the selected Windows audio session. The route target selector saves where ASIOA should route that app once the native engine and audio-policy helper are active. If Windows does not expose an adjustable audio session for an app, ASIOA reports that in the status line instead of failing silently.

### Inputs

Use this tab to review and manage application captures, physical inputs, and virtual input buses. Each row exposes enabled state, monitoring state, mute state, volume, and buffer override.

### Outputs

Use this tab to review DAW returns, monitoring buses, and utility buses.

### Monitoring

Use this tab to choose whether ASIOA monitors audio directly or only passes audio through the DAW path.

- `Monitor directly in ASIOA`: listen from the router app/engine.
- `Bypass ASIOA monitoring and route through DAW only`: prevent local monitoring and let the DAW handle the audible path.

### Smart Buffer

Use this tab to choose driver mode, sample rate, starting buffer size, and smart buffer behavior.

Driver modes:

- ASIOA Native driver: the main intended system-wide virtual ASIO driver.
- Auto select best available: lets the engine choose the best available backend.
- miniaudio / WASAPI: lightweight WASAPI capture and playback path.
- PortAudio compatibility: broad compatibility path for unusual devices.
- JACK professional routing: optional professional patchbay backend.
- ASIO4ALL compatibility: fallback for systems already depending on ASIO4ALL.
- WASAPI exclusive and shared: Windows endpoint paths for direct device access.

Smart buffer modes:

- Ultra low latency: smallest practical buffer; raises quickly on dropouts.
- Balanced: default for stable DAW use.
- Stability: favors fewer dropouts over minimum latency.
- Streaming: favors continuous playback and capture.
- Manual: uses the chosen fixed buffer until changed.

Supported buffer sizes:

```text
16, 32, 64, 128, 256, 512, 1024, 2048 samples
```

Supported sample rates:

```text
44100, 48000, 88200, 96000, 176400, 192000 Hz
```

### Devices

Use this tab to review available devices and what each backend is meant to provide. Devices refresh automatically in the background, so there is no refresh button to press.

### Live Effects

Live effects are off by default. VST3 and CLAP are the preferred plug-in formats. VST2 is legacy and disabled by default because the SDK is end-of-life and licensing is not suitable for new public development.

### Startup

Use this tab to control Windows startup and tray behavior.

- Run ASIOA when Windows starts.
- Start minimized to system tray.
- Keep audio engine active when the window is closed.
- Automatically check for updates.
- Choose update channel and source. GitHub is primary until the server Gitea repository is reachable; when both are configured, matching GitHub and Gitea versions are preferred.

### Diagnostics

Use this tab to review diagnostics and save reports to the local hidden agent inbox under the user's ASIOA AppData folder.

### Accessibility

Use this tab to choose where screen-reader audio should go. You can leave it on the current default accessibility device, route it to the Windows default playback device, choose headphones, or route it through ASIOA protected buses such as Screen Reader Bus 61/62 or TTS Bus 63/64.

Direct ASIOA screen-reader capture is off by default. When enabled, separate checkboxes control whether screen-reader audio may be included in streams or recordings.

On launch, ASIOA announces the current enabled endpoints, route count, driver mode, Smart Buffer mode, and screen-reader route through NVDA when `nvdaControllerClient64.dll` is available beside the installed app.

The only sound setting is `Enable built-in background and action sounds`. ASIOA uses bundled OpenLink-derived cue sounds for online, offline, connect, disconnect, message received, notification, success, and error events so users can notice important changes while the app is minimized or TTS is silent. Individual sound files are not user-configurable in the UI.

## Keyboard Use

- Tab and Shift+Tab move through controls.
- Arrow keys move through lists.
- Enter activates focused buttons or opens focused item details when implemented.
- Space toggles checkboxes.
- Applications key opens context menus where available.
- Escape closes dialogs.
- Control+S saves settings.
- Control+D opens diagnostics.

## Screen Reader Notes

List items are written as complete route or channel summaries. For example:

```text
DAW Cue A Left to Capture A Left, enabled, not muted, monitoring on, gain -6 dB
```

The route list is the accessible alternative to a visual patchbay grid. Native wxPython tabs, menus, list controls, buttons, checkboxes, combo boxes, and sliders are used so NVDA and other Windows screen readers can read normal name, role, value, and state.
