from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from .screen_parser import ScreenParser
from .offer_scorer import OfferScorer
from .action_policy import evaluate_action_request
from .kill_switch import KillSwitch


@dataclass
class MobileSession:
    session_id: str
    device_id: str
    platform: str
    mode: str
    kill_switch: KillSwitch


@dataclass
class MobileScreenAgentService:
    rules: dict
    sessions: dict[str, MobileSession] = field(default_factory=dict)
    parser: ScreenParser = field(default_factory=ScreenParser)

    def start_mobile_session(self, device_id: str, platform: str, mode: str = "recommend_only") -> str:
        sid = str(uuid4())
        self.sessions[sid] = MobileSession(sid, device_id, platform, mode, KillSwitch(sid, active=(mode=="supervised_executor")))
        return sid

    def stop_mobile_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def parse_current_offer(self, session_id: str, ui_tree: str, ocr_text: str | None = None) -> dict:
        return self.parser.parse(ui_tree, ocr_text)

    def score_current_offer(self, session_id: str, fields: dict) -> dict:
        scorer = OfferScorer(self.rules)
        s = scorer.score(fields)
        return {"score": s.score, "recommendation": s.recommendation, "reasons": s.reasons, "confidence": s.confidence}

    def recommend_action(self, session_id: str, parsed: dict) -> dict:
        score = self.score_current_offer(session_id, parsed["fields"])
        action = f"RECOMMEND_{score['recommendation']}"
        return {"action": action, "confidence": score["confidence"], "reason": ",".join(score["reasons"]), "fields": parsed["fields"]}

    def request_supervised_action(self, session_id: str, action: str, confidence: float, screen_type: str, context: dict) -> dict:
        decision = evaluate_action_request({"action": action, "confidence": confidence, "screen_type": screen_type}, context)
        return decision.__dict__
