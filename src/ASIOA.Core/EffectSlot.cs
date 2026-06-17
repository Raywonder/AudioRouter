namespace ASIOA.Core;

public enum PluginFormat
{
    VST3,
    CLAP,
    VST2Legacy
}

public sealed record EffectSlot(
    string Id,
    string Name,
    PluginFormat Format,
    string TargetBus,
    bool Enabled = false,
    bool Bypassed = true,
    double WetPercent = 100.0,
    double GainDb = 0.0)
{
    public string AccessibleSummary
    {
        get
        {
            var enabled = Enabled ? "enabled" : "disabled";
            var bypass = Bypassed ? "bypassed" : "active";
            return $"{Name}, {Format}, target {TargetBus}, {enabled}, {bypass}, wet {WetPercent:0} percent, gain {GainDb:0.#} dB";
        }
    }
}
