"""Modern Dark Gaming UI Control Panel for VD Crosshair Overlay."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QAction,
    QColor,
    QGuiApplication,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.config import ConfigManager
from src.overlay import CrosshairOverlay, draw_crosshair_painter


SHAPE_OPTIONS = [
    ("Classic Cross (+)", "cross"),
    ("T-Cross (⊤) [Headshot]", "t_cross"),
    ("Center Dot (•)", "dot"),
    ("Circle (○) [Shotgun]", "circle"),
    ("Circle + Cross (⊕)", "circle_cross"),
    ("Tactical Chevron (^)", "chevron"),
    ("X-Mark (×) [Hitmarker]", "x_mark"),
]

QUICK_COLORS = [
    ("Neon Green", "#00FF66"),
    ("Cyan", "#00FFFF"),
    ("Crimson Red", "#FF2244"),
    ("Yellow", "#FFEA00"),
    ("Magenta", "#FF00FF"),
    ("Pure White", "#FFFFFF"),
]


class CrosshairPreviewWidget(QFrame):
    """Interactive preview box showing the crosshair against light/dark test zones."""

    def __init__(self, config_manager: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.setMinimumSize(220, 150)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._bg_mode = "split"  # split, dark, bright

    def mousePressEvent(self, event) -> None:
        modes = ["split", "dark", "bright"]
        self._bg_mode = modes[(modes.index(self._bg_mode) + 1) % len(modes)]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        # Draw simulated game background (click preview to cycle Dark/Bright/Split)
        if self._bg_mode == "dark":
            painter.fillRect(0, 0, w, h, QColor("#141820"))
        elif self._bg_mode == "bright":
            painter.fillRect(0, 0, w, h, QColor("#DCE4EC"))
        else:
            painter.fillRect(0, 0, w // 2, h, QColor("#141820"))
            painter.fillRect(w // 2, 0, w - (w // 2), h, QColor("#C8D2DC"))

        # Subtle grid lines
        grid_pen = QPen(QColor(128, 128, 128, 45), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)

        # Draw actual crosshair in center of preview
        draw_crosshair_painter(
            painter,
            w / 2.0,
            h / 2.0,
            self.config_manager.settings,
            ads_active=False,
        )

        # Hint text
        painter.setPen(QColor("#8892B0"))
        painter.drawText(
            8,
            h - 8,
            f"Background: {self._bg_mode.title()} (Click to test contrast)",
        )
        painter.end()


def create_app_icon() -> QIcon:
    """Generate a crisp vector crosshair icon for window & system tray."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Outer dark circle
    painter.setBrush(QColor("#111622"))
    painter.setPen(QPen(QColor("#00FF66"), 3))
    painter.drawEllipse(6, 6, 52, 52)

    # Inner crosshair lines
    pen = QPen(QColor("#00FF66"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(32, 14, 32, 24)
    painter.drawLine(32, 40, 32, 50)
    painter.drawLine(14, 32, 24, 32)
    painter.drawLine(40, 32, 50, 32)
    painter.drawEllipse(30, 30, 4, 4)
    painter.end()
    return QIcon(pix)


class SettingsWindow(QMainWindow):
    """Main Control Panel for customizing the VD Crosshair Overlay."""

    def __init__(
        self,
        config_manager: ConfigManager,
        overlay: CrosshairOverlay,
    ) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.overlay = overlay
        self._updating_ui = False

        self.app_icon = create_app_icon()
        self.setWindowTitle("Violence District (VD) — Crosshair Overlay")
        self.setWindowIcon(self.app_icon)
        self.setMinimumWidth(520)

        self._apply_dark_stylesheet()
        self._build_ui()
        self._setup_system_tray()
        self.sync_ui_from_settings()

    def _apply_dark_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #0F131A;
                color: #E6EDF3;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #262C36;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: 600;
                color: #58A6FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QPushButton {
                background-color: #21262D;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 6px 12px;
                color: #E6EDF3;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363D;
                border-color: #58A6FF;
            }
            QPushButton#ToggleActiveBtn {
                background-color: #1F6FEB;
                border-color: #388BFD;
                font-weight: bold;
            }
            QComboBox, QSpinBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 5px;
                padding: 4px 8px;
                color: #E6EDF3;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #21262D;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #58A6FF;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            """
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # --- Top Header & Master Toggle ---
        header_layout = QHBoxLayout()
        title_label = QLabel("🎯 VD Crosshair Studio")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FF66;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.toggle_btn = QPushButton("Overlay: ON (F8)")
        self.toggle_btn.setObjectName("ToggleActiveBtn")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_overlay_visibility)
        header_layout.addWidget(self.toggle_btn)
        main_layout.addLayout(header_layout)

        # --- Live Preview Box ---
        self.preview_widget = CrosshairPreviewWidget(self.config_manager)
        main_layout.addWidget(self.preview_widget)

        # --- Preset Profiles Bar ---
        preset_group = QGroupBox("Preset Profiles (Cycle in-game with F9)")
        preset_layout = QHBoxLayout(preset_group)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo, stretch=1)

        save_preset_btn = QPushButton("Save As...")
        save_preset_btn.clicked.connect(self._on_save_preset)
        preset_layout.addWidget(save_preset_btn)

        del_preset_btn = QPushButton("Delete")
        del_preset_btn.clicked.connect(self._on_delete_preset)
        preset_layout.addWidget(del_preset_btn)

        main_layout.addWidget(preset_group)

        # --- Shape & Geometry Group ---
        geom_group = QGroupBox("Shape & Geometry")
        geom_layout = QFormLayout(geom_group)

        self.shape_combo = QComboBox()
        for label, val in SHAPE_OPTIONS:
            self.shape_combo.addItem(label, val)
        self.shape_combo.currentIndexChanged.connect(self._on_ui_changed)
        geom_layout.addRow("Reticle Shape:", self.shape_combo)

        self.size_slider, self.size_spin = self._create_slider_row(2, 60)
        geom_layout.addRow("Size / Length:", self._wrap_row(self.size_slider, self.size_spin))

        self.thickness_slider, self.thickness_spin = self._create_slider_row(1, 15)
        geom_layout.addRow("Line Thickness:", self._wrap_row(self.thickness_slider, self.thickness_spin))

        self.gap_slider, self.gap_spin = self._create_slider_row(0, 40)
        geom_layout.addRow("Center Gap:", self._wrap_row(self.gap_slider, self.gap_spin))

        dot_row = QHBoxLayout()
        self.dot_check = QCheckBox("Enable Center Dot")
        self.dot_check.toggled.connect(self._on_ui_changed)
        dot_row.addWidget(self.dot_check)
        dot_row.addSpacing(12)
        dot_row.addWidget(QLabel("Dot Size:"))
        self.dot_size_spin = QSpinBox()
        self.dot_size_spin.setRange(1, 12)
        self.dot_size_spin.valueChanged.connect(self._on_ui_changed)
        dot_row.addWidget(self.dot_size_spin)
        dot_row.addStretch()
        geom_layout.addRow("Center Dot:", dot_row)

        self.ads_check = QCheckBox("Dynamic Right-Click (ADS) Tightening")
        self.ads_check.setToolTip("Automatically tightens the crosshair gap by 40% while holding Right-Click")
        self.ads_check.toggled.connect(self._on_ui_changed)
        geom_layout.addRow("Gameplay:", self.ads_check)

        main_layout.addWidget(geom_group)

        # --- Color & Visibility Enhancements Group ---
        vis_group = QGroupBox("Color & Visibility Enhancements")
        vis_layout = QFormLayout(vis_group)

        color_row = QHBoxLayout()
        self.color_btn = QPushButton("Pick Custom Color")
        self.color_btn.clicked.connect(self._pick_main_color)
        color_row.addWidget(self.color_btn)

        for cname, chex in QUICK_COLORS:
            swatch = QPushButton()
            swatch.setFixedSize(QSize(24, 24))
            swatch.setToolTip(f"{cname} ({chex})")
            swatch.setStyleSheet(
                f"background-color: {chex}; border: 1px solid #444; border-radius: 4px;"
            )
            swatch.clicked.connect(lambda checked=False, c=chex: self._set_quick_color(c))
            color_row.addWidget(swatch)
        color_row.addStretch()
        vis_layout.addRow("Crosshair Color:", color_row)

        self.opacity_slider, self.opacity_spin = self._create_slider_row(10, 100)
        self.opacity_spin.setSuffix("%")
        vis_layout.addRow("Opacity:", self._wrap_row(self.opacity_slider, self.opacity_spin))

        outline_row = QHBoxLayout()
        self.outline_check = QCheckBox("High-Contrast Outline")
        self.outline_check.toggled.connect(self._on_ui_changed)
        outline_row.addWidget(self.outline_check)
        outline_row.addSpacing(10)
        outline_row.addWidget(QLabel("Width:"))
        self.outline_spin = QSpinBox()
        self.outline_spin.setRange(1, 5)
        self.outline_spin.valueChanged.connect(self._on_ui_changed)
        outline_row.addWidget(self.outline_spin)

        self.outline_color_btn = QPushButton("Outline Color")
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        outline_row.addWidget(self.outline_color_btn)
        outline_row.addStretch()
        vis_layout.addRow("Contrast Stroke:", outline_row)

        main_layout.addWidget(vis_group)

        # --- Position & Screen Offset Group ---
        pos_group = QGroupBox("Screen Position & Shift-Lock Calibration")
        pos_layout = QFormLayout(pos_group)

        self.offset_x_slider, self.offset_x_spin = self._create_slider_row(-500, 500)
        self.offset_x_spin.setSuffix(" px")
        pos_layout.addRow("Horizontal (X):", self._wrap_row(self.offset_x_slider, self.offset_x_spin))

        self.offset_y_slider, self.offset_y_spin = self._create_slider_row(-500, 500)
        self.offset_y_spin.setSuffix(" px")
        pos_layout.addRow("Vertical (Y):", self._wrap_row(self.offset_y_slider, self.offset_y_spin))

        mon_row = QHBoxLayout()
        self.monitor_combo = QComboBox()
        screens = QGuiApplication.screens()
        for idx, scr in enumerate(screens):
            g = scr.geometry()
            self.monitor_combo.addItem(f"Display {idx + 1}: {scr.name()} ({g.width()}x{g.height()})", idx)
        self.monitor_combo.currentIndexChanged.connect(self._on_ui_changed)
        mon_row.addWidget(self.monitor_combo, stretch=1)

        reset_pos_btn = QPushButton("Reset Center (0, 0)")
        reset_pos_btn.clicked.connect(self.reset_position_offset)
        mon_row.addWidget(reset_pos_btn)
        pos_layout.addRow("Monitor:", mon_row)

        main_layout.addWidget(pos_group)

        # --- Hotkeys Footer ---
        hotkey_lbl = QLabel(
            "⌨️ <b>In-Game Hotkeys:</b>  "
            "<code>F8</code> / <code>Ins</code> Toggle Crosshair  |  "
            "<code>F9</code> Cycle Preset  |  "
            "<code>F10</code> Hide/Show App  |  "
            "<code>Ctrl + Arrows</code> Nudge X/Y"
        )
        hotkey_lbl.setStyleSheet("color: #8B949E; font-size: 11px; padding: 4px;")
        hotkey_lbl.setWordWrap(True)
        main_layout.addWidget(hotkey_lbl)

    def _create_slider_row(self, min_val: int, max_val: int) -> tuple[QSlider, QSpinBox]:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setFixedWidth(72)

        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(self._on_ui_changed)
        return slider, spin

    def _wrap_row(self, slider: QSlider, spin: QSpinBox) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(slider, stretch=1)
        layout.addWidget(spin)
        return container

    def _setup_system_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self.app_icon, self)
        self.tray_icon.setToolTip("Violence District Crosshair Overlay")

        tray_menu = QMenu()
        show_action = QAction("Open Crosshair Studio (F10)", self)
        show_action.triggered.connect(self.bring_to_front)
        tray_menu.addAction(show_action)

        toggle_action = QAction("Toggle Crosshair On/Off (F8)", self)
        toggle_action.triggered.connect(self.toggle_overlay_visibility)
        tray_menu.addAction(toggle_action)

        tray_menu.addSeparator()
        quit_action = QAction("Quit Completely", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.bring_to_front()

    def bring_to_front(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def toggle_ui_window(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.bring_to_front()

    def sync_ui_from_settings(self) -> None:
        """Populate UI widgets from current ConfigManager state."""
        self._updating_ui = True
        s = self.config_manager.settings

        # Refresh presets dropdown
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for name in self.config_manager.presets.keys():
            self.preset_combo.addItem(name)
        self.preset_combo.setCurrentText(self.config_manager.active_preset_name)
        self.preset_combo.blockSignals(False)

        # Shape combo
        for i in range(self.shape_combo.count()):
            if self.shape_combo.itemData(i) == s.shape:
                self.shape_combo.setCurrentIndex(i)
                break

        self.size_slider.setValue(s.size)
        self.thickness_slider.setValue(s.thickness)
        self.gap_slider.setValue(s.gap)
        self.dot_check.setChecked(s.dot_enabled)
        self.dot_size_spin.setValue(s.dot_size)
        self.ads_check.setChecked(s.ads_dynamic)

        self.opacity_slider.setValue(s.opacity)
        self.outline_check.setChecked(s.outline_enabled)
        self.outline_spin.setValue(s.outline_thickness)

        self.offset_x_slider.setValue(s.offset_x)
        self.offset_y_slider.setValue(s.offset_y)
        if 0 <= s.monitor_index < self.monitor_combo.count():
            self.monitor_combo.setCurrentIndex(s.monitor_index)

        self._update_color_buttons()
        self._update_toggle_button()

        self._updating_ui = False
        self.preview_widget.update()
        self.overlay.update_settings(s)

    def _update_color_buttons(self) -> None:
        s = self.config_manager.settings
        self.color_btn.setText(f"Color: {s.color.upper()}")
        self.color_btn.setStyleSheet(
            f"background-color: {s.color}; color: #000000; font-weight: bold; border-radius: 5px;"
        )
        self.outline_color_btn.setText(f"Stroke: {s.outline_color.upper()}")

    def _update_toggle_button(self) -> None:
        if self.config_manager.settings.visible:
            self.toggle_btn.setText("Overlay: ON (F8)")
            self.toggle_btn.setStyleSheet(
                "background-color: #238636; border-color: #2EA043; color: white; font-weight: bold;"
            )
        else:
            self.toggle_btn.setText("Overlay: OFF (F8)")
            self.toggle_btn.setStyleSheet(
                "background-color: #DA3633; border-color: #F85149; color: white; font-weight: bold;"
            )

    def _on_ui_changed(self) -> None:
        if self._updating_ui:
            return
        s = self.config_manager.settings
        s.shape = self.shape_combo.currentData()
        s.size = self.size_slider.value()
        s.thickness = self.thickness_slider.value()
        s.gap = self.gap_slider.value()
        s.dot_enabled = self.dot_check.isChecked()
        s.dot_size = self.dot_size_spin.value()
        s.ads_dynamic = self.ads_check.isChecked()
        s.opacity = self.opacity_slider.value()
        s.outline_enabled = self.outline_check.isChecked()
        s.outline_thickness = self.outline_spin.value()
        s.offset_x = self.offset_x_slider.value()
        s.offset_y = self.offset_y_slider.value()
        s.monitor_index = max(0, self.monitor_combo.currentIndex())

        self.config_manager.save()
        self.preview_widget.update()
        self.overlay.update_settings(s)

    def _set_quick_color(self, hex_color: str) -> None:
        self.config_manager.settings.color = hex_color
        self._update_color_buttons()
        self._on_ui_changed()

    def _pick_main_color(self) -> None:
        initial = QColor(self.config_manager.settings.color)
        chosen = QColorDialog.getColor(initial, self, "Select Crosshair Color")
        if chosen.isValid():
            self._set_quick_color(chosen.name().upper())

    def _pick_outline_color(self) -> None:
        initial = QColor(self.config_manager.settings.outline_color)
        chosen = QColorDialog.getColor(initial, self, "Select Outline Color")
        if chosen.isValid():
            self.config_manager.settings.outline_color = chosen.name().upper()
            self._update_color_buttons()
            self._on_ui_changed()

    def toggle_overlay_visibility(self) -> None:
        s = self.config_manager.settings
        s.visible = not s.visible
        self.config_manager.save()
        self._update_toggle_button()
        self.overlay.update_settings(s)

    def nudge_position_offset(self, dx: int, dy: int) -> None:
        s = self.config_manager.settings
        s.offset_x = max(-500, min(500, s.offset_x + dx))
        s.offset_y = max(-500, min(500, s.offset_y + dy))
        self.sync_ui_from_settings()
        self.config_manager.save()

    def reset_position_offset(self) -> None:
        s = self.config_manager.settings
        s.offset_x = 0
        s.offset_y = 0
        self.sync_ui_from_settings()
        self.config_manager.save()

    def _on_preset_selected(self, name: str) -> None:
        if self._updating_ui or not name:
            return
        if self.config_manager.apply_preset(name):
            self.sync_ui_from_settings()

    def cycle_preset(self) -> None:
        next_name = self.config_manager.cycle_next_preset()
        if next_name:
            self.sync_ui_from_settings()

    def _on_save_preset(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Save Preset Profile",
            "Enter a name for this crosshair preset:",
            text=self.config_manager.active_preset_name,
        )
        if ok and name.strip():
            self.config_manager.save_current_as_preset(name.strip())
            self.sync_ui_from_settings()

    def _on_delete_preset(self) -> None:
        curr = self.preset_combo.currentText()
        if len(self.config_manager.presets) <= 1:
            QMessageBox.information(
                self, "Cannot Delete", "At least one preset must remain."
            )
            return
        if self.config_manager.delete_preset(curr):
            self.sync_ui_from_settings()
