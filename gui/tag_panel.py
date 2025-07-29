import wx
import colorsys
import hashlib
import logging

logger = logging.getLogger(__name__)


class TagPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_THEME)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.tag_buttons = {}
        self.on_tag_click_callback = None

        # Header
        header = wx.StaticText(self, label="TAGS")
        header_font = header.GetFont()
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        self.sizer.Add(header, 0, wx.ALL, 10)

    def set_on_tag_click(self, callback):
        self.on_tag_click_callback = callback

    def update_tags(self, tag_counts):
        # Clear existing buttons
        self.tag_buttons.clear()

        # Remove old items (keep header)
        while self.sizer.GetItemCount() > 1:
            self.sizer.Hide(1)
            self.sizer.Remove(1)

        # Add tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags:
            btn = self.create_tag_button(tag, count)
            btn.Bind(wx.EVT_BUTTON, lambda evt, t=tag: self.on_tag_click(t))
            self.sizer.Add(btn, 0, wx.ALL | wx.EXPAND, 2)
            self.tag_buttons[tag] = btn

        # Add "No tags" if needed
        if "No tags" in tag_counts and tag_counts["No tags"] > 0:
            btn = self.create_tag_button("No tags", tag_counts["No tags"])
            btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_tag_click("No tags"))
            self.sizer.Add(btn, 0, wx.ALL | wx.EXPAND, 2)

        self.sizer.AddStretchSpacer()
        self.Layout()

    def create_tag_button(self, tag, count):
        btn = wx.Button(self, label=f"#{tag} ({count})" if count > 0 else f"#{tag}")
        color = self.get_tag_color(tag)
        btn.SetBackgroundColour(color)
        btn.SetForegroundColour(wx.WHITE)
        btn.SetWindowStyle(wx.BORDER_NONE)

        # Make it look like a tag blob
        btn.SetMinSize((-1, 25))
        return btn

    def get_tag_color(self, tag):
        # Generate consistent color for tag
        hash_object = hashlib.md5(tag.encode())
        hash_hex = hash_object.hexdigest()
        hue = int(hash_hex[:8], 16) % 360 / 360.0
        saturation = 0.7 + (int(hash_hex[8:10], 16) % 30) / 100.0
        value = 0.6 + (int(hash_hex[10:12], 16) % 40) / 100.0

        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        r, g, b = [int(c * 255) for c in rgb]
        return wx.Colour(r, g, b)

    def on_tag_click(self, tag):
        if self.on_tag_click_callback:
            self.on_tag_click_callback(tag)
