"""Configuration and Preset Manager for VD Crosshair Overlay."""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class CrosshairSettings:
    """Data model representing all customizable crosshair parameters."""
    shape: str = "cross"               # cross, t_cross, dot, circle, circle_cross, chevron, x_mark
    color: str = "#00FF66"             # Main hex color
    opacity: int = 95                  # 10 to 100 (%)
    scale: int = 100                   # Master scale percentage (20% to 200%)
    size: int = 6                      # Line length or radius (1 to 60 px)
    thickness: int = 1                 # Stroke thickness (1 to 15 px)
    gap: int = 2                       # Center gap (-10 to 40 px)
    dot_enabled: bool = False          # Show center dot
    dot_size: int = 1                  # Center dot radius (1 to 12 px)
    outline_enabled: bool = True       # High-contrast outline
    outline_color: str = "#000000"     # Outline hex color
    outline_thickness: int = 1         # Outline stroke width (1 to 5 px)
    offset_x: int = 0                  # Horizontal offset from screen center (-500 to +500 px)
    offset_y: int = 0                  # Vertical offset from screen center (-500 to +500 px)
    monitor_index: int = 0             # Target display monitor index
    visible: bool = True               # Master overlay visibility
    ads_dynamic: bool = True           # Tighten gap when holding Right-Click (ADS)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrosshairSettings":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "VD Micro Cross (Ultra Small)": CrosshairSettings(
        shape="cross",
        color="#00FF66",
        opacity=95,
        scale=60,
        size=3,
        thickness=1,
        gap=1,
        dot_enabled=False,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
    "VD Precision Cross (Default)": CrosshairSettings(
        shape="cross",
        color="#00FF66",
        opacity=95,
        scale=85,
        size=5,
        thickness=1,
        gap=2,
        dot_enabled=False,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
    "Pinpoint Micro Dot (1px)": CrosshairSettings(
        shape="dot",
        color="#00FFFF",
        opacity=100,
        scale=50,
        size=2,
        thickness=1,
        gap=0,
        dot_enabled=True,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
    "Headshot T-Cross": CrosshairSettings(
        shape="t_cross",
        color="#00FFFF",
        opacity=95,
        scale=85,
        size=5,
        thickness=1,
        gap=2,
        dot_enabled=False,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
    "Shotgun Spread Circle": CrosshairSettings(
        shape="circle_cross",
        color="#FFCC00",
        opacity=85,
        scale=90,
        size=12,
        thickness=1,
        gap=4,
        dot_enabled=True,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
    "Tactical Chevron (^)": CrosshairSettings(
        shape="chevron",
        color="#FF00FF",
        opacity=95,
        scale=80,
        size=5,
        thickness=1,
        gap=1,
        dot_enabled=False,
        dot_size=1,
        outline_enabled=True,
        outline_color="#000000",
        outline_thickness=1,
    ).to_dict(),
}


class ConfigManager:
    """Manages loading, saving, and switching crosshair settings and presets."""

    def __init__(self, config_path: str = "config.json") -> None:
        self.config_path = config_path
        self.settings = CrosshairSettings()
        self.presets: Dict[str, Dict[str, Any]] = dict(DEFAULT_PRESETS)
        self.active_preset_name: str = "VD Precision Cross (Default)"
        self.load()

    def load(self) -> None:
        """Load configuration and presets from disk if available."""
        if not os.path.exists(self.config_path):
            self.save()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if "current" in raw and isinstance(raw["current"], dict):
                self.settings = CrosshairSettings.from_dict(raw["current"])

            if "presets" in raw and isinstance(raw["presets"], dict):
                merged = dict(DEFAULT_PRESETS)
                merged.update(raw["presets"])
                self.presets = merged

            if "active_preset" in raw and isinstance(raw["active_preset"], str):
                self.active_preset_name = raw["active_preset"]
        except Exception as exc:
            print(f"[ConfigManager] Warning: failed to load {self.config_path}: {exc}")

    def save(self) -> None:
        """Persist current settings and presets to disk."""
        payload = {
            "active_preset": self.active_preset_name,
            "current": self.settings.to_dict(),
            "presets": self.presets,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            print(f"[ConfigManager] Warning: failed to save {self.config_path}: {exc}")

    def apply_preset(self, name: str) -> bool:
        """Load a named preset into current settings while preserving screen offsets."""
        if name not in self.presets:
            return False

        # Preserve monitor & offset calibration unless user explicitly overwrote them in preset
        preset_data = dict(self.presets[name])
        self.settings = CrosshairSettings.from_dict(preset_data)
        self.active_preset_name = name
        self.save()
        return True

    def save_current_as_preset(self, name: str) -> None:
        """Save current settings under a preset name."""
        clean_name = name.strip()
        if not clean_name:
            return
        self.presets[clean_name] = self.settings.to_dict()
        self.active_preset_name = clean_name
        self.save()

    def delete_preset(self, name: str) -> bool:
        """Delete a user preset (keeps at least one preset available)."""
        if name in self.presets and len(self.presets) > 1:
            del self.presets[name]
            if self.active_preset_name == name:
                self.active_preset_name = next(iter(self.presets.keys()))
                self.apply_preset(self.active_preset_name)
            else:
                self.save()
            return True
        return False

    def cycle_next_preset(self) -> str:
        """Switch to the next available preset in order and return its name."""
        names = list(self.presets.keys())
        if not names:
            return ""
        try:
            idx = names.index(self.active_preset_name)
            next_idx = (idx + 1) % len(names)
        except ValueError:
            next_idx = 0
        next_name = names[next_idx]
        self.apply_preset(next_name)
        return next_name
