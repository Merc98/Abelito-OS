from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from .backend import SandboxBackend

router = APIRouter(prefix='/sandbox')
svc = SandboxBackend()

class TestReq(BaseModel):
    repo_path: str

@router.post('/run-tests')
def run_tests(req: TestReq):
    return svc.run_tests_in_copy(req.repo_path)
