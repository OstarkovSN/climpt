from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import colorsys
import hashlib
import logging
from gui.styles import style_manager

logger = logging.getLogger(__name__)


class TagPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        style_manager.attach(self, "tag_panel")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        self.tag_buttons = {}
        self.on_tag_click_callback = None

        # Header
        header = QLabel("TAGS")
        header_font = QFont()
        header_font.setBold(True)
        header.setFont(header_font)
        self.layout.addWidget(header)

    def set_on_tag_click(self, callback):
        self.on_tag_click_callback = callback

    def update_tags(self, tag_counts):
        # Clear existing buttons
        self.tag_buttons.clear()

        # Remove old items (keep header)
        while self.layout.count() > 1:
            item = self.layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # Add tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags:
            btn = self.create_tag_button(tag, count)
            btn.clicked.connect(lambda checked, t=tag: self.on_tag_click(t))
            self.layout.addWidget(btn)
            self.tag_buttons[tag] = btn

        # Add "No tags" if needed
        if "No tags" in tag_counts and tag_counts["No tags"] > 0:
            btn = self.create_tag_button("No tags", tag_counts["No tags"])
            btn.clicked.connect(lambda: self.on_tag_click("No tags"))
            self.layout.addWidget(btn)

        self.layout.addStretch()
        self.updateGeometry()

    def create_tag_button(self, tag, count):
        btn = QPushButton(f"#{tag} ({count})" if count > 0 else f"#{tag}")
        color = self.get_tag_color(tag)

        # Convert QColor to hex for stylesheet
        color_hex = color.name()

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                min-height: 25px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.adjust_brightness(color, 20).name()};
            }}
        """)

        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def get_tag_color(self, tag):
        # Generate consistent color for tag
        hash_object = hashlib.md5(tag.encode())
        hash_hex = hash_object.hexdigest()
        hue = int(hash_hex[:8], 16) % 360 / 360.0
        saturation = 0.7 + (int(hash_hex[8:10], 16) % 30) / 100.0
        value = 0.6 + (int(hash_hex[10:12], 16) % 40) / 100.0

        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        r, g, b = [int(c * 255) for c in rgb]
        return QColor(r, g, b)

    def adjust_brightness(self, color, delta):
        """Adjust the brightness of a QColor"""
        hsl = color.toHsl()
        lightness = min(255, max(0, hsl.lightness() + delta))
        adjusted = QColor.fromHsl(hsl.hue(), hsl.saturation(), lightness)
        return adjusted

    def on_tag_click(self, tag):
        if self.on_tag_click_callback:
            self.on_tag_click_callback(tag)
