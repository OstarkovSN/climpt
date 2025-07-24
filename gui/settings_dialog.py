import wx

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent, title="Settings", size=(400, 300))
        self.config_manager = config_manager
        self.setup_ui()
        
    def setup_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Hotkeys section
        hotkeys_label = wx.StaticText(panel, label="Hotkeys")
        hotkeys_font = hotkeys_label.GetFont()
        hotkeys_font.SetWeight(wx.FONTWEIGHT_BOLD)
        hotkeys_label.SetFont(hotkeys_font)
        sizer.Add(hotkeys_label, 0, wx.ALL, 5)
        
        # Overlay hotkey
        overlay_sizer = wx.BoxSizer(wx.HORIZONTAL)
        overlay_sizer.Add(wx.StaticText(panel, label="Toggle Overlay:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.overlay_hotkey = wx.TextCtrl(panel, value=self.config_manager.get('hotkeys', 'overlay', fallback='alt+p'))
        overlay_sizer.Add(self.overlay_hotkey, 1, wx.ALL, 5)
        sizer.Add(overlay_sizer, 0, wx.EXPAND)
        
        # Tags hotkey
        tags_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tags_sizer.Add(wx.StaticText(panel, label="Toggle Tags:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.tags_hotkey = wx.TextCtrl(panel, value=self.config_manager.get('hotkeys', 'tags', fallback='alt+t'))
        tags_sizer.Add(self.tags_hotkey, 1, wx.ALL, 5)
        sizer.Add(tags_sizer, 0, wx.EXPAND)
        
        # Position section
        position_label = wx.StaticText(panel, label="Overlay Position")
        position_font = position_label.GetFont()
        position_font.SetWeight(wx.FONTWEIGHT_BOLD)
        position_label.SetFont(position_font)
        sizer.Add(position_label, 0, wx.ALL, 5)
        
        # Corner selection
        corner_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner_sizer.Add(wx.StaticText(panel, label="Corner:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.corner_choice = wx.Choice(panel, choices=["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Leave"])
        current_corner = self.config_manager.get('overlay', 'corner', fallback='Leave')
        if current_corner in ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]:
            self.corner_choice.SetStringSelection(current_corner)
        else:
            self.corner_choice.SetStringSelection("Leave")
        corner_sizer.Add(self.corner_choice, 1, wx.ALL, 5)
        sizer.Add(corner_sizer, 0, wx.EXPAND)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        button_sizer.Add(ok_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        panel.SetSizer(sizer)
        
    def on_ok(self, event):
        self.EndModal(wx.ID_OK)
        
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def get_settings(self):
        return {
            'hotkeys': {
                'overlay': self.overlay_hotkey.GetValue(),
                'tags': self.tags_hotkey.GetValue()
            },
            'overlay': {
                'corner': self.corner_choice.GetStringSelection()
            }
        }