ASIO AUDIO ROUTER DESIGN BIBLE V1.0

Purpose:
Accessible-first professional Windows audio routing platform.

Current focus:
ASIO Router core, 68 inputs, 68 outputs, accessible wxPython control panel, native C++ audio engine, protected screen reader bus, TTS bus, Smart Buffer, Smart I/O, ASIO driver, WASAPI capture, OBS workflows, and future hooks for VoiceLink and TCast.

Top reading files:
- ASIO_Router_Design_Bible.txt
- ASIO_Router_Design_Bible.htm

Codex source files:
- docs/design-bible
- docs/architecture
- docs/accessibility
- docs/integrations
- docs/testing
- docs/api
- docs/decisions
- docs/codex_tasks

Important rules:
- Screen reader audio is protected and excluded from recordings/streams by default.
- TTS audio is separate from screen reader audio.
- Outputs 1/2 are Main Out and protected.
- 61/62 are reserved by default for Screen Reader Bus.
- 63/64 are reserved by default for TTS Bus.
- 65/66 are reserved by default for Communications Bus.
- 67/68 are reserved by default for Emergency Accessibility Bus.
