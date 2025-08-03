from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, Property, Signal
from PySide6.QtGui import QPainter, QColor


class ToggleSwitch(QWidget):
    # Signal emitted when the toggle state changes
    stateChanged = Signal(bool)

    def __init__(self, default_state=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)  # Fixed size for the toggle
        self._state = default_state
        self._opacity = 1.0 * default_state  # Opacity for animation
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Hand cursor on hover

        # Default colors (can be overridden by stylesheet)
        self._on_color = QColor(0, 150, 0)  # Green
        self._off_color = QColor(150, 150, 150)  # Gray
        self._handle_color = QColor(255, 255, 255)  # White

        # Animation for smooth transition
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(120)  # Animation duration in ms
        self._animation.finished.connect(self._animation_finished)

    def _animation_finished(self):
        """Emit signal when animation completes"""
        self.stateChanged.emit(self._state)

    def mousePressEvent(self, event):
        """Handle mouse click to toggle state"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def toggle(self):
        """Toggle the switch state with animation"""
        self._state = not self._state
        if self._state:
            self._animation.setStartValue(0)
            self._animation.setEndValue(1)
        else:
            self._animation.setStartValue(1)
            self._animation.setEndValue(0)
        self._animation.start()

    @Property(float)
    def opacity(self):
        """Property for animation opacity"""
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        """Setter for animation opacity"""
        self._opacity = value
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Custom painting of the toggle switch"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background track - interpolate between off and on colors
        if self._opacity <= 0:
            track_color = self._off_color
        elif self._opacity >= 1:
            track_color = self._on_color
        else:
            # Interpolate colors based on animation progress
            r = (
                self._off_color.red()
                + (self._on_color.red() - self._off_color.red()) * self._opacity
            )
            g = (
                self._off_color.green()
                + (self._on_color.green() - self._off_color.green()) * self._opacity
            )
            b = (
                self._off_color.blue()
                + (self._on_color.blue() - self._off_color.blue()) * self._opacity
            )
            track_color = QColor(int(r), int(g), int(b))

        painter.setBrush(track_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2
        )

        # Handle (knob)
        handle_size = self.height() - 4
        handle_margin = 2
        handle_x = int(
            handle_margin
            + (self.width() - handle_size - 2 * handle_margin) * self._opacity
        )

        painter.setBrush(self._handle_color)  # Configurable handle color
        painter.drawEllipse(handle_x, handle_margin, handle_size, handle_size)

    def setState(self, state):
        """Set toggle state without animation"""
        self._state = state
        self._opacity = 1.0 if state else 0.0
        self.update()
        self.stateChanged.emit(self._state)

    def getState(self):
        """Return current toggle state"""
        return self._state

    # Style sheet support methods
    def setOnColor(self, color):
        """Set the color when toggle is ON"""
        if isinstance(color, str):
            self._on_color = QColor(color)
        else:
            self._on_color = color
        self.update()

    def setOffColor(self, color):
        """Set the color when toggle is OFF"""
        if isinstance(color, str):
            self._off_color = QColor(color)
        else:
            self._off_color = color
        self.update()

    def setHandleColor(self, color):
        """Set the handle color"""
        if isinstance(color, str):
            self._handle_color = QColor(color)
        else:
            self._handle_color = color
        self.update()

    # Properties for stylesheet support
    onColor = Property(QColor, lambda self: self._on_color, setOnColor)
    offColor = Property(QColor, lambda self: self._off_color, setOffColor)
    handleColor = Property(QColor, lambda self: self._handle_color, setHandleColor)
