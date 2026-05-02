from __future__ import annotations
from typing import Any
from .decision_engine import DecisionEngine
from .graph_manager import GraphService

class BrainOrchestrator:
    def __init__(self):
        self.decision = DecisionEngine()
        self.graph = GraphService()

    def process(self, message: str) -> dict[str, Any]:
        tasks = self.decision.decompose(message)
        node_id = f"evt-{abs(hash(message))%100000}"
        self.graph.add_node(node_id, message, kind="intent")
        return {"tasks": tasks, "graph_node": node_id}
