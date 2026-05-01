from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that imports like
# `from apps.ceo_api import main` and `import shared.nats_client` work
# when tests are run from any working directory.
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
