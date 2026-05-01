from __future__ import annotations
from typing import Any

class AppiumClient:
    def __init__(self, driver: Any):
        self.driver = driver

    def get_page_source(self) -> str:
        return self.driver.page_source

    def find_and_click(self, selector: dict[str, str]) -> bool:
        by = selector.get("by", "xpath")
        value = selector.get("value", "")
        el = self.driver.find_element(by, value)
        el.click()
        return True

    def take_screenshot(self) -> bytes:
        return self.driver.get_screenshot_as_png()

    def execute_script(self, script: str) -> Any:
        return self.driver.execute_script(script)
