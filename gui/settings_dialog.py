from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QWidget, QFrame
)
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Hotkeys section
        hotkeys_label = QLabel("Hotkeys")
        hotkeys_font = QFont()
        hotkeys_font.setBold(True)
        hotkeys_label.setFont(hotkeys_font)
        layout.addWidget(hotkeys_label)

        # Overlay hotkey
        overlay_layout = QHBoxLayout()
        overlay_layout.addWidget(QLabel("Toggle Overlay:"), 0)
        self.overlay_hotkey = QLineEdit(
            self.config_manager.get("hotkeys", "overlay", fallback="alt+p")
        )
        overlay_layout.addWidget(self.overlay_hotkey, 1)
        layout.addLayout(overlay_layout)

        # Tags hotkey
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Toggle Tags:"), 0)
        self.tags_hotkey = QLineEdit(
            self.config_manager.get("hotkeys", "tags", fallback="alt+t")
        )
        tags_layout.addWidget(self.tags_hotkey, 1)
        layout.addLayout(tags_layout)

        # Add some spacing
        layout.addSpacing(10)

        # Position section
        position_label = QLabel("Overlay Position")
        position_font = QFont()
        position_font.setBold(True)
        position_label.setFont(position_font)
        layout.addWidget(position_label)

        # Corner selection
        corner_layout = QHBoxLayout()
        corner_layout.addWidget(QLabel("Corner:"), 0)
        self.corner_choice = QComboBox()
        self.corner_choice.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Leave"])
        current_corner = self.config_manager.get("overlay", "corner", fallback="Leave")
        index = self.corner_choice.findText(current_corner)
        if index >= 0:
            self.corner_choice.setCurrentIndex(index)
        else:
            self.corner_choice.setCurrentIndex(self.corner_choice.findText("Leave"))
        corner_layout.addWidget(self.corner_choice, 1)
        layout.addLayout(corner_layout)

        # Add some spacing
        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.on_cancel)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()

    def get_settings(self):
        return {
            "hotkeys": {
                "overlay": self.overlay_hotkey.text(),
                "tags": self.tags_hotkey.text(),
            },
            "overlay": {"corner": self.corner_choice.currentText()},
        }