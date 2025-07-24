import wx
import sys
from gui.main_frame import MainFrame
from storage import load_prompts, save_prompts
from utils import insert_prompt
from hotkeys import HotkeyManager

class ClimptApp(wx.App):
    def OnInit(self):
        self.hotkey_manager = HotkeyManager()
        self.frame = MainFrame(self)
        self.prompts = load_prompts()
        self.frame.load_prompts(self.prompts)
        
        # Register hotkeys
        self.hotkey_manager.register_hotkey('alt+p', self.toggle_overlay)
        self.hotkey_manager.register_hotkey('alt+t', self.toggle_tags)
        
        # Start hotkey listener
        self.hotkey_manager.start()
        
        self.frame.Show()
        return True
        
    def toggle_overlay(self):
        """Called from hotkey"""
        if hasattr(self, 'frame') and self.frame:
            wx.CallAfter(self._safe_toggle_overlay)
            
    def _safe_toggle_overlay(self):
        """Safe overlay toggle with state checking"""
        if hasattr(self, 'frame') and self.frame:
            try:
                self.frame.toggle_overlay()
            except Exception as e:
                print(f"Error toggling overlay: {e}")
            
    def toggle_tags(self):
        """Called from hotkey"""
        if hasattr(self, 'frame') and self.frame:
            wx.CallAfter(self._safe_toggle_tags)
            
    def _safe_toggle_tags(self):
        """Safe tags toggle"""
        if hasattr(self, 'frame') and self.frame:
            try:
                self.frame.toggle_tags_panel(None)
            except Exception as e:
                print(f"Error toggling tags: {e}")
        
    def insert_prompt(self, content):
        """Insert prompt content to clipboard - returns success status"""
        success = insert_prompt(content)
        if success:
            print("Prompt copied to clipboard!")
        return success
            
    def save_prompts(self, prompts):
        """Save prompts to file"""
        return save_prompts(prompts)
        
    def on_window_close(self):
        """Called when window is closing"""
        try:
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.stop()
        except:
            pass
            
    def OnExit(self):
        # Ensure cleanup
        try:
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.stop()
        except:
            pass
        return super().OnExit()