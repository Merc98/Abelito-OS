class AppiumSession:
    def __init__(self, capabilities: dict):
        self.capabilities = capabilities
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False
