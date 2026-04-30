"""
Bootstrap module for Session 9 Autonomous Capabilities.
This script initializes all new components and hooks them together.
"""
import asyncio
import logging
from core.memory import MemoryCore
from core.decision_graph import DecisionGraph
from core.intent_logger import IntentLogger
from core.watchdog import GuardrailsWatchdog
from core.monitor import SystemMonitor
from core.scheduler import TaskScheduler
from core.multi_agent import MultiAgentOrchestrator
from shared.nats_client import connect_nats_from_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("abel.bootstrap")

async def bootstrap():
    # 1. Memory foundation
    memory = MemoryCore()
    decision_graph = DecisionGraph()
    intent_logger = IntentLogger(memory)
    
    # 2. NATS Connectivity
    try:
        nc = await connect_nats_from_env()
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {e}. Some features will be limited.")
        nc = None

    # 3. Guardrails & Safety
    watchdog = GuardrailsWatchdog(nc)
    if nc:
        await watchdog.start()

    # 4. Autonomous Loops
    monitor = SystemMonitor(nc)
    await monitor.start()
    
    scheduler = TaskScheduler(nc)
    await scheduler.start()

    # 5. Multi-Agent Orchestration
    orchestrator = MultiAgentOrchestrator(nc, intent_logger)
    
    # Register a sample agent
    async def sample_handler(payload):
        logger.info(f"Sample agent processing: {payload}")
        return {"status": "ok"}
    
    orchestrator.register_agent("Specialist", "abel.tasks.specialist.>", sample_handler)
    
    if nc:
        logger.info("ABEL OS+ Session 9 Autonomous Core is ONLINE.")
        # Keeping loops alive
        await orchestrator.start()
    else:
        logger.warning("No NATS connection. Multi-Agent Orchestrator is in manual mode.")

if __name__ == "__main__":
    asyncio.run(bootstrap())
