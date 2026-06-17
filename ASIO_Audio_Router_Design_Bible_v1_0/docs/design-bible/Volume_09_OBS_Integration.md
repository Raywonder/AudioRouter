# Volume 09 - OBS Integration, Multi-Track Recording, Broadcast Buses, Stream Mixes, and Creator Workflows

## Purpose

OBS is a primary target workflow for ASIO Audio Router.

The goal is to replace "Desktop Audio plus Mic" with clean, independent, multi-track routing.

## OBS Routing Model

Example:

- 1/2: Main monitor.
- 3/4: Chrome.
- 5/6: VoiceLink or communications.
- 7/8: Microphone.
- 21/22: TCast.
- 61/62: Screen Reader Bus, excluded by default.
- 63/64: TTS Bus, excluded by default.
- 65/66: Stream Mix.
- 67/68: Emergency Accessibility Bus.

## Default Privacy

Screen reader and TTS buses are not included in OBS output unless explicitly enabled.

## Stream Mix

The Stream Mix is separate from Monitor Mix and Recording Mix.

A user may hear screen reader audio locally while OBS does not receive it.

## Multi-Track Recording

OBS can receive separate stems:

- Mic.
- Chrome.
- VoiceLink.
- TCast.
- Music.
- Program Mix.
- Broadcast Mix.
- Recording Mix.

## Scene Automation

Future hooks:

OBS scene changed -> ASIO Router scene changed.

Examples:

- Starting Soon: mute mic, music to stream.
- Live: enable mic and communications.
- Interview: enable VoiceLink routes.
- Ending: disable recording and fade music.

## Accessibility

All OBS integration settings must be available through the wxPython UI, command palette, and text manual.

## Success Criteria

A user can stream and record separate tracks, exclude private accessibility audio, route apps independently, and recover from routing errors without VoiceMeeter.
