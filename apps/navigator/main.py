"""Entry point for the browser navigator service."""
from __future__ import annotations

import uvicorn

from apps.navigator import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="info")
