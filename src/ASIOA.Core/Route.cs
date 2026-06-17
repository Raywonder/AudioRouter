namespace ASIOA.Core;

public sealed record Route(
    string Id,
    AudioChannel Source,
    AudioChannel Destination,
    bool Enabled = true,
    bool Muted = false,
    bool MonitoringEnabled = false,
    double GainDb = 0.0)
{
    public string AccessibleSummary
    {
        get
        {
            var enabled = Enabled ? "enabled" : "disabled";
            var muted = Muted ? "muted" : "not muted";
            var monitoring = MonitoringEnabled ? "monitoring on" : "monitoring off";
            return $"{Source.Name} to {Destination.Name}, {enabled}, {muted}, {monitoring}, gain {GainDb:0.#} dB";
        }
    }
}
