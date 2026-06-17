# Volume 12 - API Architecture, Codex Roadmap, Repository Structure, Testing Bible, and Future Extensions

## Purpose

This volume defines how other tools and Codex interact with the project.

## API Philosophy

VoiceLink, TCast, OBS helpers, OpenClaw, and future tools should use APIs, not simulated keyboard presses or UI scraping.

## API Categories

- Routes.
- Devices.
- Projects.
- Presets.
- Accessibility buses.
- Smart Buffer.
- Smart I/O.
- Diagnostics.

## Accessibility API Examples

GET /api/accessibility/buses

GET /api/accessibility/routes

POST /api/accessibility/screenreader/output

POST /api/accessibility/tts/output

POST /api/accessibility/emergency/mute

## Device API Examples

GET /api/devices

POST /api/devices/defaults

POST /api/devices/profiles

POST /api/devices/classify

## Codex Repository Layout

Required folders:

- docs/design-bible
- docs/architecture
- docs/accessibility
- docs/integrations
- docs/testing
- docs/api
- docs/future
- docs/decisions
- docs/codex_tasks
- schemas
- examples
- presets
- manual

## Codex Rules

Codex must:

- Work in small commits.
- Keep accessibility intact.
- Avoid real-time unsafe code.
- Avoid blocking the audio callback.
- Update docs when changing architecture.
- Add tests when adding features.

## Implementation Phases

1. Repository foundation.
2. wxPython UI shell.
3. C++ engine stub.
4. IPC ping.
5. Config loader.
6. 68x68 channel model.
7. Audio class model.
8. Screen Reader Bus.
9. TTS Bus.
10. Smart I/O profiles.
11. Smart Buffer telemetry.
12. ASIO driver skeleton.
13. WASAPI app detection.
14. Routing graph.
15. Feedback validator.
16. Plugin metadata model.
17. Rack model.
18. Preset model.
19. OBS workflow preset.
20. Diagnostics export.

## Testing Bible

Test:

- NVDA.
- JAWS.
- Narrator.
- Keyboard only.
- 44.1k, 48k, 96k.
- 64, 128, 256, 512, 1024 sample buffers.
- Device disconnect/reconnect.
- Plug-in crash.
- Route feedback attempts.
- OBS multitrack.
- Screen reader privacy.

## Success Criteria

The repository becomes a permanent memory source for Codex and future developers.
