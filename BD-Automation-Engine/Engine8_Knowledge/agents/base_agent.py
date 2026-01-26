"""
Base Agent Class for BD Intelligence Hub
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.memory_layer import get_memory
from scripts.lightrag_engine import get_knowledge_graph
from scripts.hybrid_retriever import get_hybrid_retriever

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic not available")


@dataclass
class AgentResponse:
    success: bool
    content: str
    sources: List[Dict]
    confidence: float
    agent_name: str
    metadata: Dict[str, Any]


class BDAgent(ABC):
    """Base class for BD specialized agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

        self.memory = get_memory()
        self.graph = get_knowledge_graph()
        self.retriever = get_hybrid_retriever()

        if ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.client = None

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return f"""You are {self.name}, a specialized BD intelligence agent.

Role: {self.description}

You have access to:
- Federal program data (DCGS portfolio, DoD contracts)
- Company intelligence (prime contractors, teaming partners)
- Contact information (cleared personnel, decision makers)
- Historical BD interactions and insights

Guidelines:
1. Always cite sources
2. Provide actionable intelligence
3. Flag uncertainty
4. Consider clearance requirements
5. Focus on DCGS, IC, DoD opportunities"""

    @abstractmethod
    async def process(self, query: str, context: Optional[Dict] = None) -> AgentResponse:
        pass

    async def _call_claude(self, prompt: str, context: str = "", max_tokens: int = 2000) -> str:
        if not self.client:
            return "Claude API not available. Please set ANTHROPIC_API_KEY."

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": f"{context}\n\n{prompt}" if context else prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Error calling Claude API: {str(e)}"

    async def _get_context(self, query: str, collections: List[str] = None) -> str:
        collections = collections or ["programs", "contacts", "companies"]
        parts = []

        # Memory context
        memories = self.memory.get_context(query, limit=5)
        if memories:
            parts.append("## Past Context")
            for m in memories:
                parts.append(f"- {m.get('memory', '')[:200]}")

        # Retrieved docs
        for col in collections:
            try:
                results = self.retriever.search(query, col, limit=3)
                if results:
                    parts.append(f"\n## From {col.title()}")
                    for r in results:
                        parts.append(f"- {r.text[:200]}...")
            except Exception as e:
                logger.debug(f"Error searching {col}: {e}")

        return "\n".join(parts)

    def _store_interaction(self, query: str, response: AgentResponse):
        self.memory.add_interaction(
            f"[{self.name}] Q: {query[:100]}\nA: {response.content[:300]}",
            metadata={"agent": self.name, "success": response.success}
        )
