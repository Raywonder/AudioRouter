namespace ASIOA.Core;

public enum SmartBufferState
{
    Stable,
    Monitoring,
    Warning,
    Recovery,
    Protected,
    ManualLock
}

public sealed record SmartBufferTelemetry(
    double AverageCallbackMilliseconds = 0,
    double PeakCallbackMilliseconds = 0,
    double CpuLoadPercent = 0,
    double PluginProcessingMilliseconds = 0,
    double WasapiDriftMilliseconds = 0,
    int Underruns = 0,
    int Overruns = 0,
    int MissedDeadlines = 0,
    int CaptureQueueDepth = 0,
    bool DeviceHealthDegraded = false)
{
    public bool HasInstability =>
        Underruns > 0
        || Overruns > 0
        || MissedDeadlines > 0
        || DeviceHealthDegraded
        || CpuLoadPercent >= 85
        || PeakCallbackMilliseconds >= 12;
}

public sealed record SmartBufferDecision(
    SmartBufferState State,
    int RecommendedBufferSamples,
    string Announcement,
    bool RequiresSafeBoundary = true);

public sealed class SmartBufferController
{
    public SmartBufferDecision Evaluate(AudioEngineSettings settings, SmartBufferTelemetry telemetry)
    {
        settings.Validate();

        if (settings.SmartBufferMode == SmartBufferMode.Manual)
        {
            return new SmartBufferDecision(
                SmartBufferState.ManualLock,
                settings.BufferSizeSamples,
                $"Manual buffer lock enabled at {settings.BufferSizeSamples} samples.");
        }

        if (telemetry.DeviceHealthDegraded)
        {
            return new SmartBufferDecision(
                SmartBufferState.Protected,
                settings.MaximumBufferSamples,
                $"Device health degraded. Smart Buffer protected mode recommends {settings.MaximumBufferSamples} samples.");
        }

        if (telemetry.HasInstability && settings.AutoRaiseBufferOnDropouts)
        {
            var raised = NextHigherBuffer(settings.BufferSizeSamples, settings.MaximumBufferSamples);
            return new SmartBufferDecision(
                SmartBufferState.Recovery,
                raised,
                $"Smart Buffer increased to {raised} samples due to underrun, overrun, or callback pressure.");
        }

        if (telemetry.CpuLoadPercent >= 70 || telemetry.CaptureQueueDepth > 3)
        {
            return new SmartBufferDecision(
                SmartBufferState.Warning,
                settings.BufferSizeSamples,
                "Smart Buffer is monitoring elevated CPU or capture queue pressure.");
        }

        if (settings.AutoLowerBufferWhenStable && settings.BufferSizeSamples > settings.MinimumBufferSamples)
        {
            var lowered = NextLowerBuffer(settings.BufferSizeSamples, settings.MinimumBufferSamples);
            return new SmartBufferDecision(
                SmartBufferState.Stable,
                lowered,
                $"Audio stable. Smart Buffer may reduce to {lowered} samples at the next safe boundary.");
        }

        return new SmartBufferDecision(
            SmartBufferState.Stable,
            settings.BufferSizeSamples,
            $"Audio stable at {settings.BufferSizeSamples} samples.");
    }

    private static int NextHigherBuffer(int current, int maximum)
    {
        return AudioEngineSettings.SupportedBufferSizes
            .Where(size => size > current && size <= maximum)
            .DefaultIfEmpty(maximum)
            .First();
    }

    private static int NextLowerBuffer(int current, int minimum)
    {
        return AudioEngineSettings.SupportedBufferSizes
            .Reverse()
            .Where(size => size < current && size >= minimum)
            .DefaultIfEmpty(minimum)
            .First();
    }
}
