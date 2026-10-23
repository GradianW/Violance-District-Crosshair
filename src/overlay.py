"""Transparent Click-Through Overlay Window and Vector Crosshair Renderer."""

import ctypes
import sys
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QGuiApplication, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QWidget

from src.config import CrosshairSettings


# Win32 Constants for Click-Through Transparent Window
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000


def draw_crosshair_painter(
    painter: QPainter,
    cx: float,
    cy: float,
    settings: CrosshairSettings,
    ads_active: bool = False,
) -> None:
    """
    Shared vector rendering routine used by both the live desktop overlay
    and the Settings UI preview canvas.
    """
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    alpha = int(max(10, min(100, settings.opacity)) * 2.55)

    main_color = QColor(settings.color)
    main_color.setAlpha(alpha)

    outline_color = QColor(settings.outline_color)
    outline_color.setAlpha(alpha)

    scale_factor = max(0.15, min(3.0, float(getattr(settings, "scale", 100)) / 100.0))
    size = float(settings.size) * scale_factor
    thickness = max(0.5, float(settings.thickness) * scale_factor)
    gap = float(settings.gap) * scale_factor
    if ads_active and settings.ads_dynamic:
        gap = gap * 0.6

    outline_on = settings.outline_enabled and settings.outline_thickness > 0
    outline_w = float(settings.outline_thickness) * 1.5 * scale_factor

    def draw_stroked_line(x1: float, y1: float, x2: float, y2: float) -> None:
        if outline_on:
            out_pen = QPen(
                outline_color,
                thickness + outline_w,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.FlatCap,
                Qt.PenJoinStyle.MiterJoin,
            )
            painter.setPen(out_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        in_pen = QPen(
            main_color,
            thickness,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.FlatCap,
            Qt.PenJoinStyle.MiterJoin,
        )
        painter.setPen(in_pen)
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def draw_stroked_circle(radius: float) -> None:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)
        if outline_on:
            out_pen = QPen(outline_color, thickness + outline_w)
            painter.setPen(out_pen)
            painter.drawEllipse(rect)

        in_pen = QPen(main_color, thickness)
        painter.setPen(in_pen)
        painter.drawEllipse(rect)

    shape = settings.shape

    # 1. Classic Cross (+) or T-Cross (⊤) or Circle + Cross (⊕)
    if shape in ("cross", "t_cross", "circle_cross"):
        # Left arm
        draw_stroked_line(cx - gap - size, cy, cx - gap, cy)
        # Right arm
        draw_stroked_line(cx + gap, cy, cx + gap + size, cy)
        # Bottom arm
        draw_stroked_line(cx, cy + gap, cx, cy + gap + size)
        # Top arm (omitted for t_cross)
        if shape != "t_cross":
            draw_stroked_line(cx, cy - gap - size, cx, cy - gap)

    # 2. Circle (○) or Circle + Cross (⊕)
    if shape in ("circle", "circle_cross"):
        circle_radius = max(0.5, size)
        draw_stroked_circle(circle_radius)

    # 3. Chevron (^)
    if shape == "chevron":
        apex_y = cy - gap
        wing_x = size * 0.85
        wing_y = size * 0.85
        draw_stroked_line(cx - wing_x, apex_y + wing_y, cx, apex_y)
        draw_stroked_line(cx, apex_y, cx + wing_x, apex_y + wing_y)

    # 4. X-Mark (×)
    if shape == "x_mark":
        diag_gap = gap * 0.7071
        diag_len = size * 0.7071
        # Top-Left
        draw_stroked_line(cx - diag_gap - diag_len, cy - diag_gap - diag_len, cx - diag_gap, cy - diag_gap)
        # Top-Right
        draw_stroked_line(cx + diag_gap, cy - diag_gap, cx + diag_gap + diag_len, cy - diag_gap - diag_len)
        # Bottom-Left
        draw_stroked_line(cx - diag_gap - diag_len, cy + diag_gap + diag_len, cx - diag_gap, cy + diag_gap)
        # Bottom-Right
        draw_stroked_line(cx + diag_gap, cy + diag_gap, cx + diag_gap + diag_len, cy + diag_gap + diag_len)

    # 5. Center Dot (either standalone 'dot' shape or dot_enabled toggle)
    if shape == "dot" or settings.dot_enabled:
        dot_r = max(0.4, float(settings.dot_size) * scale_factor * 0.65)
        if outline_on:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(outline_color))
            out_r = dot_r + (float(settings.outline_thickness) * 0.75 * scale_factor)
            painter.drawEllipse(QPointF(cx, cy), out_r, out_r)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(main_color))
        painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)


class CrosshairOverlay(QWidget):
    """Frameless, always-on-top, click-through overlay window."""

    def __init__(self, settings: CrosshairSettings) -> None:
        super().__init__()
        self.settings = settings
        self.ads_active = False

        self.setWindowTitle("VD Crosshair Overlay")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.update_monitor_geometry()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_win32_click_through()

    def _apply_win32_click_through(self) -> None:
        """Apply native Win32 extended styles so clicks pass directly into Roblox."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = (
                ex_style
                | WS_EX_LAYERED
                | WS_EX_TRANSPARENT
                | WS_EX_TOOLWINDOW
                | WS_EX_NOACTIVATE
            )
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as exc:
            print(f"[CrosshairOverlay] Win32 click-through setup warning: {exc}")

    def update_monitor_geometry(self) -> None:
        """Position overlay across the target monitor."""
        screens = QGuiApplication.screens()
        if not screens:
            return
        idx = max(0, min(self.settings.monitor_index, len(screens) - 1))
        target_screen = screens[idx]
        geom = target_screen.geometry()
        self.setGeometry(geom)
        self.update()

    def update_settings(self, settings: CrosshairSettings) -> None:
        """Refresh overlay state and trigger repaint."""
        self.settings = settings
        self.update_monitor_geometry()
        if self.settings.visible:
            if not self.isVisible():
                self.show()
            self._apply_win32_click_through()
            self.update()
        else:
            self.hide()

    def set_ads_state(self, active: bool) -> None:
        """Update Right-Click ADS state and repaint if changed."""
        if self.ads_active != active:
            self.ads_active = active
            if self.settings.ads_dynamic and self.isVisible():
                self.update()

    def paintEvent(self, event) -> None:
        if not self.settings.visible:
            return

        painter = QPainter(self)
        cx = (self.width() / 2.0) + float(self.settings.offset_x)
        cy = (self.height() / 2.0) + float(self.settings.offset_y)
        draw_crosshair_painter(painter, cx, cy, self.settings, ads_active=self.ads_active)
        painter.end()
