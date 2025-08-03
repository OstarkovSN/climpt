import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal
from gui.main_frame import MainFrame
from storage import load_prompts, save_prompts
from utils import insert_prompt
import logging
from gui.styles import style_manager

logger = logging.getLogger(__name__)


class ClimptApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setApplicationName("Climpt")
        self.setApplicationVersion("0.1.0")

        self.frame = MainFrame(self)
        self.prompts = load_prompts()
        self.frame.load_prompts(self.prompts)
        self.timers = []


        self.frame.show()

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
            logger.debug("on_window_close called")
            if hasattr(self, "hotkey_manager"):
                self.hotkey_manager.stop()
            for timer in self.timers:
                logger.debug("Stopping timer %s", timer)
                timer.stop()
            style_manager.cleanup()
            self.processEvents()
        except Exception as e:
            logger.error(f"Error stopping hotkey manager: {e}")
        logger.debug("on_window_close finished")
