namespace ASIOA.Core;

public sealed record AudioEngineSettings(
    int SampleRate = 48000,
    int BufferSizeSamples = 128,
    AudioDriverMode DriverMode = AudioDriverMode.Auto,
    SmartBufferMode SmartBufferMode = SmartBufferMode.Balanced,
    int MinimumBufferSamples = 64,
    int MaximumBufferSamples = 1024,
    int TargetLatencyMilliseconds = 8,
    int JitterSafetyMilliseconds = 12,
    int XrunRecoveryMilliseconds = 250,
    bool AutoRaiseBufferOnDropouts = true,
    bool AutoLowerBufferWhenStable = true,
    bool ProtectDawMasterFeedback = true,
    bool LiveEffectsEnabled = false,
    bool Vst3EffectsEnabled = true,
    bool ClapEffectsEnabled = true,
    bool Vst2EffectsEnabled = false,
    bool RunOnStartup = false,
    bool StartMinimizedToTray = true,
    bool MonitoringEnabled = true,
    bool BypassDawRouting = false)
{
    public static readonly int[] SupportedBufferSizes = [16, 32, 64, 128, 256, 512, 1024, 2048];

    public static readonly int[] SupportedSampleRates = [44100, 48000, 88200, 96000, 176400, 192000];

    public static readonly int[] SupportedLatencyTargets = [2, 4, 6, 8, 10, 12, 16, 24, 32, 48];

    public static readonly int[] SupportedSafetyMargins = [0, 2, 4, 8, 12, 16, 24, 32, 48, 64];

    public void Validate()
    {
        if (!SupportedSampleRates.Contains(SampleRate))
        {
            throw new ArgumentOutOfRangeException(nameof(SampleRate), "Unsupported sample rate.");
        }

        if (!SupportedBufferSizes.Contains(BufferSizeSamples))
        {
            throw new ArgumentOutOfRangeException(nameof(BufferSizeSamples), "Unsupported buffer size.");
        }

        if (!SupportedBufferSizes.Contains(MinimumBufferSamples))
        {
            throw new ArgumentOutOfRangeException(nameof(MinimumBufferSamples), "Unsupported minimum buffer size.");
        }

        if (!SupportedBufferSizes.Contains(MaximumBufferSamples))
        {
            throw new ArgumentOutOfRangeException(nameof(MaximumBufferSamples), "Unsupported maximum buffer size.");
        }

        if (MinimumBufferSamples > MaximumBufferSamples)
        {
            throw new ArgumentOutOfRangeException(nameof(MinimumBufferSamples), "Minimum buffer cannot be larger than maximum buffer.");
        }

        if (TargetLatencyMilliseconds < 1 || TargetLatencyMilliseconds > 250)
        {
            throw new ArgumentOutOfRangeException(nameof(TargetLatencyMilliseconds), "Target latency must be between 1 and 250 milliseconds.");
        }

        if (JitterSafetyMilliseconds < 0 || JitterSafetyMilliseconds > 250)
        {
            throw new ArgumentOutOfRangeException(nameof(JitterSafetyMilliseconds), "Jitter safety must be between 0 and 250 milliseconds.");
        }

        if (XrunRecoveryMilliseconds < 0 || XrunRecoveryMilliseconds > 5000)
        {
            throw new ArgumentOutOfRangeException(nameof(XrunRecoveryMilliseconds), "Dropout recovery time must be between 0 and 5000 milliseconds.");
        }
    }
}

public enum AudioDriverMode
{
    Auto,
    ASIOA,
    WASAPIExclusive,
    WASAPIShared,
    MiniAudio,
    PortAudio,
    Jack,
    ASIO4ALLCompatibility
}

public enum SmartBufferMode
{
    UltraLowLatency,
    Balanced,
    Stability,
    Streaming,
    Manual
}
