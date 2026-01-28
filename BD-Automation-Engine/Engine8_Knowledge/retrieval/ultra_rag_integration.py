"""
Integration layer connecting UltraRAG to existing retrieval infrastructure.
"""
from typing import List, Dict, Optional

try:
    from .ultra_rag import UltraRAG, PipelineConfig, RetrievalStrategy
    from .page_index import PageIndex
except ImportError:
    from ultra_rag import UltraRAG, PipelineConfig, RetrievalStrategy
    from page_index import PageIndex


class BDUltraRAG:
    """
    BD-specific UltraRAG integration with existing Hub infrastructure.
    """

    def __init__(self,
                 qdrant_client=None,
                 bm25_index=None,
                 page_index: PageIndex = None,
                 knowledge_graph=None,
                 llm_client=None):
        """
        Initialize with existing retrieval components.

        Args:
            qdrant_client: Qdrant client for vector search
            bm25_index: BM25 index for keyword search
            page_index: PageIndex for document-level retrieval
            knowledge_graph: Knowledge graph client
            llm_client: LLM client for reasoning (Anthropic, OpenAI, etc.)
        """
        self.qdrant = qdrant_client
        self.bm25 = bm25_index
        self.page_index = page_index
        self.kg = knowledge_graph
        self.llm = llm_client

        # Initialize UltraRAG with our retriever
        config = PipelineConfig(
            parallel_retrieval=True,
            self_reflection=llm_client is not None,
            citation_required=True
        )

        self.ultra = UltraRAG(
            retriever_func=self._unified_retrieve,
            llm_func=self._llm_generate if llm_client else None,
            config=config
        )

    def _unified_retrieve(self,
                          query: str,
                          strategy: str = "hybrid",
                          top_k: int = 5,
                          collection: str = None) -> List[Dict]:
        """
        Unified retrieval across all backends.
        """
        results = []

        if strategy in ["vector", "hybrid"]:
            # Vector search via Qdrant
            try:
                if self.qdrant:
                    collections = [collection] if collection else ["jobs", "contacts", "programs"]
                    for coll in collections:
                        try:
                            # Qdrant search implementation
                            # search_results = self.qdrant.search(
                            #     collection_name=coll,
                            #     query_vector=embed(query),
                            #     limit=top_k
                            # )
                            # for r in search_results:
                            #     results.append({
                            #         "content": r.payload.get("content", ""),
                            #         "source": r.payload.get("source", coll),
                            #         "score": r.score,
                            #         "collection": coll
                            #     })
                            pass
                        except Exception as e:
                            print(f"Qdrant search error for {coll}: {e}")
            except Exception as e:
                print(f"Vector search error: {e}")

        if strategy in ["bm25", "hybrid"]:
            # BM25 search
            try:
                if self.bm25:
                    # BM25 search implementation
                    # bm25_results = self.bm25.search(query, top_k=top_k)
                    # results.extend(bm25_results)
                    pass
            except Exception as e:
                print(f"BM25 search error: {e}")

        if strategy == "pageindex" and self.page_index:
            # PageIndex search
            try:
                page_results = self.page_index.search(query, top_k=top_k)
                for r in page_results:
                    results.append({
                        "content": r.content,
                        "source": r.document_name,
                        "page": r.page_number,
                        "score": r.score,
                        "citation": r.citation,
                        "matched_terms": r.matched_terms
                    })
            except Exception as e:
                print(f"PageIndex search error: {e}")

        if strategy == "knowledge_graph" and self.kg:
            # Knowledge graph search
            try:
                # KG search implementation
                # kg_results = self.kg.search(query, top_k=top_k)
                # results.extend(kg_results)
                pass
            except Exception as e:
                print(f"KG search error: {e}")

        return results

    def _llm_generate(self, prompt: str) -> str:
        """Generate text using configured LLM."""
        if not self.llm:
            return ""

        try:
            # Anthropic client
            if hasattr(self.llm, 'messages'):
                response = self.llm.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            # OpenAI client
            if hasattr(self.llm, 'chat'):
                response = self.llm.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            # Generic callable
            if callable(self.llm):
                return self.llm(prompt)

        except Exception as e:
            print(f"LLM generation error: {e}")

        return ""

    async def analyze_program(self, program_name: str) -> Dict:
        """
        Comprehensive program analysis using UltraRAG.
        """
        query = f"Analyze the {program_name} program: What is the contract value, who is the prime contractor, what are the key locations, and what staffing opportunities exist?"

        plan = await self.ultra.query(query, pipeline="bd_intelligence")

        return {
            "program": program_name,
            "analysis": plan.final_answer,
            "confidence": plan.confidence,
            "citations": plan.citations,
            "execution_time_ms": plan.execution_time_ms
        }

    async def research_contact(self, contact_name: str) -> Dict:
        """
        Deep research on a contact using UltraRAG.
        """
        query = f"What do we know about {contact_name}? Include their role, program involvement, company, and any past interactions."

        plan = await self.ultra.query(query, pipeline="multisource")

        return {
            "contact": contact_name,
            "research": plan.final_answer,
            "confidence": plan.confidence,
            "citations": plan.citations
        }

    async def compare_programs(self, program1: str, program2: str) -> Dict:
        """
        Compare two programs using complex query decomposition.
        """
        query = f"Compare {program1} and {program2}: What are the differences in contract value, prime contractors, and staffing requirements?"

        plan = await self.ultra.query(query, pipeline="complex")

        return {
            "programs": [program1, program2],
            "comparison": plan.final_answer,
            "sub_queries": plan.sub_queries,
            "confidence": plan.confidence,
            "citations": plan.citations
        }

    async def verify_fact(self, claim: str) -> Dict:
        """
        Verify a factual claim using the factcheck pipeline.
        """
        query = f"Verify: {claim}"

        plan = await self.ultra.query(query, pipeline="factcheck")

        return {
            "claim": claim,
            "verification": plan.final_answer,
            "confidence": plan.confidence,
            "citations": plan.citations,
            "verified": plan.confidence > 0.7
        }

    def query_sync(self, query: str, pipeline: str = "auto") -> Dict:
        """Synchronous query interface."""
        plan = self.ultra.query_sync(query, pipeline)

        return {
            "query": query,
            "pipeline_used": plan.pipeline_used,
            "answer": plan.final_answer,
            "confidence": plan.confidence,
            "citations": plan.citations,
            "sub_queries": plan.sub_queries,
            "execution_time_ms": plan.execution_time_ms
        }

    def list_pipelines(self) -> List[Dict]:
        """List all available pipelines."""
        return self.ultra.list_pipelines()
