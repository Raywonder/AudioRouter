from __future__ import annotations

import json
import os
import subprocess
import sys
import webbrowser
import ctypes
import winsound
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import wx
import wx.html2


APP_NAME = "ASIOA Audio Router"
APP_VERSION = "0.2.2"
CHANNEL_COUNT = 68


def app_data_dir() -> Path:
    root = os.environ.get("APPDATA")
    if root:
        return Path(root) / "ASIOA Audio Router"
    return Path.home() / "AppData" / "Roaming" / "ASIOA Audio Router"


SETTINGS_PATH = app_data_dir() / "settings.json"
DIAGNOSTICS_INBOX = app_data_dir() / ".diagnostics-inbox"


def resource_path(*parts: str) -> Path:
    candidates = [
        Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)),
        Path(sys.executable).parent,
        Path.cwd(),
        Path(__file__).resolve().parents[2],
    ]
    for base in candidates:
        path = base.joinpath(*parts)
        if path.exists():
            return path
    return candidates[0].joinpath(*parts)


DRIVER_MODES = [
    "ASIOA Native driver",
    "Auto select best available",
    "miniaudio / WASAPI",
    "PortAudio compatibility",
    "JACK professional routing",
    "ASIO4ALL compatibility",
    "WASAPI exclusive",
    "WASAPI shared",
]

SMART_BUFFER_MODES = [
    "Ultra low latency",
    "Balanced",
    "Stability",
    "Streaming",
    "Manual",
]

SAMPLE_RATES = ["44100", "48000", "88200", "96000", "176400", "192000"]
BUFFER_SIZES = ["16", "32", "64", "128", "256", "512", "1024", "2048"]
LATENCY_TARGETS = ["2", "4", "6", "8", "10", "12", "16", "24", "32", "48"]
SAFETY_MARGINS = ["0", "2", "4", "8", "12", "16", "24", "32", "48", "64"]


@dataclass(slots=True)
class Endpoint:
    name: str
    kind: str
    channels: str
    enabled: bool = True
    monitor: bool = False
    muted: bool = False
    volume: int = 100
    buffer_override: str = "Smart"

    def row(self) -> list[str]:
        return [
            self.name,
            self.kind,
            self.channels,
            "Yes" if self.enabled else "No",
            "On" if self.monitor else "Off",
            "Muted" if self.muted else "Not muted",
            f"{self.volume}%",
            self.buffer_override,
        ]


@dataclass(slots=True)
class Route:
    source: str
    destination: str
    enabled: bool = True
    muted: bool = False
    monitor: bool = True
    volume: int = 100

    def row(self) -> list[str]:
        return [
            self.source,
            self.destination,
            "Yes" if self.enabled else "No",
            "Muted" if self.muted else "Not muted",
            "On" if self.monitor else "Off",
            f"{self.volume}%",
        ]


@dataclass(slots=True)
class EffectSlot:
    name: str
    fmt: str
    target: str
    enabled: bool = False
    bypassed: bool = True
    wet: int = 100

    def row(self) -> list[str]:
        return [
            self.name,
            self.fmt,
            self.target,
            "Yes" if self.enabled else "No",
            "Bypassed" if self.bypassed else "Active",
            f"{self.wet}%",
        ]


@dataclass(slots=True)
class Settings:
    driver_mode: str = "ASIOA Native driver"
    sample_rate: str = "48000"
    buffer_size: str = "128"
    smart_buffer_mode: str = "Balanced"
    minimum_buffer: str = "64"
    maximum_buffer: str = "1024"
    target_latency_ms: str = "8"
    jitter_safety_ms: str = "12"
    dropout_recovery_ms: int = 250
    auto_raise_on_dropouts: bool = True
    auto_lower_when_stable: bool = True
    protect_daw_master_feedback: bool = True
    live_effects_enabled: bool = False
    vst3_enabled: bool = True
    clap_enabled: bool = True
    vst2_enabled: bool = False
    monitor_in_app: bool = True
    bypass_to_daw: bool = False
    run_on_startup: bool = False
    start_minimized: bool = False
    keep_engine_active: bool = True
    auto_check_updates: bool = True
    update_channel: str = "Stable"
    update_source: str = "GitHub first, Gitea when available"
    screen_reader_output: str = "Current default accessibility device"
    screen_reader_router_capture: bool = False
    screen_reader_include_stream: bool = False
    screen_reader_include_recording: bool = False
    enable_builtin_sounds: bool = True
    silent_diagnostics: bool = True
    endpoints: list[Endpoint] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    effects: list[EffectSlot] = field(default_factory=list)

    @staticmethod
    def defaults() -> "Settings":
        endpoints = [
            Endpoint("Capture A 1/2", "Application or physical input", "1-2", monitor=True),
            Endpoint("Capture B 3/4", "Application", "3-4"),
            Endpoint("DAW Master return 1/2", "DAW return", "1-2", monitor=True),
            Endpoint("DAW cue return 3/4", "DAW return", "3-4"),
            Endpoint("Monitoring bus", "Virtual bus", "65-66", monitor=True),
            Endpoint("Utility bus", "Virtual bus", "67-68"),
        ]
        routes = [
            Route("DAW cue return 3/4", "Capture A 1/2", volume=85),
            Route("Capture B 3/4", "Monitoring bus", volume=100),
        ]
        effects = [
            EffectSlot("No effect loaded", "VST3", "Monitoring bus"),
            EffectSlot("No CLAP effect loaded", "CLAP", "Capture A 1/2"),
            EffectSlot("Legacy VST2 disabled", "VST2 legacy", "Utility bus", enabled=False, bypassed=True),
        ]
        return Settings(endpoints=endpoints, routes=routes, effects=effects)

    @staticmethod
    def load() -> "Settings":
        defaults = Settings.defaults()
        if not SETTINGS_PATH.exists():
            return defaults
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            for key, value in raw.items():
                if key == "endpoints":
                    defaults.endpoints = [Endpoint(**item) for item in value]
                elif key == "routes":
                    defaults.routes = [Route(**item) for item in value]
                elif key == "effects":
                    defaults.effects = [EffectSlot(**item) for item in value]
                elif hasattr(defaults, key):
                    setattr(defaults, key, value)
            return defaults
        except Exception:
            return defaults

    def save(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


class ASIOAFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, title=f"{APP_NAME} {APP_VERSION}", size=(1120, 780))
        self.settings = Settings.load()
        self.status_text: wx.StaticText
        self.status_console: wx.TextCtrl
        self.overview_view: wx.html2.WebView | wx.TextCtrl
        self.notebook: wx.Notebook
        self.route_list: wx.ListCtrl
        self.input_list: wx.ListCtrl
        self.output_list: wx.ListCtrl
        self.effects_list: wx.ListCtrl
        self.controls: dict[str, wx.Window] = {}
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self.device_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_device_timer, self.device_timer)
        self.device_timer.Start(30000)
        self.Centre()
        self.SetStatus("ASIOA control panel ready. Open the Smart Buffer tab to tune latency and stability.")
        self.update_overview()
        self.announce_startup_status()
        self.play_sound("ready")

    def _build_menu(self) -> None:
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        save_item = file_menu.Append(wx.ID_SAVE, "&Save settings\tCtrl+S")
        command_item = file_menu.Append(wx.ID_ANY, "&Command palette\tCtrl+Shift+P")
        updates_item = file_menu.Append(wx.ID_ANY, "Check for &updates")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit")
        view_menu = wx.Menu()
        diagnostics_item = view_menu.Append(wx.ID_ANY, "&Diagnostics tab\tCtrl+D")
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_HELP, "&ASIOA help\tF1")
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(view_menu, "&View")
        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, lambda _event: self.save_settings(), save_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.open_command_palette(), command_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.check_for_updates(), updates_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.select_tab("Diagnostics"), diagnostics_item)
        self.Bind(wx.EVT_MENU, lambda _event: self.open_help(), help_item)

    def _bind_shortcuts(self) -> None:
        entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("S"), wx.ID_SAVE),
            wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("P"), wx.ID_ANY),
        ]
        # wx.Menu handles Ctrl+S through its ID. Ctrl+Shift+P is also bound at the window level for reliability.
        command_id = wx.NewIdRef()
        entries[1] = wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("P"), command_id)
        self.Bind(wx.EVT_MENU, lambda _event: self.open_command_palette(), id=command_id)
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _build_ui(self) -> None:
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(root)

        heading = wx.StaticText(panel, label="ASIOA Audio Router control panel")
        font = heading.GetFont()
        font.MakeBold()
        heading.SetFont(font)
        root.Add(heading, 0, wx.ALL, 8)

        self.notebook = wx.Notebook(panel)
        root.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        self._add_overview_tab()
        self._add_routing_tab()
        self._add_inputs_tab()
        self._add_outputs_tab()
        self._add_monitoring_tab()
        self._add_buffer_tab()
        self._add_devices_tab()
        self._add_effects_tab()
        self._add_accessibility_tab()
        self._add_startup_tab()
        self._add_diagnostics_tab()

        button_row = wx.BoxSizer(wx.HORIZONTAL)
        save = wx.Button(panel, label="Save settings")
        apply = wx.Button(panel, label="Apply to engine")
        close = wx.Button(panel, label="Close")
        save.Bind(wx.EVT_BUTTON, lambda _event: self.save_settings())
        apply.Bind(wx.EVT_BUTTON, lambda _event: self.apply_to_engine())
        close.Bind(wx.EVT_BUTTON, lambda _event: self.Close())
        for button in (save, apply, close):
            button_row.Add(button, 0, wx.RIGHT, 8)
        root.Add(button_row, 0, wx.ALL, 8)

        self.status_text = wx.StaticText(panel, label="")
        root.Add(self.status_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        console_label = wx.StaticText(panel, label="Status console:")
        self.status_console = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        self.status_console.SetName("Accessible status console")
        self.status_console.SetMinSize((-1, 90))
        root.Add(console_label, 0, wx.LEFT | wx.RIGHT, 8)
        root.Add(self.status_console, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

    def _add_overview_tab(self) -> None:
        panel, sizer = self._new_tab("Overview")
        self.overview_view = wx.html2.WebView.New(panel)
        self.overview_view.SetName("ASIOA overview")
        sizer.Add(self.overview_view, 1, wx.EXPAND | wx.ALL, 6)

    def _add_routing_tab(self) -> None:
        panel, sizer = self._new_tab("Routing")
        self.route_list = self._make_list(
            panel,
            ["Source", "Destination", "Enabled", "Mute state", "Monitoring", "Volume"],
            "Configured audio routes",
        )
        sizer.Add(self.route_list, 1, wx.EXPAND | wx.ALL, 6)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in [
            ("Add safe route", self.add_safe_route),
            ("Toggle selected route mute", self.toggle_route_mute),
            ("Volume down 5 percent", lambda _event: self.adjust_route_volume(-5)),
            ("Volume up 5 percent", lambda _event: self.adjust_route_volume(5)),
            ("Remove selected route", self.remove_route),
        ]:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            buttons.Add(button, 0, wx.RIGHT, 6)
        sizer.Add(buttons, 0, wx.ALL, 6)
        self.populate_routes()

    def _add_inputs_tab(self) -> None:
        panel, sizer = self._new_tab("Inputs")
        self.input_list = self._make_list(
            panel,
            ["Name", "Kind", "Channels", "Enabled", "Monitoring", "Mute state", "Volume", "Buffer"],
            "Input endpoints",
        )
        sizer.Add(self.input_list, 1, wx.EXPAND | wx.ALL, 6)
        self._add_endpoint_actions(panel, sizer, self.input_list)
        self.populate_endpoints()

    def _add_outputs_tab(self) -> None:
        panel, sizer = self._new_tab("Outputs")
        self.output_list = self._make_list(
            panel,
            ["Name", "Kind", "Channels", "Enabled", "Monitoring", "Mute state", "Volume", "Buffer"],
            "Output endpoints and DAW returns",
        )
        sizer.Add(self.output_list, 1, wx.EXPAND | wx.ALL, 6)
        self._add_endpoint_actions(panel, sizer, self.output_list)
        self.populate_endpoints()

    def _add_monitoring_tab(self) -> None:
        panel, sizer = self._new_tab("Monitoring")
        self.controls["monitor_in_app"] = self._add_checkbox(panel, sizer, "Monitor directly in ASIOA", self.settings.monitor_in_app)
        self.controls["bypass_to_daw"] = self._add_checkbox(panel, sizer, "Bypass ASIOA monitoring and route directly through the DAW", self.settings.bypass_to_daw)
        self._add_slider(panel, sizer, "Default monitor volume percent:", "monitor_volume", 100, 0, 150)
        self._add_readonly_text(
            panel,
            sizer,
            "Monitoring note:",
            "Monitoring can be direct, bypassed through the DAW, or both. Direct monitoring uses the selected driver mode and smart buffer settings.",
        )

    def _add_buffer_tab(self) -> None:
        panel, sizer = self._new_tab("Smart Buffer")
        self.controls["driver_mode"] = self._add_choice(panel, sizer, "Driver mode:", DRIVER_MODES, self.settings.driver_mode)
        self.controls["smart_buffer_mode"] = self._add_choice(panel, sizer, "Smart buffer mode:", SMART_BUFFER_MODES, self.settings.smart_buffer_mode)
        self.controls["sample_rate"] = self._add_choice(panel, sizer, "Sample rate:", SAMPLE_RATES, self.settings.sample_rate)
        self.controls["buffer_size"] = self._add_choice(panel, sizer, "Starting buffer size in samples:", BUFFER_SIZES, self.settings.buffer_size)
        self.controls["minimum_buffer"] = self._add_choice(panel, sizer, "Minimum smart buffer size:", BUFFER_SIZES, self.settings.minimum_buffer)
        self.controls["maximum_buffer"] = self._add_choice(panel, sizer, "Maximum smart buffer size:", BUFFER_SIZES, self.settings.maximum_buffer)
        self.controls["target_latency_ms"] = self._add_choice(panel, sizer, "Target latency in milliseconds:", LATENCY_TARGETS, self.settings.target_latency_ms)
        self.controls["jitter_safety_ms"] = self._add_choice(panel, sizer, "Jitter safety margin in milliseconds:", SAFETY_MARGINS, self.settings.jitter_safety_ms)
        self._add_slider(panel, sizer, "Dropout recovery hold time in milliseconds:", "dropout_recovery_ms", self.settings.dropout_recovery_ms, 0, 2000)
        self.controls["auto_raise_on_dropouts"] = self._add_checkbox(panel, sizer, "Automatically raise buffer when dropouts are detected", self.settings.auto_raise_on_dropouts)
        self.controls["auto_lower_when_stable"] = self._add_checkbox(panel, sizer, "Automatically lower buffer after stable playback", self.settings.auto_lower_when_stable)
        self.controls["protect_daw_master_feedback"] = self._add_checkbox(panel, sizer, "Protect DAW master 1 and 2 from feedback into capture 1 and 2", self.settings.protect_daw_master_feedback)

    def _add_devices_tab(self) -> None:
        panel, sizer = self._new_tab("Devices")
        self._add_readonly_text(
            panel,
            sizer,
            "Device discovery:",
            "Devices are refreshed automatically in the background. Native driver enumeration will be provided by the selected engine mode.",
        )
        self._add_readonly_text(
            panel,
            sizer,
            "Driver modes:",
            "ASIOA Native is the main target. miniaudio/WASAPI gives lightweight capture/playback, PortAudio is a compatibility layer, JACK is an optional professional patchbay backend, and ASIO4ALL compatibility is available for systems that already depend on it.",
        )

    def _add_effects_tab(self) -> None:
        panel, sizer = self._new_tab("Live Effects")
        self.controls["live_effects_enabled"] = self._add_checkbox(panel, sizer, "Enable live effects processing", self.settings.live_effects_enabled)
        self.controls["vst3_enabled"] = self._add_checkbox(panel, sizer, "Enable VST3 effects", self.settings.vst3_enabled)
        self.controls["clap_enabled"] = self._add_checkbox(panel, sizer, "Enable CLAP effects", self.settings.clap_enabled)
        self.controls["vst2_enabled"] = self._add_checkbox(panel, sizer, "Enable legacy VST2 effects", self.settings.vst2_enabled)
        self.effects_list = self._make_list(panel, ["Effect", "Format", "Target", "Enabled", "State", "Wet"], "Live effects slots")
        sizer.Add(self.effects_list, 1, wx.EXPAND | wx.ALL, 6)
        self.populate_effects()

    def _add_accessibility_tab(self) -> None:
        panel, sizer = self._new_tab("Accessibility")
        self.controls["screen_reader_output"] = self._add_choice(
            panel,
            sizer,
            "Screen reader output route:",
            [
                "Current default accessibility device",
                "Default Windows playback device",
                "Headphones",
                "ASIOA Screen Reader Bus 61/62",
                "ASIOA TTS Bus 63/64",
                "Do not route through ASIOA",
            ],
            self.settings.screen_reader_output,
        )
        self.controls["screen_reader_router_capture"] = self._add_checkbox(
            panel,
            sizer,
            "Capture screen reader audio directly inside ASIOA Audio Router",
            self.settings.screen_reader_router_capture,
        )
        self.controls["screen_reader_include_stream"] = self._add_checkbox(
            panel,
            sizer,
            "Include screen reader audio in stream",
            self.settings.screen_reader_include_stream,
        )
        self.controls["screen_reader_include_recording"] = self._add_checkbox(
            panel,
            sizer,
            "Include screen reader audio in recording",
            self.settings.screen_reader_include_recording,
        )
        self.controls["enable_builtin_sounds"] = self._add_checkbox(
            panel,
            sizer,
            "Enable built-in background and action sounds",
            self.settings.enable_builtin_sounds,
        )
        self._add_readonly_text(
            panel,
            sizer,
            "Screen Reader Bus:",
            "Default channels 61 and 62. Excluded from stream and recording by default. Route to headphones or another accessibility output. Built-in sounds use the bundled OpenLink sound set and are not user-selectable.",
        )
        self._add_readonly_text(
            panel,
            sizer,
            "TTS Bus:",
            "Default channels 63 and 64. Excluded from stream and recording by default. Use this for OpenClaw, VoiceLink, screen-reader bridges, and status speech.",
        )
        self._add_readonly_text(
            panel,
            sizer,
            "Emergency Accessibility Bus:",
            "Default channels 67 and 68. This bus is for critical warnings, emergency mute, and recovery status.",
        )

    def _add_startup_tab(self) -> None:
        panel, sizer = self._new_tab("Startup")
        self.controls["run_on_startup"] = self._add_checkbox(panel, sizer, "Run ASIOA when Windows starts", self.settings.run_on_startup)
        self.controls["start_minimized"] = self._add_checkbox(panel, sizer, "Start minimized to the system tray", self.settings.start_minimized)
        self.controls["keep_engine_active"] = self._add_checkbox(panel, sizer, "Keep audio engine active when the control panel closes", self.settings.keep_engine_active)
        self.controls["auto_check_updates"] = self._add_checkbox(panel, sizer, "Automatically check for updates", self.settings.auto_check_updates)
        self.controls["update_channel"] = self._add_choice(panel, sizer, "Update channel:", ["Stable", "Beta", "Developer"], self.settings.update_channel)
        self.controls["update_source"] = self._add_choice(
            panel,
            sizer,
            "Update source:",
            [
                "GitHub first, Gitea when available",
                "GitHub only",
                "Gitea only when available",
                "Both must match",
            ],
            self.settings.update_source,
        )

    def _add_diagnostics_tab(self) -> None:
        panel, sizer = self._new_tab("Diagnostics")
        text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        text.SetValue(self.diagnostics_text())
        sizer.Add(text, 1, wx.EXPAND | wx.ALL, 6)
        self.controls["silent_diagnostics"] = self._add_checkbox(panel, sizer, "Allow silent diagnostics reports to local agent inbox", self.settings.silent_diagnostics)
        send = wx.Button(panel, label="Send diagnostics to local agent inbox")
        send.Bind(wx.EVT_BUTTON, lambda _event: self.send_diagnostics_silently())
        sizer.Add(send, 0, wx.ALL, 6)

    def _new_tab(self, name: str) -> tuple[wx.Panel, wx.BoxSizer]:
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, name)
        return panel, sizer

    def _add_choice(self, panel: wx.Panel, sizer: wx.BoxSizer, label: str, choices: list[str], value: str) -> wx.Choice:
        text = wx.StaticText(panel, label=label)
        choice = wx.Choice(panel, choices=choices)
        if value in choices:
            choice.SetStringSelection(value)
        else:
            choice.SetSelection(0)
        sizer.Add(text, 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        sizer.Add(choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        return choice

    def _add_checkbox(self, panel: wx.Panel, sizer: wx.BoxSizer, label: str, value: bool) -> wx.CheckBox:
        checkbox = wx.CheckBox(panel, label=label)
        checkbox.SetValue(value)
        sizer.Add(checkbox, 0, wx.ALL, 6)
        return checkbox

    def _add_slider(self, panel: wx.Panel, sizer: wx.BoxSizer, label: str, key: str, value: int, minimum: int, maximum: int) -> wx.Slider:
        text = wx.StaticText(panel, label=label)
        slider = wx.Slider(panel, value=value, minValue=minimum, maxValue=maximum, style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.controls[key] = slider
        sizer.Add(text, 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        sizer.Add(slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        return slider

    def _add_readonly_text(self, panel: wx.Panel, sizer: wx.BoxSizer, label: str, value: str) -> None:
        sizer.Add(wx.StaticText(panel, label=label), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        text = wx.TextCtrl(panel, value=value, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        text.SetMinSize((-1, 76))
        sizer.Add(text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

    def _make_list(self, parent: wx.Window, columns: list[str], name: str) -> wx.ListCtrl:
        control = wx.ListCtrl(parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        control.SetName(name)
        for index, column in enumerate(columns):
            control.InsertColumn(index, column, width=wx.LIST_AUTOSIZE_USEHEADER)
        return control

    def _add_endpoint_actions(self, panel: wx.Panel, sizer: wx.BoxSizer, target: wx.ListCtrl) -> None:
        row = wx.BoxSizer(wx.HORIZONTAL)
        actions = [
            ("Toggle selected enabled state", lambda _event: self.toggle_endpoint(target, "enabled")),
            ("Toggle selected monitoring", lambda _event: self.toggle_endpoint(target, "monitor")),
            ("Toggle selected mute", lambda _event: self.toggle_endpoint(target, "muted")),
            ("Volume down 5 percent", lambda _event: self.adjust_endpoint_volume(target, -5)),
            ("Volume up 5 percent", lambda _event: self.adjust_endpoint_volume(target, 5)),
        ]
        for label, handler in actions:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            row.Add(button, 0, wx.RIGHT, 6)
        sizer.Add(row, 0, wx.ALL, 6)

    def populate_routes(self) -> None:
        self.route_list.DeleteAllItems()
        for route in self.settings.routes:
            self._append_row(self.route_list, route.row())

    def populate_endpoints(self) -> None:
        for control, predicate in [
            (getattr(self, "input_list", None), lambda item: item.kind != "DAW return"),
            (getattr(self, "output_list", None), lambda item: item.kind == "DAW return" or item.kind == "Virtual bus"),
        ]:
            if control is None:
                continue
            control.DeleteAllItems()
            for endpoint in self.settings.endpoints:
                if predicate(endpoint):
                    self._append_row(control, endpoint.row())

    def populate_effects(self) -> None:
        self.effects_list.DeleteAllItems()
        for effect in self.settings.effects:
            self._append_row(self.effects_list, effect.row())

    @staticmethod
    def _append_row(control: wx.ListCtrl, values: list[str]) -> None:
        index = control.InsertItem(control.GetItemCount(), values[0])
        for column, value in enumerate(values[1:], start=1):
            control.SetItem(index, column, value)
        for column in range(len(values)):
            control.SetColumnWidth(column, wx.LIST_AUTOSIZE_USEHEADER)

    def selected_index(self, control: wx.ListCtrl) -> int:
        return control.GetFirstSelected()

    def add_safe_route(self, _event: wx.CommandEvent) -> None:
        self.settings.routes.append(Route("DAW cue return 3/4", "Capture A 1/2", volume=85))
        self.populate_routes()
        self.SetStatus("Added safe route from DAW cue return 3 and 4 to Capture A 1 and 2.")

    def toggle_route_mute(self, _event: wx.CommandEvent) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        route = self.settings.routes[index]
        route.muted = not route.muted
        self.populate_routes()
        self.SetStatus(f"Route mute is now {'on' if route.muted else 'off'}.")

    def adjust_route_volume(self, delta: int) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        route = self.settings.routes[index]
        route.volume = max(0, min(150, route.volume + delta))
        self.populate_routes()
        self.SetStatus(f"Route volume is now {route.volume} percent.")

    def remove_route(self, _event: wx.CommandEvent) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        del self.settings.routes[index]
        self.populate_routes()
        self.SetStatus("Route removed.")

    def endpoint_for_row(self, control: wx.ListCtrl, row: int) -> Endpoint | None:
        if row < 0:
            return None
        name = control.GetItemText(row, 0)
        return next((item for item in self.settings.endpoints if item.name == name), None)

    def toggle_endpoint(self, control: wx.ListCtrl, attr: str) -> None:
        endpoint = self.endpoint_for_row(control, self.selected_index(control))
        if endpoint is None:
            self.SetStatus("No endpoint selected.")
            return
        setattr(endpoint, attr, not getattr(endpoint, attr))
        self.populate_endpoints()
        self.SetStatus(f"{endpoint.name} {attr.replace('_', ' ')} updated.")

    def adjust_endpoint_volume(self, control: wx.ListCtrl, delta: int) -> None:
        endpoint = self.endpoint_for_row(control, self.selected_index(control))
        if endpoint is None:
            self.SetStatus("No endpoint selected.")
            return
        endpoint.volume = max(0, min(150, endpoint.volume + delta))
        self.populate_endpoints()
        self.SetStatus(f"{endpoint.name} volume is now {endpoint.volume} percent.")

    def collect_settings(self) -> None:
        for key, control in self.controls.items():
            if isinstance(control, wx.Choice):
                setattr(self.settings, key, control.GetStringSelection())
            elif isinstance(control, wx.CheckBox):
                setattr(self.settings, key, control.GetValue())
            elif isinstance(control, wx.Slider):
                setattr(self.settings, key, control.GetValue())

    def save_settings(self) -> None:
        self.collect_settings()
        self.settings.save()
        self.update_overview()
        self.SetStatus(f"Settings saved to {SETTINGS_PATH}.")
        self.play_sound("success")

    def apply_to_engine(self) -> None:
        self.save_settings()
        self.SetStatus("Settings saved and queued for the ASIOA engine. Restart the engine if the driver is already loaded by a DAW.")
        self.play_sound("notification")

    def refresh_devices(self) -> None:
        self.update_overview()

    def on_device_timer(self, _event: wx.TimerEvent) -> None:
        self.refresh_devices()

    def select_tab(self, name: str) -> None:
        for index in range(self.notebook.GetPageCount()):
            if self.notebook.GetPageText(index) == name:
                self.notebook.SetSelection(index)
                self.notebook.GetPage(index).SetFocus()
                self.SetStatus(f"{name} tab selected.")
                return

    def open_help(self) -> None:
        candidates = [
            Path(sys.executable).parent / "docs" / "user-guide.md",
            Path(__file__).resolve().parents[2] / "docs" / "user-guide.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                webbrowser.open(candidate.as_uri())
                self.SetStatus("Opened ASIOA help.")
                return
        self.SetStatus("Help file was not found.")

    def open_command_palette(self) -> None:
        dialog = wx.TextEntryDialog(
            self,
            "Type a routing or control command. Examples: route Chrome to 3/4, mute main out, enable smart buffer, export diagnostics.",
            "ASIOA command palette",
            "",
        )
        try:
            if dialog.ShowModal() == wx.ID_OK:
                command = dialog.GetValue().strip()
                if not command:
                    self.SetStatus("Command palette closed with no command.")
                    return
                self.handle_command(command)
        finally:
            dialog.Destroy()

    def handle_command(self, command: str) -> None:
        normalized = command.lower()
        if "enable smart buffer" in normalized:
            control = self.controls.get("smart_buffer_mode")
            if isinstance(control, wx.Choice):
                control.SetStringSelection("Balanced")
            self.SetStatus("Smart Buffer enabled in Balanced mode.")
        elif "mute main" in normalized or "mute main out" in normalized:
            self.SetStatus("Main output mute command queued. Live engine connection is required to apply it.")
        elif "export diagnostics" in normalized:
            path = SETTINGS_PATH.parent / "diagnostics.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.diagnostics_text(), encoding="utf-8")
            self.SetStatus(f"Diagnostics exported to {path}.")
        elif normalized.startswith("route "):
            self.settings.routes.append(Route(command, "Pending engine route", volume=100))
            self.populate_routes()
            self.SetStatus(f"Route command recorded: {command}.")
        else:
            self.SetStatus(f"Command recorded for engine: {command}.")

    def check_for_updates(self) -> None:
        self.SetStatus(
            "Update check queued. GitHub is the primary update source until Gitea is reachable; matching GitHub and Gitea versions will be preferred when both are available."
        )
        self.play_sound("notification")

    def send_diagnostics_silently(self) -> None:
        if not self.settings.silent_diagnostics:
            self.SetStatus("Silent diagnostics are disabled in settings.")
            return
        DIAGNOSTICS_INBOX.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["attrib", "+h", str(DIAGNOSTICS_INBOX)], check=False, capture_output=True)
        except Exception:
            pass
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = DIAGNOSTICS_INBOX / f"diagnostics-{stamp}.txt"
        path.write_text(self.diagnostics_text(), encoding="utf-8")
        self.SetStatus(f"Diagnostics saved for agents at {path}.")
        self.play_sound("success")

    def diagnostics_text(self) -> str:
        return "\n".join(
            [
                f"Application: {APP_NAME} {APP_VERSION}",
                f"Python: {sys.version.split()[0]}",
                f"wxPython: {wx.version()}",
                f"Settings path: {SETTINGS_PATH}",
                f"Configured driver mode: {self.settings.driver_mode}",
                f"Smart buffer mode: {self.settings.smart_buffer_mode}",
                f"Sample rate: {self.settings.sample_rate}",
                f"Starting buffer: {self.settings.buffer_size} samples",
                f"Channel count target: {CHANNEL_COUNT} inputs and {CHANNEL_COUNT} outputs",
                "Protected buses: screen reader 61/62, TTS 63/64, communications 65/66, emergency accessibility 67/68.",
                "Live effects: off by default; VST3 and CLAP are preferred; VST2 is legacy and disabled by default.",
                f"Update channel: {self.settings.update_channel}",
                f"Update source: {self.settings.update_source}",
                f"Built-in sounds: {self.settings.enable_builtin_sounds}",
                f"Diagnostics inbox: {DIAGNOSTICS_INBOX}",
            ]
        )

    def render_overview_html(self) -> str:
        active_routes = "".join(f"<li>{route.source} to {route.destination}, {'muted' if route.muted else 'not muted'}, volume {route.volume}%</li>" for route in self.settings.routes)
        endpoints = "".join(f"<li>{endpoint.name}: {'enabled' if endpoint.enabled else 'disabled'}, {endpoint.kind}, channels {endpoint.channels}</li>" for endpoint in self.settings.endpoints)
        effects = "".join(f"<li>{effect.name}: {effect.fmt}, {'enabled' if effect.enabled else 'disabled'}, {'bypassed' if effect.bypassed else 'active'}</li>" for effect in self.settings.effects)
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ASIOA Overview</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 14px; line-height: 1.45; color: #111; background: #fff; }}
    h1 {{ font-size: 1.4rem; }}
    h2 {{ font-size: 1.1rem; margin-top: 1rem; }}
    ul {{ margin-top: .2rem; }}
  </style>
</head>
<body>
  <h1>ASIOA Audio Router overview</h1>
  <p>Driver mode: <strong>{self.settings.driver_mode}</strong>. Smart Buffer: <strong>{self.settings.smart_buffer_mode}</strong>, {self.settings.buffer_size} samples at {self.settings.sample_rate} Hz.</p>
  <p>Screen reader output: <strong>{self.settings.screen_reader_output}</strong>. Direct ASIOA capture is <strong>{'on' if self.settings.screen_reader_router_capture else 'off'}</strong>.</p>
  <p>Built-in background and action sounds are <strong>{'on' if self.settings.enable_builtin_sounds else 'off'}</strong>. Sounds use the bundled OpenLink sound set.</p>
  <h2>Protected buses</h2>
  <ul>
    <li>Screen Reader Bus: channels 61 and 62. Stream inclusion is {'on' if self.settings.screen_reader_include_stream else 'off'}. Recording inclusion is {'on' if self.settings.screen_reader_include_recording else 'off'}.</li>
    <li>TTS Bus: channels 63 and 64.</li>
    <li>Communications Bus: channels 65 and 66.</li>
    <li>Emergency Accessibility Bus: channels 67 and 68.</li>
  </ul>
  <h2>Routes</h2>
  <ul>{active_routes or '<li>No routes configured.</li>'}</ul>
  <h2>Endpoints</h2>
  <ul>{endpoints}</ul>
  <h2>Effects</h2>
  <ul>{effects}</ul>
  <h2>Updates and diagnostics</h2>
  <ul>
    <li>Automatic update checks are {'on' if self.settings.auto_check_updates else 'off'} on the {self.settings.update_channel} channel.</li>
    <li>Update source: {self.settings.update_source}.</li>
    <li>Silent diagnostics inbox: {DIAGNOSTICS_INBOX}</li>
  </ul>
</body>
</html>"""

    def update_overview(self) -> None:
        if not hasattr(self, "overview_view"):
            return
        self.overview_view.SetPage(self.render_overview_html(), "")

    def startup_summary(self) -> str:
        route_count = len(self.settings.routes)
        endpoint_count = len([endpoint for endpoint in self.settings.endpoints if endpoint.enabled])
        return (
            f"ASIOA Audio Router {APP_VERSION} ready. "
            f"{endpoint_count} endpoints enabled. {route_count} routes configured. "
            f"Driver mode {self.settings.driver_mode}. Smart Buffer {self.settings.smart_buffer_mode}. "
            f"Screen reader route {self.settings.screen_reader_output}. "
            "Use the Accessibility tab to route screen reader audio to a sound card or directly through ASIOA."
        )

    def announce_startup_status(self) -> None:
        ScreenReaderNotifier.announce(self.startup_summary())

    def play_sound(self, event_name: str) -> None:
        if not self.settings.enable_builtin_sounds:
            return
        sound_map = {
            "ready": "online.wav",
            "online": "online.wav",
            "offline": "offline.wav",
            "connected": "connected.wav",
            "connect": "connected.wav",
            "disconnect": "disconnect.wav",
            "message-received": "message-received.wav",
            "message": "message-received.wav",
            "success": "success.wav",
            "notification": "notification.wav",
            "error": "error.wav",
        }
        filename = sound_map.get(event_name)
        if not filename:
            return
        sound_path = resource_path("assets", "sounds", filename)
        if not sound_path.exists():
            return
        try:
            winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except RuntimeError:
            return

    def SetStatus(self, message: str) -> None:  # noqa: N802 - wx-style name.
        self.status_text.SetLabel(f"Status: {message}")
        self.status_text.SetName(f"Status: {message}")
        if hasattr(self, "status_console"):
            timestamp = wx.DateTime.Now().FormatISOTime()
            self.status_console.AppendText(f"{timestamp} {message}\n")


class ScreenReaderNotifier:
    @staticmethod
    def announce(message: str) -> None:
        if ScreenReaderNotifier._announce_with_nvda(message):
            return
        wx.CallAfter(lambda: None)

    @staticmethod
    def _announce_with_nvda(message: str) -> bool:
        candidates = [
            Path(sys.executable).parent / "nvdaControllerClient64.dll",
            Path(sys.executable).parent / "_internal" / "nvdaControllerClient64.dll",
            Path.cwd() / "nvdaControllerClient64.dll",
        ]
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                dll = ctypes.WinDLL(str(candidate))
                dll.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
                return dll.nvdaController_speakText(message) == 0
            except Exception:
                continue
        return False


def main() -> int:
    app = wx.App(False)
    frame = ASIOAFrame()
    frame.Show()
    return app.MainLoop() or 0


if __name__ == "__main__":
    raise SystemExit(main())
