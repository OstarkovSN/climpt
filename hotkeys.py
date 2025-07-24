import keyboard
import threading
from typing import Callable
import time

class HotkeyManager:
    def __init__(self):
        self.callbacks = {}
        self.listener_thread = None
        self.running = False
        self.last_trigger_time = {}  # Track last trigger time for each hotkey
        
    def register_hotkey(self, hotkey: str, callback: Callable):
        """Register a hotkey with callback"""
        self.callbacks[hotkey] = callback
        
    def start(self):
        """Start hotkey listener in separate thread"""
        if self.running:
            return
            
        self.running = True
        
        def listen():
            try:
                # Register all hotkeys with suppress=False to avoid conflicts
                for hotkey, callback in self.callbacks.items():
                    # Use lambda to ensure proper closure
                    keyboard.add_hotkey(
                        hotkey, 
                        lambda cb=callback: self._safe_call(cb), 
                        suppress=False,
                        trigger_on_release=False  # Trigger on press, not release
                    )
                
                # Keep thread alive
                while self.running:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Hotkey listener error: {e}")
            finally:
                self.running = False
                
        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()
        
    def _safe_call(self, callback):
        """Safely call callback with debounce"""
        current_time = time.time()
        hotkey_key = str(callback)
        
        # Debounce: prevent multiple calls within 0.3 seconds
        if hotkey_key in self.last_trigger_time:
            if current_time - self.last_trigger_time[hotkey_key] < 0.3:
                return  # Too soon, ignore
                
        self.last_trigger_time[hotkey_key] = current_time
        callback()
        
    def stop(self):
        """Stop hotkey listener"""
        if self.running:
            self.running = False
            try:
                keyboard.unhook_all()
            except:
                pass
            
            # Wait a bit for thread to finish
            if self.listener_thread and self.listener_thread.is_alive():
                try:
                    self.listener_thread.join(timeout=1.0)
                except:
                    pass