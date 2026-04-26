"""Computer Use Skill — OS-level interaction (Windows)."""
from __future__ import annotations

import logging
import base64
from io import BytesIO
from typing import Any, Dict, Optional

logger = logging.getLogger("abel.skills.computer_use")

class ComputerUseSkill:
    """Skill for controlling the host computer GUI."""

    def __init__(self):
        try:
            import pyautogui
            self.pyautogui = pyautogui
            # Disable failsafe for specific automated tasks, but usually keep it on
            self.pyautogui.FAILSAFE = True
        except ImportError:
            self.pyautogui = None
            logger.warning("pyautogui not installed. computer_use skill will be limited.")

    def get_screen_info(self) -> Dict[str, Any]:
        """Return screen resolution and mouse position."""
        if not self.pyautogui:
            return {"error": "pyautogui not available"}
        
        try:
            w, h = self.pyautogui.size()
            x, y = self.pyautogui.position()
            return {
                "screen_width": w,
                "screen_height": h,
                "mouse_x": x,
                "mouse_y": y
            }
        except Exception as e:
            return {"error": str(e)}

    def screenshot(self) -> Dict[str, Any]:
        """Take a screenshot of the primary monitor."""
        if not self.pyautogui:
            return {"error": "pyautogui not available"}

        try:
            import PIL.ImageGrab as ImageGrab
            # PyAutoGUI screenshot can also work, but ImageGrab is often more robust on Windows
            img = ImageGrab.grab()
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
            return {
                "screenshot_base64": img_str,
                "format": "png",
                "size": img.size
            }
        except Exception as e:
            return {"error": str(e)}

    def mouse_click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Click at specific coordinates."""
        if not self.pyautogui:
            return {"error": "pyautogui not available"}
        
        try:
            self.pyautogui.click(x=x, y=y, button=button)
            return {"status": "success", "action": f"click_{button}", "x": x, "y": y}
        except Exception as e:
            return {"error": str(e)}

    def type_text(self, text: str, interval: float = 0.1) -> Dict[str, Any]:
        """Type text using the keyboard."""
        if not self.pyautogui:
            return {"error": "pyautogui not available"}

        try:
            self.pyautogui.write(text, interval=interval)
            return {"status": "success", "action": "type", "length": len(text)}
        except Exception as e:
            return {"error": str(e)}

def setup():
    return ComputerUseSkill()
