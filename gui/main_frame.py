import wx
import wx.lib.scrolledpanel as scrolled
from gui.tag_panel import TagPanel
from gui.edit_dialog import EditPromptDialog
from gui.settings_dialog import SettingsDialog
from gui.prompt_card import PromptCard
from config import ConfigManager
import logging

logger = logging.getLogger(__name__)


class MainFrame(wx.Frame):
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
        drag_offset: wx.Point object representing the drag offset.
        config_manager: Instance of ConfigManager to handle app configuration.
    """

    def __init__(self, app):
        """
        Initialize the main application frame.

        Args:
            app: The wx.App instance to which this frame belongs.

        Attributes:
            app: Reference to the application instance.
            prompts: List to hold all prompts.
            filtered_prompts: List to hold currently filtered prompts.
            is_overlay: Boolean indicating if the overlay is active.
            tag_panel: Reference to the TagPanel instance.
            tag_panel_shown: Boolean indicating if the tag panel is shown.
            dragging: Boolean indicating if the window is being dragged.
            drag_offset: wx.Point object representing the drag offset.
            config_manager: Instance of ConfigManager to handle app configuration.
        """

        super().__init__(None, title="Climpt", size=(500, 600))
        self.app = app
        self.prompts = []
        self.filtered_prompts = []
        self.is_overlay = False
        self.tag_panel = None
        self.tag_panel_shown = False
        self.dragging = False
        self.drag_offset = wx.Point(0, 0)

        # Load configuration
        self.config_manager = ConfigManager()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

        self.setup_ui()

    def setup_ui(self):
        # Main panel - this is what gets the sizer
        """
        Setup the main application UI.

        This method creates the main panel and its UI elements, including the
        top button panel, search control, and content area with prompts.

        It also sets up the sizer for the main panel and does some additional
        setup, such as setting up the accelerators from the configuration file.
        """
        # Create the main panel which holds all other UI components
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)  # Vertical box sizer for main layout

        # Create a top button panel for various control buttons
        button_panel = wx.Panel(main_panel)
        button_sizer = wx.WrapSizer(wx.HORIZONTAL)  # WrapSizer for automatic wrapping

        # "Tags" button to toggle the tags panel
        self.tags_btn = wx.Button(button_panel, label="Tags")
        self.tags_btn.Bind(wx.EVT_BUTTON, self.toggle_tags_panel)

        # "Settings" button to show settings dialog
        self.settings_btn = wx.Button(button_panel, label="Settings")
        self.settings_btn.Bind(wx.EVT_BUTTON, self.show_settings)

        # "About" button to show about information
        self.about_btn = wx.Button(button_panel, label="About")
        self.about_btn.Bind(wx.EVT_BUTTON, self.show_about)

        # "Overlay" button to toggle overlay visibility
        self.overlay_btn = wx.Button(button_panel, label="Overlay")
        self.overlay_btn.Bind(wx.EVT_BUTTON, self.toggle_overlay)

        # "+ Add Prompt" button to add a new prompt
        self.add_btn = wx.Button(button_panel, label="+ Add Prompt")
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_prompt)

        # Add all buttons to the button sizer with padding
        button_sizer.Add(self.tags_btn, 0, wx.ALL, 2)
        button_sizer.Add(self.settings_btn, 0, wx.ALL, 2)
        button_sizer.Add(self.about_btn, 0, wx.ALL, 2)
        button_sizer.Add(self.overlay_btn, 0, wx.ALL, 2)
        button_sizer.Add(self.add_btn, 0, wx.ALL, 2)

        # Set the sizer for the button panel
        button_panel.SetSizer(button_sizer)
        main_sizer.Add(
            button_panel, 0, wx.EXPAND | wx.ALL, 5
        )  # Add button panel to main sizer

        # Create a search control for searching prompts or tags, full width
        self.search_ctrl = wx.SearchCtrl(main_panel)
        self.search_ctrl.ShowCancelButton(
            True
        )  # Show cancel button in the search control
        self.search_ctrl.SetHint("Search prompts or #tags...")  # Placeholder hint text
        self.search_ctrl.Bind(
            wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_search
        )  # Bind search event
        self.search_ctrl.Bind(
            wx.EVT_TEXT, self.on_search_text
        )  # Bind text change event

        main_sizer.Add(
            self.search_ctrl, 0, wx.ALL | wx.EXPAND, 5
        )  # Add search control to main sizer

        # Create a content panel to hold the list of prompts
        self.content_panel = wx.Panel(main_panel)
        self.content_sizer = wx.BoxSizer(
            wx.HORIZONTAL
        )  # Horizontal sizer for content layout

        # Scrolled panel for displaying prompts with vertical scroll
        self.prompts_scroll = scrolled.ScrolledPanel(
            self.content_panel, style=wx.VSCROLL
        )
        self.prompts_scroll.SetBackgroundColour(
            wx.Colour(248, 248, 248)
        )  # Light background color
        self.prompts_sizer = wx.BoxSizer(wx.VERTICAL)  # Vertical sizer for prompts
        self.prompts_scroll.SetSizer(self.prompts_sizer)  # Set sizer for scrolled panel
        self.prompts_scroll.SetupScrolling()  # Enable scrolling

        self.content_sizer.Add(
            self.prompts_scroll, 1, wx.EXPAND
        )  # Add scrolled panel to content sizer
        self.content_panel.SetSizer(self.content_sizer)  # Set sizer for content panel

        main_sizer.Add(
            self.content_panel, 1, wx.EXPAND
        )  # Add content panel to main sizer
        main_panel.SetSizer(main_sizer)  # Set sizer for main panel, not the frame

        # Setup accelerators (keyboard shortcuts) from configuration
        self.setup_accelerators()

    def setup_accelerators(self):
        """
        Setup accelerators (hotkeys) from configuration.

        This function parses the hotkeys from the configuration and creates an
        accelerator table for the main frame. The accelerator table is then
        set on the main frame.

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
            entries = []

            # Overlay hotkey
            overlay_key = self.config_manager.get(
                "hotkeys", "overlay", fallback="alt+p"
            )
            if overlay_key:
                # Parse hotkey (simple parsing for common formats)
                modifiers = 0
                key_char = None

                if "alt" in overlay_key.lower():
                    modifiers |= wx.ACCEL_ALT
                if "ctrl" in overlay_key.lower():
                    modifiers |= wx.ACCEL_CTRL
                if "shift" in overlay_key.lower():
                    modifiers |= wx.ACCEL_SHIFT

                # Extract key character
                key_part = overlay_key.split("+")[-1].upper()
                if len(key_part) == 1:
                    key_char = ord(key_part)
                    entries.append((modifiers, key_char, self.overlay_btn.GetId()))

            # Tags hotkey
            tags_key = self.config_manager.get("hotkeys", "tags", fallback="alt+t")
            if tags_key:
                modifiers = 0
                key_char = None

                if "alt" in tags_key.lower():
                    modifiers |= wx.ACCEL_ALT
                if "ctrl" in tags_key.lower():
                    modifiers |= wx.ACCEL_CTRL
                if "shift" in tags_key.lower():
                    modifiers |= wx.ACCEL_SHIFT

                # Extract key character
                key_part = tags_key.split("+")[-1].upper()
                if len(key_part) == 1:
                    key_char = ord(key_part)
                    entries.append((modifiers, key_char, self.tags_btn.GetId()))

            if entries:
                accel_tbl = wx.AcceleratorTable(entries)
                self.SetAcceleratorTable(accel_tbl)
        except Exception as e:
            logger.error(f"Error setting up accelerators: {e}")

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
            wx.MessageBox(f"Error loading prompts: {e}", "Error", wx.OK | wx.ICON_ERROR)

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
            self.prompts_sizer.Clear(True)

            # Add prompt cards
            for prompt in self.filtered_prompts:
                try:
                    card = PromptCard(
                        self.prompts_scroll,
                        prompt,
                        self.on_prompt_click,
                        self.edit_prompt,
                        self.delete_prompt,
                    )
                    self.prompts_sizer.Add(card, 0, wx.ALL | wx.EXPAND, 5)
                except Exception as e:
                    logger.error(f"Error creating prompt card: {e}")
                    continue

            self.prompts_sizer.AddStretchSpacer()
            self.prompts_scroll.Layout()
            self.prompts_scroll.SetupScrolling()
        except Exception as e:
            wx.MessageBox(
                f"Error updating prompts list: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

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

                self.content_sizer.Prepend(self.tag_panel, 0, wx.EXPAND)
                self.tag_panel.Show()
                self.tag_panel_shown = True
                self.tags_btn.SetLabel("Hide Tags")
            else:
                # Hide tag panel
                if self.tag_panel:
                    self.content_sizer.Detach(self.tag_panel)
                    self.tag_panel.Hide()
                    self.tag_panel_shown = False
                    self.tags_btn.SetLabel("Tags")

            self.content_panel.Layout()
        except Exception as e:
            wx.MessageBox(
                f"Error toggling tags panel: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

    def show_settings(self, event):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self, self.config_manager)
            if dialog.ShowModal() == wx.ID_OK:
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

            dialog.Destroy()
        except Exception as e:
            wx.MessageBox(
                f"Error showing settings: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

    def show_about(self, event):
        """Show about dialog"""
        try:
            dlg = wx.MessageDialog(
                self,
                "Climpt - Clipboard Prompt Manager\nVersion 0.1.0\n\nA lightweight tool for managing and inserting text prompts.",
                "About Climpt",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")

    def show_copied_message(self):
        """Show 'Copied!' message"""
        try:
            # Create a temporary message panel
            msg_panel = wx.Panel(self)
            msg_panel.SetBackgroundColour(wx.Colour(46, 204, 113))  # Green color

            msg_sizer = wx.BoxSizer(wx.HORIZONTAL)
            msg_text = wx.StaticText(msg_panel, label="Copied!")
            msg_text.SetForegroundColour(wx.WHITE)
            msg_font = msg_text.GetFont()
            msg_font.SetWeight(wx.FONTWEIGHT_BOLD)
            msg_text.SetFont(msg_font)

            msg_sizer.Add(msg_text, 1, wx.ALL | wx.CENTER, 10)
            msg_panel.SetSizer(msg_sizer)

            # Position it at the bottom center
            main_panel = self.GetChildren()[0]  # Get the main panel
            panel_size = main_panel.GetSize()
            msg_panel.SetSize((200, 40))
            msg_panel.SetPosition((panel_size.width // 2 - 100, panel_size.height - 60))

            msg_panel.Show()
            msg_panel.Refresh()

            # Hide after 1.5 seconds
            def hide_message():
                try:
                    msg_panel.Hide()
                    msg_panel.Destroy()
                except:
                    pass

            wx.CallLater(1500, hide_message)
        except Exception as e:
            logger.error(f"Error showing copied message: {e}")

    def move_overlay_to_corner(self):
        """Move overlay window to configured corner"""
        try:
            corner = self.config_manager.get("overlay", "corner", fallback="Top Right")
            screen_size = wx.GetDisplaySize()
            window_size = self.GetSize()

            if corner == "Top Left":
                self.SetPosition((0, 0))
            elif corner == "Top Right":
                self.SetPosition((screen_size.width - window_size.width, 0))
            elif corner == "Bottom Left":
                self.SetPosition((0, screen_size.height - window_size.height))
            elif corner == "Bottom Right":
                self.SetPosition(
                    (
                        screen_size.width - window_size.width,
                        screen_size.height - window_size.height,
                    )
                )
        except Exception as e:
            logger.error(f"Error moving overlay to corner: {e}")

    def on_search_text(self, event):
        try:
            self.filter_prompts()
        except Exception as e:
            logger.error(f"Error in search text: {e}")
        event.Skip()

    def on_search(self, event):
        try:
            self.filter_prompts()
        except Exception as e:
            logger.error(f"Error in search: {e}")
        event.Skip()

    def filter_prompts(self):
        try:
            search_text = self.search_ctrl.GetValue().lower()

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
            wx.MessageBox(
                f"Error filtering prompts: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

    def on_tag_filter(self, tag):
        try:
            if tag == "No tags":
                self.filtered_prompts = [p for p in self.prompts if not p.get("tags")]
                self.search_ctrl.SetValue("#No tags")
            else:
                self.filtered_prompts = [
                    p for p in self.prompts if tag in p.get("tags", [])
                ]
                self.search_ctrl.SetValue(f"#{tag}")
            self.update_prompts_list()
        except Exception as e:
            logger.error(f"Error in tag filter: {e}")

    def on_prompt_click(self, prompt):
        try:
            success = self.app.insert_prompt(prompt["content"])
            if success:
                self.show_copied_message()
        except Exception as e:
            wx.MessageBox(f"Error copying prompt: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_add_prompt(self, event):
        try:
            self.edit_prompt(None)
        except Exception as e:
            wx.MessageBox(f"Error adding prompt: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def edit_prompt(self, prompt):
        try:
            dialog = EditPromptDialog(self, prompt)
            if dialog.ShowModal() == wx.ID_OK:
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
                    self.search_ctrl.SetValue("")
                except Exception as e:
                    wx.MessageBox(
                        f"Error saving prompt: {e}", "Error", wx.OK | wx.ICON_ERROR
                    )

            dialog.Destroy()
        except Exception as e:
            wx.MessageBox(f"Error editing prompt: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def delete_prompt(self, prompt_id):
        try:
            self.prompts = [p for p in self.prompts if p["id"] != prompt_id]
            self.filtered_prompts = [
                p for p in self.filtered_prompts if p["id"] != prompt_id
            ]
            self.app.save_prompts(self.prompts)
            self.refresh_display()
        except Exception as e:
            wx.MessageBox(f"Error deleting prompt: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def toggle_overlay(self, event=None):
        try:
            self.is_overlay = not self.is_overlay
            self.apply_overlay_mode()
        except Exception as e:
            wx.MessageBox(
                f"Error toggling overlay: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

    def apply_overlay_mode(self):
        try:
            if self.is_overlay:
                # Overlay mode
                self.overlay_btn.SetLabel("Normal")
                self.SetWindowStyle(
                    wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.BORDER_NONE
                )
                self.SetTransparent(220)  # Semi-transparent
                self.SetBackgroundColour(wx.Colour(30, 30, 30))
                # Make it narrower in overlay mode
                self.SetSize((400, 500))
                # Move to configured corner
                self.move_overlay_to_corner()
            else:
                # Normal mode
                self.overlay_btn.SetLabel("Overlay")
                self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE)
                self.SetTransparent(255)  # Opaque
                self.SetBackgroundColour(
                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
                )
                # Restore normal size
                self.SetSize((500, 600))

            self.Refresh()
        except Exception as e:
            wx.MessageBox(
                f"Error applying overlay mode: {e}", "Error", wx.OK | wx.ICON_ERROR
            )

    def on_mouse_down(self, event):
        try:
            if self.is_overlay:
                self.dragging = True
                self.drag_offset = event.GetPosition()
        except Exception as e:
            logger.error(f"Error in mouse down: {e}")
        event.Skip()

    def on_mouse_up(self, event):
        try:
            if self.is_overlay:
                self.dragging = False
        except Exception as e:
            logger.error(f"Error in mouse up: {e}")
        event.Skip()

    def on_mouse_move(self, event):
        try:
            if self.is_overlay and self.dragging and event.Dragging():
                screen_pos = event.GetPosition() + self.GetPosition() - self.drag_offset
                self.Move(screen_pos)
        except Exception as e:
            logger.error(f"Error in mouse move: {e}")
        event.Skip()

    def on_close(self, event):
        try:
            self.app.on_window_close()
        except Exception as e:
            logger.error(f"Error in close handler: {e}")
        event.Skip()  # Always skip to allow normal close
