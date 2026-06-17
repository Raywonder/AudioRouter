# Architecture

## Why This Needs More Than A Plug-In

A DAW plug-in can process audio that the DAW sends to it, but it cannot directly capture arbitrary Windows application audio by itself. Per-application capture lives on the Windows audio side, while DAW low-latency I/O lives on the ASIO/VST side.

ASIOA therefore uses a multi-component architecture:

1. Windows capture layer.
2. Real-time route/mix engine.
3. Virtual ASIO driver for DAWs.
4. Optional VST3/CLAP control, bridge, and live-effects host.
5. Accessible wxPython desktop control app, with the WPF prototype retained as a secondary shell.

## Windows Capture Layer

Use WASAPI process loopback for individual app capture where supported. Microsoft's application loopback sample documents process-tree include/exclude capture using `ActivateAudioInterfaceAsync`, and requires Windows 10 build 20348 or later.

Use normal WASAPI endpoint capture for physical microphones and interface inputs that are not exposed through the ASIO driver path.

## Driver Backend Modes

ASIOA Native is the primary intended driver mode. The control panel also models these backend modes so the engine can choose stable fallbacks where appropriate:

- miniaudio / WASAPI for lightweight Windows endpoint capture, playback, mixing, and full-duplex routing.
- PortAudio for broad compatibility with unusual devices and host APIs.
- JACK for advanced users who already use a professional routing graph.
- ASIO4ALL compatibility for systems that already depend on ASIO4ALL.
- WASAPI exclusive and shared for direct Windows endpoint access.

These are engine modes, not separate user-facing products.

## Smart Buffer Engine

The smart buffer controller tracks dropout/xrun events, jitter, clock drift, and stable playback windows.

Modes:

- Ultra low latency keeps the buffer low and reacts quickly to dropouts.
- Balanced is the default.
- Stability raises buffer limits and recovery hold time.
- Streaming prioritizes continuous playback and capture.
- Manual disables automatic buffer movement.

Smart buffer settings include minimum buffer, maximum buffer, target latency, jitter safety margin, dropout recovery hold time, auto-raise on dropouts, and auto-lower after stable playback.

## Real-Time Engine

The audio engine should be native C++:

- lock-free ring buffers
- no allocation on audio callbacks
- fixed block-size processing when possible
- sample-rate conversion when a source does not match the DAW engine rate
- 32-bit float internal mix bus
- per-route gain, mute, phase, pan, and monitor flags

## ASIO Driver

The virtual ASIO driver exposes the DAW-facing channel set:

- 68 inputs to the DAW
- 68 outputs from the DAW
- configurable sample rate
- configurable buffer size
- stable channel names
- feedback guard metadata enforced by the router engine

The driver must be signed for normal Windows distribution.

## VST3 And CLAP Bridge Plug-Ins

The VST3 and CLAP plug-ins are optional but useful:

- shows ASIOA status inside the DAW
- exposes automatable route gains and mute states
- can receive DAW audio as an insert/send path
- gives hosts a normal plug-in UI when the ASIO driver cannot be selected

The plug-ins cannot replace the capture service for per-app Windows audio.

## Live Effects Host

Live effects processing is off by default. VST3 and CLAP are preferred for new development. VST2 is treated as legacy and disabled by default because it is end-of-life and unsuitable as the main public plug-in path.

## Desktop App

The desktop app controls the engine and driver:

- route matrix
- application list
- physical device list
- input/output mute and gain
- monitor/bypass mode
- buffer/sample-rate settings
- startup and tray settings
- diagnostics and logs

The app should use wxPython as the primary Windows UI because it gives classic native menus, tabs, list controls, checkboxes, buttons, and dialogs that screen readers already understand. WPF remains as a secondary prototype until the wx control panel fully replaces it.
