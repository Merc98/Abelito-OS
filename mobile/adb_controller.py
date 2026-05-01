class ADBController:
    def discover_devices(self): return []
    def screenshot(self, device_id: str): return b""
    def input_tap(self, device_id: str, x: int, y: int): return {"ok": True}
