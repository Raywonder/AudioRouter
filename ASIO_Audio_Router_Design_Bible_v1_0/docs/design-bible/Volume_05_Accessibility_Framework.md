# Volume 05 - Accessibility Framework, Screen Reader Interaction Models, Speech Feedback Systems, and Keyboard Navigation

## Purpose

Accessibility is the central differentiator of ASIO Audio Router. This volume defines how blind, low-vision, keyboard-only, and power users operate the system.

## Supported Screen Readers

Primary:

- NVDA.
- JAWS.
- Narrator.

Future:

- VoiceOver.
- Orca.

## UI Technology

The primary UI should use wxPython because it can work well with NVDA through accessible Python output and standard Windows accessibility behavior.

The UI must prefer standard controls:

- Buttons.
- Checkboxes.
- Combo boxes.
- Sliders.
- List views.
- Tree views.
- Menus.
- Dialogs.
- Notebooks/tabs.

Avoid custom owner-drawn controls unless they expose proper accessible roles, names, states, focus, and keyboard behavior.

## Accessibility Event Bus

The audio engine emits events to an accessibility event queue. The Accessibility Service converts events into status text and optional speech.

Event priorities:

1. Critical.
2. Warning.
3. Status.
4. Verbose.
5. Diagnostic.

Critical examples:

- Feedback detected.
- Engine stopped.
- Device disconnected.
- Emergency mute activated.

## Speech Modes

- Silent.
- Basic.
- Standard.
- Verbose.
- Developer.

Standard should be the default.

## Command Palette

Global command palette:

Ctrl+Shift+P.

Examples:

- route Chrome to 3/4.
- mute Main Out.
- load VoiceLink preset.
- route NVDA to headphones.
- enable Smart Buffer.
- open Smart I/O settings.
- export diagnostics.

## Screen Reader Bus Controls

Settings must include:

Screen Reader Bus:

- Output destination.
- Include in recording checkbox.
- Include in stream checkbox.
- Volume.
- Mute.
- Test speech.
- Route lock.

Default:

- Output: user-selected accessibility/headphone device.
- Include in recording: off.
- Include in stream: off.

## TTS Bus Controls

TTS Bus:

- Output destination.
- Include in recording.
- Include in stream.
- Volume.
- Mute.
- Source list.
- Route lock.

Default:

- Output: headphones or selected accessibility device.
- Include in recording: off.
- Include in stream: off.

## Meter Accessibility

Every meter must have text equivalents.

Examples:

- "Mic peak minus 12 dB."
- "Main output clipping."
- "Chrome silent."
- "VoiceLink near clip."

Meter announcement modes:

- Off.
- Manual query.
- Threshold based.
- Periodic.
- Developer.

Recommended default: threshold based.

## Keyboard Navigation

Required:

- Tab and Shift+Tab navigate controls.
- Arrow keys adjust values.
- Enter activates.
- Space toggles.
- Escape cancels.
- Ctrl+S saves.
- F1 opens context help.
- Ctrl+Shift+M emergency mute.

## Status Console

The app must include an accessible status console.

It should be searchable, copyable, exportable, and readable with screen readers.

Example entries:

- 10:31 Chrome routed to 3/4.
- 10:32 Screen Reader Bus routed to Headphones.
- 10:35 Plugin compressor inserted.
- 10:38 Smart Buffer increased to 256 samples.

## Accessibility Profiles

Profiles:

- Default.
- NVDA optimized.
- JAWS optimized.
- Narrator optimized.
- Minimal speech.
- Verbose speech.
- Developer speech.

## Success Criteria

A blind user can install, configure, route, monitor, record, stream, load plugins, save presets, recover from errors, and diagnose problems without sighted assistance.
