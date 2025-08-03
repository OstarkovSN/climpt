import sys
import os
import gc
import re
import shiboken6
from PySide6.QtWidgets import (
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
    QDialog,
    QAbstractButton,
)
from PySide6.QtCore import Qt, QPoint, Signal, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QKeyEvent
from gui.tag_panel import TagPanel
from gui.edit_dialog import EditPromptDialog
from gui.settings_dialog import SettingsDialog
from gui.prompt_card import PromptCard
from config import ConfigManager
from gui.styles import style_manager
import logging
import time
import threading

logger = logging.getLogger(__name__)

OBJ_WAS_DELETED_REGEX = r"Internal C\+\+ object.*?already deleted"


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

    hole_for_X_height = 34
    hole_for_taskbar_height = 40

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
        self.filtered_prompts = set()
        self.is_overlay = False
        self.tag_panel = None
        self.tag_panel_shown = False
        self.dragging = False
        self.drag_offset = QPoint(0, 0)
        self.displayed_cards = []
        self.collapsed = False
        self.resize(500, 600)
        self.setMinimumSize(200, 200)
        self.collapsed_width = 50

        # Load configuration
        self.config_manager = ConfigManager()

        self.previous_pos = None

        # Set up mouse tracking for dragging
        self.setMouseTracking(True)

        self.setup_ui()

        style_manager.attach(self, "main_frame")
        self.uncollapsed_size = None

    def setup_ui(self):
        """
        Setup the main application UI.

        This method creates the main panel and its UI elements, including the
        top button panel, search control, and content area with prompts.

        It also sets up the sizer for the main panel and does some additional
        setup, such as setting up the accelerators from the configuration file.
        """
        if self.collapsed:
            self.setup_collapsed_ui()
        else:
            self.setup_full_ui()

    def setup_collapsed_ui(self):
        # Create the central widget which holds all other UI components
        if self.centralWidget():
            logger.debug("Clearing central widget")
            logger.debug(list(threading.enumerate()))
            style_manager.clear()
            self.cleanup()
        central_widget = QWidget()
        central_widget.setFixedWidth(self.collapsed_width)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        uncollapse_button = QPushButton(self.get_uncollapse_icon())
        main_layout.addWidget(uncollapse_button)
        uncollapse_button.clicked.connect(self.setup_full_ui)
        uncollapse_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        style_manager.attach(uncollapse_button, "collapse_control")
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.collapsed = True
        logger.debug(self.windowFlags())
        self.setWindowTitle("")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.Window
            | Qt.WindowType.Tool
            & ~Qt.WindowType.CustomizeWindowHint
            & ~Qt.WindowType.WindowMaximizeButtonHint
            & ~Qt.WindowType.WindowTitleHint
            & ~Qt.WindowType.WindowMinimizeButtonHint
            & ~Qt.WindowCloseButtonHint
        )
        self.show()
        self.uncollapsed_size = self.size()
        logger.debug(f"Uncollapsed size: {self.uncollapsed_size}")
        self.setMinimumSize(self.collapsed_width, 200)
        self.resize(self.collapsed_width, self.uncollapsed_size.height())
        if not (
            self.is_overlay
            and self.transform_overlay_to_side_panel
            and self.side_for_side_panel == "Left"
        ):
            self.move(
                self.pos().x() + self.uncollapsed_size.width() - self.collapsed_width,
                self.pos().y(),
            )
        logger.debug(f"Collapsed size: {self.size()}")

    def setup_full_ui(self):
        # Create the central widget which holds all other UI components
        if self.collapsed:
            style_manager.clear()
            self.resize(self.uncollapsed_size.width(), self.uncollapsed_size.height())
            if not (
                self.is_overlay
                and self.transform_overlay_to_side_panel
                and self.side_for_side_panel == "Left"
            ):
                self.move(
                    self.pos().x() - self.uncollapsed_size.width() + 50, self.pos().y()
                )
            self.collapsed = False
            self.setWindowTitle("Climpt")

        if self.centralWidget():
            style_manager.clear()
            self.cleanup()

        central_widget = QWidget()

        core_widget = QWidget()

        core_layout = QVBoxLayout()
        core_layout.setContentsMargins(0, 0, 0, 0)

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
        core_layout.addWidget(button_panel)

        # Create a search control for searching prompts or tags, full width
        self.search_ctrl = QLineEdit()
        self.search_ctrl.setPlaceholderText("Search prompts or #tags...")
        self.search_ctrl.returnPressed.connect(self.on_search)
        self.search_ctrl.textChanged.connect(self.on_search_text)

        core_layout.addWidget(self.search_ctrl)

        # Create a content area to hold the list of prompts
        self.content_widget = QWidget()
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
        style_manager.attach(self.prompts_container, "prompts_container")
        self.prompts_sizer = QVBoxLayout()
        # self.prompts_sizer.setContentsMargins(5, 5, 5, 5)
        self.prompts_sizer.setSpacing(5)
        self.prompts_container.setLayout(self.prompts_sizer)

        self.prompts_scroll.setWidget(self.prompts_container)

        content_layout.addWidget(self.prompts_scroll)
        self.content_widget.setLayout(content_layout)

        core_layout.addWidget(self.content_widget)
        core_widget.setLayout(core_layout)

        # Add core widget to central widget
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(core_widget)
        collapse_button = QPushButton(self.get_collapse_icon())
        style_manager.attach(collapse_button, "collapse_control")
        collapse_button.setFixedWidth(self.collapsed_width)
        collapse_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        collapse_button.clicked.connect(self.setup_collapsed_ui)
        main_layout.addWidget(collapse_button)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.update_prompts_list()
        if not self.is_overlay:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.Tool
                | Qt.WindowType.Window
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
            )
        self.show()

    def load_prompts(self, prompts):
        """Load prompts from storage and update the display.

        Args:
            prompts (list of dict): List of prompts to load.
        """
        try:
            self.prompts = prompts
            self.filtered_prompts = set(range(len(prompts)))
            self.refresh_display()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

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
            for card in self.displayed_cards:
                try:
                    card.cleanup()
                except AttributeError as e:
                    logger.warning(
                        "Ignoring error occured during cleanup of prompt card: [%s]: %s",
                        type(e),
                        e,
                    )
                except RuntimeError as e:
                    if not re.search(OBJ_WAS_DELETED_REGEX, str(e)):
                        print(str(e))
                        raise

            # Add prompt cards
            current_index = 0
            self.displayed_cards = []
            for original_index, prompt in enumerate(self.prompts):
                try:
                    if original_index in self.filtered_prompts:
                        card = PromptCard(
                            self.prompts_container,  # Parent widget
                            prompt,
                            self.on_prompt_click,
                            self.edit_prompt,
                            self.delete_prompt,
                            original_index,
                            current_index,
                        )
                        # card_wrapper = QWidget()
                        # card_wrapper_layout = QVBoxLayout()
                        # card_wrapper_layout.addWidget(card)
                        # card_wrapper.setLayout(card_wrapper_layout)
                        self.prompts_sizer.addWidget(card)
                        card.card_moved.connect(self.on_prompt_move)
                        self.displayed_cards.append(card)
                        current_index += 1
                except Exception as e:
                    logger.error(f"Error creating prompt card: {e}")
                    continue

            self.prompts_sizer.addStretch()
            self.prompts_container.setLayout(self.prompts_sizer)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            logger.error(f"Error updating prompts list: [{type(e)}]: {e}")
            QMessageBox.critical(self, "Error", f"Error updating prompts list: {e}")

    def on_prompt_move(self, from_index, to_index):
        logger.debug(f"on_prompt_move: {from_index} -> {to_index}")
        to_card = self.displayed_cards[to_index]
        to_card.current_index = to_index
        from_card = self.displayed_cards.pop(from_index)
        from_card.current_index = to_index
        self.prompts[to_card.original_index], self.prompts[from_card.original_index] = (
            self.prompts[from_card.original_index],
            self.prompts[to_card.original_index],
        )
        to_card.original_index, from_card.original_index = (
            from_card.original_index,
            to_card.original_index,
        )
        self.displayed_cards.insert(to_index, from_card)
        self.app.save_prompts(self.prompts)
        self.refresh_display()

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
                from PySide6.QtWidgets import QApplication

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

    def cleanup(self):
        logger.debug("Cleaning up window...")
        logger.debug("Threads: %s", threading.enumerate())
        try:
            self.search_ctrl.textChanged.disconnect()
            self.search_ctrl.returnPressed.disconnect()
        except RuntimeError as e:
            if not re.search(OBJ_WAS_DELETED_REGEX, str(e)):
                print("'" + str(e) + "'")
                raise
        for dialog in self.findChildren(QDialog):
            dialog.close()
        for child in self.findChildren(QWidget):
            if hasattr(child, "cleanup"):
                child.cleanup()
        for child in self.findChildren(QAbstractButton):
            try:
                child.clicked.disconnect()
            except TypeError:
                logger.debug(
                    "Attempted to disconnect button %s (with text %s) already disconnected",
                    child,
                    child.text(),
                )
        logger.debug("Threads after cleanup: %s", threading.enumerate())
        logger.debug("Cleanup complete")

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            gc.collect()
            logger.debug("Closing window...")
            self.cleanup()
            self.app.on_window_close()
        except Exception as e:
            logger.error(f"Error in close handler: {e}")
        finally:
            logger.debug("Accepting close event...")
            event.accept()  # Always accept to prevent hanging
            gc.collect()
            logger.debug("Close event accepted")
            logger.debug("Threads: %s", threading.enumerate())
            logger.debug("Starting forced exit timer (30 seconds)...")

            def force_exit():
                time.sleep(10)
                logger.debug("20 seconds until forced exit...")
                time.sleep(5)
                logger.debug("15 seconds until forced exit...")
                for i in range(9):
                    logger.debug("%d seconds until forced exit...", 10 - i)
                    time.sleep(1)
                logger.debug("1 second until forced exit...")
                time.sleep(1)
                logger.debug("Forcing exit...")
                logger.debug("Threads on forced exit: %s", threading.enumerate())
                logger.debug("Forced exit timer thread: %s", threading.current_thread())
                logger.critical(
                    "Application was forced to exit. This is a known bug that I've faild to fix"
                )
                logger.critical(
                    "Pls, send help -→ https://github.com/OstarkovSN/climpt/issues/1",
                )
                os._exit(0)

            killer = threading.Thread(target=force_exit, daemon=True, name="App killer")
            killer.start()

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
                self.setWindowOpacity(0.86)  # Semi-transparent.
                # Make it narrower in overlay mode
                self.resize(500, 500)
                # Move to configured corner
                self.move_overlay_to_corner()
                # Transform into side panel (if configured)
                self.transform_into_side_panel()
                # Enable mouse tracking for hover effects
                self.setMouseTracking(True)
            else:
                # Normal mode
                self.overlay_btn.setText("Overlay")
                self.setWindowFlags(
                    Qt.WindowType.Window
                    | Qt.WindowCloseButtonHint
                    | Qt.WindowType.WindowMinimizeButtonHint
                    | Qt.WindowType.WindowMaximizeButtonHint
                )
                self.setWindowOpacity(1.0)  # Opaque
                # Restore normal size
                self.resize(500, 600)
                # Disable mouse tracking in normal mode
                self.setMouseTracking(False)
                if self.previous_pos:
                    self.move(self.previous_pos)

            self.show()  # Required after changing window flags
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            logger.critical(f"Error applying overlay mode: {e}")
            QMessageBox.critical(self, "Error", f"Error applying overlay mode: {e}")

    def transform_into_side_panel(self):
        if self.is_overlay:
            if self.transform_overlay_to_side_panel:
                if re.search("Bottom", self.overlay_corner):
                    self.move(self.x(), 0)
                full_height = QApplication.primaryScreen().size().height()
                if self.side_panel_leave_holes:
                    if self.side_for_side_panel == "Left":
                        self.resize(
                            self.width(),
                            full_height - self.hole_for_taskbar_height,
                        )
                    else:
                        self.resize(
                            self.width(),
                            full_height
                            - self.hole_for_X_height
                            - self.hole_for_taskbar_height,
                        )
                        self.move(self.x(), self.hole_for_X_height)
                else:
                    self.resize(self.width(), full_height)

        else:
            logger.warning(
                "Tried to transform into side panel in normal mode, please report a bug"
            )
            # REPORT BUG!

    @property
    def overlay_corner(self):
        return self.config_manager.get("overlay", "corner", fallback="Top Right")

    @property
    def transform_overlay_to_side_panel(self):
        return (
            self.config_manager.get("overlay", "transform_into_side_panel", False)
            and self.side_for_side_panel is not None
        )  # self.side_for_side_panel is None if overlay should be left on its previous place

    @property
    def side_panel_leave_holes(self):
        return self.config_manager.get("overlay", "side_panel_leave_holes", False)

    @property
    def side_for_side_panel(self):
        if re.search("Left", self.overlay_corner):
            return "Left"
        elif re.search("Right", self.overlay_corner):
            return "Right"

    def get_collapse_icon(self):
        if self.side_for_side_panel == "Left" and self.is_overlay:
            return "<"
        else:
            return ">"

    def get_uncollapse_icon(self):
        if self.get_collapse_icon() == "<":
            return ">"
        else:
            return "<"

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
                    self.tag_panel = TagPanel(self.content_widget)
                    self.tag_panel.set_on_tag_click(self.on_tag_filter)
                    self.update_tags_panel()

                # Insert tag panel at the beginning of the layout
                self.content_layout = self.content_widget.layout()
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
            if self.content_widget.layout() is not None:
                self.content_widget.layout().update()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error toggling tags panel: {e}")

    def show_settings(self, event):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self, self.config_manager)
            if dialog.exec():
                settings = dialog.get_settings()

                # Update config
                for section, values in settings.items():
                    for key, value in values.items():
                        self.config_manager.set(section, key, value)

                # Save config
                self.config_manager.save_config()

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error showing settings: {e}")

    def show_about(self, event):
        """Show about dialog"""
        try:
            from PySide6.QtWidgets import QMessageBox

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
            from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PySide6.QtCore import QTimer
            from PySide6.QtGui import QPalette

            # Create a temporary message widget
            msg_widget = QWidget(self)
            style_manager.attach(msg_widget, "copied_message")
            msg_widget.setFixedHeight(40)
            msg_widget.setFixedWidth(200)

            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)

            msg_label = QLabel("Copied!")
            style_manager.attach(msg_label, "copied_message_label")

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
            self.app.timers.append(timer)

        except Exception as e:
            logger.error(f"Error showing copied message: {e}")

    def move_overlay_to_corner(self):
        """Move overlay window to configured corner"""
        try:
            corner = self.overlay_corner
            from PySide6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            window_size = self.size()
            self.previous_pos = self.pos()
            if corner == "Leave":
                self.previous_pos = None
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
                    self.filtered_prompts = {
                        i for i, p in enumerate(self.prompts) if not p.get("tags")
                    }
                else:
                    self.filtered_prompts = {
                        i
                        for i, p in enumerate(self.prompts)
                        if tag in p.get("tags", [])
                    }
            else:
                self.filtered_prompts = {
                    i
                    for i, p in enumerate(self.prompts)
                    if search_text in p["name"].lower()
                    or search_text in p["content"].lower()
                    or any(
                        tag for tag in p.get("tags", []) if search_text in tag.lower()
                    )
                }

            self.update_prompts_list()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error filtering prompts: {e}")

    def on_tag_filter(self, tag):
        try:
            if tag == "No tags":
                self.filtered_prompts = {
                    i for i, p in enumerate(self.prompts) if not p.get("tags")
                }
                self.search_ctrl.setText("#No tags")
            else:
                self.filtered_prompts = {
                    i for i, p in enumerate(self.prompts) if tag in p.get("tags", [])
                }
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
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error copying prompt: {e}")

    def on_add_prompt(self):
        try:
            self.edit_prompt(None)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

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
                    self.filtered_prompts = set(
                        range(len(self.prompts))
                    )  # Reset filter
                    self.refresh_display()
                    self.search_ctrl.setText("")
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error saving prompt: {e}")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error editing prompt: {e}")

    def delete_prompt(self, prompt_id):
        try:
            self.prompts = [p for p in self.prompts if p["id"] != prompt_id]
            self.filtered_prompts = {
                i for i, p in enumerate(self.prompts) if p["id"] != prompt_id
            }
            self.app.save_prompts(self.prompts)
            self.refresh_display()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error deleting prompt: {e}")

    def toggle_overlay_from_hotkey(self):
        logger.debug("Toggling overlay from hotkey")
        self.toggle_overlay()

    def toggle_overlay(self):
        try:
            self.is_overlay = not self.is_overlay
            self.apply_overlay_mode()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            logger.error(f"Error toggling overlay: {e}")
            QMessageBox.critical(self, "Error", f"Error toggling overlay: {e}")
