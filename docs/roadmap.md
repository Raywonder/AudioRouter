# Roadmap

## Phase 1: Route Model And Accessible UI Prototype

- Build channel and route model.
- Enforce the default feedback guard.
- Build WPF prototype with accessible lists/tables.
- Add startup/tray settings.
- Add mute, volume, monitor, and bypass state.

## Phase 2: WASAPI Capture Prototype

- Capture a selected process using process loopback.
- Capture endpoint loopback as fallback.
- Capture selected physical inputs.
- Resample to the engine rate.
- Route one stereo app into a mock DAW input bus.

## Phase 3: Virtual ASIO Driver

- Expose 68 input and 68 output channels.
- Publish stable channel names.
- Support 44.1, 48, 88.2, 96, 176.4, and 192 kHz where practical.
- Support configurable buffer sizes.
- Stage built driver DLLs into the installer publish folder for local registration tests.
- Sign the driver before public distribution.

## Phase 4: VST3 Bridge Plug-In

- Add a DAW plug-in that connects to the ASIOA engine.
- Expose status, meters, route controls, and automatable parameters.
- Provide an accessible fallback editor.

## Phase 5: Public Release

- Installer.
- Driver signing.
- First-run setup wizard.
- NVDA/Narrator test pass.
- DAW test pass in Ableton Live, REAPER, and other ASIO/VST3 hosts.
