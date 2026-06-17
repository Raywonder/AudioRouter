# Shared Memory Transport

The ASIO driver and engine exchange real-time buffers through shared memory.

Regions:
- Audio buffers.
- Control messages.
- Telemetry.
- Heartbeats.

The UI is never in the audio data path.
