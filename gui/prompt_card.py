import wx
import wx.lib.scrolledpanel as scrolled

class PromptCard(wx.Panel):
    def __init__(self, parent, prompt, on_click, on_edit, on_delete):
        super().__init__(parent, style=wx.BORDER_THEME)
        self.prompt = prompt
        self.on_click = on_click
        self.on_edit = on_edit
        self.on_delete = on_delete # This is MainFrame.delete_prompt
        self.SetBackgroundColour(wx.WHITE)
        self.setup_ui()
        
        # Bind events to the main panel
        self.Bind(wx.EVT_LEFT_DOWN, self.on_card_click)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_card_click)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        
        # Bind events to all child controls
        self.bind_events_recursive(self)
        
    def bind_events_recursive(self, widget):
        """Bind events to all child widgets"""
        try:
            # Only bind to widgets that support these events
            if isinstance(widget, (wx.StaticText, wx.Panel, wx.Button)):
                widget.Bind(wx.EVT_LEFT_DOWN, self.on_card_click)
                widget.Bind(wx.EVT_LEFT_DCLICK, self.on_card_click)
                widget.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        except Exception as e:
            # Silently ignore binding errors for unsupported widgets
            pass
        
        # Bind to children
        for child in widget.GetChildren():
            self.bind_events_recursive(child)
        
    def setup_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        prompt_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header with bold font
        header = wx.StaticText(self, label=self.prompt["name"])
        header_font = header.GetFont()
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header_font.SetPointSize(11)
        header.SetFont(header_font)
        header.SetForegroundColour(wx.Colour(70, 130, 180))  # Steel blue
        
        prompt_sizer.Add(header, 0, wx.ALL, 8)
        
        # Content - first few lines
        content_lines = self.prompt["content"].split('\n')
        content_preview = '\n'.join(content_lines[:1])  # First line
        if len(content_lines) > 3:
            content_preview += "\n..."
            
        content = wx.StaticText(self, label=content_preview)
        content.Wrap(300)  # Wrap text
        prompt_sizer.Add(content, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        main_sizer.Add(prompt_sizer, 0, wx.LEFT | wx.RIGHT, 8)
        
        # Tags as blobs
        if self.prompt.get("tags"):
            tags_sizer = wx.BoxSizer(wx.HORIZONTAL)
            for tag in self.prompt["tags"]:
                tag_blob = wx.Button(self, label=f"#{tag}", size=(-1, 22))
                tag_blob.SetBackgroundColour(wx.Colour(240, 240, 240))
                tag_blob.SetForegroundColour(wx.BLACK)
                tag_blob.SetWindowStyle(wx.BORDER_NONE)
                # Bind click to copy tag to search
                tag_blob.Bind(wx.EVT_BUTTON, lambda evt, t=tag: self.copy_tag_to_search(t))
                tags_sizer.Add(tag_blob, 0, wx.ALL, 2)
            main_sizer.Add(tags_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        self.SetSizer(main_sizer)
        self.SetMinSize((-1, 120))
        
    def copy_tag_to_search(self, tag):
        """Copy tag to search box"""
        try:
            # Navigate up the parent hierarchy to find the main frame
            # Adjust the navigation based on your actual structure
            # This is a common source of errors if the structure changes
            parent = self.GetParent()  # prompts_scroll
            if parent:
                parent = parent.GetParent()  # content_panel
                if parent:
                    parent = parent.GetParent()  # main_panel
                    # Get the top-level parent (MainFrame)
                    top_parent = self.GetTopLevelParent()
                    if top_parent and hasattr(top_parent, 'search_ctrl'):
                        search_ctrl = top_parent.search_ctrl
                        wx.CallAfter(search_ctrl.SetValue, f"#{tag}")
                        # Trigger search after a short delay to ensure value is set
                        def trigger_search():
                            try:
                                evt = wxCommandEvent(wx.wxEVT_SEARCHCTRL_SEARCH_BTN)
                                wx.PostEvent(search_ctrl, evt)
                            except Exception as e:
                                print(f"Error triggering search: {e}")
                        wx.CallAfter(trigger_search)
                    else:
                        print("Could not find search control in top-level parent")
        except Exception as e:
            print(f"Error copying tag to search: {e}")
        
    def on_card_click(self, event):
        try:
            self.on_click(self.prompt)
        except Exception as e:
            wx.MessageBox(f"Error handling card click: {e}", "Error", wx.OK | wx.ICON_ERROR)
        # Always skip to allow normal event processing
        event.Skip()
        
    def on_right_click(self, event):
        """Show context menu"""
        try:
            menu = wx.Menu()
            
            edit_item = menu.Append(wx.ID_ANY, "Edit Prompt")
            delete_item = menu.Append(wx.ID_ANY, "Delete Prompt")
            
            # Add separator and copy content option
            menu.AppendSeparator()
            copy_content_item = menu.Append(wx.ID_ANY, "Copy Content")
            
            def on_edit(evt):
                try:
                    if self.on_edit: # Check if callback exists
                        self.on_edit(self.prompt)
                    else:
                        wx.MessageBox("Edit callback not set", "Error", wx.OK | wx.ICON_WARNING)
                except Exception as e:
                    wx.MessageBox(f"Error editing prompt: {e}", "Error", wx.OK | wx.ICON_ERROR)
                
            def on_delete(evt):
                try:
                    # Show confirmation dialog
                    dlg = wx.MessageDialog(
                        self, 
                        f"Are you sure you want to delete '{self.prompt['name']}'?",
                        "Confirm Delete",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                    )
                    result = dlg.ShowModal()
                    dlg.Destroy()
                    
                    if result == wx.ID_YES:
                        # Ensure the callback exists before calling
                        if self.on_delete:
                            # Call the delete callback passed from MainFrame
                            # Wrap in try/except specifically for this call
                            try:
                                self.on_delete(self.prompt["id"])
                            except Exception as delete_error:
                                wx.MessageBox(f"Error deleting prompt in callback: {delete_error}", "Error", wx.OK | wx.ICON_ERROR)
                                print(f"Detailed delete error: {delete_error}") # Log for debugging
                        else:
                            wx.MessageBox("Delete callback not set", "Error", wx.OK | wx.ICON_WARNING)
                            
                except Exception as e:
                    # Catch any errors in the dialog or confirmation logic
                    wx.MessageBox(f"Error in delete confirmation: {e}", "Error", wx.OK | wx.ICON_ERROR)
                    print(f"Detailed confirmation error: {e}") # Log for debugging
                
            def on_copy_content(evt):
                try:
                    if self.on_click: # Check if callback exists
                        self.on_click(self.prompt)  # This copies to clipboard
                    else:
                        wx.MessageBox("Copy callback not set", "Error", wx.OK | wx.ICON_WARNING)
                except Exception as e:
                    wx.MessageBox(f"Error copying content: {e}", "Error", wx.OK | wx.ICON_ERROR)
                
            # Bind menu events
            self.Bind(wx.EVT_MENU, on_edit, edit_item)
            self.Bind(wx.EVT_MENU, on_delete, delete_item)
            self.Bind(wx.EVT_MENU, on_copy_content, copy_content_item)
            
            # Show the popup menu
            self.PopupMenu(menu)
            menu.Destroy()
            
        except Exception as e:
            # Catch any general errors in creating or showing the menu
            wx.MessageBox(f"Error showing context menu: {e}", "Error", wx.OK | wx.ICON_ERROR)
            print(f"Detailed menu error: {e}") # Log for debugging