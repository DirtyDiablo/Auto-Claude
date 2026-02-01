"""
Dify Integration for BD-Automation-Engine

Bridges Dify's visual AI workflow builder to your existing:
- Qdrant vector store (8,447+ indexed records)
- CrewAI agents (bd_strategy, company_research, contact_finder, program_intel)
- n8n workflows (18 automation workflows)
- Knowledge API (FastAPI on :8100)

This integration adds:
- Visual AI workflow builder (drag-drop)
- Prompt IDE with A/B testing
- LLMOps monitoring (token usage, latency, quality)
- Non-technical team access to AI features
"""

from .dify_qdrant_bridge import DifyQdrantBridge
from .dify_crewai_bridge import DifyCrewAIBridge
from .dify_n8n_bridge import DifyN8NBridge
from .dify_apps import BDDifyApps
from .tools_config import DIFY_EXTERNAL_TOOLS

__all__ = [
    'DifyQdrantBridge',
    'DifyCrewAIBridge',
    'DifyN8NBridge',
    'BDDifyApps',
    'DIFY_EXTERNAL_TOOLS'
]

__version__ = '1.0.0'
