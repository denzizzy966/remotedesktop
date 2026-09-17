import sys
import platform
import pyautogui

# Optimization: eliminate PyAutoGUI's default 0.1s pause between actions
pyautogui.PAUSE = 0.0
# Prevent fail-safe crash when mouse hits corner (0, 0)
pyautogui.FAILSAFE = False

# Mapping from web KeyboardEvent `key` / `code` to PyAutoGUI key names
KEY_MAP = {
    "Enter": "enter",
    "Backspace": "backspace",
    "Tab": "tab",
    "Escape": "esc",
    "Esc": "esc",
    "Space": "space",
    " ": "space",
    "ArrowUp": "up",
    "ArrowDown": "down",
    "ArrowLeft": "left",
    "ArrowRight": "right",
    "Delete": "delete",
    "Home": "home",
    "End": "end",
    "PageUp": "pageup",
    "PageDown": "pagedown",
    "Insert": "insert",
    "Shift": "shift",
    "ShiftLeft": "shiftleft",
    "ShiftRight": "shiftright",
    "Control": "ctrl",
    "ControlLeft": "ctrlleft",
    "ControlRight": "ctrlright",
    "Alt": "alt",
    "AltLeft": "altleft",
    "AltRight": "altright",
    "Meta": "win",
    "MetaLeft": "winleft",
    "MetaRight": "winright",
    "CapsLock": "capslock",
    "NumLock": "numlock",
    "ScrollLock": "scrolllock",
    "PrintScreen": "printscreen",
    "Pause": "pause",
    "ContextMenu": "apps",
    # Function keys
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4",
    "F5": "f5", "F6": "f6", "F7": "f7", "F8": "f8",
    "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
}

def switch_to_input_desktop():
    if platform.system() == "Windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hDesk:
                user32.SetThreadDesktop(hDesk)
                user32.CloseDesktop(hDesk)
                return True
        except Exception:
            pass
    return False

def wake_display():
    """Wakes the monitor display from sleep or screensaver."""
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
            user32 = ctypes.windll.user32
            user32.mouse_event(0x0001, 1, 0, 0, 0)
            user32.mouse_event(0x0001, -1, 0, 0, 0)
            return True
        except Exception:
            pass
    return False

def keep_screen_awake(enable=True):
    """Prevents OS display sleep while active streaming session is connected."""
    if platform.system() == "Windows":
        try:
            import ctypes
            flags = 0x80000000 | 0x00000001 | 0x00000002 if enable else 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(flags)
        except Exception:
            pass

def send_ctrl_alt_del():
    """Triggers SAS / Secure Attention Sequence on Windows to open lock screen credential prompt."""
    if platform.system() == "Windows":
        try:
            import ctypes
            sas = ctypes.windll.sas
            res = sas.SendSAS(False)
            if res == 1:
                return True
        except Exception:
            pass
        try:
            pyautogui.press('esc')
            pyautogui.press('space')
            return True
        except Exception:
            pass
    return False

class InputHandler:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"

    def keep_screen_awake(self, enable=True):
        keep_screen_awake(enable)

    def wake_display(self):
        return wake_display()

    def send_ctrl_alt_del(self):
        return send_ctrl_alt_del()

    def update_screen_size(self, width: int, height: int):
        if width > 0 and height > 0:
            self.screen_width = width
            self.screen_height = height

    def to_screen_coords(self, norm_x: float, norm_y: float):
        """Converts normalized (0.0 - 1.0) coordinates to actual pixel coordinates."""
        x = int(norm_x * self.screen_width)
        y = int(norm_y * self.screen_height)
        # Clamp within screen bounds
        x = max(0, min(self.screen_width - 1, x))
        y = max(0, min(self.screen_height - 1, y))
        return x, y

    def handle_mouse(self, event: dict):
        """
        Handles mouse events from the web client.
        event: {"action": "move|down|up|click|dblclick|wheel", "x": 0.5, "y": 0.5, "button": "left|right|middle", "deltaY": int}
        """
        try:
            if self.is_windows:
                switch_to_input_desktop()

            action = event.get("action")
            norm_x = event.get("x", 0)
            norm_y = event.get("y", 0)
            button = event.get("button", "left")
            if button not in ["left", "right", "middle"]:
                button = "left"

            real_x, real_y = self.to_screen_coords(norm_x, norm_y)

            if action == "move":
                pyautogui.moveTo(real_x, real_y)

            elif action == "down":
                pyautogui.moveTo(real_x, real_y)
                pyautogui.mouseDown(button=button)

            elif action == "up":
                pyautogui.moveTo(real_x, real_y)
                pyautogui.mouseUp(button=button)

            elif action == "click":
                pyautogui.moveTo(real_x, real_y)
                pyautogui.click(button=button)

            elif action == "dblclick":
                pyautogui.moveTo(real_x, real_y)
                pyautogui.doubleClick(button=button)

            elif action == "wheel":
                delta = event.get("deltaY", 0)
                # Invert web wheel delta to match OS scroll direction
                scroll_amount = -int(delta / 30) if delta != 0 else 0
                if scroll_amount != 0:
                    pyautogui.scroll(scroll_amount, x=real_x, y=real_y)

        except Exception as e:
            # Silently catch input simulation errors to prevent agent crash
            pass

    def handle_keyboard(self, event: dict):
        """
        Handles keyboard events from the web client.
        event: {"action": "down|up|type|shortcut", "key": "a", "code": "KeyA", "keys": [...]}
        """
        try:
            if self.is_windows:
                switch_to_input_desktop()

            action = event.get("action")
            key = event.get("key", "")
            code = event.get("code", "")

            # Shortcut action (e.g. ['ctrl', 'c'])
            if action == "shortcut":
                keys = event.get("keys", [])
                if keys:
                    mapped = [self._map_key(k) for k in keys]
                    pyautogui.hotkey(*mapped)
                return

            # Direct text typing (for paste or string injection)
            if action == "type":
                text = event.get("text", "")
                if text:
                    pyautogui.write(text)
                return

            mapped_key = self._map_key(key, code)
            if not mapped_key:
                return

            if action == "down":
                pyautogui.keyDown(mapped_key)
            elif action == "up":
                pyautogui.keyUp(mapped_key)

        except Exception as e:
            pass

    def _map_key(self, key: str, code: str = "") -> str:
        """Translates web key identifiers to PyAutoGUI compatible key names."""
        # Direct lookup
        if key in KEY_MAP:
            return KEY_MAP[key]
        if code in KEY_MAP:
            return KEY_MAP[code]

        # Single character (letters, numbers, basic symbols)
        if len(key) == 1:
            return key.lower()

        # Check lowercase match
        low = key.lower()
        if low in pyautogui.KEYBOARD_KEYS:
            return low

        return ""
