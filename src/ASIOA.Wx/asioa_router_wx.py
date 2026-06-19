from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
import threading
import urllib.request
from urllib.parse import unquote, urlparse
import webbrowser
import ctypes
import winsound
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import wx
import wx.adv
import wx.html2

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev/test environments.
    winreg = None


APP_NAME = "ASIOA Audio Router"
APP_VERSION = "0.2.8"
CHANNEL_COUNT = 68
CHANNEL_PAIRS = [f"{left}-{left + 1}" for left in range(1, CHANNEL_COUNT, 2)]
UPDATE_MANIFEST_URLS = [
    "https://tappedin.fm/downloads/asioa/latest.json",
    "https://raw.githubusercontent.com/Raywonder/AudioRouter/main/updates/latest.json",
    "https://git.tappedin.fm/raywonder/audiorouter/raw/branch/main/updates/latest.json",
]


def app_data_dir() -> Path:
    root = os.environ.get("APPDATA")
    if root:
        return Path(root) / "ASIOA Audio Router"
    return Path.home() / "AppData" / "Roaming" / "ASIOA Audio Router"


SETTINGS_PATH = app_data_dir() / "settings.json"
INSTALLER_DRIVER_CHOICE_PATH = app_data_dir() / "installer-driver-choice.json"
DIAGNOSTICS_INBOX = app_data_dir() / ".diagnostics-inbox"
SETTINGS_BACKUP_DIR = app_data_dir() / "settings-backups"


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
DRIVER_INSTALL_OPTIONS = [
    "Install ASIOA driver now",
    "Install ASIOA ASIO driver now",
    "Ask me later",
    "Control panel only",
]
PLUGIN_SCAN_INTERVAL_MS = 300000
AUTOSAVE_DELAY_MS = 500
ASIOA_DRIVER_REGISTRY_PATH = r"SOFTWARE\ASIO\ASIOA Audio Router"
COMMUNICATION_BRIDGE_INPUT = "ASIOA Communication input 1/2"
COMMUNICATION_BRIDGE_OUTPUT = "ASIOA Communication output 1/2"


def discover_windows_audio_devices() -> list[str]:
    if os.name != "nt":
        return []
    try:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-CimInstance Win32_SoundDevice | Where-Object { $_.Name } | Select-Object -ExpandProperty Name",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
    except Exception:
        return []
    names: list[str] = []
    seen: set[str] = set()
    for line in (result.stdout or "").splitlines():
        name = line.strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        names.append(name)
    return names


def discover_asioa_windows_endpoints() -> list[str]:
    if os.name != "nt":
        return []
    try:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "$items = @(); "
            "$items += Get-CimInstance Win32_SoundDevice -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'ASIOA' } | Select-Object -ExpandProperty Name; "
            "$items += Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match 'ASIOA' -or $_.Name -match 'ASIOA' } | ForEach-Object { if ($_.FriendlyName) { $_.FriendlyName } else { $_.Name } }; "
            "$items | Where-Object { $_ } | Sort-Object -Unique",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
    except Exception:
        return []
    names: list[str] = []
    seen: set[str] = set()
    for line in (result.stdout or "").splitlines():
        name = line.strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        names.append(name)
    return names


def compare_versions(left: str, right: str) -> int:
    def parts(value: str) -> list[int]:
        result: list[int] = []
        for token in value.replace("-", ".").replace("_", ".").split("."):
            digits = "".join(ch for ch in token if ch.isdigit())
            result.append(int(digits or "0"))
        return result

    left_parts = parts(left)
    right_parts = parts(right)
    max_len = max(len(left_parts), len(right_parts))
    left_parts.extend([0] * (max_len - len(left_parts)))
    right_parts.extend([0] * (max_len - len(right_parts)))
    if left_parts == right_parts:
        return 0
    return 1 if left_parts > right_parts else -1


def filename_from_url(url: str, fallback: str) -> str:
    try:
        parsed = urlparse(url)
        name = unquote(Path(parsed.path).name)
        return name or fallback
    except Exception:
        return fallback


@dataclass(slots=True)
class PluginInventory:
    vst3: int = 0
    clap: int = 0
    vst2: int = 0
    scanned_paths: int = 0
    last_scan: str = "Not scanned yet"
    scanning: bool = False

    def status_lines(self) -> list[str]:
        state = "Scanning now" if self.scanning else f"Last scan: {self.last_scan}"
        return [
            state,
            f"VST3 plug-ins found: {self.vst3}.",
            f"CLAP plug-ins found: {self.clap}.",
            f"Legacy VST2 plug-ins found: {self.vst2}.",
            f"Plug-in folders checked: {self.scanned_paths}.",
        ]


@dataclass(slots=True)
class DriverHealth:
    registered: bool = False
    dll_path: str = ""
    dll_exists: bool = False
    package_available: bool = False
    marker_present: bool = False
    windows_endpoint_names: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def healthy(self) -> bool:
        return self.registered and self.dll_exists

    @property
    def needs_repair(self) -> bool:
        return not self.healthy

    @property
    def windows_endpoint_present(self) -> bool:
        return bool(self.windows_endpoint_names)


@dataclass(slots=True)
class DriverCapability:
    name: str
    status: str
    detail: str

    def sentence(self) -> str:
        return f"{self.name}: {self.status}. {self.detail}"


@dataclass(slots=True)
class UpdateInfo:
    version: str
    channel: str
    notes: str
    installer_url: str
    portable_url: str
    page_url: str = ""

    @property
    def has_download(self) -> bool:
        return bool(self.installer_url or self.portable_url)


@dataclass(slots=True)
class Endpoint:
    name: str
    kind: str
    channels: str
    enabled: bool = True
    monitor: bool = False
    solo: bool = False
    muted: bool = False
    volume: int = 100
    buffer_override: str = "Smart"
    role: str = "General"
    white_noise_guard: bool = False

    def row(self) -> list[str]:
        return [
            self.name,
            self.kind,
            f"channels {self.channels}",
            self.role,
            "enabled" if self.enabled else "disabled",
            "monitoring on" if self.monitor else "monitoring off",
            "solo on" if self.solo else "solo off",
            "muted" if self.muted else "not muted",
            f"volume {self.volume} percent",
            self.buffer_override,
            "white-noise guard on" if self.white_noise_guard else "white-noise guard off",
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
            "enabled" if self.enabled else "disabled",
            "muted" if self.muted else "not muted",
            "monitoring on" if self.monitor else "monitoring off",
            f"volume {self.volume} percent",
        ]


@dataclass(slots=True)
class EffectSlot:
    name: str
    fmt: str
    target: str
    enabled: bool = False
    bypassed: bool = True
    wet: int = 100
    path: str = ""
    parameters: dict[str, int] = field(default_factory=dict)

    def row(self) -> list[str]:
        return [
            self.name,
            self.fmt,
            self.target,
            "enabled" if self.enabled else "disabled",
            "bypassed" if self.bypassed else "active",
            f"wet mix {self.wet} percent",
            self.path or "Bundled or not selected",
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
    monitor_volume: int = 100
    run_on_startup: bool = False
    start_minimized: bool = False
    keep_engine_active: bool = True
    auto_check_updates: bool = True
    update_channel: str = "Stable"
    update_source: str = "GitHub first, Gitea when available"
    driver_install_option: str = "Install ASIOA ASIO driver now"
    driver_install_prompt_dismissed: bool = False
    default_monitor_device: str = "Main output 1/2"
    system_audio_master_pair: str = "Main output 1/2"
    screen_reader_master_pair: str = "Main output 1/2"
    screen_reader_output: str = "Current default accessibility device"
    screen_reader_router_capture: bool = False
    screen_reader_include_stream: bool = False
    screen_reader_include_recording: bool = False
    sessionwire_white_noise_guard: bool = True
    sessionwire_noise_floor_db: int = -60
    enable_builtin_sounds: bool = True
    silent_diagnostics: bool = True
    endpoints: list[Endpoint] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    effects: list[EffectSlot] = field(default_factory=list)

    @staticmethod
    def defaults() -> "Settings":
        endpoints = [
            Endpoint("Main output 1/2", "Default monitoring output", "1-2", monitor=True, role="Master monitor"),
            Endpoint(COMMUNICATION_BRIDGE_INPUT, "Windows communication bridge input", "1-2", monitor=False, muted=True, volume=0, role="Windows app input"),
            Endpoint(COMMUNICATION_BRIDGE_OUTPUT, "Windows communication bridge output", "1-2", monitor=True, role="Windows app output"),
            Endpoint("System audio capture 1/2", "Application or physical input", "1-2", monitor=True, role="System audio"),
            Endpoint("Capture B 3/4", "Application", "3-4", role="Application capture"),
            Endpoint("Primary microphone 7/8", "Physical input", "7-8", monitor=False, muted=True, volume=0, role="Microphone"),
            Endpoint("DAW Master return 1/2", "DAW return", "1-2", monitor=True, role="DAW master return"),
            Endpoint("DAW cue return 3/4", "DAW return", "3-4", role="DAW cue return"),
            Endpoint("Screen Reader Bus 61/62", "Virtual bus", "61-62", monitor=True, role="Screen reader"),
            Endpoint("TTS Bus 63/64", "Virtual bus", "63-64", monitor=True, role="TTS"),
            Endpoint("Communications Bus 65/66", "Virtual bus", "65-66", monitor=True, role="Communications"),
            Endpoint("Emergency Accessibility Bus 67/68", "Virtual bus", "67-68", monitor=True, role="Emergency accessibility"),
            Endpoint("Sessionwire input guard", "Application", "55-56", monitor=False, muted=True, role="Sessionwire", white_noise_guard=True),
            Endpoint("Sessionwire output guard", "DAW return", "57-58", monitor=False, muted=True, role="Sessionwire", white_noise_guard=True),
        ]
        routes = [
            Route(COMMUNICATION_BRIDGE_OUTPUT, "Main output 1/2", volume=100),
            Route("System audio capture 1/2", COMMUNICATION_BRIDGE_INPUT, volume=100),
            Route("System audio capture 1/2", "Main output 1/2", volume=100),
            Route("Screen Reader Bus 61/62", "Main output 1/2", volume=100),
            Route("TTS Bus 63/64", "Main output 1/2", volume=100),
            Route("DAW cue return 3/4", "System audio capture 1/2", volume=85),
        ]
        effects = [
            EffectSlot("No effect loaded", "VST3", "Monitoring bus"),
            EffectSlot("No CLAP effect loaded", "CLAP", "Capture A 1/2"),
            EffectSlot("Legacy VST2 disabled", "VST2 legacy", "Utility bus", enabled=False, bypassed=True),
        ]
        return Settings(endpoints=endpoints, routes=routes, effects=effects)

    def ensure_core_audio_policy(self) -> None:
        required = {endpoint.name: endpoint for endpoint in Settings.defaults().endpoints}
        existing = {endpoint.name for endpoint in self.endpoints}
        for name, endpoint in required.items():
            if name not in existing:
                self.endpoints.append(endpoint)
                existing.add(name)
        self.ensure_windows_bridge_pairs(existing)
        self.ensure_windows_audio_devices()
        for endpoint in self.endpoints:
            if "sessionwire" in endpoint.name.lower() and self.sessionwire_white_noise_guard:
                endpoint.white_noise_guard = True
        route_names = {(route.source, route.destination) for route in self.routes}
        for route in Settings.defaults().routes:
            if (route.source, route.destination) not in route_names:
                self.routes.append(route)
        if self.protect_daw_master_feedback:
            for route in self.routes:
                source = route.source.lower()
                destination = route.destination.lower()
                master_source = ("daw master" in source or "main output 1/2" in source or "output 1/2" in source)
                capture_destination = "system audio capture 1/2" in destination or "capture a" in destination or "input 1/2" in destination
                if master_source and capture_destination:
                    route.enabled = False
                    route.muted = True
                    route.monitor = False

    def ensure_windows_audio_devices(self) -> None:
        existing = {endpoint.name for endpoint in self.endpoints}
        for device_name in discover_windows_audio_devices():
            output_name = f"Windows output: {device_name}"
            input_name = f"Windows input: {device_name}"
            if output_name not in existing:
                self.endpoints.append(
                    Endpoint(output_name, "System playback device", "1-2", monitor=True, role="Windows audio device")
                )
                existing.add(output_name)
            if input_name not in existing:
                self.endpoints.append(
                    Endpoint(input_name, "System recording device", "1-2", monitor=False, muted=True, volume=0, role="Windows audio device input")
                )
                existing.add(input_name)

    def ensure_windows_bridge_pairs(self, existing: set[str]) -> None:
        for pair in CHANNEL_PAIRS:
            input_name = f"WDM/WASAPI bridge input {pair}"
            output_name = f"WDM/WASAPI bridge output {pair}"
            if input_name not in existing:
                self.endpoints.append(
                    Endpoint(input_name, "Windows bridge input pair", pair, monitor=False, muted=True, volume=0, role="Windows app input")
                )
                existing.add(input_name)
            if output_name not in existing:
                self.endpoints.append(
                    Endpoint(output_name, "Windows bridge output pair", pair, monitor=True, role="Windows app output")
                )
                existing.add(output_name)

    @staticmethod
    def load() -> "Settings":
        defaults = Settings.defaults()
        if INSTALLER_DRIVER_CHOICE_PATH.exists():
            try:
                installer_choice = json.loads(INSTALLER_DRIVER_CHOICE_PATH.read_text(encoding="utf-8"))
                choice = installer_choice.get("driver_install_option")
                if choice in DRIVER_INSTALL_OPTIONS:
                    defaults.driver_install_option = choice
                    defaults.driver_install_prompt_dismissed = choice == "Control panel only"
            except Exception:
                pass
        if not SETTINGS_PATH.exists():
            defaults.ensure_core_audio_policy()
            return defaults
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            for key, value in raw.items():
                if key == "endpoints":
                    endpoint_fields = Endpoint.__dataclass_fields__
                    defaults.endpoints = [Endpoint(**{field_name: item[field_name] for field_name in endpoint_fields if field_name in item}) for item in value]
                elif key == "routes":
                    route_fields = Route.__dataclass_fields__
                    defaults.routes = [Route(**{field_name: item[field_name] for field_name in route_fields if field_name in item}) for item in value]
                elif key == "effects":
                    effect_fields = EffectSlot.__dataclass_fields__
                    defaults.effects = [EffectSlot(**{field_name: item[field_name] for field_name in effect_fields if field_name in item}) for item in value]
                elif hasattr(defaults, key):
                    setattr(defaults, key, value)
            defaults.ensure_core_audio_policy()
            return defaults
        except Exception:
            defaults.ensure_core_audio_policy()
            return defaults

    def save(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


class PluginControlsDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, effect: EffectSlot, targets: list[str]) -> None:
        super().__init__(parent, title=f"{effect.name} controls", size=(560, 520))
        self.effect = effect
        self.parameter_sliders: dict[str, wx.Slider] = {}
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(root)

        root.Add(wx.StaticText(panel, label=f"Plug-in: {effect.name}"), 0, wx.ALL, 6)
        root.Add(wx.StaticText(panel, label=f"Format: {effect.fmt}"), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        path_text = wx.TextCtrl(panel, value=effect.path or "No plug-in file selected for this default rack slot.", style=wx.TE_READONLY)
        path_text.SetName("Plug-in file path")
        root.Add(path_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        root.Add(wx.StaticText(panel, label="Target route or bus:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        self.target_choice = wx.Choice(panel, choices=targets or [effect.target])
        if effect.target in (targets or []):
            self.target_choice.SetStringSelection(effect.target)
        elif self.target_choice.GetCount():
            self.target_choice.SetSelection(0)
        root.Add(self.target_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self.enabled_checkbox = wx.CheckBox(panel, label=f"Enable {effect.name}")
        self.enabled_checkbox.SetValue(effect.enabled)
        root.Add(self.enabled_checkbox, 0, wx.ALL, 6)

        self.bypass_checkbox = wx.CheckBox(panel, label=f"Bypass {effect.name}")
        self.bypass_checkbox.SetValue(effect.bypassed)
        root.Add(self.bypass_checkbox, 0, wx.ALL, 6)

        params = ASIOAFrame.effect_parameters(effect)
        for name, value in params.items():
            root.Add(wx.StaticText(panel, label=f"{name} percent:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
            slider = wx.Slider(panel, value=max(0, min(100, int(value))), minValue=0, maxValue=100, style=wx.SL_HORIZONTAL | wx.SL_LABELS)
            slider.SetName(f"{effect.name} {name} control")
            self.parameter_sliders[name] = slider
            root.Add(slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        note = wx.TextCtrl(
            panel,
            value=(
                "This is ASIOA's accessible rack control surface. It stores parameters for the selected plug-in and exposes them to the audio engine. "
                "Native vendor editor windows can be added later when the plug-in host can safely wrap them for screen readers."
            ),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
        )
        note.SetMinSize((-1, 90))
        root.Add(note, 0, wx.EXPAND | wx.ALL, 6)

        buttons = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        if buttons:
            root.Add(buttons, 0, wx.EXPAND | wx.ALL, 6)

    def apply_to_effect(self) -> None:
        self.effect.target = self.target_choice.GetStringSelection() or self.effect.target
        self.effect.enabled = self.enabled_checkbox.GetValue()
        self.effect.bypassed = self.bypass_checkbox.GetValue()
        self.effect.parameters = {name: slider.GetValue() for name, slider in self.parameter_sliders.items()}
        if "Mix" in self.effect.parameters:
            self.effect.wet = self.effect.parameters["Mix"]


class ASIOAFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, title=f"{APP_NAME} {APP_VERSION}", size=(1120, 780))
        self.settings = Settings.load()
        self.plugin_inventory = PluginInventory()
        self._plugin_scan_running = False
        self._update_check_running = False
        self._pending_overview_refresh = False
        self.status_text: wx.StaticText
        self.overview_view: wx.html2.WebView | wx.TextCtrl
        self.notebook: wx.Notebook
        self.route_list: wx.ListCtrl
        self.input_list: wx.ListCtrl
        self.output_list: wx.ListCtrl
        self.effects_list: wx.ListCtrl
        self.plugin_param_list: wx.ListCtrl
        self.driver_action_button: wx.Button | None = None
        self.route_source_choice: wx.Choice | None = None
        self.route_destination_choice: wx.Choice | None = None
        self.controls: dict[str, wx.Window] = {}
        self.route_action_buttons: dict[str, wx.Button] = {}
        self.endpoint_action_buttons: dict[int, dict[str, wx.Button]] = {}
        self._list_selection_memory: dict[int, int] = {}
        self._populating_lists = False
        self._force_exit = False
        self._last_escape_at: datetime | None = None
        self._last_overview_html = ""
        self._settings_dirty = False
        self._last_saved_payload = ""
        self._last_announced_status = ""
        self.status_history: list[str] = []
        self.tray_icon: ASIOATrayIcon | None = None
        self._build_menu()
        self._build_ui()
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_page_changed)
        self._build_tray_icon()
        self._bind_shortcuts()
        self._bind_autosave_events()
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        self.autosave_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_autosave_timer, self.autosave_timer)
        self.device_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_device_timer, self.device_timer)
        self.device_timer.Start(30000)
        self.plugin_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_plugin_timer, self.plugin_timer)
        self.plugin_timer.Start(PLUGIN_SCAN_INTERVAL_MS)
        self.Centre()
        self.SetStatus("ASIOA control panel ready. Open the Smart Buffer tab to tune latency and stability.")
        self.update_driver_action_visibility()
        self.update_overview()
        self.announce_startup_status()
        wx.CallAfter(self.start_plugin_scan)
        if self.settings.auto_check_updates:
            wx.CallLater(4500, lambda: self.check_for_updates(auto=True))
        self.play_sound("ready")
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _build_tray_icon(self) -> None:
        try:
            self.tray_icon = ASIOATrayIcon(self)
        except Exception:
            self.tray_icon = None

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
        self.Bind(wx.EVT_MENU, lambda _event: self.exit_application(), exit_item)
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

    def _bind_autosave_events(self) -> None:
        for key, control in self.controls.items():
            if isinstance(control, wx.Choice):
                control.Bind(wx.EVT_CHOICE, lambda _event, control_key=key: self.on_control_changed(control_key))
            elif isinstance(control, wx.CheckBox):
                control.Bind(wx.EVT_CHECKBOX, lambda _event, control_key=key: self.on_control_changed(control_key))
            elif isinstance(control, wx.Slider):
                control.Bind(wx.EVT_SLIDER, lambda _event, control_key=key: self.on_control_changed(control_key))

    def on_control_changed(self, key: str) -> None:
        self.collect_settings()
        self.mark_settings_dirty()
        self.update_overview()
        if key in {"monitor_volume", "dropout_recovery_ms", "sessionwire_noise_floor_db"}:
            value = getattr(self.settings, key)
            label = {
                "monitor_volume": "Default monitor volume",
                "dropout_recovery_ms": "Dropout recovery hold time",
                "sessionwire_noise_floor_db": "Sessionwire white-noise guard threshold",
            }.get(key, key.replace("_", " "))
            unit = " percent" if key == "monitor_volume" else (" dB" if key.endswith("_db") else " milliseconds")
            self.SetStatus(f"{label}, {value}{unit}.")
        elif key in {"driver_mode", "smart_buffer_mode", "sample_rate", "buffer_size", "minimum_buffer", "maximum_buffer", "target_latency_ms", "jitter_safety_ms", "default_monitor_device", "system_audio_master_pair", "screen_reader_master_pair", "screen_reader_output", "update_source", "update_channel"}:
            self.SetStatus(f"{key.replace('_', ' ').title()}, {getattr(self.settings, key)}.")
        elif key in {"monitor_in_app", "bypass_to_daw", "auto_raise_on_dropouts", "auto_lower_when_stable", "protect_daw_master_feedback", "live_effects_enabled", "vst3_enabled", "clap_enabled", "vst2_enabled", "sessionwire_white_noise_guard", "enable_builtin_sounds", "auto_check_updates", "run_on_startup", "start_minimized", "keep_engine_active"}:
            state = "on" if bool(getattr(self.settings, key)) else "off"
            self.SetStatus(f"{key.replace('_', ' ').title()}, {state}.")

    def mark_settings_dirty(self) -> None:
        self._settings_dirty = True
        self.autosave_timer.StartOnce(AUTOSAVE_DELAY_MS)

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
        close = wx.Button(panel, label="Minimize to tray")
        close.Bind(wx.EVT_BUTTON, lambda _event: self.minimize_to_tray("ASIOA minimized to the system tray."))
        button_row.Add(close, 0, wx.RIGHT, 8)
        root.Add(button_row, 0, wx.ALL, 8)

        self.status_text = wx.StaticText(panel, label="")
        root.Add(self.status_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

    def _add_overview_tab(self) -> None:
        panel, sizer = self._new_tab("Overview")
        self.overview_view = wx.html2.WebView.New(panel)
        self.overview_view.SetName("ASIOA overview")
        sizer.Add(self.overview_view, 1, wx.EXPAND | wx.ALL, 6)
        driver_button = wx.Button(panel, label="Install or repair ASIOA audio driver")
        driver_button.SetName("Install or repair ASIOA audio driver")
        driver_button.Bind(wx.EVT_BUTTON, lambda _event: self.install_or_repair_driver())
        self.driver_action_button = driver_button
        sizer.Add(driver_button, 0, wx.ALL, 6)

    def _add_routing_tab(self) -> None:
        panel, sizer = self._new_tab("Routing")
        choice_row = wx.BoxSizer(wx.HORIZONTAL)
        source_box = wx.BoxSizer(wx.VERTICAL)
        source_box.Add(wx.StaticText(panel, label="Route source:"), 0, wx.BOTTOM, 2)
        self.route_source_choice = wx.Choice(panel, choices=self.route_endpoint_choices())
        if self.route_source_choice.GetCount():
            self.route_source_choice.SetSelection(0)
        source_box.Add(self.route_source_choice, 0, wx.EXPAND)
        destination_box = wx.BoxSizer(wx.VERTICAL)
        destination_box.Add(wx.StaticText(panel, label="Route destination:"), 0, wx.BOTTOM, 2)
        self.route_destination_choice = wx.Choice(panel, choices=self.route_endpoint_choices())
        if self.route_destination_choice.GetCount():
            self.route_destination_choice.SetSelection(0)
        destination_box.Add(self.route_destination_choice, 0, wx.EXPAND)
        choice_row.Add(source_box, 1, wx.RIGHT, 8)
        choice_row.Add(destination_box, 1, wx.RIGHT, 8)
        sizer.Add(choice_row, 0, wx.EXPAND | wx.ALL, 6)
        self.route_list = self._make_list(
            panel,
            ["Source", "Destination", "Enabled", "Mute state", "Monitoring", "Volume"],
            "Configured audio routes",
        )
        sizer.Add(self.route_list, 1, wx.EXPAND | wx.ALL, 6)
        self.route_list.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda event: self.on_route_list_selection(event))
        self.route_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda _event: self.update_route_action_labels())
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        for key, label, handler in [
            ("add", "Add selected route", self.add_selected_route),
            ("mute", "Select a route to mute or unmute it", self.toggle_route_mute),
            ("volume_down", "Select a route to lower its volume 5 percent", lambda event: self.adjust_route_volume(-5, event)),
            ("volume_up", "Select a route to raise its volume 5 percent", lambda event: self.adjust_route_volume(5, event)),
            ("remove", "Select a route to remove it", self.remove_route),
        ]:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            button.Bind(wx.EVT_SET_FOCUS, lambda event, list_control=self.route_list: self.on_action_button_focus(event, list_control))
            self.route_action_buttons[key] = button
            buttons.Add(button, 0, wx.RIGHT, 6)
        sizer.Add(buttons, 0, wx.ALL, 6)
        self.populate_routes()
        self.ensure_list_selection(self.route_list)
        self.update_route_action_labels()

    def _add_inputs_tab(self) -> None:
        panel, sizer = self._new_tab("Inputs")
        self.input_list = self._make_list(
            panel,
            ["Name", "Kind", "Channels", "Role", "Enabled", "Monitoring", "Solo state", "Mute state", "Volume", "Buffer", "Noise guard"],
            "Input endpoints",
            checkboxes=True,
        )
        sizer.Add(self.input_list, 1, wx.EXPAND | wx.ALL, 6)
        self._add_endpoint_actions(panel, sizer, self.input_list)
        self.populate_endpoints()
        self.ensure_list_selection(self.input_list)
        self.update_endpoint_action_labels(self.input_list)

    def _add_outputs_tab(self) -> None:
        panel, sizer = self._new_tab("Outputs")
        self.output_list = self._make_list(
            panel,
            ["Name", "Kind", "Channels", "Role", "Enabled", "Monitoring", "Solo state", "Mute state", "Volume", "Buffer", "Noise guard"],
            "Output endpoints and DAW returns",
            checkboxes=True,
        )
        sizer.Add(self.output_list, 1, wx.EXPAND | wx.ALL, 6)
        self._add_endpoint_actions(panel, sizer, self.output_list)
        self.populate_endpoints()
        self.ensure_list_selection(self.output_list)
        self.update_endpoint_action_labels(self.output_list)

    def _add_monitoring_tab(self) -> None:
        panel, sizer = self._new_tab("Monitoring")
        self.controls["monitor_in_app"] = self._add_checkbox(panel, sizer, "Monitor directly in ASIOA", self.settings.monitor_in_app)
        self.controls["bypass_to_daw"] = self._add_checkbox(panel, sizer, "Bypass ASIOA monitoring and route directly through the DAW", self.settings.bypass_to_daw)
        self.controls["default_monitor_device"] = self._add_choice(
            panel,
            sizer,
            "Default monitoring output device:",
            self.monitor_device_choices(),
            self.settings.default_monitor_device,
        )
        self.controls["system_audio_master_pair"] = self._add_choice(
            panel,
            sizer,
            "System audio master pair:",
            ["Main output 1/2", *CHANNEL_PAIRS],
            self.settings.system_audio_master_pair,
        )
        self.controls["screen_reader_master_pair"] = self._add_choice(
            panel,
            sizer,
            "Screen reader and TTS default pair:",
            ["Main output 1/2", *CHANNEL_PAIRS],
            self.settings.screen_reader_master_pair,
        )
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
        self.controls["sessionwire_white_noise_guard"] = self._add_checkbox(
            panel,
            sizer,
            "Auto-mute Sessionwire monitoring when steady white noise is detected",
            self.settings.sessionwire_white_noise_guard,
        )
        self._add_slider(panel, sizer, "Sessionwire white-noise guard threshold in dB:", "sessionwire_noise_floor_db", self.settings.sessionwire_noise_floor_db, -90, -20)
        self._add_readonly_text(
            panel,
            sizer,
            "Device discovery:",
            "Devices are refreshed automatically in the background. The control panel keeps the selected item and action labels stable while the device lists refresh.",
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
        self.effects_list = self._make_list(panel, ["Effect", "Format", "Target", "Enabled", "State", "Wet", "Path"], "Live effects slots")
        sizer.Add(self.effects_list, 1, wx.EXPAND | wx.ALL, 6)
        self.effects_list.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda event: self.on_effect_list_selection(event))
        effects_buttons = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in [
            ("Add plug-in to rack", self.add_plugin_to_rack),
            ("Open selected plug-in controls", self.open_selected_plugin_controls),
            ("Toggle selected plug-in bypass", self.toggle_selected_plugin_bypass),
            ("Remove selected plug-in from rack", self.remove_selected_plugin),
        ]:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            button.Bind(wx.EVT_SET_FOCUS, lambda event, list_control=self.effects_list: self.on_action_button_focus(event, list_control))
            effects_buttons.Add(button, 0, wx.RIGHT, 6)
        sizer.Add(effects_buttons, 0, wx.ALL, 6)
        self.plugin_param_list = self._make_list(
            panel,
            ["Parameter", "Value", "Control type"],
            "Selected plug-in accessible parameters",
        )
        sizer.Add(self.plugin_param_list, 0, wx.EXPAND | wx.ALL, 6)
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

    def current_tab_name(self) -> str:
        if not hasattr(self, "notebook"):
            return ""
        index = self.notebook.GetSelection()
        if index == wx.NOT_FOUND:
            return ""
        return self.notebook.GetPageText(index)

    def on_notebook_page_changed(self, event: wx.BookCtrlEvent) -> None:
        if self.current_tab_name() == "Overview" and self._pending_overview_refresh:
            self._pending_overview_refresh = False
            wx.CallAfter(lambda: self.update_overview(force=True))
        event.Skip()

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

    def _make_list(self, parent: wx.Window, columns: list[str], name: str, checkboxes: bool = False) -> wx.ListCtrl:
        control = wx.ListCtrl(parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        control.SetName(name)
        if checkboxes and hasattr(control, "EnableCheckBoxes"):
            control.EnableCheckBoxes(True)
        for index, column in enumerate(columns):
            control.InsertColumn(index, column, width=wx.LIST_AUTOSIZE_USEHEADER)
        control.Bind(wx.EVT_SET_FOCUS, lambda event, list_control=control: self.on_list_focus(event, list_control))
        if checkboxes and hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
            control.Bind(wx.EVT_LIST_ITEM_CHECKED, self.on_list_item_checked)
        if checkboxes and hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
            control.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.on_list_item_checked)
        return control

    def _add_endpoint_actions(self, panel: wx.Panel, sizer: wx.BoxSizer, target: wx.ListCtrl) -> None:
        target.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda event: self.on_endpoint_list_selection(event, target))
        target.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda _event: self.update_endpoint_action_labels(target))
        row = wx.BoxSizer(wx.HORIZONTAL)
        actions = [
            ("enabled", "Select a channel to enable or disable it", lambda event: self.toggle_endpoint(target, "enabled", event)),
            ("monitor", "Select a channel to turn monitoring on or off", lambda event: self.toggle_endpoint(target, "monitor", event)),
            ("solo", "Select a channel to turn solo on or off", lambda event: self.toggle_endpoint(target, "solo", event)),
            ("muted", "Select a channel to mute or unmute it", lambda event: self.toggle_endpoint(target, "muted", event)),
            ("volume_down", "Select a channel to lower its volume 5 percent", lambda event: self.adjust_endpoint_volume(target, -5, event)),
            ("volume_up", "Select a channel to raise its volume 5 percent", lambda event: self.adjust_endpoint_volume(target, 5, event)),
        ]
        buttons: dict[str, wx.Button] = {}
        for key, label, handler in actions:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            button.Bind(wx.EVT_SET_FOCUS, lambda event, list_control=target: self.on_action_button_focus(event, list_control))
            buttons[key] = button
            row.Add(button, 0, wx.RIGHT, 6)
        self.endpoint_action_buttons[id(target)] = buttons
        sizer.Add(row, 0, wx.ALL, 6)

    def monitor_device_choices(self) -> list[str]:
        choices = [
            endpoint.name
            for endpoint in self.settings.endpoints
            if endpoint.kind in {"Default monitoring output", "DAW return", "Virtual bus", "System playback device", "Windows communication bridge output", "Windows bridge output pair"} or endpoint.monitor
        ]
        return choices or ["Main output 1/2"]

    def route_endpoint_choices(self) -> list[str]:
        choices = [endpoint.name for endpoint in self.settings.endpoints]
        return choices or ["Main output 1/2"]

    @staticmethod
    def is_feedback_risk(source: str, destination: str) -> bool:
        source_l = source.lower()
        destination_l = destination.lower()
        master_source = "main output 1/2" in source_l or "daw master" in source_l or "output 1/2" in source_l
        capture_destination = "system audio capture 1/2" in destination_l or "capture a" in destination_l or "input 1/2" in destination_l
        return master_source and capture_destination

    @staticmethod
    def set_choice_items(choice: wx.Choice | None, values: list[str], preferred: str | None = None) -> None:
        if choice is None:
            return
        current = preferred or choice.GetStringSelection()
        choice.Set(values)
        if current in values:
            choice.SetStringSelection(current)
        elif values:
            choice.SetSelection(0)

    def on_list_focus(self, event: wx.FocusEvent, control: wx.ListCtrl) -> None:
        self.ensure_list_selection(control)
        event.Skip()

    def on_action_button_focus(self, event: wx.FocusEvent, control: wx.ListCtrl) -> None:
        self.ensure_list_selection(control)
        if control is getattr(self, "route_list", None):
            self.update_route_action_labels()
        else:
            self.update_endpoint_action_labels(control)
        event.Skip()

    def on_route_list_selection(self, event: wx.ListEvent) -> None:
        self.remember_list_selection(self.route_list, event.GetIndex())
        self.update_route_action_labels()
        event.Skip()

    def on_endpoint_list_selection(self, event: wx.ListEvent, control: wx.ListCtrl) -> None:
        self.remember_list_selection(control, event.GetIndex())
        self.update_endpoint_action_labels(control)
        event.Skip()

    def on_effect_list_selection(self, event: wx.ListEvent) -> None:
        self.remember_list_selection(self.effects_list, event.GetIndex())
        self.populate_plugin_parameters()
        event.Skip()

    def remember_list_selection(self, control: wx.ListCtrl, index: int) -> None:
        if index >= 0:
            self._list_selection_memory[id(control)] = index

    def ensure_list_selection(self, control: wx.ListCtrl) -> int:
        selected = control.GetFirstSelected()
        if selected >= 0:
            self.remember_list_selection(control, selected)
            return selected
        count = control.GetItemCount()
        if count <= 0:
            return -1
        preferred = self._list_selection_memory.get(id(control), 0)
        index = max(0, min(preferred, count - 1))
        control.Select(index)
        control.Focus(index)
        control.EnsureVisible(index)
        self.remember_list_selection(control, index)
        return index

    def restore_list_selection(self, control: wx.ListCtrl, preferred_index: int | None = None, focus_row: bool = True) -> int:
        count = control.GetItemCount()
        if count <= 0:
            return -1
        if preferred_index is None:
            preferred_index = self._list_selection_memory.get(id(control), 0)
        index = max(0, min(preferred_index, count - 1))
        control.Select(index)
        if focus_row:
            control.Focus(index)
        control.EnsureVisible(index)
        self.remember_list_selection(control, index)
        return index

    def restore_endpoint_selection(self, control: wx.ListCtrl, endpoint_name: str | None, focus_row: bool = True) -> int:
        if endpoint_name:
            for row in range(control.GetItemCount()):
                if control.GetItemText(row, 0) == endpoint_name:
                    return self.restore_list_selection(control, row, focus_row=focus_row)
        return self.restore_list_selection(control, focus_row=focus_row)

    def populate_routes(self) -> None:
        self._populating_lists = True
        self.route_list.DeleteAllItems()
        for route in self.settings.routes:
            row = self._append_row(self.route_list, route.row())
            self._check_list_row(self.route_list, row, route.enabled)
        self._populating_lists = False

    def populate_endpoints(self) -> None:
        self._populating_lists = True
        for control, predicate in [
            (getattr(self, "input_list", None), lambda item: item.kind in {"Application or physical input", "Application", "Physical input", "System recording device", "Windows communication bridge input", "Windows bridge input pair"}),
            (getattr(self, "output_list", None), lambda item: item.kind in {"Default monitoring output", "DAW return", "Virtual bus", "System playback device", "Windows communication bridge output", "Windows bridge output pair"}),
        ]:
            if control is None:
                continue
            control.DeleteAllItems()
            for endpoint in self.settings.endpoints:
                if predicate(endpoint):
                    row = self._append_row(control, endpoint.row())
                    self._check_list_row(control, row, endpoint.enabled)
        self._populating_lists = False

    def populate_effects(self) -> None:
        self._populating_lists = True
        self.effects_list.DeleteAllItems()
        for effect in self.settings.effects:
            row = self._append_row(self.effects_list, effect.row())
            self._check_list_row(self.effects_list, row, effect.enabled)
        self._populating_lists = False
        self.ensure_list_selection(self.effects_list)
        self.populate_plugin_parameters()

    def populate_plugin_parameters(self) -> None:
        if not hasattr(self, "plugin_param_list"):
            return
        self.plugin_param_list.DeleteAllItems()
        effect = self.selected_effect()
        if effect is None:
            self._append_row(self.plugin_param_list, ["No plug-in selected", "None", "Status"])
            return
        params = self.effect_parameters(effect)
        for name, value in params.items():
            self._append_row(self.plugin_param_list, [name, f"{value} percent", "Accessible slider"])
        self.ensure_list_selection(self.plugin_param_list)

    @staticmethod
    def _append_row(control: wx.ListCtrl, values: list[str]) -> int:
        index = control.InsertItem(control.GetItemCount(), values[0])
        for column, value in enumerate(values[1:], start=1):
            control.SetItem(index, column, value)
        for column in range(len(values)):
            control.SetColumnWidth(column, wx.LIST_AUTOSIZE_USEHEADER)
        return index

    @staticmethod
    def _check_list_row(control: wx.ListCtrl, row: int, checked: bool) -> None:
        if row >= 0 and hasattr(control, "CheckItem"):
            try:
                control.CheckItem(row, checked)
            except Exception:
                pass

    def on_list_item_checked(self, event: wx.ListEvent) -> None:
        if self._populating_lists:
            event.Skip()
            return
        control = event.GetEventObject()
        if not isinstance(control, wx.ListCtrl):
            event.Skip()
            return
        row = event.GetIndex()
        checked = True
        if hasattr(control, "IsItemChecked"):
            try:
                checked = bool(control.IsItemChecked(row))
            except Exception:
                checked = True
        if control is getattr(self, "route_list", None):
            if 0 <= row < len(self.settings.routes):
                route = self.settings.routes[row]
                route.enabled = checked
                self.remember_list_selection(control, row)
                self.update_route_action_labels()
                self.mark_settings_dirty()
                self.SetStatus(f"{self.route_action_name(route)}, {'enabled' if checked else 'disabled'}.")
        elif control is getattr(self, "input_list", None) or control is getattr(self, "output_list", None):
            endpoint = self.endpoint_for_row(control, row)
            if endpoint is not None:
                endpoint.enabled = checked
                self.remember_list_selection(control, row)
                self.update_endpoint_action_labels(control)
                self.mark_settings_dirty()
                self.SetStatus(f"{self.endpoint_action_name(endpoint)}, {'enabled' if checked else 'disabled'}.")
        elif control is getattr(self, "effects_list", None) and 0 <= row < len(self.settings.effects):
            effect = self.settings.effects[row]
            effect.enabled = checked
            self.remember_list_selection(control, row)
            self.mark_settings_dirty()
            self.SetStatus(f"{effect.name}, {'enabled' if checked else 'disabled'}.")
        event.Skip()

    def selected_index(self, control: wx.ListCtrl) -> int:
        return self.ensure_list_selection(control)

    def selected_route(self) -> Route | None:
        index = self.selected_index(self.route_list)
        if index < 0 or index >= len(self.settings.routes):
            return None
        return self.settings.routes[index]

    def selected_effect(self) -> EffectSlot | None:
        if not hasattr(self, "effects_list"):
            return None
        index = self.selected_index(self.effects_list)
        if index < 0 or index >= len(self.settings.effects):
            return None
        return self.settings.effects[index]

    @staticmethod
    def effect_parameters(effect: EffectSlot) -> dict[str, int]:
        if not effect.parameters:
            effect.parameters = {
                "Input gain": 100,
                "Output gain": 100,
                "Mix": effect.wet,
                "Bypass": 100 if effect.bypassed else 0,
            }
        return effect.parameters

    def route_action_name(self, route: Route) -> str:
        return f"{route.source} to {route.destination}"

    def update_route_action_labels(self) -> None:
        route = self.selected_route() if hasattr(self, "route_list") else None
        if route is None:
            labels = {
                "mute": "Select a route to mute or unmute it",
                "volume_down": "Select a route to lower its volume 5 percent",
                "volume_up": "Select a route to raise its volume 5 percent",
                "remove": "Select a route to remove it",
            }
        else:
            name = self.route_action_name(route)
            labels = {
                "mute": f"{'Unmute' if route.muted else 'Mute'} {name}",
                "volume_down": f"Lower {name} volume 5 percent",
                "volume_up": f"Raise {name} volume 5 percent",
                "remove": f"Remove route {name}",
            }
        for key, label in labels.items():
            button = self.route_action_buttons.get(key)
            if button:
                button.SetLabel(label)
                button.SetName(label)

    def endpoint_action_name(self, endpoint: Endpoint) -> str:
        return f"{endpoint.name}, channels {endpoint.channels}"

    def endpoint_summary(self, endpoint: Endpoint) -> str:
        return (
            f"{endpoint.name}, channels {endpoint.channels}, "
            f"role {endpoint.role}, "
            f"{'enabled' if endpoint.enabled else 'disabled'}, "
            f"{'monitoring on' if endpoint.monitor else 'monitoring off'}, "
            f"{'solo on' if endpoint.solo else 'solo off'}, "
            f"{'muted' if endpoint.muted else 'not muted'}, "
            f"volume {endpoint.volume} percent, "
            f"buffer {endpoint.buffer_override}, "
            f"{'white-noise guard on' if endpoint.white_noise_guard else 'white-noise guard off'}"
        )

    def route_summary(self, route: Route) -> str:
        return (
            f"{route.source} to {route.destination}, "
            f"{'enabled' if route.enabled else 'disabled'}, "
            f"{'muted' if route.muted else 'not muted'}, "
            f"{'monitoring on' if route.monitor else 'monitoring off'}, "
            f"volume {route.volume} percent"
        )

    def update_endpoint_action_labels(self, control: wx.ListCtrl) -> None:
        endpoint = self.endpoint_for_row(control, self.selected_index(control))
        buttons = self.endpoint_action_buttons.get(id(control), {})
        if endpoint is None:
            labels = {
                "enabled": "Select a channel to enable or disable it",
                "monitor": "Select a channel to turn monitoring on or off",
                "solo": "Select a channel to turn solo on or off",
                "muted": "Select a channel to mute or unmute it",
                "volume_down": "Select a channel to lower its volume 5 percent",
                "volume_up": "Select a channel to raise its volume 5 percent",
            }
        else:
            name = self.endpoint_action_name(endpoint)
            labels = {
                "enabled": f"{'Disable' if endpoint.enabled else 'Enable'} {name}",
                "monitor": f"{'Turn monitoring off for' if endpoint.monitor else 'Turn monitoring on for'} {name}",
                "solo": f"{'Turn solo off for' if endpoint.solo else 'Turn solo on for'} {name}",
                "muted": f"{'Unmute' if endpoint.muted else 'Mute'} {name}",
                "volume_down": f"Lower {name} volume 5 percent",
                "volume_up": f"Raise {name} volume 5 percent",
            }
        for key, label in labels.items():
            button = buttons.get(key)
            if button:
                button.SetLabel(label)
                button.SetName(label)

    @staticmethod
    def refocus_action_button(event_or_window: wx.Event | wx.Window | None) -> None:
        if event_or_window is None:
            return
        window = event_or_window.GetEventObject() if isinstance(event_or_window, wx.Event) else event_or_window
        if isinstance(window, wx.Window):
            wx.CallAfter(window.SetFocus)

    def add_selected_route(self, _event: wx.CommandEvent) -> None:
        source = self.route_source_choice.GetStringSelection() if self.route_source_choice else "DAW cue return 3/4"
        destination = self.route_destination_choice.GetStringSelection() if self.route_destination_choice else "System audio capture 1/2"
        if not source or not destination:
            self.SetStatus("Choose a route source and destination first.")
            self.refocus_action_button(_event)
            return
        if source == destination:
            self.SetStatus(f"Route not added. {source} cannot route to itself.")
            self.refocus_action_button(_event)
            return
        if self.settings.protect_daw_master_feedback and self.is_feedback_risk(source, destination):
            self.SetStatus(f"Route not added. Feedback guard blocked {source} to {destination}.")
            self.refocus_action_button(_event)
            return
        if any(route.source == source and route.destination == destination for route in self.settings.routes):
            self.SetStatus(f"Route already exists: {source} to {destination}.")
            self.refocus_action_button(_event)
            return
        self.settings.routes.append(Route(source, destination, volume=100))
        self.populate_routes()
        self.restore_list_selection(self.route_list, len(self.settings.routes) - 1, focus_row=False)
        self.update_route_action_labels()
        self.mark_settings_dirty()
        self.SetStatus(f"Added route {source} to {destination}.")
        self.refocus_action_button(_event)

    def toggle_route_mute(self, _event: wx.CommandEvent) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        route = self.settings.routes[index]
        route.muted = not route.muted
        self.populate_routes()
        self.restore_list_selection(self.route_list, index, focus_row=False)
        self.update_route_action_labels()
        self.mark_settings_dirty()
        self.SetStatus(f"{self.route_action_name(route)}, {'muted' if route.muted else 'unmuted'}.")
        self.refocus_action_button(_event)

    def adjust_route_volume(self, delta: int, event: wx.Event | None = None) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        route = self.settings.routes[index]
        route.volume = max(0, min(150, route.volume + delta))
        self.populate_routes()
        self.restore_list_selection(self.route_list, index, focus_row=False)
        self.update_route_action_labels()
        self.mark_settings_dirty()
        self.SetStatus(f"{self.route_action_name(route)}, volume {route.volume} percent.")
        self.refocus_action_button(event)

    def remove_route(self, _event: wx.CommandEvent) -> None:
        index = self.selected_index(self.route_list)
        if index < 0:
            self.SetStatus("No route selected.")
            return
        removed = self.settings.routes[index]
        del self.settings.routes[index]
        self.populate_routes()
        self.restore_list_selection(self.route_list, index, focus_row=False)
        self.update_route_action_labels()
        self.mark_settings_dirty()
        self.SetStatus(f"Removed route {self.route_action_name(removed)}.")
        self.refocus_action_button(_event)

    def add_plugin_to_rack(self, event: wx.CommandEvent) -> None:
        wildcard = "Audio plug-ins (*.vst3;*.clap;*.dll)|*.vst3;*.clap;*.dll|VST3 plug-ins (*.vst3)|*.vst3|CLAP plug-ins (*.clap)|*.clap|Legacy VST2 DLLs (*.dll)|*.dll|All files (*.*)|*.*"
        dialog = wx.FileDialog(
            self,
            "Choose a VST3, CLAP, or legacy VST2 plug-in",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                self.SetStatus("Add plug-in canceled.")
                self.refocus_action_button(event)
                return
            path = Path(dialog.GetPath())
        finally:
            dialog.Destroy()
        fmt = self.plugin_format_for_path(path)
        if fmt == "VST2 legacy" and not self.settings.vst2_enabled:
            self.SetStatus("Legacy VST2 plug-in not added because legacy VST2 support is disabled.")
            self.refocus_action_button(event)
            return
        effect = EffectSlot(
            path.stem,
            fmt,
            self.settings.default_monitor_device,
            enabled=self.settings.live_effects_enabled,
            bypassed=not self.settings.live_effects_enabled,
            wet=100,
            path=str(path),
        )
        self.settings.effects.append(effect)
        self.populate_effects()
        self.restore_list_selection(self.effects_list, len(self.settings.effects) - 1, focus_row=False)
        self.populate_plugin_parameters()
        self.mark_settings_dirty()
        self.SetStatus(f"Added {effect.name}, {effect.fmt}, to the plug-in rack.")
        self.refocus_action_button(event)

    @staticmethod
    def plugin_format_for_path(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".clap":
            return "CLAP"
        if suffix == ".vst3":
            return "VST3"
        if suffix == ".dll":
            return "VST2 legacy"
        return "Unknown plug-in"

    def toggle_selected_plugin_bypass(self, event: wx.CommandEvent) -> None:
        effect = self.selected_effect()
        if effect is None:
            self.SetStatus("No plug-in selected.")
            self.refocus_action_button(event)
            return
        effect.bypassed = not effect.bypassed
        effect.enabled = not effect.bypassed
        self.effect_parameters(effect)["Bypass"] = 100 if effect.bypassed else 0
        index = self.selected_index(self.effects_list)
        self.populate_effects()
        self.restore_list_selection(self.effects_list, index, focus_row=False)
        self.mark_settings_dirty()
        self.SetStatus(f"{effect.name}, {'bypassed' if effect.bypassed else 'active'}.")
        self.refocus_action_button(event)

    def remove_selected_plugin(self, event: wx.CommandEvent) -> None:
        index = self.selected_index(self.effects_list)
        if index < 0 or index >= len(self.settings.effects):
            self.SetStatus("No plug-in selected.")
            self.refocus_action_button(event)
            return
        effect = self.settings.effects[index]
        if effect.name.startswith("No ") or effect.name == "Legacy VST2 disabled":
            self.SetStatus(f"{effect.name} is a default rack slot and was not removed.")
            self.refocus_action_button(event)
            return
        del self.settings.effects[index]
        self.populate_effects()
        self.restore_list_selection(self.effects_list, index, focus_row=False)
        self.mark_settings_dirty()
        self.SetStatus(f"Removed {effect.name} from the plug-in rack.")
        self.refocus_action_button(event)

    def open_selected_plugin_controls(self, event: wx.CommandEvent) -> None:
        effect = self.selected_effect()
        if effect is None:
            self.SetStatus("No plug-in selected.")
            self.refocus_action_button(event)
            return
        dialog = PluginControlsDialog(self, effect, self.route_endpoint_choices())
        try:
            if dialog.ShowModal() == wx.ID_OK:
                dialog.apply_to_effect()
                index = self.selected_index(self.effects_list)
                self.populate_effects()
                self.restore_list_selection(self.effects_list, index, focus_row=False)
                self.mark_settings_dirty()
                self.SetStatus(f"Updated controls for {effect.name}.")
            else:
                self.SetStatus(f"Closed controls for {effect.name} without changes.")
        finally:
            dialog.Destroy()
        self.refocus_action_button(event)

    def endpoint_for_row(self, control: wx.ListCtrl, row: int) -> Endpoint | None:
        if row < 0:
            return None
        name = control.GetItemText(row, 0)
        return next((item for item in self.settings.endpoints if item.name == name), None)

    def toggle_endpoint(self, control: wx.ListCtrl, attr: str, event: wx.Event | None = None) -> None:
        endpoint = self.endpoint_for_row(control, self.selected_index(control))
        if endpoint is None:
            self.SetStatus("No endpoint selected.")
            return
        endpoint_name = endpoint.name
        setattr(endpoint, attr, not getattr(endpoint, attr))
        self.populate_endpoints()
        self.restore_endpoint_selection(control, endpoint_name, focus_row=False)
        self.update_endpoint_action_labels(control)
        self.mark_settings_dirty()
        if attr == "muted":
            state = "muted" if endpoint.muted else "unmuted"
            self.SetStatus(f"{self.endpoint_action_name(endpoint)}, {state}.")
        elif attr == "monitor":
            state = "on" if endpoint.monitor else "off"
            self.SetStatus(f"Monitoring for {self.endpoint_action_name(endpoint)}, {state}.")
        elif attr == "solo":
            state = "on" if endpoint.solo else "off"
            self.SetStatus(f"Solo for {self.endpoint_action_name(endpoint)}, {state}.")
        elif attr == "enabled":
            state = "enabled" if endpoint.enabled else "disabled"
            self.SetStatus(f"{self.endpoint_action_name(endpoint)}, {state}.")
        else:
            self.SetStatus(f"{endpoint.name} {attr.replace('_', ' ')} updated.")
        self.refocus_action_button(event)

    def adjust_endpoint_volume(self, control: wx.ListCtrl, delta: int, event: wx.Event | None = None) -> None:
        endpoint = self.endpoint_for_row(control, self.selected_index(control))
        if endpoint is None:
            self.SetStatus("No endpoint selected.")
            return
        endpoint_name = endpoint.name
        endpoint.volume = max(0, min(150, endpoint.volume + delta))
        self.populate_endpoints()
        self.restore_endpoint_selection(control, endpoint_name, focus_row=False)
        self.update_endpoint_action_labels(control)
        self.mark_settings_dirty()
        self.SetStatus(f"{self.endpoint_action_name(endpoint)}, volume {endpoint.volume} percent.")
        self.refocus_action_button(event)

    def collect_settings(self) -> None:
        for key, control in self.controls.items():
            if isinstance(control, wx.Choice):
                setattr(self.settings, key, control.GetStringSelection())
            elif isinstance(control, wx.CheckBox):
                setattr(self.settings, key, control.GetValue())
            elif isinstance(control, wx.Slider):
                setattr(self.settings, key, control.GetValue())

    def driver_package_path(self) -> Path:
        return resource_path("driver", "install-asioa-driver.ps1")

    def driver_dll_package_path(self) -> Path:
        return resource_path("driver", "ASIOA.Driver.dll")

    def driver_marker_path(self) -> Path:
        return SETTINGS_PATH.parent / "driver-installed.json"

    def installed_driver_health(self) -> DriverHealth:
        package_available = self.driver_package_path().exists() and self.driver_dll_package_path().exists()
        marker_present = self.driver_marker_path().exists()
        health = DriverHealth(
            package_available=package_available,
            marker_present=marker_present,
            windows_endpoint_names=discover_asioa_windows_endpoints(),
        )
        if winreg is None:
            health.error = "Windows registry access is unavailable in this runtime."
            return health
        views = [0]
        for view_name in ("KEY_WOW64_64KEY", "KEY_WOW64_32KEY"):
            view = getattr(winreg, view_name, 0)
            if view and view not in views:
                views.append(view)
        errors: list[str] = []
        for view in views:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ASIOA_DRIVER_REGISTRY_PATH, 0, winreg.KEY_READ | view) as asio_key:
                    clsid, _kind = winreg.QueryValueEx(asio_key, "CLSID")
                clsid_key_path = rf"SOFTWARE\Classes\CLSID\{clsid}\InprocServer32"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ | view) as clsid_key:
                    dll_path, _kind = winreg.QueryValueEx(clsid_key, None)
                health.registered = True
                health.dll_path = str(dll_path)
                health.dll_exists = Path(str(dll_path)).exists()
                if not health.dll_exists:
                    health.error = f"Registered driver DLL was not found at {dll_path}."
                return health
            except OSError as exc:
                errors.append(str(exc))
        if marker_present and not health.registered:
            health.error = "A previous install marker exists, but Windows ASIO registration was not found."
        elif errors:
            health.error = errors[-1]
        return health

    def is_driver_installed(self) -> bool:
        return self.installed_driver_health().healthy

    def driver_status_lines(self) -> list[str]:
        health = self.installed_driver_health()
        if health.healthy:
            install_state = "The ASIOA native ASIO driver is installed, registered with Windows ASIO, and the registered driver DLL is present."
        elif health.registered and not health.dll_exists:
            install_state = "The ASIOA native ASIO driver registration exists, but the registered DLL is missing. Repair the ASIO driver before using it from ASIO hosts."
        elif health.package_available:
            install_state = "The ASIOA native ASIO driver package is available for install or repair."
        else:
            install_state = "The ASIOA control panel is installed. The native ASIO driver package is not bundled with this build yet."
        if health.windows_endpoint_present:
            endpoint_state = "Windows-visible ASIOA endpoint detected: " + ", ".join(health.windows_endpoint_names) + "."
        else:
            endpoint_state = "Windows-visible ASIOA speaker or microphone endpoint is not detected yet. Ordinary Windows apps can still use their normal devices while ASIOA models the communication bridge."
        lines = [
            install_state,
            endpoint_state,
            "The current packaged driver exposes the ASIOA 68-in and 68-out ASIO surface to ASIO-capable hosts. The Windows WDM, WASAPI, and DirectSound endpoint layer is the next native-driver milestone.",
            "miniaudio, WASAPI, PortAudio, JACK, and ASIO4ALL compatibility modes remain available for control-panel configuration, device discovery, and bridge planning.",
        ]
        if health.dll_path:
            lines.append(f"Registered driver DLL: {health.dll_path}.")
        if health.error and not health.healthy:
            lines.append(f"Driver health note: {health.error}")
        return lines

    def driver_capability_map(self) -> list[DriverCapability]:
        health = self.installed_driver_health()
        asio_status = "available" if health.healthy else ("repair needed" if health.registered else "not installed")
        windows_status = "detected" if health.windows_endpoint_present else "not exposed yet"
        return [
            DriverCapability(
                "ASIO host surface",
                asio_status,
                "This is the native 68 input and 68 output ASIO driver used by DAWs and ASIO-aware audio software.",
            ),
            DriverCapability(
                "Communication bridge 1/2 model",
                "configured",
                "ASIOA maps Windows app audio intent to ASIOA Communication input 1/2 and output 1/2 in the routing model, with feedback protection on by default.",
            ),
            DriverCapability(
                "Windows WDM/WASAPI/DirectSound endpoint",
                windows_status,
                "This must appear as an actual Windows speaker or microphone device before apps like TeamTalk can pick ASIOA directly without an ASIO host.",
            ),
            DriverCapability(
                "Per-application WASAPI capture",
                "planned native engine work",
                "The control panel can discover devices now; process-loopback capture and app-to-route binding still need the native engine worker.",
            ),
            DriverCapability(
                "System sound device routing",
                "modeled and selectable",
                "Detected Windows sound devices are added as routable monitoring and input choices so the future engine can patch them without changing the UI shape.",
            ),
        ]

    def update_driver_action_visibility(self) -> None:
        if self.driver_action_button is None:
            return
        health = self.installed_driver_health()
        if health.healthy:
            self.driver_action_button.Hide()
            self.driver_action_button.SetLabel("ASIOA audio driver installed and healthy")
            self.driver_action_button.SetName("ASIOA audio driver installed and healthy")
        elif health.package_available:
            self.driver_action_button.Show()
            label = "Install or repair ASIOA audio driver"
            self.driver_action_button.SetLabel(label)
            self.driver_action_button.SetName(label)
        else:
            self.driver_action_button.Hide()
            self.driver_action_button.SetLabel("ASIOA audio driver package not bundled")
            self.driver_action_button.SetName("ASIOA audio driver package not bundled")
        self.driver_action_button.GetParent().Layout()

    def show_driver_install_alert_if_needed(self) -> None:
        if self.installed_driver_health().healthy:
            return
        if self.settings.driver_install_prompt_dismissed:
            return
        if self.settings.driver_install_option == "Control panel only":
            return
        message = (
            "Audio driver installation is required before ASIOA Audio Router can be used system-wide by DAWs and ASIO-linked devices.\n\n"
            "Choose Yes to install or repair the driver now.\n"
            "Choose No to keep using the control panel and install the driver later from the Overview or Devices tab."
        )
        result = wx.MessageBox(message, "ASIOA audio driver installation", wx.YES_NO | wx.ICON_INFORMATION, self)
        if result == wx.YES:
            self.install_or_repair_driver()
        else:
            self.settings.driver_install_prompt_dismissed = True
            self.settings.driver_install_option = "Ask me later"
            self.settings.save()
            self.update_overview()
            self.SetStatus("Driver installation deferred. Use the Overview or Devices tab when you are ready.")

    def install_or_repair_driver(self) -> None:
        health = self.installed_driver_health()
        if health.healthy:
            self.SetStatus("ASIOA native ASIO driver is already installed and healthy. No repair is needed.")
            self.update_driver_action_visibility()
            return
        package = self.driver_package_path()
        if not package.exists():
            self.SetStatus("ASIOA native ASIO driver package is not bundled with this build yet. The control panel remains available.")
            wx.MessageBox(
                "The ASIOA control panel is installed, but the native ASIO driver package is not bundled with this build yet.\n\n"
                "You can still configure routes, smart buffer behavior, effects policy, accessibility routing, and diagnostics. "
                "When the ASIO driver package is included, this button will install or repair it. "
                "The Windows WDM/WASAPI endpoint driver is a separate native-driver milestone.",
                "ASIOA ASIO driver not bundled",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return
        command = [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(package),
        ]
        try:
            subprocess.Popen(command, shell=False)
            self.SetStatus("ASIOA driver installer launched. Follow the installer prompts and restart audio applications after it finishes.")
            wx.CallLater(3000, self.update_driver_action_visibility)
            self.play_sound("notification")
        except OSError as exc:
            self.SetStatus(f"Could not launch ASIOA driver installer: {exc}.")
            self.play_sound("error")

    def engine_restart_required(self) -> bool:
        restart_keys = {
            "driver_mode",
            "sample_rate",
            "buffer_size",
            "minimum_buffer",
            "maximum_buffer",
        }
        try:
            saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8")) if SETTINGS_PATH.exists() else {}
        except Exception:
            saved = {}
        return any(str(saved.get(key, getattr(self.settings, key, ""))) != str(getattr(self.settings, key, "")) for key in restart_keys)

    def queue_engine_patch(self, section: str, restart_required: bool) -> Path:
        queue_dir = SETTINGS_PATH.parent / "engine-patches"
        queue_dir.mkdir(parents=True, exist_ok=True)
        patch = {
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "section": section,
            "restartRequired": restart_required,
            "settings": asdict(self.settings),
        }
        path = queue_dir / f"engine-patch-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path.write_text(json.dumps(patch, indent=2), encoding="utf-8")
        return path

    def settings_payload(self) -> str:
        return json.dumps(asdict(self.settings), indent=2, sort_keys=True)

    def backup_settings(self, payload: str) -> None:
        SETTINGS_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = SETTINGS_BACKUP_DIR / f"asioa-settings-{stamp}"
        flx = base.with_suffix(".flx")
        flxx = base.with_suffix(".flxx")
        flx.write_text(payload, encoding="utf-8")
        with gzip.open(flxx, "wt", encoding="utf-8") as compressed:
            compressed.write(payload)
        backups = sorted(SETTINGS_BACKUP_DIR.glob("asioa-settings-*.flx"), key=lambda item: item.stat().st_mtime, reverse=True)
        for old in backups[20:]:
            old.unlink(missing_ok=True)
            old.with_suffix(".flxx").unlink(missing_ok=True)

    def restart_audio_engine_if_needed(self, restart_required: bool) -> None:
        if not restart_required:
            self.SetStatus("Settings were sent to the ASIOA engine without restarting audio.")
            return
        restart_script = resource_path("engine", "restart-asioa-engine.ps1")
        if restart_script.exists():
            subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(restart_script)], shell=False)
            self.SetStatus("Settings were sent to the ASIOA engine. The audio engine restart was launched because driver or buffer settings changed.")
            return
        self.SetStatus("Settings were sent to the ASIOA engine. A restart is required when the native engine is running, but the restart helper is not bundled yet.")

    def save_settings(self) -> None:
        self.collect_settings()
        payload = self.settings_payload()
        self.settings.save()
        if payload != self._last_saved_payload:
            self.backup_settings(payload)
            self._last_saved_payload = payload
        self.update_overview()
        self._settings_dirty = False
        self.SetStatus("Settings saved automatically.")
        self.play_sound("success")

    def apply_to_engine(self) -> None:
        self.collect_settings()
        restart_required = self.engine_restart_required()
        payload = self.settings_payload()
        self.settings.save()
        if payload != self._last_saved_payload:
            self.backup_settings(payload)
            self._last_saved_payload = payload
        patch = self.queue_engine_patch("current-tab", restart_required)
        self.update_overview()
        self.restart_audio_engine_if_needed(restart_required)
        self._settings_dirty = False
        self.append_status_history(f"Engine patch file: {patch}")
        self.play_sound("notification")

    def autosave_and_hot_apply(self) -> None:
        if not self._settings_dirty:
            return
        self.apply_to_engine()

    def on_autosave_timer(self, _event: wx.TimerEvent) -> None:
        self.autosave_and_hot_apply()

    def on_char_hook(self, event: wx.KeyEvent) -> None:
        if event.GetKeyCode() != wx.WXK_ESCAPE:
            self._last_escape_at = None
            event.Skip()
            return
        now = datetime.now()
        if self._last_escape_at and (now - self._last_escape_at).total_seconds() <= 1.4:
            self._last_escape_at = None
            self.minimize_to_tray("ASIOA minimized to the system tray after double Escape.")
            return
        self._last_escape_at = now
        event.Skip()

    def minimize_to_tray(self, message: str) -> None:
        self.autosave_and_hot_apply()
        self.Iconize(True)
        self.Hide()
        self.SetStatus(message)
        self.play_sound("notification")

    def restore_from_tray(self) -> None:
        self.Show(True)
        self.Iconize(False)
        self.Raise()
        self.SetFocus()
        self.SetStatus("ASIOA restored from the system tray.")

    def exit_application(self) -> None:
        self._force_exit = True
        self.autosave_and_hot_apply()
        if self.tray_icon is not None:
            self.tray_icon.RemoveIcon()
            self.tray_icon.Destroy()
            self.tray_icon = None
        self.Destroy()

    def on_close(self, event: wx.CloseEvent) -> None:
        self.autosave_and_hot_apply()
        if self._force_exit or not self.settings.keep_engine_active:
            event.Skip()
            return
        if event.CanVeto():
            event.Veto()
        self.minimize_to_tray("ASIOA is still running in the system tray so audio routes stay active.")

    def refresh_devices(self) -> None:
        previous_count = len(self.settings.endpoints)
        self.settings.ensure_windows_audio_devices()
        choices = self.route_endpoint_choices()
        self.set_choice_items(self.route_source_choice, choices)
        self.set_choice_items(self.route_destination_choice, choices)
        monitor_control = self.controls.get("default_monitor_device")
        if isinstance(monitor_control, wx.Choice):
            self.set_choice_items(monitor_control, self.monitor_device_choices(), self.settings.default_monitor_device)
        if len(self.settings.endpoints) != previous_count:
            self.populate_endpoints()
            self.mark_settings_dirty()
            self.SetStatus(f"Audio device list updated. {len(self.settings.endpoints) - previous_count} new routable endpoint entries added.")
        self.update_overview()

    def on_device_timer(self, _event: wx.TimerEvent) -> None:
        self.refresh_devices()

    def on_plugin_timer(self, _event: wx.TimerEvent) -> None:
        self.start_plugin_scan()

    def plugin_search_roots(self) -> list[tuple[Path, str]]:
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        common_files = Path(os.environ.get("CommonProgramFiles", str(program_files / "Common Files")))
        local_app_data = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        roaming_app_data = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        return [
            (common_files / "VST3", "vst3"),
            (common_files / "CLAP", "clap"),
            (program_files / "Common Files" / "VST3", "vst3"),
            (program_files / "Common Files" / "CLAP", "clap"),
            (program_files / "VSTPlugins", "vst2"),
            (program_files / "Steinberg" / "VSTPlugins", "vst2"),
            (program_files_x86 / "VSTPlugins", "vst2"),
            (program_files_x86 / "Steinberg" / "VSTPlugins", "vst2"),
            (local_app_data / "Programs" / "Common" / "VST3", "vst3"),
            (local_app_data / "Programs" / "Common" / "CLAP", "clap"),
            (roaming_app_data / "VST3", "vst3"),
            (roaming_app_data / "CLAP", "clap"),
        ]

    def start_plugin_scan(self) -> None:
        if self._plugin_scan_running:
            return
        self._plugin_scan_running = True
        self.plugin_inventory.scanning = True
        thread = threading.Thread(target=self.scan_plugins_worker, name="ASIOAPluginScanner", daemon=True)
        thread.start()

    def scan_plugins_worker(self) -> None:
        counts = {"vst3": 0, "clap": 0, "vst2": 0}
        scanned_paths = 0
        for root, kind in self.plugin_search_roots():
            if not root.exists():
                continue
            scanned_paths += 1
            try:
                if kind == "vst3":
                    counts[kind] += sum(1 for _item in root.rglob("*.vst3"))
                elif kind == "clap":
                    counts[kind] += sum(1 for _item in root.rglob("*.clap"))
                else:
                    counts[kind] += sum(1 for _item in root.rglob("*.dll"))
            except (OSError, PermissionError):
                continue
        wx.CallAfter(self.finish_plugin_scan, counts, scanned_paths)

    def finish_plugin_scan(self, counts: dict[str, int], scanned_paths: int) -> None:
        changed = (
            self.plugin_inventory.last_scan == "Not scanned yet"
            or self.plugin_inventory.vst3 != counts.get("vst3", 0)
            or self.plugin_inventory.clap != counts.get("clap", 0)
            or self.plugin_inventory.vst2 != counts.get("vst2", 0)
            or self.plugin_inventory.scanned_paths != scanned_paths
        )
        self.plugin_inventory = PluginInventory(
            vst3=counts.get("vst3", 0),
            clap=counts.get("clap", 0),
            vst2=counts.get("vst2", 0),
            scanned_paths=scanned_paths,
            last_scan=datetime.now().strftime("%I:%M %p").lstrip("0"),
            scanning=False,
        )
        self._plugin_scan_running = False
        if changed:
            self.update_overview()
            self.SetStatus(
                f"Plug-in scan complete. Found {self.plugin_inventory.vst3} VST3, {self.plugin_inventory.clap} CLAP, and {self.plugin_inventory.vst2} legacy VST2 plug-ins."
            )

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

    def check_for_updates(self, auto: bool = False) -> None:
        if self._update_check_running:
            if not auto:
                self.SetStatus("Update check is already running.")
            return
        self._update_check_running = True
        if not auto:
            self.SetStatus("Checking for ASIOA updates.")
        thread = threading.Thread(target=self.update_check_worker, args=(auto,), name="ASIOAUpdateCheck", daemon=True)
        thread.start()

    def update_check_worker(self, auto: bool) -> None:
        try:
            update = self.fetch_update_manifest()
            wx.CallAfter(self.finish_update_check, update, auto, "")
        except Exception as exc:
            wx.CallAfter(self.finish_update_check, None, auto, str(exc))

    def fetch_update_manifest(self) -> UpdateInfo:
        last_error = ""
        for url in self.update_manifest_urls():
            try:
                with urllib.request.urlopen(url, timeout=12) as response:
                    payload = response.read(512 * 1024)
                data = json.loads(payload.decode("utf-8", errors="replace"))
                return UpdateInfo(
                    version=str(data.get("version", "") or data.get("appVersion", "") or data.get("tag", "")).lstrip("v"),
                    channel=str(data.get("channel", "Stable")),
                    notes=str(data.get("notes", "") or data.get("releaseNotes", "")),
                    installer_url=str(data.get("installerUrl", "") or data.get("windowsInstallerUrl", "")),
                    portable_url=str(data.get("portableUrl", "") or data.get("windowsPortableUrl", "")),
                    page_url=str(data.get("pageUrl", "") or data.get("releaseUrl", "")),
                )
            except Exception as exc:
                last_error = f"{url}: {exc}"
        raise RuntimeError(last_error or "No update manifest could be read.")

    def update_manifest_urls(self) -> list[str]:
        if self.settings.update_source == "GitHub only":
            return [UPDATE_MANIFEST_URLS[1]]
        if self.settings.update_source == "Gitea only when available":
            return [UPDATE_MANIFEST_URLS[2]]
        if self.settings.update_source == "Both must match":
            return UPDATE_MANIFEST_URLS
        return UPDATE_MANIFEST_URLS

    def finish_update_check(self, update: UpdateInfo | None, auto: bool, error: str) -> None:
        self._update_check_running = False
        if update is None:
            if not auto:
                self.SetStatus(f"Update check failed. {error}")
                self.play_sound("error")
            return
        if not update.version:
            if not auto:
                self.SetStatus("Update manifest was read, but it did not include a version.")
                self.play_sound("error")
            return
        if compare_versions(update.version, APP_VERSION) <= 0:
            if not auto:
                self.SetStatus(f"ASIOA is up to date. Installed {APP_VERSION}, latest {update.version}.")
                self.play_sound("success")
            return
        if not update.has_download:
            self.SetStatus(f"ASIOA {update.version} is available, but no Windows download URL was listed.")
            self.play_sound("notification")
            return
        self.SetStatus(f"ASIOA {update.version} is available. Downloading update.")
        self.play_sound("notification")
        threading.Thread(target=self.download_update_worker, args=(update, auto), name="ASIOAUpdateDownload", daemon=True).start()

    def download_update_worker(self, update: UpdateInfo, auto: bool) -> None:
        url = update.installer_url or update.portable_url
        filename = filename_from_url(url, f"ASIOA-Audio-Router-Setup-{update.version}.exe")
        target = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads" / filename
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                target.write_bytes(response.read())
            wx.CallAfter(self.finish_update_download, update, target, auto, "")
        except Exception as exc:
            wx.CallAfter(self.finish_update_download, update, target, auto, str(exc))

    def finish_update_download(self, update: UpdateInfo, target: Path, auto: bool, error: str) -> None:
        if error:
            self.SetStatus(f"Could not download ASIOA {update.version}. {error}")
            self.play_sound("error")
            return
        self.SetStatus(f"Downloaded ASIOA {update.version} to {target}.")
        self.play_sound("success")
        if target.suffix.lower() == ".exe":
            message = (
                f"ASIOA {update.version} has been downloaded.\n\n"
                "Do you want to run the installer now? Audio routing may restart during installation."
            )
            if update.notes:
                message += f"\n\nWhat's new:\n{update.notes[:1200]}"
            answer = wx.MessageBox(message, "ASIOA update ready", wx.YES_NO | wx.ICON_INFORMATION, self)
            if answer == wx.YES:
                try:
                    subprocess.Popen([str(target)], shell=False)
                    self.SetStatus(f"Started ASIOA {update.version} installer.")
                except Exception as exc:
                    self.SetStatus(f"Downloaded update, but could not start installer. {exc}")

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
                *self.driver_status_lines(),
                "Driver capability map:",
                *(capability.sentence() for capability in self.driver_capability_map()),
                f"Default monitor device: {self.settings.default_monitor_device}",
                f"System audio master pair: {self.settings.system_audio_master_pair}",
                f"Screen reader and TTS default pair: {self.settings.screen_reader_master_pair}",
                f"Smart buffer mode: {self.settings.smart_buffer_mode}",
                f"Sample rate: {self.settings.sample_rate}",
                f"Starting buffer: {self.settings.buffer_size} samples",
                *self.plugin_inventory.status_lines(),
                f"Channel count target: {CHANNEL_COUNT} inputs and {CHANNEL_COUNT} outputs",
                "Protected buses: screen reader 61/62, TTS 63/64, communications 65/66, emergency accessibility 67/68.",
                "Live effects: off by default; VST3 and CLAP are preferred; VST2 is legacy and disabled by default.",
                f"Update channel: {self.settings.update_channel}",
                f"Update source: {self.settings.update_source}",
                f"Built-in sounds: {self.settings.enable_builtin_sounds}",
                f"Sessionwire white-noise guard: {self.settings.sessionwire_white_noise_guard}",
                f"Sessionwire white-noise threshold: {self.settings.sessionwire_noise_floor_db} dB",
                f"Diagnostics inbox: {DIAGNOSTICS_INBOX}",
            ]
        )

    def render_overview_html(self) -> str:
        status_items = "".join(f"<li>{item}</li>" for item in self.status_history[-8:])
        active_routes = "".join(
            f"<li>{self.route_summary(route)}.</li>"
            for route in self.settings.routes
        )
        endpoints = "".join(
            f"<li>{self.endpoint_summary(endpoint)}.</li>"
            for endpoint in self.settings.endpoints
        )
        effects = "".join(
            f"<li><strong>{effect.name}</strong><br>Format: {effect.fmt}.<br>Status: {'enabled' if effect.enabled else 'disabled'}.<br>Processing state: {'bypassed' if effect.bypassed else 'active'}.</li>"
            for effect in self.settings.effects
        )
        driver_status = "".join(f"<li>{line}</li>" for line in self.driver_status_lines())
        capability_status = "".join(f"<li>{capability.sentence()}</li>" for capability in self.driver_capability_map())
        plugin_status = "".join(f"<li>{line}</li>" for line in self.plugin_inventory.status_lines())
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ASIOA Overview</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 14px; line-height: 1.55; color: #111; background: #fff; }}
    h1 {{ font-size: 1.4rem; }}
    h2 {{ font-size: 1.1rem; margin-top: 1rem; }}
    ul {{ margin-top: .2rem; padding-left: 1.4rem; }}
    li {{ margin-bottom: .75rem; }}
    .status-line {{ margin: .35rem 0; }}
  </style>
</head>
<body>
  <h1>ASIOA Audio Router overview</h1>
  <p class="status-line">Driver mode: <strong>{self.settings.driver_mode}</strong>.</p>
  <p class="status-line">Smart Buffer mode: <strong>{self.settings.smart_buffer_mode}</strong>.</p>
  <p class="status-line">Starting buffer: <strong>{self.settings.buffer_size} samples</strong>.</p>
  <p class="status-line">Sample rate: <strong>{self.settings.sample_rate} Hz</strong>.</p>
  <p class="status-line">Default monitoring output: <strong>{self.settings.default_monitor_device}</strong>.</p>
  <p class="status-line">System audio master pair: <strong>{self.settings.system_audio_master_pair}</strong>.</p>
  <p class="status-line">Screen reader and TTS default pair: <strong>{self.settings.screen_reader_master_pair}</strong>.</p>
  <p class="status-line">Screen reader output: <strong>{self.settings.screen_reader_output}</strong>.</p>
  <p class="status-line">Direct ASIOA screen reader capture: <strong>{'on' if self.settings.screen_reader_router_capture else 'off'}</strong>.</p>
  <p class="status-line">Built-in background and action sounds: <strong>{'on' if self.settings.enable_builtin_sounds else 'off'}</strong>.</p>
  <p class="status-line">Sessionwire white-noise guard: <strong>{'on' if self.settings.sessionwire_white_noise_guard else 'off'}</strong>, threshold <strong>{self.settings.sessionwire_noise_floor_db} dB</strong>.</p>
  <h2>Driver installation</h2>
  <ul>{driver_status}</ul>
  <h2>Driver capability map</h2>
  <ul>{capability_status}</ul>
  <h2>Recent status</h2>
  <ul>{status_items or '<li>No status messages yet.</li>'}</ul>
  <h2>Protected buses</h2>
  <ul>
    <li>Screen Reader Bus.<br>Channels: 61 and 62.<br>Stream inclusion: {'on' if self.settings.screen_reader_include_stream else 'off'}.<br>Recording inclusion: {'on' if self.settings.screen_reader_include_recording else 'off'}.</li>
    <li>TTS Bus: channels 63 and 64.</li>
    <li>Communications Bus: channels 65 and 66.</li>
    <li>Emergency Accessibility Bus: channels 67 and 68.</li>
  </ul>
  <h2>Routes</h2>
  <ul>{active_routes or '<li>No routes configured.</li>'}</ul>
  <h2>Plug-in inventory</h2>
  <ul>{plugin_status}</ul>
  <p>Plug-in processing can stay disabled while ASIOA still scans installed VST3, CLAP, and legacy VST2 plug-ins in the background.</p>
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

    def update_overview(self, force: bool = False) -> None:
        if not hasattr(self, "overview_view"):
            return
        if not force and self.current_tab_name() != "Overview":
            self._pending_overview_refresh = True
            self.update_driver_action_visibility()
            return
        html = self.render_overview_html()
        if html == self._last_overview_html:
            return
        self._last_overview_html = html
        self.overview_view.SetPage(html, "")
        self.update_driver_action_visibility()

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
        if self.IsShown() and not self.IsIconized():
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
        self.append_status_history(message)
        if message != self._last_announced_status:
            self._last_announced_status = message
            ScreenReaderNotifier.announce(message)

    def append_status_history(self, message: str) -> None:
        timestamp = wx.DateTime.Now().FormatISOTime()
        entry = f"{timestamp} {message}"
        if not self.status_history or self.status_history[-1] != entry:
            self.status_history.append(entry)
            self.status_history = self.status_history[-40:]
            self.update_overview()


class ASIOATrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame: ASIOAFrame) -> None:
        super().__init__()
        self.frame = frame
        icon = wx.ArtProvider.GetIcon(wx.ART_INFORMATION, wx.ART_FRAME_ICON, (16, 16))
        self.SetIcon(icon, APP_NAME)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, lambda _event: self.frame.restore_from_tray())

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        restore = menu.Append(wx.ID_ANY, "Restore ASIOA Audio Router")
        exit_item = menu.Append(wx.ID_EXIT, "Exit ASIOA Audio Router")
        self.Bind(wx.EVT_MENU, lambda _event: self.frame.restore_from_tray(), restore)
        self.Bind(wx.EVT_MENU, lambda _event: self.frame.exit_application(), exit_item)
        return menu


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
