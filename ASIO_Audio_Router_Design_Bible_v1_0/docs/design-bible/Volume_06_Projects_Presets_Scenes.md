# Volume 06 - Projects, Presets, Scenes, Rack Serialization, Macro Actions, and Workflow Automation

## Purpose

Users should not rebuild studios manually every session. ASIO Audio Router must remember complete workflows through projects, presets, scenes, macros, and templates.

## Preset Levels

1. Plugin Preset.
2. Rack Preset.
3. Route Preset.
4. Scene Preset.
5. Project Preset.
6. Accessibility Preset.
7. Device Profile Preset.

## Project File

Suggested extension:

.aarproject

Project stores:

- Routes.
- Devices.
- Smart I/O profiles.
- Smart Buffer profile.
- Plugin racks.
- Scenes.
- Macros.
- Accessibility bus settings.
- Screen reader and TTS routing.
- OBS setup.
- VoiceLink hooks.
- TCast hooks.

## Scenes

A scene is a snapshot of a production state.

Examples:

- Podcast Recording.
- OBS Stream.
- VoiceLink Host.
- TCast Production.
- Blind Creator Mode.
- Emergency Safe Mode.

## Macros

Macros automate multi-step workflows.

Example: Prepare VoiceLink.

- Load VoiceLink scene.
- Route communications to 65/66.
- Route screen reader to headphones.
- Route TTS to headphones.
- Enable recording bus.
- Load host mic rack.
- Announce ready.

## Undo and History

Minimum undo target: 50 actions.

Undo should support:

- Route changes.
- Plugin insertion/removal.
- Preset loading.
- Scene switching.
- Device profile edits.

## Auto Save

Default every 5 minutes.

Options:

- 1 minute.
- 5 minutes.
- 10 minutes.
- 30 minutes.
- Manual only.

## Crash Recovery

On restart, offer:

- Restore last stable session.
- Open safe mode.
- Load default routing.
- Export diagnostics.

## Export and Import

Export:

- Project.
- Rack.
- Preset.
- Scene.
- Device profile.
- Accessibility profile.
- Diagnostics bundle.

## Success Criteria

Users can save, restore, export, import, automate, and recover production environments without manually rebuilding routes.
