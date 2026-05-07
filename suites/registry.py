from __future__ import annotations
from importlib import import_module
from pathlib import Path

def load_suite_registries() -> dict[str, object]:
    loaded = {}
    root = Path(__file__).parent
    for mod in root.rglob('*_registry.py'):
        rel = mod.with_suffix("").relative_to(root.parent)
        name = ".".join(rel.parts)
        loaded[name] = import_module(name)
    return loaded
