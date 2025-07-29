import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from gui.main_frame import MainFrame
from storage import load_prompts, save_prompts
from utils import insert_prompt
from hotkeys import HotkeyManager
import logging

logger = logging.getLogger(__name__)


class ClimptApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setApplicationName("Climpt")
        self.setApplicationVersion("0.1.0")

        # Initialize components
        self.hotkey_manager = HotkeyManager()
        self.frame = MainFrame(self)
        self.prompts = load_prompts()
        self.frame.load_prompts(self.prompts)

        # Register hotkeys
        self.hotkey_manager.register_hotkey("alt+p", self.toggle_overlay)
        self.hotkey_manager.register_hotkey("alt+t", self.toggle_tags)

        # Start hotkey listener
        self.hotkey_manager.start()

        self.frame.show()

    def toggle_overlay(self):
        """Called from hotkey"""
        if hasattr(self, "frame") and self.frame:
            # Use QTimer to ensure thread-safe execution
            QTimer.singleShot(0, self._safe_toggle_overlay)

    def _safe_toggle_overlay(self):
        """Safe overlay toggle with state checking"""
        if hasattr(self, "frame") and self.frame:
            try:
                self.frame.toggle_overlay()
            except Exception as e:
                logger.error(f"Error toggling overlay: {e}")

    def toggle_tags(self):
        """Called from hotkey"""
        if hasattr(self, "frame") and self.frame:
            QTimer.singleShot(0, self._safe_toggle_tags)

    def _safe_toggle_tags(self):
        """Safe tags toggle"""
        if hasattr(self, "frame") and self.frame:
            try:
                self.frame.toggle_tags_panel(None)
            except Exception as e:
                logger.error(f"Error toggling tags: {e}")

    def insert_prompt(self, content):
        """Insert prompt content to clipboard - returns success status"""
        try:
            success = insert_prompt(content)
            if success:
                logger.debug("Prompt copied to clipboard!")
            else:
                logger.warning("Failed to copy prompt to clipboard")
            return success
        except Exception as e:
            logger.error(f"Error inserting prompt: {e}")
            return False

    def save_prompts(self, prompts):
        """Save prompts to file"""
        try:
            return save_prompts(prompts)
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            return False

    def on_window_close(self):
        """Called when window is closing"""
        try:
            if hasattr(self, "hotkey_manager"):
                self.hotkey_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping hotkey manager: {e}")

    def cleanup(self):
        """Proper cleanup before application exit"""
        try:
            self.on_window_close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def exec(self):
        """Execute the application and handle cleanup"""
        try:
            return super().exec()
        finally:
            self.cleanup()
