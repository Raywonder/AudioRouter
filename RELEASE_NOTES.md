# ASIOA Audio Router 0.2.8

This hotfix makes driver capability reporting more honest and useful while ASIOA moves toward its first real Windows-visible communication endpoint.

## Added

- Adds a driver capability map to the Overview and diagnostics output, covering ASIO host availability, the communication bridge model, Windows WDM/WASAPI/DirectSound endpoint exposure, per-application WASAPI capture, and system sound device routing.
- Detects whether any ASIOA-named Windows audio endpoint is actually visible to Windows, instead of assuming modeled bridge entries are real speaker or microphone devices.

## Changed

- Updates driver health wording to clearly distinguish the native ASIO driver from the future Windows speaker/microphone endpoint layer.
- Updates the installer agreement and wizard text so users know the current driver registers with ASIO-capable hosts, while normal Windows app endpoint support remains the next native-driver milestone.
- Keeps the install or repair button hidden when the ASIO driver is already registered and healthy.

# ASIOA Audio Router 0.2.7

This hotfix makes the control panel react faster and models the Windows-facing audio bridge more clearly for apps that need normal system audio endpoints.

## Added

- Adds the ASIOA Communication input/output 1/2 bridge as the default Windows-facing 2-in/2-out bus for apps that need a normal system audio endpoint.
- Adds WDM/WASAPI bridge pair endpoints for ASIO channel pairs so routing can model which stereo pairs should become Windows-visible pairs when the native driver layer exposes them.
- Keeps GitHub and Gitea manifest sources in the updater while public downloads come from the hosted ASIOA artifact path.

## Changed

- Settings autosave and hot-apply now run after half a second instead of three seconds.
- Volume sliders, buffer controls, choices, and toggles update the running control model immediately and announce the changed value.
- Built-in sounds stay quiet while the control panel is open; they are reserved for minimized/tray and close/save confirmation behavior.

# ASIOA Audio Router 0.2.6

This hotfix cleans up routing and plug-in-rack accessibility so the control panel behaves more like a real audio router instead of a generic list editor.

## Added

- Windows sound devices discovered from the system are added as routable input and output endpoints, making them available in the Routing tab's source and destination selectors.
- The Routing tab now has route source and destination combo boxes, plus an Add selected route button with feedback-loop protection.
- The Live Effects rack now supports adding VST3, CLAP, and legacy VST2 files, removing selected plug-ins, toggling bypass, and opening an accessible ASIOA control dialog for the selected plug-in.
- The selected plug-in controls dialog exposes target route, enabled state, bypass state, and accessible parameter sliders for values ASIOA stores and can hand to the engine.
- Update checking now reads the ASIOA update manifest, compares installed vs latest version, downloads newer installers or portable packages to Downloads, and asks before launching an installer.

## Changed

- Checkboxes are now opt-in for list controls. Input and output endpoint lists keep row checkboxes because they represent device/channel enable state; routing and plug-in rack lists use explicit action buttons instead.
- Input and output tabs now show more appropriate endpoint types instead of mixing every endpoint into the Inputs tab.
- Overview WebView content now refreshes only while the Overview tab is active, preventing screen readers from being pulled back to Overview while the user is working in another tab.

# ASIOA Audio Router 0.2.5

This build is packaged for hands-on local driver testing, not only control-panel preview.

## Added

- The release build now rebuilds and stages the native ASIOA driver package before creating the installer and portable zip.
- The installer and portable artifact names now use version 0.2.5 so this build is clearly newer than the previous 0.2.4 package.
- The packaged driver folder includes `ASIOA.Driver.dll`, `install-asioa-driver.ps1`, and `uninstall-asioa-driver.ps1` when the native build succeeds.

## Changed

- Public driver signing is still a separate requirement, but this package now includes the local registerable driver payload needed for hands-on DAW/app detection tests on this machine.
- The installer release agreement now matches the current package contents, including the packaged native driver option and the remaining signing and production limitations.

# ASIOA Audio Router 0.2.4

This hotfix improves keyboard focus, default routing policy, monitoring-device setup, and driver-install prompting.

## Added

- Route, input, and output lists now remember the last focused item. If focus moves to an action button, that button still acts on the remembered list item; if no item has ever been touched, the first row is selected silently.
- Route and endpoint action buttons now keep specific labels such as muting, unmuting, soloing, enabling, or lowering volume for the selected route or channel.
- Route, input, output, and effect lists now expose checkbox state where wxPython supports it, so enabled and disabled state can be changed from the list while add and remove actions remain outside the list.
- Action buttons now keep focus after activation, preserve the selected list item, and announce the exact changed item and state to screen readers.
- Default routing now includes Main output 1/2, System audio capture 1/2, a muted Primary microphone 7/8, Screen Reader Bus 61/62, TTS Bus 63/64, Communications Bus 65/66, Emergency Accessibility Bus 67/68, and Sessionwire guard endpoints.
- Monitoring settings now include the default monitoring output device, system audio master pair, and screen-reader/TTS default pair.
- Devices now include a Sessionwire white-noise guard setting and threshold for the audio engine policy.
- Overview and diagnostics now show the current monitor device, master pairs, protected bus policy, and Sessionwire guard state.

## Changed

- The control panel no longer opens a driver-install prompt on every normal launch. Driver installation is offered during setup, and the Overview tab only shows install or repair when a packaged driver is present and the installed driver is missing or unhealthy.
- Driver health now checks Windows ASIO registry registration and the registered driver DLL path instead of trusting only a local marker file.
- The main app no longer shows the system driver installation preference selector. That choice stays in the installer wizard.
- The obvious DAW or master output 1/2 to capture or input 1/2 feedback path is disabled and muted when settings load with feedback protection enabled.
- Microphones are muted and monitoring-off by default on a fresh profile, but saved user choices are not forcibly reset on later launches.

## Notes

- This release updates the control-panel routing policy and packaged app metadata. Real system-wide capture, driver signing, and sample-level white-noise detection still depend on the native audio engine and signed driver path being installed and verified.

# ASIOA Audio Router 0.2.3

This release improves the Overview dashboard, driver-install flow, and live apply behavior.

## Added

- Overview tab now uses more natural line-by-line wording for driver status, buffer status, screen-reader routing, routes, endpoints, and effects.
- Overview web view no longer refreshes when the content has not changed, preventing screen readers from being pushed back to the top during background device refresh.
- Installer now asks how to handle the ASIOA system audio driver with three radio-button choices: install now, ask later, or control panel only.
- Overview and Devices tabs now expose a one-time install or repair button for the ASIOA system audio driver.
- Apply to engine now writes an engine patch file and only requests an audio engine restart when driver or buffer-critical settings changed.
- Background plug-in scanning now counts installed VST3, CLAP, and legacy VST2 plug-ins even when live effects processing is disabled.
- Settings now autosave and hot-apply after a short quiet delay when controls change.
- Closing the control panel now flushes pending settings automatically.
- Settings backups are written as readable `.flx` files and compressed `.flxx` files in the user's ASIOA settings backup folder.
- Recent status messages now appear inside the Overview tab instead of a separate read-only status console.
- Native ASIO driver source has been added under `src\ASIOA.Driver` with COM/ASIO registration hooks, 68 input and 68 output metadata, protected channel names, sample-rate/buffer reporting, and safe silence behavior until the engine transport is connected.
- Driver packaging scripts now stage `ASIOA.Driver.dll` with register/unregister scripts when a native DLL is built or supplied.

## Notes

- This build prepares the control-panel and installer flow for the signed ASIOA system driver. If the signed driver package is not bundled, the app clearly says so and keeps the control panel available for routing, smart-buffer, accessibility, and diagnostics setup.
- The current Windows build machine is missing MSVC headers and `vcvarsall.bat`, so local native driver compilation is blocked until the Visual Studio C++ workload is repaired. Driver staging has been verified with a supplied DLL path.

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
