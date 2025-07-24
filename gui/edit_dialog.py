import wx

class EditPromptDialog(wx.Dialog):
    def __init__(self, parent, prompt=None):
        title = "Edit Prompt" if prompt else "Add New Prompt"
        super().__init__(parent, title=title, size=(500, 400))
        
        self.prompt = prompt or {"id": None, "name": "", "content": "", "tags": []}
        self.setup_ui()
        
    def setup_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Name
        name_label = wx.StaticText(panel, label="Name:")
        self.name_ctrl = wx.TextCtrl(panel, value=self.prompt["name"])
        sizer.Add(name_label, 0, wx.ALL, 5)
        sizer.Add(self.name_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # Content
        content_label = wx.StaticText(panel, label="Content:")
        self.content_ctrl = wx.TextCtrl(panel, value=self.prompt["content"], 
                                       style=wx.TE_MULTILINE | wx.HSCROLL)
        self.content_ctrl.SetMinSize((400, 150))
        sizer.Add(content_label, 0, wx.ALL, 5)
        sizer.Add(self.content_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # Tags
        tags_label = wx.StaticText(panel, label="Tags (comma separated):")
        tags_str = ", ".join(self.prompt["tags"])
        self.tags_ctrl = wx.TextCtrl(panel, value=tags_str)
        sizer.Add(tags_label, 0, wx.ALL, 5)
        sizer.Add(self.tags_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
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
        
    def get_data(self):
        tags_str = self.tags_ctrl.GetValue()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        return {
            "id": self.prompt["id"],
            "name": self.name_ctrl.GetValue(),
            "content": self.content_ctrl.GetValue(),
            "tags": tags
        }