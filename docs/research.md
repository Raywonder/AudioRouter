# Research Notes

## Per-Application Audio Capture

Microsoft's application loopback capture sample demonstrates process-tree audio capture using `ActivateAudioInterfaceAsync`. It can capture a specific process and its child processes, or capture everything except that process tree. The documented requirement is Windows 10 build 20348 or later.

Source: https://learn.microsoft.com/en-us/samples/microsoft/windows-classic-samples/applicationloopbackaudio-sample/

## System Loopback

WASAPI loopback can capture the audio stream played by a rendering endpoint. It works in shared mode and does not require a hardware loopback device.

Source: https://learn.microsoft.com/windows/win32/coreaudio/loopback-recording

## VST3

VST3 is useful for the optional DAW bridge/control plug-in. The VST3 SDK supports multi-input/output plug-ins and dynamic I/O, but a VST3 plug-in is still hosted inside the DAW. It is not the right layer for global Windows per-app capture.

Sources:

- https://github.com/steinbergmedia/vst3sdk
- https://steinbergmedia.github.io/vst3_dev_portal/

## Practical Conclusion

The product should be built as:

- Windows capture/router service for per-app audio.
- Virtual ASIO driver for DAW integration.
- VST3 helper plug-in for DAW status/control.
- Accessible desktop app for routing and monitoring.

