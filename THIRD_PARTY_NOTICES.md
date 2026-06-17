# Third-party notices

ASIOA Audio Router currently ships as a managed Windows control app, route model,
and documentation. This installer does not bundle Steinberg ASIO SDK
source, ASIO driver binaries, VST3 SDK source, or any third-party virtual audio
driver.

## Steinberg ASIO

Steinberg's open-source ASIO SDK path is GPLv3. A proprietary ASIO distribution
path requires using Steinberg's proprietary ASIO license terms. ASIOA does not
currently include or install an ASIO driver, so this installer is not an ASIO
driver distribution.

## Steinberg VST3 SDK

Steinberg VST3 SDK 3.8 and newer are available under the MIT license. If the
optional ASIOA VST3 bridge is implemented later, use VST3 SDK 3.8 or newer for
redistributable builds unless a different reviewed license path is documented.

## Microsoft .NET and WPF

The ASIOA desktop control app uses .NET/WPF. Self-contained installers may
include Microsoft .NET runtime components according to Microsoft's .NET license
terms.
