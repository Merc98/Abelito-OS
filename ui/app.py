from __future__ import annotations
from fastapi import APIRouter
from suites.mobile.device_manager import list_devices

router = APIRouter()

@router.get('/ui/mobile/devices')
def mobile_devices() -> dict:
    return {"devices": list_devices()}


from pathlib import Path
@router.get("/ui/repos")
def list_repos() -> dict:
    root = Path("data/repos")
    repos = [d.name for d in root.iterdir() if d.is_dir()] if root.exists() else []
    return {"repositories": repos}
