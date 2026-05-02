from __future__ import annotations

def propose_refactors(analysis: dict) -> list[dict]:
    actions=[]
    if analysis.get('complexity',0) > 30:
        actions.append({"type":"extract_function","reason":"high_complexity","hitl_required":True})
    if analysis.get('unused_imports',0) > 0:
        actions.append({"type":"remove_unused_imports","reason":"cleanup","hitl_required":True})
    if analysis.get('maintainability',100) < 70:
        actions.append({"type":"simplify_conditionals","reason":"low_maintainability","hitl_required":True})
    return actions
