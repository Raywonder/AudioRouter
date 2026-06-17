# Volume 04 - CLAP/VST3 Hosting Architecture, Crash Isolation, Accessibility Wrappers, Preset Serialization, and Plugin Management

## Purpose

Plug-in hosting transforms ASIO Audio Router from a virtual router into a creator production platform.

Users need EQ, compression, limiting, restoration, meters, loudness tools, and creative effects on microphones, applications, VoiceLink sources, TCast playback, OBS feeds, recording buses, and monitor buses.

## Supported Formats

Priority:

1. CLAP.
2. VST3.
3. VST2 only if licensing permits.

CLAP is preferred because it is modern and open. VST3 is required for broad compatibility. VST2 is optional and should not block the core product.

## Plugin Discovery

Default scan paths:

CLAP:

- C:\Program Files\Common Files\CLAP
- C:\Program Files\CLAP
- %LOCALAPPDATA%\Programs\CLAP

VST3:

- C:\Program Files\Common Files\VST3
- C:\Program Files\VST3

Users may add custom paths.

## Plugin Database

Store:

- Plugin ID.
- Name.
- Manufacturer.
- Version.
- Format.
- File path.
- Category.
- Input count.
- Output count.
- Latency samples.
- Last scan status.
- Crash count.
- Favorite flag.
- Accessibility rating.
- Parameter metadata.

## Plugin Validation

On scan:

- Verify file exists.
- Verify format.
- Load in a safe validation context.
- Query name and parameters.
- Query latency.
- Unload.
- Cache metadata.

If validation fails, mark failed and continue. One bad plug-in must not stop the entire scan.

## Crash Isolation

Plug-ins are untrusted.

The preferred design is out-of-process plug-in hosting or a sandbox layer. If a plug-in crashes, the audio engine should bypass the plug-in, preserve routes, report the issue, and continue audio.

User message:

"Plugin TDR Nova crashed and has been bypassed."

## Rack Architecture

Each route, channel pair, bus, or output may have a rack.

A rack supports up to 12 slots.

Each slot supports:

- Load.
- Remove.
- Bypass.
- Move up.
- Move down.
- Duplicate.
- Open accessible parameters.
- Save slot preset.

Processing order is top to bottom.

## Rack Types

- Channel Rack.
- Stereo Pair Rack.
- Bus Rack.
- Monitor Rack.
- Recording Rack.
- Broadcast Rack.
- Accessibility Bus Rack.
- TTS Bus Rack.

By default, screen reader and emergency accessibility buses should avoid heavy processing that may delay critical messages.

## Accessible Parameter Layer

Most plug-in GUIs are not accessible. Therefore, the host must expose parameters through its own accessible control panel.

Every parameter should provide:

- Name.
- Current value.
- Units.
- Minimum.
- Maximum.
- Default.
- Automation support.
- Group/category if available.

Keyboard controls:

- Arrow: adjust.
- Ctrl+Arrow: fine adjust.
- Shift+Arrow: coarse adjust.
- Home: minimum.
- End: maximum.
- Enter: edit numeric value.
- F1: help.

## Preset Serialization

Save:

- Rack name.
- Rack version.
- Slot order.
- Plugin IDs.
- Plugin paths.
- Parameter values.
- Bypass states.
- Wet/dry mix if supported.
- Latency metadata.
- Target bus/route.
- Audio class compatibility.

Presets must be versioned and migratable.

## Accessibility Rules

Do not require opening the vendor GUI.

Do not rely on visual meters.

Do not expose unlabeled parameters.

If a parameter name is missing, create a safe fallback such as "Parameter 12" and include plugin name context.

## Example Racks

Broadcast Mic Rack:

- Noise Gate.
- EQ.
- Compressor.
- De-Esser.
- Limiter.

TCast Playback Rack:

- EQ.
- Loudness Processor.
- Limiter.

VoiceLink Room Rack:

- High-pass filter.
- Compressor.
- Limiter.

## Success Criteria

The plug-in system scans CLAP/VST3 plug-ins, loads them safely, exposes accessible parameter controls, supports 12-slot racks, serializes presets, survives crashes, and never compromises real-time audio stability.
