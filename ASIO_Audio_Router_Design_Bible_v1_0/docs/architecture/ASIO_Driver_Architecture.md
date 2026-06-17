# Volume 03 - ASIO Driver, Virtual Device, WASAPI Capture, Clock Domains, Shared Memory, and Feedback Prevention Architecture

## Purpose

This volume defines the low-level transport architecture for the Windows ASIO Router.

The virtual ASIO layer exposes 68 inputs and 68 outputs to DAWs and compatible applications while the external Audio Engine performs routing, policy, and processing.

## ASIO Driver Role

The ASIO driver exposes virtual channels to ASIO hosts such as REAPER, Cubase, Studio One, Ableton Live, OBS ASIO plug-ins, and ASIO-capable builds of other software.

The driver should not perform complex routing or UI functions.

It should:

- Register with ASIO hosts.
- Report driver name and version.
- Report channel count.
- Report channel names.
- Report buffer sizes.
- Report sample rates.
- Exchange audio buffers.
- Report latency.
- Communicate with the Audio Engine.

It should not:

- Scan plug-ins.
- Save user settings.
- Render UI.
- Call cloud services.
- Apply license policy on the callback.
- Run screen reader logic.

## Channel Layout

Inputs: 68 channels.

Outputs: 68 channels.

Default interpretation:

- 1/2: Main Out / protected main monitor.
- 3/4: Application Pair 1.
- 5/6: Application Pair 2.
- 7/8: Primary Microphone.
- 9/10: Secondary Microphone.
- 11/12: VoiceLink or communications source.
- 13/14: Discord or secondary communications.
- 15/16: Browser media.
- 17/18: System audio.
- 19/20: Recording bus.
- 21-60: Dynamic app/device/production pairs.
- 61/62: Screen Reader Bus.
- 63/64: TTS Bus.
- 65/66: Communications Bus.
- 67/68: Emergency Accessibility Bus.

Users may rename and reassign pairs, but default privacy rules must remain intact.

## Main Output Protection

Outputs 1/2 are special.

Rules:

- Do not automatically self-loop input 1/2 to output 1/2.
- Do not route captured Main Out back into itself.
- Do not monitor app captures into the same endpoint they came from unless the user explicitly allows it.
- Emergency mute must always be able to mute Main Out.

## Shared Memory Transport

The driver and engine should exchange real-time audio through shared memory.

Suggested regions:

- Audio buffers.
- Control messages.
- Telemetry.
- Driver status.
- Engine heartbeat.

The UI must not be in the audio buffer path.

## Buffer Flow

ASIO Host -> ASIO Driver -> Shared Memory -> Audio Engine -> Routing Graph -> Shared Memory -> ASIO Driver -> ASIO Host.

## Clock Domains

The system may involve multiple clocks:

- ASIO device clock.
- WASAPI shared-mode clock.
- USB audio interface clock.
- Bluetooth device clock.
- VoiceLink stream clock.
- Future network audio clock.

Only one master clock should be selected.

Priority:

1. ASIO clock.
2. Professional USB audio interface.
3. WASAPI exclusive mode device.
4. WASAPI shared device.
5. Virtual/software clock.

All other sources must adapt.

## Drift Correction

WASAPI and ASIO streams may drift over time.

The engine must monitor expected frames vs actual frames and apply small resampling adjustments. It must avoid sudden drops or insertions unless recovery is required.

## WASAPI App Capture

The WASAPI Capture Manager detects audio sessions and routes per-application audio.

Track:

- Process ID.
- Process name.
- Executable path.
- Display name.
- Endpoint ID.
- Session state.
- Preferred route.
- Audio class.
- Privacy policy.

Example:

Chrome starts -> detected as Program Audio -> assigned to 3/4.

NVDA starts -> detected or user-classified as Screen Reader Audio -> assigned to Screen Reader Bus 61/62 -> output to user-selected headphones by default.

## App Route Persistence

Store per app:

- Friendly name.
- Executable path.
- Process name.
- Input pair.
- Output pair.
- Audio class.
- Gain.
- Mute.
- Monitor.
- Lock route.
- Include in recording.
- Include in stream.

## Feedback Prevention

Feedback prevention must exist below the UI level.

Before enabling any route, validate:

- Source endpoint.
- Destination endpoint.
- Graph loop risk.
- Monitor loop risk.
- Capture loop risk.
- Main Out loop risk.
- Accessibility privacy risk.

If unsafe, block and announce.

Example:

"Route blocked. Chrome capture would feed back into Main Out."

## Emergency Mute

Global command:

Ctrl+Shift+M.

Behavior:

- Mute all outputs.
- Preserve routes.
- Preserve settings.
- Keep emergency accessibility messages available if possible.
- Log the event.

## Failure Recovery

If the ASIO host crashes, the engine continues.

If the UI crashes, the engine continues.

If the engine disconnects, the driver outputs safe silence.

If a device disconnects, routes pause and restore when the device returns.

## Success Criteria

The driver exposes 68 inputs and 68 outputs, communicates with the Audio Engine safely, protects Main Out, supports app capture routing, maintains clock discipline, prevents common feedback loops, and supports protected accessibility buses.
