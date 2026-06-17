# Volume 01 - Product Vision, Core Principles, Design Goals, Accessibility Philosophy, and System Requirements

## Purpose

This volume defines why ASIO Audio Router exists and what every future design decision must protect.

ASIO Audio Router is an accessibility-first Windows audio routing platform for creators, streamers, podcasters, broadcasters, blind users, accessibility trainers, VoiceLink hosts, TCast users, OBS users, and advanced audio workflows.

The first goal is not to be flashy. The first goal is to be reliable, understandable, and usable without sighted assistance.

## Problem Statement

Current Windows audio-routing tools are often built around visual patch bays, unlabeled sliders, complex virtual mixers, and mouse-driven controls. Many tools work for sighted audio engineers, but become painful or impossible for blind users using NVDA, JAWS, or Narrator.

Common problems include:

- Unlabeled controls.
- Visual-only meters.
- Mouse-only patching.
- Confusing device names.
- Routes that reset after reboot.
- Screen reader audio accidentally entering streams or recordings.
- Manual buffer tuning that most users do not understand.
- Inaccessible plug-in interfaces.
- No clear recovery when devices disconnect.
- No safe emergency mute workflow.

ASIO Audio Router exists to solve these problems with a design that treats accessibility as infrastructure.

## Mission

Build the most accessible professional audio routing platform available for Windows.

The platform should allow a blind creator to install, route, record, stream, monitor, diagnose, recover, and continue working without requiring sighted assistance.

## Priority Order

Every future feature must be judged in this order:

1. Accessibility.
2. Reliability.
3. Audio quality.
4. Performance.
5. Flexibility.
6. Features.
7. Visual polish.

A visually attractive feature that is inaccessible is incomplete. A fast feature that can crash the audio engine is unacceptable. A powerful route that can create feedback without warning must be blocked by default.

## Primary Product Goals

ASIO Audio Router must provide:

- A 68 input / 68 output virtual ASIO routing system.
- A user-mode audio engine separated from the UI.
- A wxPython control panel optimized for NVDA, JAWS, and Narrator.
- WASAPI app capture and per-application routing.
- Smart I/O device detection and automatic device profiles.
- Smart Buffer adaptive latency management.
- CLAP and VST3 plug-in hosting.
- Accessible plug-in parameter controls.
- Independent screen reader, TTS, communications, monitoring, notification, program, recording, and broadcast audio classes.
- Safe feedback prevention.
- Preset and project restoration.
- OBS workflows.
- Future hooks for VoiceLink and TCast without making the first release depend on those apps.

## Audio Classes

Not all audio is equal. The engine must understand audio classes as first-class route categories.

The initial audio classes are:

1. Program Audio.
2. Communications Audio.
3. Screen Reader Audio.
4. TTS Audio.
5. Monitoring Audio.
6. Notification Audio.
7. Recording Audio.
8. Broadcast Audio.
9. Emergency Accessibility Audio.

Each class must be independently routable, monitorable, recordable, streamable, controllable, muted, soloed, persisted, and protected.

## Screen Reader Audio Rule

Screen reader audio is a first-class protected audio source.

Screen readers include:

- NVDA.
- JAWS.
- Narrator.
- Future VoiceOver or other accessibility tools.

By default, screen reader audio must not enter OBS, streams, recordings, VoiceLink send paths, or public broadcast outputs.

Recommended internal pair:

- 61/62: Screen Reader Bus.

The user may intentionally route screen reader audio to Main 1/2, headphones, a virtual device, or another output, but this must never happen by accident.

## TTS Audio Rule

TTS audio is not always screen reader audio.

TTS may come from:

- OpenClaw.
- AI assistants.
- VoiceLink assistant.
- Cloud TTS.
- Automation announcements.
- Future agents.

Recommended internal pair:

- 63/64: TTS Bus.

TTS should have independent routing from screen readers so an AI assistant can be heard by the creator without leaking into a stream unless the user intentionally enables it.

## Communications Audio Rule

Communications audio includes apps like VoiceLink, Discord, Zoom, Teams, softphones, and communication clients.

Recommended internal pair:

- 65/66: Communications Bus.

Communications audio often needs to be heard by the host but excluded from public output, or recorded separately for editing.

## Emergency Accessibility Bus

Critical warnings, emergency mutes, clipping alerts, feedback warnings, and severe device failures need a protected notification path.

Recommended internal pair:

- 67/68: Emergency Accessibility Bus.

This bus should remain available even when the rest of the routing system is in Safe Mode.

## Main Output Rule

Outputs 1/2 are Main Out.

Main Out is the primary monitor/program output. It must be protected from accidental self-loopback and feedback. No source should automatically self-route into Main Out in a way that creates a loop.

Inputs 1/2 should not self-loop to outputs 1/2 by default.

## Smart I/O Vision

When an audio device appears, the system should detect, classify, profile, and restore it.

Example:

A Rodecaster Pro 2 is connected. The system learns:

- Input 1: Host Mic.
- Input 2: Guest Mic.
- Output 1/2: Studio Monitors.
- Output 3/4: Stream Feed.
- Output 5/6: Headphones.
- Preferred screen reader destination: Headphones.

Next time the device is connected, the profile restores automatically.

## Smart Buffer Vision

Users should not need to manually understand callback pressure, buffer sizes, sample rates, drift, underruns, or plug-in CPU cost to get stable audio.

Smart Buffer should observe the system and tune latency safely. It should increase buffer size when needed and reduce it only after sustained stability.

## Accessibility Success Definition

A blind creator can:

- Install the software.
- Identify devices.
- Set a default microphone.
- Set a default monitor.
- Route a screen reader to headphones.
- Keep TTS separate from program audio.
- Route Chrome to a pair.
- Route OBS to a recording bus.
- Load a mic processing rack.
- Enable Smart Buffer.
- Recover from device disconnects.
- Export diagnostics.

without sighted assistance.

## First Release Scope

The first release should focus on the ASIO Router core:

- wxPython UI shell.
- Native C++ audio engine.
- 68x68 internal routing model.
- Screen Reader Bus.
- TTS Bus.
- Smart I/O model.
- Smart Buffer model.
- Feedback prevention.
- Configuration persistence.
- Basic WASAPI detection.
- ASIO driver design and registration path.
- Codex-friendly architecture docs.

VoiceLink, TCast, marketplace, cloud sync, AI assistant, and network audio are future hooks. They must not distract from the first ASIO Router foundation.
