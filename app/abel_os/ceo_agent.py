from __future__ import annotations

from abel_os.lanes import DEFAULT_LANES
from abel_os.schemas import LatencyClass, WorkflowPlan


class CEOAgent:
    def build_plan(self, user_message: str) -> WorkflowPlan:
        message = user_message.lower()

        if any(keyword in message for keyword in ("appium", "ios", "android", "offer", "rideshare", "uber", "lyft")):
            return WorkflowPlan(
                workflow_name="mobile_offer_response",
                intent="mobile_automation",
                ministries=["Mobile Automation", "Observability"],
                lane_policy=DEFAULT_LANES[LatencyClass.REALTIME],
                autonomy_level="MEDIUM",
                notes=[
                    "Priorizar first-confident-winner.",
                    "No bloquear por OCR o visión si el árbol UI ya basta.",
                ],
            )

        if any(keyword in message for keyword in ("investiga", "research", "osint", "analiza", "consulta")):
            return WorkflowPlan(
                workflow_name="multi_ministry_research",
                intent="research",
                ministries=["Knowledge", "Research", "OSINT"],
                lane_policy=DEFAULT_LANES[LatencyClass.DURABLE],
                autonomy_level="LOW",
                notes=[
                    "Responder por quorum antes de esperar completitud total.",
                ],
            )

        if any(keyword in message for keyword in ("código", "repo", "programa", "implementa", "api")):
            return WorkflowPlan(
                workflow_name="development_bootstrap",
                intent="development",
                ministries=["Development", "Knowledge"],
                lane_policy=DEFAULT_LANES[LatencyClass.SHORT],
                autonomy_level="MEDIUM",
                notes=[
                    "Persistencia documental fuera del camino crítico.",
                ],
            )

        return WorkflowPlan(
            workflow_name="general_execution",
            intent="general",
            ministries=["CEO", "Knowledge"],
            lane_policy=DEFAULT_LANES[LatencyClass.SHORT],
            autonomy_level="LOW",
            notes=["Aplicar lane corto por defecto."],
        )
