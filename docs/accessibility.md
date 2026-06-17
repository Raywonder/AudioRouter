# Accessibility Requirements

ASIOA must be fully controllable with NVDA, Narrator, and keyboard only.

## Main Window

The main window should expose these sections in tab order:

1. Status summary.
2. Applications.
3. DAW channels.
4. Inputs.
5. Outputs.
6. Routes.
7. Monitoring.
8. Buffering.
9. Startup and tray behavior.
10. Diagnostics.

## Screen Reader Contracts

Each route row must announce:

```text
Chrome to DAW input 3 and 4, enabled, volume -6 dB, monitoring off
```

Each channel row must announce:

```text
DAW Master 1 and 2, output, active, peak minus 12 dB, muted off
```

Each buffer control must announce:

```text
Buffer size, combo box, 128 samples
```

## Keyboard

- Tab and Shift+Tab move through major controls.
- Arrow keys move within lists and tables.
- Enter opens details for the focused app, channel, or route.
- Space toggles mute, monitor, bypass, or enabled states.
- Control+Comma opens settings.
- Escape closes dialogs.
- Applications key opens the focused item's context menu.

## UI Automation

Controls must expose:

- Name
- ControlType
- Value
- ToggleState or SelectionState where applicable
- RangeValue for sliders/meters that users can adjust
- HelpText for risky controls and feedback-protected routes

The route matrix must have a list/table mode because a visual patch grid alone is not enough for screen reader users.

## Tray App

The tray menu must be a normal keyboard-navigable Windows menu:

- Open ASIOA Audio Router
- Monitoring on/off
- Bypass DAW routing
- Mute all application feeds
- Open settings
- Quit

No menu should disappear while arrowing through submenus. Escape dismisses the menu.

