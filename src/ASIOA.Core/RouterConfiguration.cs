namespace ASIOA.Core;

public sealed class RouterConfiguration
{
    public const int DefaultChannelCount = 68;

    private readonly List<AudioChannel> _inputsToDaw = new();
    private readonly List<AudioChannel> _outputsFromDaw = new();
    private readonly List<Route> _routes = new();

    public RouterConfiguration(int channelCount = DefaultChannelCount)
    {
        if (channelCount < 2 || channelCount % 2 != 0)
        {
            throw new ArgumentOutOfRangeException(nameof(channelCount), "Channel count must be an even number of at least 2.");
        }

        ChannelCount = channelCount;
        BuildDefaultChannels(channelCount);
    }

    public int ChannelCount { get; }

    public IReadOnlyList<AudioChannel> InputsToDaw => _inputsToDaw;

    public IReadOnlyList<AudioChannel> OutputsFromDaw => _outputsFromDaw;

    public IReadOnlyList<Route> Routes => _routes;

    public bool UnsafeFeedbackRoutesEnabled { get; private set; }

    public void SetUnsafeFeedbackRoutesEnabled(bool enabled) => UnsafeFeedbackRoutesEnabled = enabled;

    public Route AddRoute(AudioChannel source, AudioChannel destination, double gainDb = 0.0, bool monitoringEnabled = false)
    {
        if (IsProtectedFeedbackRoute(source, destination) && !UnsafeFeedbackRoutesEnabled)
        {
            throw new InvalidOperationException("Feedback guard blocked routing DAW Master 1/2 back into Capture A 1/2.");
        }

        var id = $"{source.Direction}-{source.Number}-to-{destination.Direction}-{destination.Number}";
        var route = new Route(id, source, destination, GainDb: gainDb, MonitoringEnabled: monitoringEnabled);
        _routes.Add(route);
        return route;
    }

    public Route ToggleRouteMute(Route route)
    {
        var index = _routes.FindIndex(item => item.Id == route.Id);
        if (index < 0)
        {
            throw new InvalidOperationException("Route was not found.");
        }

        var updated = _routes[index] with { Muted = !_routes[index].Muted };
        _routes[index] = updated;
        return updated;
    }

    public Route SetRouteGain(Route route, double gainDb)
    {
        var index = _routes.FindIndex(item => item.Id == route.Id);
        if (index < 0)
        {
            throw new InvalidOperationException("Route was not found.");
        }

        var clamped = Math.Clamp(gainDb, -60.0, 12.0);
        var updated = _routes[index] with { GainDb = clamped };
        _routes[index] = updated;
        return updated;
    }

    public bool RemoveRoute(Route route)
    {
        return _routes.RemoveAll(item => item.Id == route.Id) > 0;
    }

    public bool IsProtectedFeedbackRoute(AudioChannel source, AudioChannel destination)
    {
        return source.Direction == AudioChannelDirection.OutputFromDaw
            && destination.Direction == AudioChannelDirection.InputToDaw
            && source.Number is 1 or 2
            && destination.Number is 1 or 2;
    }

    private void BuildDefaultChannels(int channelCount)
    {
        for (var i = 1; i <= channelCount; i++)
        {
            _inputsToDaw.Add(new AudioChannel(
                i,
                DefaultInputName(i),
                AudioChannelDirection.InputToDaw,
                IsStereoLeft: i % 2 == 1,
                IsStereoRight: i % 2 == 0));

            _outputsFromDaw.Add(new AudioChannel(
                i,
                DefaultOutputName(i),
                AudioChannelDirection.OutputFromDaw,
                IsStereoLeft: i % 2 == 1,
                IsStereoRight: i % 2 == 0));
        }
    }

    private static string DefaultInputName(int channel)
    {
        return channel switch
        {
            1 => "Capture A Left",
            2 => "Capture A Right",
            61 => "Screen Reader Bus Left",
            62 => "Screen Reader Bus Right",
            63 => "TTS Bus Left",
            64 => "TTS Bus Right",
            65 => "Communications Bus Left",
            66 => "Communications Bus Right",
            67 => "Emergency Accessibility Bus Left",
            68 => "Emergency Accessibility Bus Right",
            >= 65 => $"Utility Input {channel - 64}",
            _ => $"Capture {((channel - 1) / 2) + 1} {(channel % 2 == 1 ? "Left" : "Right")}"
        };
    }

    private static string DefaultOutputName(int channel)
    {
        return channel switch
        {
            1 => "DAW Master Left",
            2 => "DAW Master Right",
            3 => "DAW Cue A Left",
            4 => "DAW Cue A Right",
            5 => "DAW Cue B Left",
            6 => "DAW Cue B Right",
            7 => "DAW Stream Left",
            8 => "DAW Stream Right",
            61 => "Screen Reader Return Left",
            62 => "Screen Reader Return Right",
            63 => "TTS Return Left",
            64 => "TTS Return Right",
            65 => "Communications Return Left",
            66 => "Communications Return Right",
            67 => "Emergency Accessibility Return Left",
            68 => "Emergency Accessibility Return Right",
            >= 65 => $"Utility Return {channel - 64}",
            _ => $"DAW Send {((channel - 1) / 2) + 1} {(channel % 2 == 1 ? "Left" : "Right")}"
        };
    }
}
