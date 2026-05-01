class AndroidUiAutomatorController:
    def connect(self): ...
    def disconnect(self): ...
    def get_ui_tree(self): return ""
    def get_screenshot(self): return b""
    def tap_selector(self, selector): return {"ok": True, "selector": selector}
    def tap_coordinates(self, x, y): return {"ok": True, "x": x, "y": y}
    def get_current_app(self): return ""
    def health_check(self): return True
