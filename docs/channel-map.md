# Channel Map

Initial target: 68 input channels and 68 output channels.

## DAW Inputs

These are channels the DAW records or monitors from ASIOA.

| Channels | Default Name | Purpose |
|---|---|---|
| 1-2 | Capture A L/R | First stereo app/input capture pair |
| 3-4 | Capture B L/R | Second stereo app/input capture pair |
| 5-6 | Capture C L/R | Third stereo app/input capture pair |
| 7-8 | Capture D L/R | Fourth stereo app/input capture pair |
| 9-64 | Capture 5-32 L/R | Additional stereo app/input pairs |
| 65-68 | Utility 1-4 | Talkback, click, reference, or spare routing |

## DAW Outputs

These are channels the DAW sends into ASIOA.

| Channels | Default Name | Purpose |
|---|---|---|
| 1-2 | DAW Master L/R | Main DAW return to speakers, apps, and monitor |
| 3-4 | DAW Cue A L/R | Cue or alternate app feed |
| 5-6 | DAW Cue B L/R | Cue or alternate app feed |
| 7-8 | DAW Stream L/R | Stream/broadcast feed |
| 9-64 | DAW Sends 5-32 L/R | Additional stereo sends |
| 65-68 | Utility Returns 1-4 | Talkback, click, reference, or spare routing |

## Feedback Guard

The first DAW master output pair, channels 1-2, must not be routable into DAW input channels 1-2 by default. This prevents instant feedback when the DAW monitor path is active.

Advanced users may create explicit feedback-capable routes only after enabling an unsafe routing mode and acknowledging the risk. The default accessible UI should hide or disable those unsafe routes.

