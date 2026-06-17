# ASIOA DAW And Plug-In Guide

## Intended DAW Integration

ASIOA will integrate with a DAW in two ways:

1. Select the ASIOA virtual ASIO driver as the DAW audio device.
2. Optionally load the ASIOA VST3 bridge plug-in on a track or master bus for status and route control.

The driver is the main audio path. The VST3 bridge is a control and routing helper.

## DAW Channel Layout

In the DAW, ASIOA exposes up to 68 inputs and 68 outputs.

Recommended Ableton setup:

1. Open Ableton Live preferences.
2. Go to Audio.
3. Choose ASIO as the driver type.
4. Choose ASIOA Audio Router as the audio device.
5. Enable input channels 1 through 68 as needed.
6. Enable output channels 1 through 68 as needed.

Default routing:

- Inputs 1/2: first captured application or input pair.
- Outputs 1/2: DAW master return.
- Outputs 3/4 and higher: cue, stream, app, or monitor sends.

## Feedback Safety

ASIOA blocks DAW output 1/2 from routing directly into DAW input 1/2. This prevents the common feedback loop where the DAW master is recorded back into the first capture pair.

Use higher-numbered channels for DAW cue sends or app return feeds.

## Monitoring Modes

Direct monitoring:

- ASIOA plays selected feeds directly to the chosen monitor output.
- Useful for hearing an app before the DAW is armed.

DAW-only monitoring:

- ASIOA sends feeds into the DAW and does not monitor locally.
- Useful when all monitoring should come from Ableton, REAPER, or another DAW.

## VST3 Bridge Behavior

The planned VST3 bridge will:

- show ASIOA connection status
- expose meters and route names
- expose route mute, gain, monitor, and bypass controls
- provide an accessible fallback editor

It will not replace the ASIO driver for global per-application capture.

