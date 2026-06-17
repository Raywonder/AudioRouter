using System.IO;
using System.Text.Json;
using ASIOA.Core;

namespace ASIOA.App;

public sealed class AppSettings
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    public int SampleRate { get; set; } = 48000;

    public int BufferSizeSamples { get; set; } = 128;

    public bool RunOnStartup { get; set; }

    public bool StartMinimizedToTray { get; set; } = true;

    public bool KeepEngineActiveOnClose { get; set; } = true;

    public bool MonitoringEnabled { get; set; } = true;

    public bool BypassDawRouting { get; set; }

    public static string SettingsDirectory =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ASIOA Audio Router");

    public static string SettingsPath => Path.Combine(SettingsDirectory, "settings.json");

    public static AppSettings Load()
    {
        try
        {
            if (!File.Exists(SettingsPath))
            {
                return new AppSettings();
            }

            return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(SettingsPath)) ?? new AppSettings();
        }
        catch
        {
            return new AppSettings();
        }
    }

    public void Save()
    {
        Directory.CreateDirectory(SettingsDirectory);
        File.WriteAllText(SettingsPath, JsonSerializer.Serialize(this, JsonOptions));
    }

    public AudioEngineSettings ToAudioEngineSettings()
    {
        var settings = new AudioEngineSettings(
            SampleRate: SampleRate,
            BufferSizeSamples: BufferSizeSamples,
            RunOnStartup: RunOnStartup,
            StartMinimizedToTray: StartMinimizedToTray,
            MonitoringEnabled: MonitoringEnabled,
            BypassDawRouting: BypassDawRouting);
        settings.Validate();
        return settings;
    }
}
