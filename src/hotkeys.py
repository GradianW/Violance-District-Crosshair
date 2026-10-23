"""Win32 Global Hotkey & Right-Click ADS Listener using lightweight polling."""

import ctypes
import sys
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


# Win32 Virtual Key Codes
VK_RBUTTON = 0x02
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_INSERT = 0x2D
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_R = 0x52
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79


class GlobalHotkeyManager(QObject):
    """
    Polls Win32 GetAsyncKeyState every 25ms to provide zero-dependency,
    admin-free global hotkeys and right-click ADS detection while inside Roblox.
    """

    toggle_visibility_requested = pyqtSignal()
    cycle_preset_requested = pyqtSignal()
    toggle_ui_requested = pyqtSignal()
    nudge_offset_requested = pyqtSignal(int, int)
    reset_offset_requested = pyqtSignal()
    ads_state_changed = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._prev_keys: dict[int, bool] = {}
        self._ads_pressed = False

        self.timer = QTimer(self)
        self.timer.setInterval(25)  # 40 Hz responsive polling
        self.timer.timeout.connect(self._poll_inputs)

    def start(self) -> None:
        if sys.platform == "win32":
            self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def _is_key_down(self, vk_code: int) -> bool:
        if sys.platform != "win32":
            return False
        state = ctypes.windll.user32.GetAsyncKeyState(vk_code)
        return bool(state & 0x8000)

    def _just_pressed(self, vk_code: int) -> bool:
        down = self._is_key_down(vk_code)
        was_down = self._prev_keys.get(vk_code, False)
        self._prev_keys[vk_code] = down
        return down and not was_down

    def _poll_inputs(self) -> None:
        # 1. Right Mouse Button (ADS Dynamic Crosshair)
        rmb_down = self._is_key_down(VK_RBUTTON)
        if rmb_down != self._ads_pressed:
            self._ads_pressed = rmb_down
            self.ads_state_changed.emit(rmb_down)

        # 2. Single-key Global Function Hotkeys
        if self._just_pressed(VK_F8) or self._just_pressed(VK_INSERT):
            self.toggle_visibility_requested.emit()

        if self._just_pressed(VK_F9):
            self.cycle_preset_requested.emit()

        if self._just_pressed(VK_F10):
            self.toggle_ui_requested.emit()

        # 3. Ctrl + Arrow Keys (Live In-Game Position Nudge)
        ctrl_down = self._is_key_down(VK_CONTROL)
        shift_down = self._is_key_down(VK_SHIFT)

        if ctrl_down:
            step = 5 if shift_down else 1
            if self._just_pressed(VK_LEFT):
                self.nudge_offset_requested.emit(-step, 0)
            if self._just_pressed(VK_RIGHT):
                self.nudge_offset_requested.emit(step, 0)
            if self._just_pressed(VK_UP):
                self.nudge_offset_requested.emit(0, -step)
            if self._just_pressed(VK_DOWN):
                self.nudge_offset_requested.emit(0, step)

            # Ctrl + Shift + R -> Reset Center Offset
            if shift_down and self._just_pressed(VK_R):
                self.reset_offset_requested.emit()
        else:
            # Keep edge-detection state updated even when Ctrl isn't held
            for vk in (VK_LEFT, VK_RIGHT, VK_UP, VK_DOWN, VK_R):
                self._prev_keys[vk] = self._is_key_down(vk)
