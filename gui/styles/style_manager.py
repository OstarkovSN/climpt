"""Style Manager for Climpt application"""

import os
import yaml
from PySide6.QtCore import QFileSystemWatcher
import logging
from utils import correct_qss

logger = logging.getLogger(__name__)


class StyleManager:
    def __init__(self, styles_dir="gui/styles"):
        self.styles_dir = styles_dir
        self.themes_dir = os.path.join(styles_dir, "theme")
        self.components_dir = os.path.join(styles_dir, "components")

        # Create directories if they don't exist
        os.makedirs(self.themes_dir, exist_ok=True)
        os.makedirs(self.components_dir, exist_ok=True)

        # Set up file watcher for live reloading
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._on_directory_changed)
        self.watcher.fileChanged.connect(self._on_file_changed)

        # Watch style directories
        if os.path.exists(self.themes_dir):
            self.watcher.addPath(self.themes_dir)
        if os.path.exists(self.components_dir):
            self.watcher.addPath(self.components_dir)

        self.attached_objects = {}
        try:
            self.current_theme = yaml.safe_load(
                open(os.path.join(self.themes_dir, "default.yaml"), "r")
            )
        except FileNotFoundError:
            try:
                self.current_theme_name = open(
                    os.path.join(self.themes_dir, "default-theme-name"), "r"
                ).read()
                self.current_theme = yaml.safe_load(
                    open(
                        os.path.join(
                            self.themes_dir, f"{self.current_theme_name}.yaml"
                        ),
                        "r",
                    )
                )
            except FileNotFoundError:
                logger.warning("No default theme found. Trying random theme.")
                for theme_file in os.listdir(self.themes_dir):
                    if theme_file.endswith(".yaml"):
                        self.current_theme = yaml.safe_load(
                            open(
                                os.path.join(self.themes_dir, theme_file),
                                "r",
                            )
                        )
                        break
                else:
                    logger.warning("No themes found. Using empty theme.")
                    self.current_theme = {}

    def get(self, component_name, theme=None):
        """
        Get style for a specific component.

        Args:
            component_name (str): Name of the component (e.g., 'prompt_card', 'main_window')
            theme (str, optional): Theme name. If None, uses current theme.

        Returns:
            str: QSS stylesheet for the component
        """
        theme = theme or self.current_theme

        # Try theme-specific component file
        component_file = os.path.join(self.components_dir, f"{component_name}.qss")
        if os.path.exists(component_file):
            try:
                with open(component_file, "r") as f:
                    return correct_qss(f.read()).format(**theme)
            except Exception as e:
                logger.error(
                    f"Error loading theme component style {component_file}: {e}"
                )

        return None

    def attach(self, obj, name, theme=None, theme_persistent=False):
        if name in self.attached_objects:
            self.attached_objects[name].append(
                {"obj": obj, "theme": theme, "theme_persistent": theme_persistent}
            )
        else:
            self.attached_objects[name] = [
                {"obj": obj, "theme": theme, "theme_persistent": theme_persistent}
            ]
        obj.setStyleSheet(self.get(name, theme))

    def refresh_styles(self):
        for name, objects in self.attached_objects.items():
            for obj in objects:
                obj["obj"].setStyleSheet(self.get(name, obj["theme"]))

    def apply_theme(self, theme_name):
        """
        Apply a complete theme to the application.

        Args:
            theme_name (str): Name of the theme to apply
            app (QApplication, optional): Application instance. If None, uses current app.
        """

        theme_file = os.path.join(self.themes_dir, theme_name + ".yaml")

        self.current_theme = yaml.safe_load(open(theme_file, "r"))
        for name, objects in self.attached_objects.items():
            for obj in objects:
                if not obj["theme_persistent"]:
                    obj["theme"] = self.current_theme
        self.refresh_styles()

    def get_available_themes(self):
        """Get list of available themes"""
        themes = []
        if os.path.exists(self.themes_dir):
            for item in os.listdir(self.themes_dir):
                if item.endswith(".yaml"):
                    themes.append(item[:-5])
        return themes

    def get_available_components(self):
        """Get list of styled components"""
        components = set()

        # Check global components
        if os.path.exists(self.components_dir):
            for file in os.listdir(self.components_dir):
                if file.endswith(".qss"):
                    components.add(file[:-4])  # Remove .qss extension
        return list(components)

    def _on_directory_changed(self, path):
        """Handle directory changes (files added/removed)"""
        logger.debug(f"Directory changed: {path}")
        # You could trigger a theme reload here if needed

    def _on_file_changed(self, path):
        """Handle file changes (live reloading)"""
        logger.debug(f"Style file changed: {path}")
        # Reload current theme when style files change
        if self.current_theme:
            self.apply_theme(self.current_theme)

    def clear(self):
        self.attached_objects = {}

    def cleanup(self):
        self.clear()
        self.watcher.directoryChanged.disconnect()
        self.watcher.fileChanged.disconnect()
        self.watcher.deleteLater()
