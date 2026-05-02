from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from .orchestrator import BrainOrchestrator

app = FastAPI(title="Abel Core", version="0.1.0")
orc = BrainOrchestrator()

class Req(BaseModel):
    message: str

@app.get('/health')
def health():
    return {'status':'ok'}

@app.post('/process')
def process(req: Req):
    return orc.process(req.message)
