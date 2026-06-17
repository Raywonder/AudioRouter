# ASIOA Audio Router 0.2.2

This release improves the wxPython control panel around readable status, screen-reader routing, and quiet background refresh.

## Added

- Overview tab now uses one readable HTML status view instead of several read-only detail boxes.
- Startup announcement is sent to NVDA through `nvdaControllerClient64.dll` when the DLL is available beside the app.
- Accessibility tab now includes screen-reader output routing choices, direct ASIOA screen-reader capture options, and a single checkbox for built-in sounds.
- Startup tab now includes automatic update-check settings, update channel, and update source selection.
- Diagnostics tab can save reports to a hidden local agent inbox under the user's ASIOA AppData folder.
- Device information now refreshes quietly in the background; there is no manual refresh button.
- Bundled OpenLink-derived cue sounds for online, offline, connect, disconnect, message received, notification, success, and error events.

# ASIOA Audio Router 0.2.1

This release folds in the revised ASIO Audio Router Design Bible v1.0 as the implementation source of truth.

## Added

- Accessible status console that records route, buffer, device, diagnostics, and command activity.
- Ctrl+Shift+P command palette for quick routing and control commands.
- Accessibility tab documenting protected buses for screen reader, TTS, communications, and emergency accessibility audio.
- Core Smart Buffer telemetry and decision model with Stable, Monitoring, Warning, Recovery, Protected, and Manual Lock states.
- Protected channel names for screen reader 61/62, TTS 63/64, communications 65/66, and emergency accessibility 67/68.
- Release build now keeps PyInstaller work files under `E:\Builds` instead of the source folder.

# ASIOA Audio Router 0.2.0

This release switches the primary Windows control panel to wxPython and expands the routing, device, smart-buffer, and effects-control model.

## Included

- Primary wxPython control panel that opens as `ASIOA Audio Router 0.2.0`.
- Classic menu bar, native tabs, accessible list controls, buttons, checkboxes, combo boxes, and sliders.
- Tabs for Overview, Routing, Inputs, Outputs, Monitoring, Smart Buffer, Devices, Live Effects, Startup, and Diagnostics.
- Driver mode selector for ASIOA Native, auto mode, miniaudio/WASAPI, PortAudio, JACK, ASIO4ALL compatibility, WASAPI exclusive, and WASAPI shared.
- Smart buffer settings for mode, sample rate, start/min/max buffer, target latency, jitter safety, dropout recovery, auto-raise on dropouts, and auto-lower after stable playback.
- Live effects controls with VST3 and CLAP preferred; VST2 is legacy and off by default.
- 68 input and 68 output channel route model.
- Feedback guard that blocks DAW master 1/2 from routing back into capture input 1/2.
- WPF control app retained as a secondary prototype.
- Packaged README, license, third-party notices, and docs.

## Not Included Yet

This release does not install the native virtual ASIO driver, kernel driver, per-application capture service, live plug-in host, or VST3/CLAP bridge binaries. Those components still require native implementation, licensing review, and signing before distribution.

# ASIOA Audio Router 0.1.0

This is the first installable Windows control-app release.

## Included

- Accessible WPF control app for DAW input channels, DAW output channels, and route summaries.
- 68 input and 68 output channel route model.
- Feedback guard that blocks DAW master 1/2 from routing back into capture input 1/2.
- Route controls for adding a safe route, muting/unmuting, adjusting gain, and removing routes.
- Buffer and sample-rate settings with validation.
- Startup setting that writes the user-level Windows startup entry.
- Settings persistence under the current user's AppData folder.
- Installer output without test-package naming.
- Packaged README, license, third-party notices, and docs.

## Not Included Yet

This release does not install a native virtual ASIO driver, kernel driver, per-application capture driver, or VST3 bridge. Those components still require native implementation, licensing review, and signing before distribution.
