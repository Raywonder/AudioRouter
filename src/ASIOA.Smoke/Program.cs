using ASIOA.Core;

var config = new RouterConfiguration();
var settings = new AudioEngineSettings();
settings.Validate();

Console.WriteLine($"ASIOA channel count: {config.ChannelCount} inputs, {config.ChannelCount} outputs");
Console.WriteLine($"Default buffer: {settings.BufferSizeSamples} samples at {settings.SampleRate} Hz");

try
{
    config.AddRoute(config.OutputsFromDaw[0], config.InputsToDaw[0]);
    Console.WriteLine("ERROR: feedback guard failed");
    return 1;
}
catch (InvalidOperationException ex)
{
    Console.WriteLine($"Feedback guard: {ex.Message}");
}

var safeRoute = config.AddRoute(config.OutputsFromDaw[2], config.InputsToDaw[0], gainDb: -6.0, monitoringEnabled: true);
Console.WriteLine(safeRoute.AccessibleSummary);
Console.WriteLine(config.InputsToDaw[0].AccessibleName);

return 0;

