using System.Windows;
using Microsoft.Win32;
using ASIOA.Core;
using System.Diagnostics;
using System.IO;

namespace ASIOA.App;

public partial class MainWindow : Window
{
    private readonly RouterConfiguration _router = new();
    private readonly AppSettings _settings = AppSettings.Load();
    private bool _loading;

    public MainWindow()
    {
        InitializeComponent();

        _loading = true;
        InputsList.ItemsSource = _router.InputsToDaw.ToList();
        OutputsList.ItemsSource = _router.OutputsFromDaw.ToList();
        RoutesList.ItemsSource = _router.Routes;
        SampleRateComboBox.ItemsSource = AudioEngineSettings.SupportedSampleRates;
        SampleRateComboBox.SelectedItem = _settings.SampleRate;
        BufferSizeComboBox.ItemsSource = AudioEngineSettings.SupportedBufferSizes;
        BufferSizeComboBox.SelectedItem = _settings.BufferSizeSamples;
        MonitoringCheckBox.IsChecked = _settings.MonitoringEnabled;
        BypassCheckBox.IsChecked = _settings.BypassDawRouting;
        RunOnStartupCheckBox.IsChecked = _settings.RunOnStartup;
        StartMinimizedCheckBox.IsChecked = _settings.StartMinimizedToTray;
        KeepEngineActiveCheckBox.IsChecked = _settings.KeepEngineActiveOnClose;
        _loading = false;

        SetStatus("ASIOA control app ready. Native ASIO driver is not installed in this release.");
    }

    private void AddSafeRoute_Click(object sender, RoutedEventArgs e)
    {
        var route = _router.AddRoute(_router.OutputsFromDaw[2], _router.InputsToDaw[0], gainDb: -6.0, monitoringEnabled: true);
        RefreshRoutes($"Added route. {route.AccessibleSummary}");
    }

    private void TestFeedbackGuard_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            _router.AddRoute(_router.OutputsFromDaw[0], _router.InputsToDaw[0]);
            SetStatus("Feedback guard failed. This route should have been blocked.");
        }
        catch (InvalidOperationException ex)
        {
            SetStatus(ex.Message);
        }
    }

    private void MuteRoute_Click(object sender, RoutedEventArgs e)
    {
        if (RoutesList.SelectedItem is not Route route)
        {
            SetStatus("No route selected.");
            return;
        }

        var updated = _router.ToggleRouteMute(route);
        RefreshRoutes(updated.AccessibleSummary);
    }

    private void RouteVolumeDown_Click(object sender, RoutedEventArgs e) => ChangeRouteGain(-3.0);

    private void RouteVolumeUp_Click(object sender, RoutedEventArgs e) => ChangeRouteGain(3.0);

    private void ChangeRouteGain(double deltaDb)
    {
        if (RoutesList.SelectedItem is not Route route)
        {
            SetStatus("No route selected.");
            return;
        }

        var updated = _router.SetRouteGain(route, route.GainDb + deltaDb);
        RefreshRoutes(updated.AccessibleSummary);
    }

    private void RemoveRoute_Click(object sender, RoutedEventArgs e)
    {
        if (RoutesList.SelectedItem is not Route route)
        {
            SetStatus("No route selected.");
            return;
        }

        _router.RemoveRoute(route);
        RefreshRoutes("Route removed.");
    }

    private void Settings_Click(object sender, RoutedEventArgs e)
    {
        SetStatus("Settings are available in the Monitoring, Buffering, and Startup tabs.");
    }

    private void SaveSettings_Click(object sender, RoutedEventArgs e)
    {
        SaveSettings();
    }

    private void Help_Click(object sender, RoutedEventArgs e)
    {
        var helpPath = Path.Combine(AppContext.BaseDirectory, "docs", "user-guide.md");
        if (!File.Exists(helpPath))
        {
            helpPath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "docs", "user-guide.md"));
        }

        if (!File.Exists(helpPath))
        {
            SetStatus("Help file was not found.");
            return;
        }

        Process.Start(new ProcessStartInfo(helpPath) { UseShellExecute = true });
        SetStatus("Opened ASIOA help.");
    }

    private void Exit_Click(object sender, RoutedEventArgs e)
    {
        SaveSettings();
        Close();
    }

    private void SettingsControl_Changed(object sender, RoutedEventArgs e)
    {
        if (!_loading)
        {
            SaveSettings();
        }
    }

    private void RefreshRoutes(string message)
    {
        RoutesList.ItemsSource = null;
        RoutesList.ItemsSource = _router.Routes;
        SetStatus(message);
    }

    private void SaveSettings()
    {
        if (SampleRateComboBox.SelectedItem is int sampleRate)
        {
            _settings.SampleRate = sampleRate;
        }

        if (BufferSizeComboBox.SelectedItem is int bufferSize)
        {
            _settings.BufferSizeSamples = bufferSize;
        }

        _settings.MonitoringEnabled = MonitoringCheckBox.IsChecked == true;
        _settings.BypassDawRouting = BypassCheckBox.IsChecked == true;
        _settings.RunOnStartup = RunOnStartupCheckBox.IsChecked == true;
        _settings.StartMinimizedToTray = StartMinimizedCheckBox.IsChecked == true;
        _settings.KeepEngineActiveOnClose = KeepEngineActiveCheckBox.IsChecked == true;

        try
        {
            _settings.ToAudioEngineSettings();
            _settings.Save();
            SetRunOnStartup(_settings.RunOnStartup);
            SetStatus("Settings saved.");
        }
        catch (Exception ex)
        {
            SetStatus($"Settings were not saved. {ex.Message}");
        }
    }

    private static void SetRunOnStartup(bool enabled)
    {
        using var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", writable: true);
        if (key is null)
        {
            return;
        }

        const string valueName = "ASIOA Audio Router";
        if (enabled)
        {
            var exePath = Environment.ProcessPath ?? Process.GetCurrentProcess().MainModule?.FileName;
            if (!string.IsNullOrWhiteSpace(exePath))
            {
                key.SetValue(valueName, $"\"{exePath}\"");
            }
        }
        else
        {
            key.DeleteValue(valueName, throwOnMissingValue: false);
        }
    }

    private void SetStatus(string message)
    {
        StatusText.Text = message;
        System.Windows.Automation.AutomationProperties.SetName(StatusText, $"Status: {message}");
    }
}
