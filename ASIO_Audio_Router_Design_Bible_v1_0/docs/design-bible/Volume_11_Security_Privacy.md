# Volume 11 - Security Architecture, Privacy Framework, Permissions Model, and Trust Boundaries

## Purpose

Audio routing software can accidentally expose private audio. This volume defines privacy and security rules.

## Trust Zones

1. Audio Engine: highest trust.
2. Routing Service: high trust.
3. UI: controlled trust.
4. Plugin Host: medium/untrusted.
5. Cloud/Marketplace: restricted.
6. User imported presets: untrusted until validated.

## Screen Reader Privacy

Screen reader audio must not automatically enter:

- Streams.
- Recordings.
- Broadcast buses.
- VoiceLink sends.
- TCast publishing outputs.

User must explicitly opt in.

## TTS Privacy

TTS may contain private assistant responses. It must not enter public outputs unless explicitly routed.

## Plugin Security

Plugins are untrusted.

Prefer sandboxing or out-of-process hosting. A plugin crash must not crash the engine.

## Credentials

Encrypt:

- VoiceLink tokens.
- TCast tokens.
- WHMCS tokens.
- API keys.
- Cloud sync tokens.
- Marketplace credentials.

## Project Export Privacy

Projects should be exportable without secrets.

Export options:

- Include credentials: never by default.
- Include private device IDs: optional.
- Include diagnostics: optional.
- Include audio: never unless explicitly exporting recordings.

## Safe Mode

Safe Mode disables:

- Plugins.
- Automation.
- Marketplace content.
- Cloud sync.
- Nonessential routing.

Safe Mode keeps:

- Core routing.
- Accessibility output.
- Emergency mute.
- Diagnostics.
- Device selection.

## Success Criteria

The system protects private audio, credentials, accessibility traffic, and projects while allowing intentional advanced routing.
