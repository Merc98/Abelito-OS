from mobile.mobile_agent import MobileScreenAgentService


def run(config: dict | None = None) -> MobileScreenAgentService:
    return MobileScreenAgentService(rules=(config or {}))
