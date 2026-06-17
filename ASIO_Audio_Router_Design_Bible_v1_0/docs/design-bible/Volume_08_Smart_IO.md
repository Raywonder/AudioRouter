# Volume 08 - Smart I/O Detection, Device Profiles, Default Routing, Accessibility Devices, and Automatic Recovery

## Purpose

Smart I/O makes audio device management sane.

When users connect microphones, interfaces, headsets, virtual devices, or accessibility devices, the system should detect, classify, profile, and restore them.

## Device Classes

- Microphone.
- Headphones.
- Speakers.
- Audio Interface.
- Mixer.
- Virtual Device.
- Accessibility Device.
- Broadcast Device.
- Unknown.

## Device Events

- Connected.
- Removed.
- Renamed.
- Driver changed.
- Sample rate changed.
- Clock changed.
- Channel count changed.
- Health degraded.

## Device Profile

Store:

- Device ID.
- Friendly name.
- User label.
- Input names.
- Output names.
- Default role.
- Sample rate.
- Buffer.
- Accessibility routing.
- TTS routing.
- Monitor routing.
- Recording routing.
- Fallback device.

## Default Devices

User can choose:

- Preferred input.
- Preferred output.
- Preferred monitor.
- Preferred recording device.
- Preferred screen reader output.
- Preferred TTS output.
- Preferred communications output.
- Emergency accessibility output.

## Smart Device Wizard

When a new device appears, ask:

"What is this device?"

Choices:

- Microphone.
- Headphones.
- Speakers.
- Audio Interface.
- Mixer.
- Virtual Device.
- Accessibility Device.
- Broadcast Device.
- Not sure.

Then ask for role and labels.

## Example

USB headset connected.

Classified as:

- Microphone input.
- Headphone output.
- Possible accessibility output.

User chooses:

- Use headphones for screen reader and TTS.
- Do not include screen reader in stream.

Stored forever.

## Recovery

When a device disconnects:

- Pause affected routes.
- Use fallback if configured.
- Announce.
- Restore when device returns.

## Success Criteria

Users can connect devices, choose defaults, rename channels, route screen reader/TTS independently, and recover automatically when hardware changes.
