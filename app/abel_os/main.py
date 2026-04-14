from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from abel_os.ceo_agent import CEOAgent
from abel_os.config import settings
from abel_os.mobile.decision_engine import MobileDecisionEngine
from abel_os.schemas import MobileDecision, MobileOffer, MobileMode, WorkflowPlan

app = FastAPI(title=settings.app_name, version="0.1.0")
ceo = CEOAgent()
mobile_engine = MobileDecisionEngine(blocked_zones={"zona roja", "high risk"})


class PlanRequest(BaseModel):
    message: str


class MobileEvaluationRequest(BaseModel):
    offer: MobileOffer
    mode: MobileMode | None = None


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.post("/workflows/plan", response_model=WorkflowPlan)
def plan_workflow(request: PlanRequest) -> WorkflowPlan:
    return ceo.build_plan(request.message)


@app.post("/mobile/evaluate", response_model=MobileDecision)
def evaluate_mobile_offer(request: MobileEvaluationRequest) -> MobileDecision:
    mode = request.mode or settings.mobile_mode
    return mobile_engine.evaluate(request.offer, mode=mode)
