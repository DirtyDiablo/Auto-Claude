"""
BD RAG Engine - Retrieval Augmented Generation for natural language queries.
Uses LlamaIndex with Qdrant vector store and Claude for response generation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore, SearchResult
from utils.llm_retry import anthropic_retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDRAGEngine')

# Check for optional dependencies
LLAMAINDEX_AVAILABLE = False
try:
    from llama_index.core import VectorStoreIndex, Settings, ServiceContext
    from llama_index.core.response_synthesizers import get_response_synthesizer
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.schema import TextNode, NodeWithScore
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    logger.warning("llama-index not installed. Using simple RAG mode.")

ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic not installed. LLM features disabled.")

# =========================================
# CONFIGURATION
# =========================================

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_CONTEXT_TOKENS = 4000
MAX_RESPONSE_TOKENS = 1000


# =========================================
# RESPONSE TYPES
# =========================================

class RAGResponse:
    """Response from a RAG query with sources."""

    def __init__(
        self,
        answer: str,
        sources: List[SearchResult],
        query: str,
        confidence: float = 0.0,
        collection_searched: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.answer = answer
        self.sources = sources
        self.query = query
        self.confidence = confidence
        self.collection_searched = collection_searched
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'answer': self.answer,
            'sources': [s.to_dict() for s in self.sources],
            'query': self.query,
            'confidence': self.confidence,
            'collection_searched': self.collection_searched,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }

    def format_with_sources(self) -> str:
        """Format answer with source citations."""
        output = [self.answer, "", "---", "Sources:"]

        for i, source in enumerate(self.sources, 1):
            payload = source.payload
            title = payload.get('title', payload.get('name', f'Source {i}'))
            score = source.score
            output.append(f"  [{i}] {title} (relevance: {score:.2f})")

        return '\n'.join(output)


# =========================================
# RAG ENGINE CLASS
# =========================================

class BDRAGEngine:
    """
    RAG engine for natural language queries over BD knowledge base.

    Uses semantic search to find relevant context, then generates
    responses using Claude.
    """

    def __init__(
        self,
        vector_store: Optional[BDKnowledgeStore] = None,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None
    ):
        """
        Initialize the RAG engine.

        Args:
            vector_store: BDKnowledgeStore instance. Creates new if None.
            model: Claude model to use for generation.
            api_key: Anthropic API key. Uses env var if None.
        """
        self.store = vector_store or BDKnowledgeStore()
        self.model = model
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"RAG Engine initialized with Claude: {model}")
        else:
            self.client = None
            logger.warning("Claude client not available - using retrieval-only mode")

    def ask(
        self,
        question: str,
        collection: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> RAGResponse:
        """
        Answer a question using RAG.

        Args:
            question: Natural language question.
            collection: Specific collection to search (all if None).
            limit: Maximum sources to retrieve.
            score_threshold: Minimum relevance score.

        Returns:
            RAGResponse with answer and sources.
        """
        # Retrieve relevant context
        if collection:
            sources = self.store.search(
                query=question,
                collection=collection,
                limit=limit,
                score_threshold=score_threshold
            )
            collection_searched = collection
        else:
            # Search all collections
            all_results = self.store.search_all(
                query=question,
                limit_per_collection=limit,
                score_threshold=score_threshold
            )
            # Flatten and sort by score
            sources = []
            for coll, results in all_results.items():
                for r in results:
                    r.collection = coll  # Tag with collection
                    sources.append(r)
            sources.sort(key=lambda x: x.score, reverse=True)
            sources = sources[:limit]
            collection_searched = 'all'

        # If no client, return retrieval results only
        if not self.client:
            return self._retrieval_only_response(question, sources, collection_searched)

        # Generate response using Claude
        answer = self._generate_response(question, sources)

        # Calculate confidence based on source scores
        confidence = sum(s.score for s in sources) / len(sources) if sources else 0.0

        return RAGResponse(
            answer=answer,
            sources=sources,
            query=question,
            confidence=confidence,
            collection_searched=collection_searched
        )

    def ask_about_program(self, program_name: str) -> RAGResponse:
        """Get comprehensive intelligence about a program."""
        question = f"What do we know about the {program_name} program? Include jobs, contacts, and past performance."
        return self.ask(question, limit=10)

    def ask_about_company(self, company_name: str) -> RAGResponse:
        """Get intelligence about a company/contractor."""
        question = f"What contacts and relationships do we have with {company_name}? Include any past performance or jobs."
        return self.ask(question, limit=10)

    def find_experts(self, topic: str) -> RAGResponse:
        """Find contacts who are experts in a topic."""
        question = f"Find contacts who have experience or expertise in {topic}"
        return self.ask(question, collection='contacts', limit=10)

    def summarize_jobs(self, criteria: str) -> RAGResponse:
        """Summarize jobs matching criteria."""
        question = f"Summarize job opportunities that match: {criteria}"
        return self.ask(question, collection='jobs', limit=15)

    @anthropic_retry
    def _generate_response(
        self,
        question: str,
        sources: List[SearchResult]
    ) -> str:
        """Generate response using Claude with retrieved context."""
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            payload = source.payload
            collection = source.collection

            # Format based on collection type
            if collection == 'jobs':
                context_parts.append(self._format_job_context(i, payload))
            elif collection == 'contacts':
                context_parts.append(self._format_contact_context(i, payload))
            elif collection == 'programs':
                context_parts.append(self._format_program_context(i, payload))
            else:
                context_parts.append(self._format_generic_context(i, payload))

        context = '\n\n'.join(context_parts)

        # Build prompt
        system_prompt = """You are a BD (Business Development) intelligence assistant for federal defense contractors.
Your role is to answer questions about jobs, contacts, programs, and opportunities using the provided context.

Guidelines:
- Answer based ONLY on the provided context
- Be specific and cite source numbers [1], [2], etc.
- If the context doesn't contain enough information, say so
- Highlight actionable insights for BD activities
- Keep responses concise and professional"""

        user_prompt = f"""Context from knowledge base:
{context}

Question: {question}

Answer based on the context above. Cite sources using [1], [2], etc."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_RESPONSE_TOKENS,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Error generating response: {e}"

    def _retrieval_only_response(
        self,
        question: str,
        sources: List[SearchResult],
        collection: str
    ) -> RAGResponse:
        """Generate response without LLM (retrieval only)."""
        if not sources:
            answer = "No relevant information found in the knowledge base."
        else:
            answer_parts = [f"Found {len(sources)} relevant items:\n"]
            for i, source in enumerate(sources, 1):
                payload = source.payload
                name = payload.get('name', payload.get('title', 'Unknown'))
                answer_parts.append(f"[{i}] {name} (score: {source.score:.2f})")
            answer = '\n'.join(answer_parts)

        return RAGResponse(
            answer=answer,
            sources=sources,
            query=question,
            confidence=0.5 if sources else 0.0,
            collection_searched=collection,
            metadata={'mode': 'retrieval_only'}
        )

    def _format_job_context(self, num: int, payload: Dict) -> str:
        """Format job data as context."""
        return f"""[{num}] JOB: {payload.get('title', 'Unknown Position')}
Company: {payload.get('company', 'N/A')}
Location: {payload.get('location', 'N/A')}
Program: {payload.get('program_name', 'N/A')}
Clearance: {payload.get('clearance', 'N/A')}
BD Score: {payload.get('bd_score', 'N/A')}
Priority: {payload.get('bd_priority', 'N/A')}"""

    def _format_contact_context(self, num: int, payload: Dict) -> str:
        """Format contact data as context."""
        name = f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
        name = name or payload.get('name', 'Unknown')
        return f"""[{num}] CONTACT: {name}
Title: {payload.get('title', 'N/A')}
Company: {payload.get('company', 'N/A')}
Program: {payload.get('program', 'N/A')}
Tier: {payload.get('tier', 'N/A')}
Email: {payload.get('email', 'N/A')}"""

    def _format_program_context(self, num: int, payload: Dict) -> str:
        """Format program data as context."""
        return f"""[{num}] PROGRAM: {payload.get('name', 'Unknown Program')}
Prime Contractor: {payload.get('prime_contractor', 'N/A')}
Contract Value: {payload.get('contract_value', 'N/A')}
Status: {payload.get('status', 'N/A')}
Location: {payload.get('location', 'N/A')}"""

    def _format_generic_context(self, num: int, payload: Dict) -> str:
        """Format generic data as context."""
        title = payload.get('title', payload.get('name', 'Document'))
        content = payload.get('content', payload.get('summary', ''))[:500]
        return f"""[{num}] {title}
{content}..."""


# =========================================
# QUERY TEMPLATES
# =========================================

QUERY_TEMPLATES = {
    'program_intel': "What intelligence do we have about the {program} program?",
    'company_contacts': "Who are our contacts at {company}?",
    'clearance_jobs': "Find {clearance} cleared positions",
    'location_jobs': "What jobs are available in {location}?",
    'contractor_past_perf': "What past performance do we have with {contractor}?",
    'hot_leads': "What are the highest priority BD opportunities?",
    'dcgs_overview': "Provide an overview of DCGS-related opportunities and contacts",
}


# =========================================
# CLI INTERFACE
# =========================================

def main():
    """CLI for the BD RAG Engine."""
    import argparse

    parser = argparse.ArgumentParser(description='BD RAG Engine')
    parser.add_argument('query', nargs='?', help='Question to ask')
    parser.add_argument('--collection', '-c', help='Collection to search')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Max sources')
    parser.add_argument('--template', '-t', help='Use query template')
    parser.add_argument('--program', help='Program name (for template)')
    parser.add_argument('--company', help='Company name (for template)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    # Initialize engine
    engine = BDRAGEngine()

    # Use template if specified
    if args.template and args.template in QUERY_TEMPLATES:
        template = QUERY_TEMPLATES[args.template]
        query = template.format(
            program=args.program or 'DCGS',
            company=args.company or 'Leidos',
            clearance='TS/SCI',
            location='Arlington, VA',
            contractor=args.company or 'GDIT'
        )
    elif args.query:
        query = args.query
    elif args.interactive:
        query = None
    else:
        parser.print_help()
        return

    if args.interactive:
        print("\nBD RAG Engine - Interactive Mode")
        print("Type 'quit' to exit\n")

        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if not query:
                    continue

                response = engine.ask(query, collection=args.collection, limit=args.limit)
                print(f"\n{response.format_with_sources()}\n")

            except KeyboardInterrupt:
                break
    else:
        print(f"\nQuery: {query}")
        response = engine.ask(query, collection=args.collection, limit=args.limit)
        print(f"\n{response.format_with_sources()}")


if __name__ == '__main__':
    main()
