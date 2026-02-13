"""
BD Knowledge Manager - BD-specific knowledge base operations.

Manages BD-specific knowledge bases and retrieval, including:
- Playbooks and strategy documents
- Federal programs and contracts
- RFPs and solicitations
- Past performance narratives
- HUMINT call notes
- Contact profiles
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .ragflow_client import (
    RAGflowClient,
    ChunkMethod,
    QueryResult,
    get_ragflow_client
)

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeBaseConfig:
    """Configuration for a BD knowledge base."""
    name: str
    chunk_method: ChunkMethod
    description: str
    file_patterns: List[str] = field(default_factory=list)


# BD Knowledge Base definitions
BD_KNOWLEDGE_BASES: Dict[str, KnowledgeBaseConfig] = {
    "bd_playbooks": KnowledgeBaseConfig(
        name="bd_playbooks",
        chunk_method=ChunkMethod.BOOK,
        description="BD strategy documents and playbooks",
        file_patterns=["*playbook*", "*strategy*", "*bd_plan*"]
    ),
    "federal_programs": KnowledgeBaseConfig(
        name="federal_programs",
        chunk_method=ChunkMethod.TABLE,
        description="Federal program contracts, FPDS data, SAM.gov",
        file_patterns=["*program*", "*contract*", "*fpds*", "*sam_*"]
    ),
    "rfp_library": KnowledgeBaseConfig(
        name="rfp_library",
        chunk_method=ChunkMethod.LAWS,
        description="RFPs, RFIs, and solicitations",
        file_patterns=["*rfp*", "*rfi*", "*solicitation*", "*proposal*"]
    ),
    "past_performance": KnowledgeBaseConfig(
        name="past_performance",
        chunk_method=ChunkMethod.QA,
        description="Past performance narratives, CPARs, references",
        file_patterns=["*past_perf*", "*cpar*", "*case_study*", "*reference*"]
    ),
    "humint_notes": KnowledgeBaseConfig(
        name="humint_notes",
        chunk_method=ChunkMethod.NAIVE,
        description="Call notes and human intelligence",
        file_patterns=["*call_note*", "*meeting_note*", "*intel*", "*humint*"]
    ),
    "contacts": KnowledgeBaseConfig(
        name="contacts",
        chunk_method=ChunkMethod.TABLE,
        description="Contact profiles and org structures",
        file_patterns=["*contact*", "*org_chart*", "*directory*"]
    ),
}


@dataclass
class ProgramIntelligence:
    """Aggregated intelligence about a federal program."""
    program_name: str
    contracts: List[Dict[str, Any]] = field(default_factory=list)
    rfps: List[Dict[str, Any]] = field(default_factory=list)
    past_performance: List[Dict[str, Any]] = field(default_factory=list)
    contacts: List[Dict[str, Any]] = field(default_factory=list)
    humint_notes: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    query_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_name": self.program_name,
            "contracts": self.contracts,
            "rfps": self.rfps,
            "past_performance": self.past_performance,
            "contacts": self.contacts,
            "humint_notes": self.humint_notes,
            "summary": self.summary,
            "query_time_ms": self.query_time_ms
        }


@dataclass
class ContactContext:
    """Everything we know about a contact."""
    contact_name: str
    profile: Optional[Dict[str, Any]] = None
    programs: List[Dict[str, Any]] = field(default_factory=list)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    related_contacts: List[Dict[str, Any]] = field(default_factory=list)
    query_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contact_name": self.contact_name,
            "profile": self.profile,
            "programs": self.programs,
            "interactions": self.interactions,
            "related_contacts": self.related_contacts,
            "query_time_ms": self.query_time_ms
        }


@dataclass
class CallPrepBrief:
    """Call preparation brief for a contact."""
    contact_name: str
    program_context: Optional[str]
    contact_background: str
    program_pain_points: List[str]
    pts_alignment: List[str]
    talking_points: List[str]
    questions_to_ask: List[str]
    sources: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    query_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contact_name": self.contact_name,
            "program_context": self.program_context,
            "contact_background": self.contact_background,
            "program_pain_points": self.program_pain_points,
            "pts_alignment": self.pts_alignment,
            "talking_points": self.talking_points,
            "questions_to_ask": self.questions_to_ask,
            "sources": self.sources,
            "generated_at": self.generated_at,
            "query_time_ms": self.query_time_ms
        }


class BDKnowledgeManager:
    """
    Manages BD-specific knowledge bases and retrieval.

    KB Structure:
    - bd_playbooks: BD playbooks, strategy docs
    - federal_programs: Contract info, FPDS data, SAM.gov
    - rfp_library: RFPs, RFIs, solicitations
    - past_performance: Case studies, CPARs, references
    - humint_notes: HUMINT call notes, intel
    - contacts: Contact profiles, org charts

    Example:
        manager = BDKnowledgeManager()
        await manager.initialize()

        # Get all intel about a program
        intel = await manager.get_program_intelligence("DCGS-A")

        # Generate call prep
        prep = await manager.generate_call_prep("John Smith", "DCGS")
    """

    def __init__(self, client: Optional[RAGflowClient] = None):
        self._client = client
        self.kb_ids: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize manager with RAGflow client."""
        if self._initialized:
            return

        if not self._client:
            self._client = await get_ragflow_client()

        self._initialized = True
        logger.info("BDKnowledgeManager initialized")

    async def close(self) -> None:
        """Close manager resources."""
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure manager is initialized."""
        if not self._initialized:
            raise RuntimeError("BDKnowledgeManager not initialized. Call initialize() first.")

    # =========================================================================
    # Knowledge Base Management
    # =========================================================================

    async def initialize_knowledge_bases(self) -> Dict[str, str]:
        """
        Create all BD knowledge bases if they don't exist.

        Returns:
            Dict mapping KB name to KB ID
        """
        self._ensure_initialized()

        for kb_name, config in BD_KNOWLEDGE_BASES.items():
            try:
                kb_id = await self._client.get_or_create_knowledge_base(
                    name=config.name,
                    description=config.description,
                    chunk_method=config.chunk_method
                )
                self.kb_ids[kb_name] = kb_id
                logger.info(f"KB ready: {kb_name} -> {kb_id}")
            except Exception as e:
                logger.error(f"Failed to create KB {kb_name}: {e}")

        return self.kb_ids

    async def get_kb_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all BD knowledge bases."""
        self._ensure_initialized()

        stats = {}
        for kb_name, kb_id in self.kb_ids.items():
            try:
                kb_info = await self._client.get_knowledge_base(kb_id)
                docs = await self._client.list_documents(kb_id)

                stats[kb_name] = {
                    "kb_id": kb_id,
                    "document_count": len(docs),
                    "chunk_count": kb_info.get("chunk_count", 0),
                    "status": "ready",
                    "description": BD_KNOWLEDGE_BASES[kb_name].description
                }
            except Exception as e:
                stats[kb_name] = {
                    "kb_id": kb_id,
                    "status": "error",
                    "error": str(e)
                }

        return stats

    # =========================================================================
    # Document Ingestion
    # =========================================================================

    async def ingest_project_files(
        self,
        project_path: str,
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """
        Scan project folder, categorize files, upload to appropriate KBs.

        Supports: .docx, .pdf, .xlsx, .md, .csv, .html, .txt

        Args:
            project_path: Root folder to scan
            auto_categorize: Auto-detect KB from filename patterns

        Returns:
            Summary of ingested files by KB
        """
        self._ensure_initialized()

        supported_extensions = {".docx", ".pdf", ".xlsx", ".md", ".csv", ".html", ".txt", ".json"}
        project_dir = Path(project_path)

        if not project_dir.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        results = {kb: [] for kb in BD_KNOWLEDGE_BASES.keys()}
        results["uncategorized"] = []

        # Scan for files
        all_files = []
        for ext in supported_extensions:
            all_files.extend(project_dir.rglob(f"*{ext}"))

        logger.info(f"Found {len(all_files)} files to process")

        for file_path in all_files:
            file_name = file_path.name.lower()

            # Categorize file
            target_kb = None

            if auto_categorize:
                for kb_name, config in BD_KNOWLEDGE_BASES.items():
                    for pattern in config.file_patterns:
                        if pattern.replace("*", "") in file_name:
                            target_kb = kb_name
                            break
                    if target_kb:
                        break

            if not target_kb:
                results["uncategorized"].append(str(file_path))
                continue

            # Upload to appropriate KB
            kb_id = self.kb_ids.get(target_kb)
            if not kb_id:
                logger.warning(f"KB not initialized: {target_kb}")
                results["uncategorized"].append(str(file_path))
                continue

            try:
                doc_id = await self._client.upload_document(
                    kb_id,
                    str(file_path),
                    BD_KNOWLEDGE_BASES[target_kb].chunk_method
                )
                results[target_kb].append({
                    "file": str(file_path),
                    "doc_id": doc_id,
                    "status": "uploaded"
                })
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                results[target_kb].append({
                    "file": str(file_path),
                    "status": "failed",
                    "error": str(e)
                })

        # Summary
        summary = {
            "total_files": len(all_files),
            "by_kb": {
                kb: len([r for r in files if isinstance(r, dict) and r.get("status") == "uploaded"])
                for kb, files in results.items()
            },
            "uncategorized": len(results["uncategorized"]),
            "details": results
        }

        logger.info(f"Ingestion complete: {summary['by_kb']}")
        return summary

    async def upload_to_kb(
        self,
        kb_name: str,
        file_path: str
    ) -> str:
        """Upload a single file to a specific KB."""
        self._ensure_initialized()

        if kb_name not in self.kb_ids:
            raise ValueError(f"Unknown KB: {kb_name}. Available: {list(self.kb_ids.keys())}")

        kb_id = self.kb_ids[kb_name]
        chunk_method = BD_KNOWLEDGE_BASES[kb_name].chunk_method

        return await self._client.upload_document(kb_id, file_path, chunk_method)

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def query_bd_intelligence(
        self,
        question: str,
        context: str = "general",
        top_k: int = 5
    ) -> QueryResult:
        """
        Smart query routing based on question context.

        Args:
            question: The query
            context: Query context hint
                - 'program': Federal programs KB
                - 'contact': Contacts KB
                - 'rfp': RFP library
                - 'past_performance': Past performance KB
                - 'humint': HUMINT notes
                - 'general': Search all KBs

        Returns:
            QueryResult with chunks and answer
        """
        self._ensure_initialized()

        # Route to appropriate KBs
        kb_mapping = {
            "program": ["federal_programs", "rfp_library"],
            "contact": ["contacts", "humint_notes"],
            "rfp": ["rfp_library"],
            "past_performance": ["past_performance"],
            "humint": ["humint_notes"],
            "playbook": ["bd_playbooks"],
            "general": list(BD_KNOWLEDGE_BASES.keys())
        }

        target_kbs = kb_mapping.get(context, kb_mapping["general"])
        kb_ids = [self.kb_ids[kb] for kb in target_kbs if kb in self.kb_ids]

        if not kb_ids:
            return QueryResult(chunks=[], answer="No knowledge bases available")

        return await self._client.query(
            kb_ids=kb_ids,
            question=question,
            top_k=top_k,
            with_answer=True
        )

    async def get_program_intelligence(
        self,
        program_name: str,
        include_related: bool = True
    ) -> ProgramIntelligence:
        """
        Gather all intel about a federal program.

        Searches:
        - Contract details from federal_programs
        - Related RFPs from rfp_library
        - Past performance on similar work
        - Known contacts
        - HUMINT notes

        Returns:
            ProgramIntelligence with all gathered data
        """
        self._ensure_initialized()
        import time
        start = time.time()

        intel = ProgramIntelligence(program_name=program_name)

        # Run parallel queries
        queries = [
            ("federal_programs", f"contract details for {program_name}"),
            ("rfp_library", f"RFPs and solicitations for {program_name}"),
            ("past_performance", f"past performance related to {program_name}"),
            ("contacts", f"key contacts for {program_name}"),
            ("humint_notes", f"intelligence notes about {program_name}"),
        ]

        async def query_kb(kb_name: str, query: str) -> tuple:
            kb_id = self.kb_ids.get(kb_name)
            if not kb_id:
                return (kb_name, [])

            try:
                result = await self._client.query([kb_id], query, top_k=5, with_answer=False)
                return (kb_name, result.chunks)
            except Exception as e:
                logger.error(f"Error querying {kb_name}: {e}")
                return (kb_name, [])

        results = await asyncio.gather(*[
            query_kb(kb, q) for kb, q in queries
        ])

        # Map results
        for kb_name, chunks in results:
            if kb_name == "federal_programs":
                intel.contracts = chunks
            elif kb_name == "rfp_library":
                intel.rfps = chunks
            elif kb_name == "past_performance":
                intel.past_performance = chunks
            elif kb_name == "contacts":
                intel.contacts = chunks
            elif kb_name == "humint_notes":
                intel.humint_notes = chunks

        # Generate summary if we have data
        total_chunks = (
            len(intel.contracts) + len(intel.rfps) +
            len(intel.past_performance) + len(intel.contacts) +
            len(intel.humint_notes)
        )

        if total_chunks > 0:
            # Use RAGflow to generate summary
            all_kb_ids = [self.kb_ids[kb] for kb in self.kb_ids.keys()]
            summary_result = await self._client.query(
                kb_ids=all_kb_ids,
                question=f"Provide a comprehensive summary of what we know about the {program_name} program, including contracts, key contacts, and opportunities.",
                top_k=10,
                with_answer=True
            )
            intel.summary = summary_result.answer

        intel.query_time_ms = (time.time() - start) * 1000
        return intel

    async def get_contact_context(
        self,
        contact_name: str
    ) -> ContactContext:
        """
        Get everything we know about a contact.

        Returns:
        - Profile info
        - Program associations
        - Past interactions (HUMINT)
        - Related decision makers
        """
        self._ensure_initialized()
        import time
        start = time.time()

        context = ContactContext(contact_name=contact_name)

        # Query contacts KB for profile
        if "contacts" in self.kb_ids:
            profile_result = await self._client.query(
                [self.kb_ids["contacts"]],
                f"full profile and background for {contact_name}",
                top_k=3,
                with_answer=False
            )
            if profile_result.chunks:
                context.profile = profile_result.chunks[0]

        # Query for program associations
        if "federal_programs" in self.kb_ids:
            program_result = await self._client.query(
                [self.kb_ids["federal_programs"]],
                f"programs and contracts associated with {contact_name}",
                top_k=5,
                with_answer=False
            )
            context.programs = program_result.chunks

        # Query HUMINT for interactions
        if "humint_notes" in self.kb_ids:
            humint_result = await self._client.query(
                [self.kb_ids["humint_notes"]],
                f"call notes and meetings with {contact_name}",
                top_k=10,
                with_answer=False
            )
            context.interactions = humint_result.chunks

        # Find related contacts using GraphRAG if available
        if "contacts" in self.kb_ids:
            try:
                related = await self._client.query_with_graph(
                    [self.kb_ids["contacts"]],
                    f"colleagues and related contacts to {contact_name}",
                    top_k=5
                )
                context.related_contacts = related.chunks
            except Exception:
                # GraphRAG may not be built
                pass

        context.query_time_ms = (time.time() - start) * 1000
        return context

    async def generate_call_prep(
        self,
        contact_name: str,
        program_context: Optional[str] = None
    ) -> CallPrepBrief:
        """
        Generate call preparation brief using RAG.

        Includes:
        - Contact background
        - Program pain points
        - PTS past performance alignment
        - Suggested talking points
        - Questions to ask

        Args:
            contact_name: Name of contact to call
            program_context: Optional program to focus on

        Returns:
            CallPrepBrief with actionable preparation
        """
        self._ensure_initialized()
        import time
        start = time.time()

        # Build comprehensive prompt
        if program_context:
            query = f"""Generate a call preparation brief for a BD call with {contact_name}
            regarding the {program_context} program. Include:
            1. Contact background and role
            2. Known pain points for this program
            3. How PTS capabilities align with their needs
            4. 3-5 key talking points
            5. 3-5 questions to ask during the call"""
        else:
            query = f"""Generate a call preparation brief for a BD call with {contact_name}. Include:
            1. Contact background and current role
            2. Programs they're associated with
            3. Previous interactions and outcomes
            4. 3-5 key talking points
            5. 3-5 discovery questions to ask"""

        # Query all relevant KBs
        all_kb_ids = [self.kb_ids[kb] for kb in self.kb_ids.keys()]

        result = await self._client.query(
            kb_ids=all_kb_ids,
            question=query,
            top_k=15,
            with_answer=True
        )

        # Parse the answer into structured brief
        # In a production system, you'd use structured output or more sophisticated parsing
        answer = result.answer or ""
        sections = answer.split("\n\n")

        brief = CallPrepBrief(
            contact_name=contact_name,
            program_context=program_context,
            contact_background=self._extract_section(answer, "background", "Contact background not found"),
            program_pain_points=self._extract_list(answer, "pain point"),
            pts_alignment=self._extract_list(answer, "alignment"),
            talking_points=self._extract_list(answer, "talking point"),
            questions_to_ask=self._extract_list(answer, "question"),
            sources=result.citations,
            generated_at=datetime.now().isoformat(),
            query_time_ms=(time.time() - start) * 1000
        )

        return brief

    def _extract_section(self, text: str, keyword: str, default: str) -> str:
        """Extract a section containing keyword from text."""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                # Return this line and next few lines
                section_lines = lines[i:i+3]
                return " ".join(section_lines).strip()
        return default

    def _extract_list(self, text: str, keyword: str) -> List[str]:
        """Extract bullet points containing keyword pattern."""
        items = []
        lines = text.split("\n")
        capture = False

        for line in lines:
            # Start capture when we hit a section with keyword
            if keyword.lower() in line.lower():
                capture = True
                continue

            # Capture bullet points
            if capture:
                line = line.strip()
                if line.startswith(("-", "•", "*", "1", "2", "3", "4", "5")):
                    # Clean the line
                    clean = line.lstrip("-•*0123456789.) ").strip()
                    if clean:
                        items.append(clean)
                elif line and not any(line.startswith(h) for h in ["#", "Background", "Pain", "Alignment", "Talking", "Question"]):
                    # Non-empty, non-header line might be continuation
                    pass
                elif any(header in line for header in ["Background", "Pain", "Alignment", "Talking", "Question"]):
                    # Hit another section, stop capturing
                    capture = False

            # Limit to reasonable number
            if len(items) >= 5:
                break

        return items if items else [f"No {keyword}s identified - review source documents"]

    # =========================================================================
    # GraphRAG Operations
    # =========================================================================

    async def build_program_knowledge_graph(self) -> Dict[str, str]:
        """
        Build GraphRAG across federal_programs KB.

        Enables queries like:
        - "Show programs related to GDIT with DCGS experience"
        - "What companies work with Leidos on ISR programs?"
        """
        self._ensure_initialized()

        results = {}

        # Build KG for relevant KBs
        kg_kbs = ["federal_programs", "contacts"]

        for kb_name in kg_kbs:
            kb_id = self.kb_ids.get(kb_name)
            if not kb_id:
                continue

            try:
                task_id = await self._client.build_knowledge_graph(kb_id)
                results[kb_name] = task_id
                logger.info(f"Started KG build for {kb_name}: {task_id}")
            except Exception as e:
                logger.error(f"Failed to start KG build for {kb_name}: {e}")
                results[kb_name] = f"error: {e}"

        return results

    async def get_graph_status(self) -> Dict[str, Any]:
        """Check knowledge graph build status for all BD KBs."""
        self._ensure_initialized()

        status = {}
        for kb_name in ["federal_programs", "contacts"]:
            kb_id = self.kb_ids.get(kb_name)
            if not kb_id:
                continue

            try:
                kb_status = await self._client.get_graph_status(kb_id)
                status[kb_name] = kb_status
            except Exception as e:
                status[kb_name] = {"error": str(e)}

        return status


# =============================================================================
# Singleton Factory
# =============================================================================

_manager: Optional[BDKnowledgeManager] = None


async def get_bd_knowledge_manager() -> BDKnowledgeManager:
    """
    Get or create the BD Knowledge Manager singleton.

    Uses lazy initialization pattern.
    """
    global _manager

    if _manager is None:
        _manager = BDKnowledgeManager()

    if not _manager._initialized:
        await _manager.initialize()

    return _manager


async def close_bd_knowledge_manager() -> None:
    """Close the BD Knowledge Manager singleton."""
    global _manager
    if _manager:
        await _manager.close()
        _manager = None
