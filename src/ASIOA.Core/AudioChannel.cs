namespace ASIOA.Core;

public enum AudioChannelDirection
{
    InputToDaw,
    OutputFromDaw
}

public sealed record AudioChannel(
    int Number,
    string Name,
    AudioChannelDirection Direction,
    bool IsStereoLeft = false,
    bool IsStereoRight = false)
{
    public string AccessibleName =>
        $"{Name}, channel {Number}, {(Direction == AudioChannelDirection.InputToDaw ? "input to DAW" : "output from DAW")}";
}

