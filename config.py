import configparser
import os
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_file="climpt.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
            else:
                # Default configuration
                self.config["hotkeys"] = {"overlay": "alt+p", "tags": "alt+t"}
                self.config["overlay"] = {"corner": "Top Right"}
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config if loading fails
            self.config["hotkeys"] = {"overlay": "alt+p", "tags": "alt+t"}
            self.config["overlay"] = {"corner": "Top Right"}

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, section, key, fallback=None):
        """Get configuration value"""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)

    def get_all_settings(self):
        """Get all settings as dictionary"""
        settings = {}
        for section in self.config.sections():
            settings[section] = {}
            for key, value in self.config[section].items():
                settings[section][key] = value
        return settings
