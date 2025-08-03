import os
import logging

from yaml import safe_load, safe_dump

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_file="climpt.yaml"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        logger.info(f"Loading config from {self.config_file}")
        try:
            self.config = safe_load(open(self.config_file, "r"))
            logger.info("Loaded config from file")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config if loading fails
            logger.info("Using default config")
            # Default configuration
            self.config["hotkeys"] = {"overlay": "alt+p", "tags": "alt+t"}
            self.config["overlay"] = {
                "corner": "Top Right",
                "transform_into_side_panel": False,
                "leave_holes": False,
            }
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as configfile:
                safe_dump(self.config, configfile)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, section, key, fallback=None):
        """Get configuration value"""
        return self.config[section].get(key, fallback)

    def set(self, section, key, value):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_all_settings(self):
        """Get all settings as dictionary"""
        settings = {}
        for section in self.config.sections():
            settings[section] = {}
            for key, value in self.config[section].items():
                settings[section][key] = value
        return settings
