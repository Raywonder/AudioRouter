# Volume 10 - VoiceLink and TCast Integration Hooks

## Purpose

ASIO Audio Router is focused on the driver and routing platform first. VoiceLink and TCast integrations are hooks for later, not first-release blockers.

## VoiceLink Hook Goals

Future VoiceLink integration should allow:

- Room mix routing.
- Participant routing.
- Background media routing.
- Recording bus routing.
- Monitoring bus routing.
- TTS/assistant routing.
- Accessibility notifications routing.

VoiceLink communications should normally use the Communications Bus 65/66 unless user config overrides it.

## VoiceLink Example

Host mic -> 7/8.
Guest 1 -> 9/10.
Guest 2 -> 11/12.
Room mix -> Communications Bus.
Screen reader -> 61/62 headphones only.
TTS assistant -> 63/64 headphones only.

## TCast Hook Goals

TCast may evolve from a podcast player into a production and publishing backend.

Future TCast integration should allow:

- Main playback route.
- Preview route.
- Chapter route.
- Crossfade route.
- Recording bus route.
- Publishing/export metadata.
- VoiceLink-to-TCast episode creation.

## TCast Backend Note

TCast backend may need upgrades to support production features instead of only playback.

Possible additions:

- User accounts.
- Subscriptions.
- Bookmarks.
- Recommendations.
- Publishing.
- Creator analytics.
- Cross-device sync.
- VoiceLink integration.
- Chapter metadata.
- Transcript storage.

## TCast Example

TCast playback -> 21/22.
TCast preview -> 23/24.
Host mic -> 7/8.
OBS stream mix -> 65/66.
Screen reader -> headphones only.

## Success Criteria

The ASIO Router core remains independent while reserving clean integration points for future VoiceLink and TCast workflows.
