class MobileTelemetry:
    def __init__(self):
        self.metrics = []

    def record(self, data: dict):
        redacted = dict(data)
        redacted.pop("screenshot_raw", None)
        self.metrics.append(redacted)
