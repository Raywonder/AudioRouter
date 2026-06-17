namespace ASIOA.Core;

public enum AudioEndpointKind
{
    Application,
    PhysicalInput,
    PhysicalOutput,
    DawReturn,
    VirtualBus
}

public sealed record AudioEndpoint(
    string Id,
    string Name,
    AudioEndpointKind Kind,
    int ChannelStart,
    int ChannelCount,
    bool Enabled = true,
    bool MonitorEnabled = false,
    bool Muted = false,
    double VolumePercent = 100.0,
    int BufferOverrideSamples = 0,
    string Notes = "")
{
    public string AccessibleSummary
    {
        get
        {
            var enabled = Enabled ? "enabled" : "disabled";
            var monitor = MonitorEnabled ? "monitoring on" : "monitoring off";
            var mute = Muted ? "muted" : "not muted";
            var buffer = BufferOverrideSamples > 0 ? $"{BufferOverrideSamples} sample buffer override" : "smart buffer";
            return $"{Name}, {Kind}, channels {ChannelStart} through {ChannelStart + ChannelCount - 1}, {enabled}, {monitor}, {mute}, volume {VolumePercent:0} percent, {buffer}";
        }
    }
}
