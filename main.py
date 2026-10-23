"""Entry point for the Violence District (VD) Crosshair Overlay application."""

import sys
from PyQt6.QtWidgets import QApplication

from src.config import ConfigManager
from src.hotkeys import GlobalHotkeyManager
from src.overlay import CrosshairOverlay
from src.settings_ui import SettingsWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("VD Crosshair Overlay")

    # Initialize configuration and presets
    config_manager = ConfigManager("config.json")

    # Create click-through desktop overlay
    overlay = CrosshairOverlay(config_manager.settings)
    if config_manager.settings.visible:
        overlay.show()

    # Create Settings Studio window
    window = SettingsWindow(config_manager, overlay)
    window.show()

    # Initialize global in-game hotkeys & Right-Click ADS listener
    hotkeys = GlobalHotkeyManager(window)
    hotkeys.toggle_visibility_requested.connect(window.toggle_overlay_visibility)
    hotkeys.cycle_preset_requested.connect(window.cycle_preset)
    hotkeys.toggle_ui_requested.connect(window.toggle_ui_window)
    hotkeys.nudge_offset_requested.connect(window.nudge_position_offset)
    hotkeys.reset_offset_requested.connect(window.reset_position_offset)
    hotkeys.ads_state_changed.connect(overlay.set_ads_state)
    hotkeys.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
