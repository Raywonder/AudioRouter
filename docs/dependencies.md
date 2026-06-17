# Dependencies

## Installed Locally

| Dependency | Path | Purpose |
|---|---|---|
| Portable CMake 4.2.6 | `E:\Tools\cmake-4.2.6-windows-x86_64` | Native configure/build |
| Portable Ninja 1.13.2 | `E:\Tools\ninja-1.13.2` | Native build system |
| Portable LLVM-MinGW 22.1.6 | `E:\Tools\llvm-mingw-20260519-ucrt-x86_64` | Native Windows C++ fallback toolchain |
| Steinberg ASIO SDK 2.3 | `E:\SDKs\asiosdk2.3\ASIOSDK2.3` | ASIO host/driver reference |
| Steinberg VST3 SDK | `E:\SDKs\vst3sdk` | Optional VST3 bridge plug-in |
| Microsoft ApplicationLoopback sample | `E:\SDKs\windows-classic-samples\Samples\ApplicationLoopback` | Per-process Windows audio capture reference |
| miniaudio | `E:\SDKs\miniaudio` | Audio device/mixing/resampling reference layer |

## Visual Studio Status

Visual Studio Community is installed, but the native C++ workload is incomplete:

- `vcvarsall.bat` is missing.
- Standard MSVC headers such as `algorithm` are missing from the detected MSVC include folder.
- Normal MSVC `lib\x64` CRT libraries are missing; only `lib\onecore\x64` CRT files were found.

Use the portable LLVM-MinGW toolchain until Visual Studio C++ is repaired.

## ASIO Licensing Note

The ASIO SDK includes `Steinberg ASIO Licensing Agreement.pdf`. Review and follow that license before redistributing driver binaries.

