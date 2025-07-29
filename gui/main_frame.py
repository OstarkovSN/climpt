import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
    QApplication,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QKeyEvent
from gui.tag_panel import TagPanel
from gui.edit_dialog import EditPromptDialog
from gui.settings_dialog import SettingsDialog
from gui.prompt_card import PromptCard
from config import ConfigManager
import logging

logger = logging.getLogger(__name__)


class MainFrame(QMainWindow):
    """
    The main application frame containing all UI elements.

    This is the top-level window of the application. It contains a scrolled
    panel with all prompts and a tag panel to filter prompts.

    Attributes:
        app: Reference to the application instance.
        prompts: List to hold all prompts.
        filtered_prompts: List to hold currently filtered prompts.
        is_overlay: Boolean indicating if the overlay is active.
        tag_panel: Reference to the TagPanel instance.
        tag_panel_shown: Boolean indicating if the tag panel is shown.
        dragging: Boolean indicating if the window is being dragged.
        drag_offset: QPoint object representing the drag offset.
        config_manager: Instance of ConfigManager to handle app configuration.
    """

    def __init__(self, app):
        """
        Initialize the main application frame.

        Args:
            app: The QApplication instance to which this frame belongs.

        Attributes:
            app: Reference to the application instance.
            prompts: List to hold all prompts.
            filtered_prompts: List to hold currently filtered prompts.
            is_overlay: Boolean indicating if the overlay is active.
            tag_panel: Reference to the TagPanel instance.
            tag_panel_shown: Boolean indicating if the tag panel is shown.
            dragging: Boolean indicating if the window is being dragged.
            drag_offset: QPoint object representing the drag offset.
            config_manager: Instance of ConfigManager to handle app configuration.
        """

        super().__init__()
        self.app = app
        self.prompts = []
        self.filtered_prompts = []
        self.is_overlay = False
        self.tag_panel = None
        self.tag_panel_shown = False
        self.dragging = False
        self.drag_offset = QPoint(0, 0)

        # Load configuration
        self.config_manager = ConfigManager()

        self.setWindowTitle("Climpt")
        self.resize(500, 600)

        # Set up mouse tracking for dragging
        self.setMouseTracking(True)

        # Connect close event
        self.closeEvent = self.on_close

        self.setup_ui()

    def setup_ui(self):
        """
        Setup the main application UI.

        This method creates the main panel and its UI elements, including the
        top button panel, search control, and content area with prompts.

        It also sets up the sizer for the main panel and does some additional
        setup, such as setting up the accelerators from the configuration file.
        """

        # Create the central widget which holds all other UI components
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create a top button panel for various control buttons
        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(5, 5, 5, 5)

        # "Tags" button to toggle the tags panel
        self.tags_btn = QPushButton("Tags")
        self.tags_btn.clicked.connect(self.toggle_tags_panel)

        # "Settings" button to show settings dialog
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)

        # "About" button to show about information
        self.about_btn = QPushButton("About")
        self.about_btn.clicked.connect(self.show_about)

        # "Overlay" button to toggle overlay visibility
        self.overlay_btn = QPushButton("Overlay")
        self.overlay_btn.clicked.connect(self.toggle_overlay)

        # "+ Add Prompt" button to add a new prompt
        self.add_btn = QPushButton("+ Add Prompt")
        self.add_btn.clicked.connect(self.on_add_prompt)

        # Add all buttons to the button layout
        button_layout.addWidget(self.tags_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addWidget(self.about_btn)
        button_layout.addWidget(self.overlay_btn)
        button_layout.addWidget(self.add_btn)
        button_layout.addStretch()  # Push buttons to the left

        button_panel.setLayout(button_layout)
        main_layout.addWidget(button_panel)

        # Create a search control for searching prompts or tags, full width
        self.search_ctrl = QLineEdit()
        self.search_ctrl.setPlaceholderText("Search prompts or #tags...")
        self.search_ctrl.returnPressed.connect(self.on_search)
        self.search_ctrl.textChanged.connect(self.on_search_text)

        main_layout.addWidget(self.search_ctrl)

        # Create a content area to hold the list of prompts
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for displaying prompts with vertical scroll
        self.prompts_scroll = QScrollArea()
        self.prompts_scroll.setWidgetResizable(True)
        self.prompts_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Create widget to hold prompts
        self.prompts_container = QWidget()
        self.prompts_container.setStyleSheet("background-color: #f8f8f8;")
        self.prompts_sizer = QVBoxLayout()
        self.prompts_sizer.setContentsMargins(5, 5, 5, 5)
        self.prompts_sizer.setSpacing(5)
        self.prompts_container.setLayout(self.prompts_sizer)

        self.prompts_scroll.setWidget(self.prompts_container)

        content_layout.addWidget(self.prompts_scroll)
        content_widget.setLayout(content_layout)

        main_layout.addWidget(content_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Setup accelerators (keyboard shortcuts) from configuration
        self.setup_accelerators()

    def setup_accelerators(self):
        """
        Setup accelerators (hotkeys) from configuration.

        This function parses the hotkeys from the configuration and creates
        keyboard shortcuts for the main frame. The shortcuts are then
        connected to their respective functions.

        The hotkeys are parsed from the configuration with the following format:

        - 'hotkeys.overlay' for the overlay hotkey
        - 'hotkeys.tags' for the tags hotkey

        The hotkeys are parsed in the following format:

        - 'alt+p' for alt key and 'p' key
        - 'ctrl+shift+t' for control key, shift key and 't' key

        If the hotkeys are not specified in the configuration, the default hotkeys
        are used:

        - 'alt+p' for the overlay hotkey
        - 'alt+t' for the tags hotkey

        If the hotkeys are specified in the configuration but have an invalid format,
        the default hotkeys are used.

        If the hotkeys are not specified in the configuration or have an invalid format,
        a warning message is printed to the console.
        """
        try:
            # Overlay hotkey
            overlay_key = self.config_manager.get(
                "hotkeys", "overlay", fallback="alt+p"
            )
            if overlay_key:
                # Convert wxPython style hotkey to Qt style
                qt_key = self._convert_hotkey_to_qt(overlay_key)
                if qt_key:
                    shortcut = QShortcut(qt_key, self)
                    shortcut.activated.connect(self.toggle_overlay)

            # Tags hotkey
            tags_key = self.config_manager.get("hotkeys", "tags", fallback="alt+t")
            if tags_key:
                # Convert wxPython style hotkey to Qt style
                qt_key = self._convert_hotkey_to_qt(tags_key)
                if qt_key:
                    shortcut = QShortcut(qt_key, self)
                    shortcut.activated.connect(self.toggle_tags_panel)

        except Exception as e:
            logger.error(f"Error setting up accelerators: {e}")

    def _convert_hotkey_to_qt(self, hotkey_str):
        """
        Convert hotkey string from config to Qt KeySequence.

        Args:
            hotkey_str (str): Hotkey string like 'alt+p' or 'ctrl+shift+t'

        Returns:
            QKeySequence or None: Converted key sequence or None if invalid
        """
        try:
            # Simple conversion for common formats
            parts = hotkey_str.lower().split("+")
            modifiers = []
            key = ""

            for part in parts:
                if part == "alt":
                    modifiers.append("Alt")
                elif part == "ctrl":
                    modifiers.append("Ctrl")
                elif part == "shift":
                    modifiers.append("Shift")
                else:
                    key = part.upper()

            if key:
                if modifiers:
                    full_key = "+".join(modifiers) + "+" + key
                else:
                    full_key = key
                return QKeySequence(full_key)
        except Exception as e:
            logger.error(f"Error converting hotkey '{hotkey_str}': {e}")
        return None

    def load_prompts(self, prompts):
        """Load prompts from storage and update the display.

        Args:
            prompts (list of dict): List of prompts to load.
        """
        try:
            self.prompts = prompts
            self.filtered_prompts = prompts
            self.refresh_display()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error loading prompts: {e}")

    def refresh_display(self):
        """
        Refresh the display of prompts.

        This method updates the list of prompt cards displayed in the main
        application window. It ensures that the current state of the filtered
        prompts is reflected in the user interface. The tags panel update is
        deferred until it is shown.

        Exceptions are caught and logged if there is an error during the refresh
        process.
        """

        try:
            self.update_prompts_list()
            # Tags panel will be updated when shown
        except Exception as e:
            logger.error(f"Error refreshing display: {e}")

    def update_prompts_list(self):
        """
        Update the list of prompts displayed in the main application window.

        This method is responsible for clearing and rebuilding the list of prompt
        cards displayed in the main application window. It ensures that the
        current state of the filtered prompts is reflected in the user interface.

        Exceptions are caught and logged if there is an error during the update
        process.
        """
        try:
            # Clear existing cards
            while self.prompts_sizer.count():
                item = self.prompts_sizer.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Add prompt cards
            for prompt in self.filtered_prompts:
                try:
                    card = PromptCard(
                        self.prompts_container,  # Parent widget
                        prompt,
                        self.on_prompt_click,
                        self.edit_prompt,
                        self.delete_prompt,
                    )
                    self.prompts_sizer.addWidget(card)
                except Exception as e:
                    logger.error(f"Error creating prompt card: {e}")
                    continue

            self.prompts_sizer.addStretch()
            self.prompts_container.setLayout(self.prompts_sizer)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error updating prompts list: {e}")

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging in overlay mode"""
        try:
            if self.is_overlay and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_offset = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        except Exception as e:
            logger.error(f"Error in mouse press: {e}")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        try:
            if self.is_overlay and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
        except Exception as e:
            logger.error(f"Error in mouse release: {e}")
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        try:
            if (
                self.is_overlay
                and self.dragging
                and event.buttons() & Qt.MouseButton.LeftButton
            ):
                # Calculate new position ensuring we don't go off-screen
                global_pos = event.globalPosition().toPoint()
                new_pos = global_pos - self.drag_offset

                # Get screen geometry to constrain movement
                from PyQt6.QtWidgets import QApplication

                screen = QApplication.primaryScreen().geometry()
                window_size = self.size()

                # Constrain to screen bounds
                new_pos.setX(
                    max(0, min(new_pos.x(), screen.width() - window_size.width()))
                )
                new_pos.setY(
                    max(0, min(new_pos.y(), screen.height() - window_size.height()))
                )

                self.move(new_pos)
        except Exception as e:
            logger.error(f"Error in mouse move: {e}")
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        """Handle mouse entering window - for overlay mode enhancements"""
        try:
            if self.is_overlay:
                # Make window slightly more opaque when hovered
                self.setWindowOpacity(0.95)
        except Exception as e:
            logger.error(f"Error in enter event: {e}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leaving window - for overlay mode enhancements"""
        try:
            if self.is_overlay:
                # Return to normal opacity when not hovered
                self.setWindowOpacity(0.86)
        except Exception as e:
            logger.error(f"Error in leave event: {e}")
        super().leaveEvent(event)

    def on_close(self, event):
        """Handle window close event"""
        try:
            self.app.on_window_close()
            event.accept()
        except Exception as e:
            logger.error(f"Error in close handler: {e}")
            event.accept()  # Always accept to prevent hanging

    def closeEvent(self, event):
        """Override close event to ensure proper cleanup"""
        self.on_close(event)

    def apply_overlay_mode(self):
        """Apply overlay mode styling and behavior"""
        try:
            if self.is_overlay:
                # Overlay mode
                self.overlay_btn.setText("Normal")
                self.setWindowFlags(
                    Qt.WindowType.WindowStaysOnTopHint
                    | Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.Tool  # Prevents taskbar entry
                )
                self.setWindowOpacity(0.86)  # Semi-transparent
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #1e1e1e;
                        border: 1px solid #444444;
                        border-radius: 8px;
                    }
                """)
                # Make it narrower in overlay mode
                self.resize(400, 500)
                # Move to configured corner
                self.move_overlay_to_corner()
                # Enable mouse tracking for hover effects
                self.setMouseTracking(True)
            else:
                # Normal mode
                self.overlay_btn.setText("Overlay")
                self.setWindowFlags(
                    Qt.WindowType.Window
                    | Qt.WindowType.WindowCloseButtonHint
                    | Qt.WindowType.WindowMinimizeButtonHint
                    | Qt.WindowType.WindowMaximizeButtonHint
                )
                self.setWindowOpacity(1.0)  # Opaque
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: palette(window);
                    }
                """)
                # Restore normal size
                self.resize(500, 600)
                # Disable mouse tracking in normal mode
                self.setMouseTracking(False)

            self.show()  # Required after changing window flags
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error applying overlay mode: {e}")

    def move_overlay_to_corner(self):
        """Move overlay window to configured corner with better positioning"""
        try:
            corner = self.config_manager.get("overlay", "corner", fallback="Top Right")
            from PyQt6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            window_size = self.size()

            margin = 20  # Margin from screen edges

            if corner == "Top Left":
                self.move(margin, margin)
            elif corner == "Top Right":
                self.move(screen.width() - window_size.width() - margin, margin)
            elif corner == "Bottom Left":
                self.move(margin, screen.height() - window_size.height() - margin)
            elif corner == "Bottom Right":
                self.move(
                    screen.width() - window_size.width() - margin,
                    screen.height() - window_size.height() - margin,
                )
            elif corner == "Leave":
                # Don't move, keep current position
                pass
        except Exception as e:
            logger.error(f"Error moving overlay to corner: {e}")

    def update_tags_panel(self):
        try:
            if self.tag_panel:
                tag_counts = {}
                for prompt in self.prompts:
                    if prompt.get("tags"):
                        for tag in prompt["tags"]:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    else:
                        tag_counts["No tags"] = tag_counts.get("No tags", 0) + 1
                self.tag_panel.update_tags(tag_counts)
        except Exception as e:
            logger.error(f"Error updating tags panel: {e}")

    def toggle_tags_panel(self, event):
        try:
            if not self.tag_panel_shown:
                # Show tag panel
                if not self.tag_panel:
                    self.tag_panel = TagPanel(self.content_panel)
                    self.tag_panel.set_on_tag_click(self.on_tag_filter)
                    self.update_tags_panel()

                # Insert tag panel at the beginning of the layout
                self.content_layout = self.content_panel.layout()
                if self.content_layout is not None:
                    self.content_layout.insertWidget(0, self.tag_panel)
                self.tag_panel.show()
                self.tag_panel_shown = True
                self.tags_btn.setText("Hide Tags")
            else:
                # Hide tag panel
                if self.tag_panel:
                    self.tag_panel.hide()
                    self.tag_panel_shown = False
                    self.tags_btn.setText("Tags")

            # Refresh layout
            if self.content_panel.layout() is not None:
                self.content_panel.layout().update()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error toggling tags panel: {e}")

    def show_settings(self, event):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self, self.config_manager)
            if dialog.exec():
                settings = dialog.get_settings()

                # Update config
                for section, values in settings.items():
                    if section not in self.config_manager.config:
                        self.config_manager.config[section] = {}
                    for key, value in values.items():
                        self.config_manager.config[section][key] = str(value)

                # Save config
                self.config_manager.save_config()

                # Update accelerators
                self.setup_accelerators()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error showing settings: {e}")

    def show_about(self, event):
        """Show about dialog"""
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                "About Climpt",
                "Climpt - Clipboard Prompt Manager\nVersion 0.1.0\n\nA lightweight tool for managing and inserting text prompts.",
            )
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")

    def show_copied_message(self):
        """Show 'Copied!' message"""
        try:
            from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PyQt6.QtCore import QTimer
            from PyQt6.QtGui import QPalette

            # Create a temporary message widget
            msg_widget = QWidget(self)
            msg_widget.setStyleSheet("""
                background-color: #2ECC71;
                border-radius: 5px;
            """)
            msg_widget.setFixedHeight(40)
            msg_widget.setFixedWidth(200)

            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)

            msg_label = QLabel("Copied!")
            msg_label.setStyleSheet("""
                color: white;
                font-weight: bold;
                qproperty-alignment: AlignCenter;
            """)

            layout.addWidget(msg_label)
            msg_widget.setLayout(layout)

            # Position it at the bottom center
            central_widget = self.centralWidget()
            if central_widget:
                central_rect = central_widget.geometry()
                msg_widget.move(
                    (central_rect.width() - msg_widget.width()) // 2,
                    central_rect.height() - msg_widget.height() - 20,
                )

            msg_widget.show()
            logger.debug("Copied message shown")
            msg_widget.raise_()

            # Hide after 1.5 seconds
            def hide_message():
                try:
                    msg_widget.hide()
                    msg_widget.deleteLater()
                    logger.debug("Copied message hidden")
                except Exception as e:
                    logger.error(f"Error hiding copied message: {e}")

            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(hide_message)
            timer.start(1500)

        except Exception as e:
            logger.error(f"Error showing copied message: {e}")

    def move_overlay_to_corner(self):
        """Move overlay window to configured corner"""
        try:
            corner = self.config_manager.get("overlay", "corner", fallback="Top Right")
            from PyQt6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            window_size = self.size()

            if corner == "Top Left":
                self.move(0, 0)
            elif corner == "Top Right":
                self.move(screen.width() - window_size.width(), 0)
            elif corner == "Bottom Left":
                self.move(0, screen.height() - window_size.height())
            elif corner == "Bottom Right":
                self.move(
                    screen.width() - window_size.width(),
                    screen.height() - window_size.height(),
                )
        except Exception as e:
            logger.error(f"Error moving overlay to corner: {e}")

    def on_search_text(self, text):
        try:
            self.filter_prompts()
        except Exception as e:
            logger.error(f"Error in search text: {e}")

    def on_search(self):
        try:
            self.filter_prompts()
        except Exception as e:
            logger.error(f"Error in search: {e}")

    def filter_prompts(self):
        try:
            search_text = self.search_ctrl.text().lower()

            if search_text.startswith("#") and len(search_text) > 1:
                tag = search_text[1:]
                if tag.lower() == "no tags":
                    self.filtered_prompts = [
                        p for p in self.prompts if not p.get("tags")
                    ]
                else:
                    self.filtered_prompts = [
                        p for p in self.prompts if tag in p.get("tags", [])
                    ]
            else:
                self.filtered_prompts = [
                    p
                    for p in self.prompts
                    if search_text in p["name"].lower()
                    or search_text in p["content"].lower()
                    or any(
                        tag for tag in p.get("tags", []) if search_text in tag.lower()
                    )
                ]

            self.update_prompts_list()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error filtering prompts: {e}")

    def on_tag_filter(self, tag):
        try:
            if tag == "No tags":
                self.filtered_prompts = [p for p in self.prompts if not p.get("tags")]
                self.search_ctrl.setText("#No tags")
            else:
                self.filtered_prompts = [
                    p for p in self.prompts if tag in p.get("tags", [])
                ]
                self.search_ctrl.setText(f"#{tag}")
            self.update_prompts_list()
        except Exception as e:
            logger.error(f"Error in tag filter: {e}")

    def on_prompt_click(self, prompt):
        try:
            success = self.app.insert_prompt(prompt["content"])
            if success:
                self.show_copied_message()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error copying prompt: {e}")

    def on_add_prompt(self):
        try:
            self.edit_prompt(None)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error adding prompt: {e}")

    def edit_prompt(self, prompt):
        try:
            dialog = EditPromptDialog(self, prompt)
            if dialog.exec():
                try:
                    data = dialog.get_data()
                    if data["id"] is None:
                        # New prompt
                        data["id"] = max([p["id"] for p in self.prompts], default=0) + 1
                        self.prompts.append(data)
                    else:
                        # Update existing
                        for i, p in enumerate(self.prompts):
                            if p["id"] == data["id"]:
                                self.prompts[i] = data
                                break

                    self.app.save_prompts(self.prompts)
                    self.filtered_prompts = self.prompts  # Reset filter
                    self.refresh_display()
                    self.search_ctrl.setText("")
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error saving prompt: {e}")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error editing prompt: {e}")

    def delete_prompt(self, prompt_id):
        try:
            self.prompts = [p for p in self.prompts if p["id"] != prompt_id]
            self.filtered_prompts = [
                p for p in self.filtered_prompts if p["id"] != prompt_id
            ]
            self.app.save_prompts(self.prompts)
            self.refresh_display()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error deleting prompt: {e}")

    def toggle_overlay(self):
        try:
            self.is_overlay = not self.is_overlay
            self.apply_overlay_mode()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error toggling overlay: {e}")
