from __future__ import annotations
from fastapi import APIRouter
from suites.mobile.device_manager import list_devices

router = APIRouter()

@router.get('/ui/mobile/devices')
def mobile_devices() -> dict:
    return {"devices": list_devices()}
