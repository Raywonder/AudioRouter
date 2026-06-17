# Volume 02 - Audio Engine Architecture, Routing Graph, Threading Model, Processing Pipeline, and Real-Time Systems

## Purpose

The Audio Engine is the heart of ASIO Audio Router. Every audio sample that is captured, routed, monitored, processed, recorded, or streamed eventually touches the engine.

The engine must remain independent from the UI. If the wxPython control panel closes, audio should continue or fail safely.

## Core Subsystems

The engine contains:

- Audio Core.
- Routing Graph.
- Channel Manager.
- Device Manager.
- Smart I/O Manager.
- Smart Buffer Manager.
- WASAPI Capture Manager.
- ASIO Transport Layer.
- Plugin Host Bridge.
- Monitoring Manager.
- Recording/Broadcast Bus Manager.
- Accessibility Event Bridge.
- Diagnostics Collector.

## Engine Responsibilities

The engine is responsible for:

- Routing audio.
- Managing graph state.
- Managing real-time audio callbacks.
- Tracking device state.
- Applying gain, mute, solo, pan, and bus assignment.
- Hosting or connecting to plug-in processing chains.
- Providing telemetry.
- Applying feedback prevention rules.
- Maintaining clock and buffer state.
- Persisting runtime route state through the configuration layer.

## Engine Non-Responsibilities

The engine must not:

- Render UI.
- Depend on wxPython.
- Show dialogs.
- Scan the marketplace.
- Validate licenses inside the audio callback.
- Perform cloud sync inside real-time paths.
- Make network calls on the audio thread.
- Log from the audio callback.
- Allocate memory in the audio callback.

## Thread Model

Recommended threads:

- Audio Thread: highest priority, real-time callback.
- Capture Thread: WASAPI app/device capture.
- Plugin Thread: plug-in processing and rack preparation.
- Device Watcher Thread: device change events.
- Smart Buffer Thread: telemetry analysis and staged buffer decisions.
- Accessibility Thread: screen reader/status event processing.
- IPC Thread: UI/service communication.
- Background Thread: scans, logs, diagnostics, config writes.

## Audio Thread Rules

The audio thread must never:

- Block.
- Sleep.
- Allocate heap memory.
- Log.
- Wait on a mutex.
- Access the UI.
- Open files.
- Call network APIs.
- Load or unload plug-ins.
- Resize buffers directly.

The audio thread should only process already prepared buffers, routes, and graph snapshots.

## Routing Graph

The Routing Graph represents all audio flow as nodes and edges.

Node types:

- Source Node.
- Gain Node.
- Pan Node.
- Meter Node.
- Processor Node.
- Plugin Rack Node.
- Bus Node.
- Monitor Node.
- Recorder Node.
- Output Node.

Example:

Chrome Source -> Gain -> Plugin Rack -> Broadcast Bus -> OBS Output.

## Graph Update Model

Routes are edited outside the audio callback. Changes are staged into a new graph snapshot. At a safe boundary, the engine swaps from the old graph snapshot to the new one.

This prevents partial graph updates from corrupting active audio.

## Audio Classes in the Engine

The engine must maintain audio class metadata for every source.

Examples:

- Chrome: Program Audio.
- VoiceLink: Communications Audio.
- NVDA: Screen Reader Audio.
- OpenClaw: TTS Audio.
- Critical warning: Emergency Accessibility Audio.

Routing policies are based on this metadata.

## Protected Buses

Recommended reserved buses:

- 61/62: Screen Reader Bus.
- 63/64: TTS Bus.
- 65/66: Communications Bus.
- 67/68: Emergency Accessibility Bus.

These can be user-configured, but defaults must protect privacy.

## Monitoring Architecture

Monitoring must be separate from recording and broadcast routing.

A user should be able to mute headphones without muting the stream. A user should be able to exclude screen reader audio from broadcast while still hearing it locally.

## Recording Architecture

Recording buses should be independent. OBS or future recorders should be able to receive:

- Program Mix.
- Communications Mix.
- Mic Track.
- App Track.
- TTS Track if user explicitly includes it.
- Screen Reader Track only if user explicitly includes it.

Default behavior excludes screen reader and accessibility/TTS audio from public outputs.

## Device Manager

The Device Manager tracks ASIO, WASAPI, USB, Bluetooth, virtual, and future network devices.

It stores:

- Device ID.
- Friendly name.
- User label.
- Device class.
- Input count.
- Output count.
- Supported sample rates.
- Preferred sample rate.
- Preferred buffer.
- Preferred role.
- Accessibility role.
- Health status.

## Smart I/O Pipeline

Device connected -> Identify -> Classify -> Match profile -> Apply defaults -> Create nodes -> Restore routes -> Announce status.

Example:

"Scarlett connected. Restored Host Mic, Studio Monitors, and Headphones."

## Accessibility Event Bridge

The audio engine emits structured events. It does not speak directly.

Example event:

- type: route_blocked
- severity: warning
- source: Chrome
- reason: feedback risk
- text: Chrome route blocked due to feedback risk.

The Accessibility Service converts this into status text and optional speech.

## Diagnostics

Diagnostics include:

- Underruns.
- Overruns.
- Drift events.
- Callback pressure.
- Plugin CPU cost.
- Device connect/disconnect events.
- Route changes.
- Feedback blocks.
- Screen reader bus changes.
- Smart Buffer actions.

Diagnostics must not disrupt audio.

## Success Criteria

The engine supports 68 inputs, 68 outputs, audio class routing, protected accessibility buses, Smart Buffer, Smart I/O, basic plug-in rack hooks, ASIO transport, WASAPI capture, monitoring, recording, and diagnostics while maintaining real-time safety.
