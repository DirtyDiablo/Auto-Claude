"""
BD Document Preprocessor - Prepare BD documents for optimal RAGflow ingestion.

Handles:
- Playbook extraction with section preservation
- Contact CSV to structured markdown
- RFP requirement extraction with metadata
- Call notes structuring
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional imports for document processing
try:
    from docx import Document as DocxDocument

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not installed - DOCX preprocessing disabled")

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not installed - CSV preprocessing disabled")

try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not installed - PDF preprocessing disabled")


@dataclass
class PreprocessedDocument:
    """Result of document preprocessing."""

    original_path: str
    processed_path: str
    document_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[str] = field(default_factory=list)
    processing_notes: str = ""


class BDDocumentPreprocessor:
    """
    Prepare BD documents for optimal RAGflow ingestion.

    Preprocessing improves chunking quality by:
    - Adding section markers for better splitting
    - Converting tables to structured markdown
    - Extracting and preserving metadata
    - Standardizing formats across document types
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize preprocessor.

        Args:
            output_dir: Directory for preprocessed files (default: temp)
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(os.getenv("TEMP", "/tmp")) / "bd_preprocessed"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Playbook Preprocessing
    # =========================================================================

    async def preprocess_playbook(self, docx_path: str) -> PreprocessedDocument:
        """
        Extract playbook sections, preserve formatting hints.

        Adds markers for:
        - Executive Summary
        - Target Programs
        - Key Contacts
        - Win Themes
        - Action Items
        - Competitive Analysis
        """
        if not DOCX_AVAILABLE:
            return self._fallback_preprocess(docx_path, "playbook")

        path = Path(docx_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {docx_path}")

        try:
            doc = DocxDocument(docx_path)
        except Exception as e:
            logger.error(f"Failed to read DOCX: {e}")
            return self._fallback_preprocess(docx_path, "playbook")

        # Extract content with section markers
        content_parts = []
        current_section = "INTRODUCTION"
        sections_found = []

        # Section patterns to detect
        section_patterns = {
            r"executive\s+summary": "EXECUTIVE_SUMMARY",
            r"target\s+program": "TARGET_PROGRAMS",
            r"key\s+contact": "KEY_CONTACTS",
            r"win\s+theme": "WIN_THEMES",
            r"action\s+item": "ACTION_ITEMS",
            r"competitive\s+analysis": "COMPETITIVE_ANALYSIS",
            r"value\s+proposition": "VALUE_PROPOSITION",
            r"pricing\s+strateg": "PRICING_STRATEGY",
            r"team": "TEAM_COMPOSITION",
            r"timeline": "TIMELINE",
        }

        content_parts.append(f"[SECTION: {current_section}]")

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check for section headers
            text_lower = text.lower()
            for pattern, section_name in section_patterns.items():
                if re.search(pattern, text_lower):
                    current_section = section_name
                    if section_name not in sections_found:
                        sections_found.append(section_name)
                    content_parts.append(f"\n[SECTION: {section_name}]")
                    break

            # Add paragraph with style hints
            style = para.style.name if para.style else ""
            if "Heading" in style:
                content_parts.append(f"\n## {text}\n")
            elif "List" in style or text.startswith(("-", "•", "*")):
                content_parts.append(f"- {text}")
            else:
                content_parts.append(text)

        # Extract tables
        for i, table in enumerate(doc.tables):
            content_parts.append(f"\n[TABLE {i + 1}]")
            table_md = self._table_to_markdown(table)
            content_parts.append(table_md)

        # Write preprocessed file
        output_path = self.output_dir / f"{path.stem}_preprocessed.md"
        content = "\n".join(content_parts)

        # Add metadata header
        header = f"""---
document_type: bd_playbook
original_file: {path.name}
preprocessed_at: {datetime.now().isoformat()}
sections: {sections_found}
---

"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + content)

        return PreprocessedDocument(
            original_path=docx_path,
            processed_path=str(output_path),
            document_type="playbook",
            metadata={
                "original_file": path.name,
                "preprocessed_at": datetime.now().isoformat(),
            },
            sections=sections_found,
            processing_notes="Extracted with section markers",
        )

    def _table_to_markdown(self, table) -> str:
        """Convert DOCX table to markdown format."""
        if not table.rows:
            return ""

        rows = []
        for row in table.rows:
            cells = [cell.text.strip().replace("|", "\\|") for cell in row.cells]
            rows.append("| " + " | ".join(cells) + " |")

        if len(rows) >= 2:
            # Add header separator
            header = rows[0]
            separator = (
                "| " + " | ".join(["---"] * len(rows[0].split("|")[1:-1])) + " |"
            )
            body = rows[1:]
            return "\n".join([header, separator] + body)

        return "\n".join(rows)

    # =========================================================================
    # Contact CSV Preprocessing
    # =========================================================================

    async def preprocess_contact_csv(self, csv_path: str) -> PreprocessedDocument:
        """
        Convert contact CSV to structured markdown for better chunking.

        Creates one markdown section per contact with:
        - Name and title
        - Organization and tier
        - Contact information
        - Associated programs
        - Notes and history
        """
        if not PANDAS_AVAILABLE:
            return self._fallback_preprocess(csv_path, "contacts")

        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return self._fallback_preprocess(csv_path, "contacts")

        content_parts = [
            f"# Contact Directory",
            f"Source: {path.name}",
            f"Total Contacts: {len(df)}",
            f"Extracted: {datetime.now().isoformat()}",
            "",
            "---",
            "",
        ]

        # Common column name mappings
        name_cols = ["name", "full_name", "contact_name", "Name", "FullName"]
        title_cols = ["title", "job_title", "position", "Title", "JobTitle"]
        org_cols = ["organization", "company", "org", "Organization", "Company"]
        email_cols = ["email", "email_address", "Email"]
        phone_cols = ["phone", "phone_number", "Phone"]
        tier_cols = ["tier", "classification", "level", "Tier"]
        program_cols = ["program", "programs", "associated_programs", "Program"]
        notes_cols = ["notes", "comments", "Notes", "Comments"]

        def find_col(df, candidates):
            for col in candidates:
                if col in df.columns:
                    return col
            return None

        name_col = find_col(df, name_cols)
        title_col = find_col(df, title_cols)
        org_col = find_col(df, org_cols)
        email_col = find_col(df, email_cols)
        phone_col = find_col(df, phone_cols)
        tier_col = find_col(df, tier_cols)
        program_col = find_col(df, program_cols)
        notes_col = find_col(df, notes_cols)

        contacts_processed = 0

        for idx, row in df.iterrows():
            name = row.get(name_col, f"Contact {idx}") if name_col else f"Contact {idx}"

            if pd.isna(name) or not str(name).strip():
                continue

            parts = [f"\n## {name}"]

            if title_col and pd.notna(row.get(title_col)):
                parts.append(f"**Title:** {row[title_col]}")

            if org_col and pd.notna(row.get(org_col)):
                parts.append(f"**Organization:** {row[org_col]}")

            if tier_col and pd.notna(row.get(tier_col)):
                parts.append(f"**Tier/Classification:** {row[tier_col]}")

            if email_col and pd.notna(row.get(email_col)):
                parts.append(f"**Email:** {row[email_col]}")

            if phone_col and pd.notna(row.get(phone_col)):
                parts.append(f"**Phone:** {row[phone_col]}")

            if program_col and pd.notna(row.get(program_col)):
                parts.append(f"**Programs:** {row[program_col]}")

            if notes_col and pd.notna(row.get(notes_col)):
                parts.append(f"**Notes:** {row[notes_col]}")

            # Add any other columns as metadata
            other_cols = [
                c
                for c in df.columns
                if c
                not in [
                    name_col,
                    title_col,
                    org_col,
                    email_col,
                    phone_col,
                    tier_col,
                    program_col,
                    notes_col,
                ]
                and pd.notna(row.get(c))
            ]
            if other_cols:
                parts.append("\n**Additional Info:**")
                for col in other_cols[:5]:  # Limit extra columns
                    parts.append(f"- {col}: {row[col]}")

            content_parts.extend(parts)
            content_parts.append("\n---\n")
            contacts_processed += 1

        # Write preprocessed file
        output_path = self.output_dir / f"{path.stem}_preprocessed.md"
        content = "\n".join(content_parts)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return PreprocessedDocument(
            original_path=csv_path,
            processed_path=str(output_path),
            document_type="contacts",
            metadata={
                "original_file": path.name,
                "total_contacts": contacts_processed,
                "preprocessed_at": datetime.now().isoformat(),
            },
            sections=[f"contact_{i}" for i in range(contacts_processed)],
            processing_notes=f"Converted {contacts_processed} contacts to markdown",
        )

    # =========================================================================
    # RFP Preprocessing
    # =========================================================================

    async def preprocess_rfp(self, pdf_path: str) -> PreprocessedDocument:
        """
        Extract RFP requirements with section markers.

        Extracts:
        - Solicitation metadata (due date, agency, NAICS)
        - Requirements sections
        - Evaluation criteria
        - Deliverables
        """
        if not PDF_AVAILABLE:
            return self._fallback_preprocess(pdf_path, "rfp")

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")

        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []

                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_parts.append(f"[PAGE {i + 1}]\n{page_text}")

                raw_text = "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to read PDF: {e}")
            return self._fallback_preprocess(pdf_path, "rfp")

        # Extract metadata
        metadata = self._extract_rfp_metadata(raw_text)

        # Add section markers
        section_patterns = {
            r"(section\s+[a-z0-9]\s*[-:])": "[SECTION_MARKER]",
            r"(part\s+[ivx0-9]+\s*[-:])": "[PART_MARKER]",
            r"(\d+\.\d+[\.\d]*\s+)": "[REQUIREMENT]",
            r"(evaluation\s+criteria)": "[SECTION: EVALUATION_CRITERIA]",
            r"(statement\s+of\s+work)": "[SECTION: SOW]",
            r"(technical\s+requirements?)": "[SECTION: TECHNICAL_REQUIREMENTS]",
            r"(deliverables?)": "[SECTION: DELIVERABLES]",
            r"(period\s+of\s+performance)": "[SECTION: PERIOD_OF_PERFORMANCE]",
        }

        processed_text = raw_text
        for pattern, marker in section_patterns.items():
            processed_text = re.sub(
                pattern, f"\n{marker} \\1", processed_text, flags=re.IGNORECASE
            )

        # Build output
        header = f"""---
document_type: rfp
original_file: {path.name}
solicitation_number: {metadata.get("solicitation_number", "Unknown")}
agency: {metadata.get("agency", "Unknown")}
naics: {metadata.get("naics", "Unknown")}
due_date: {metadata.get("due_date", "Unknown")}
set_aside: {metadata.get("set_aside", "None")}
preprocessed_at: {datetime.now().isoformat()}
---

# RFP: {metadata.get("solicitation_number", path.stem)}

"""
        output_path = self.output_dir / f"{path.stem}_preprocessed.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + processed_text)

        return PreprocessedDocument(
            original_path=pdf_path,
            processed_path=str(output_path),
            document_type="rfp",
            metadata=metadata,
            sections=list(set(re.findall(r"\[SECTION:\s*(\w+)\]", processed_text))),
            processing_notes="Extracted with section markers and metadata",
        )

    def _extract_rfp_metadata(self, text: str) -> Dict[str, str]:
        """Extract RFP metadata using patterns."""
        metadata = {}

        # Solicitation number patterns
        sol_patterns = [
            r"solicitation\s*(?:no\.?|number|#)?\s*[:=]?\s*([A-Z0-9-]+)",
            r"rfp\s*(?:no\.?|number|#)?\s*[:=]?\s*([A-Z0-9-]+)",
            r"contract\s*(?:no\.?|number|#)?\s*[:=]?\s*([A-Z0-9-]+)",
        ]
        for pattern in sol_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata["solicitation_number"] = match.group(1)
                break

        # NAICS code
        naics_match = re.search(
            r"naics\s*(?:code)?\s*[:=]?\s*(\d{6})", text, re.IGNORECASE
        )
        if naics_match:
            metadata["naics"] = naics_match.group(1)

        # Due date patterns
        date_patterns = [
            r"(?:due|closing|submission)\s*date\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"responses?\s*due\s*(?:by)?\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata["due_date"] = match.group(1)
                break

        # Agency
        agency_patterns = [
            r"(department\s+of\s+\w+)",
            r"(agency\s*[:=]?\s*[\w\s]+)",
        ]
        for pattern in agency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata["agency"] = match.group(1).strip()
                break

        # Set-aside
        setaside_patterns = [
            r"(small\s+business\s+set[- ]?aside)",
            r"(8\(?a\)?\s+set[- ]?aside)",
            r"(hubzone)",
            r"(sdvosb)",
            r"(wosb)",
        ]
        for pattern in setaside_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata["set_aside"] = match.group(1).strip()
                break

        return metadata

    # =========================================================================
    # Call Notes Preprocessing
    # =========================================================================

    async def preprocess_call_notes(
        self,
        notes: str,
        contact: str,
        date: str,
        program: Optional[str] = None,
        output_name: Optional[str] = None,
    ) -> PreprocessedDocument:
        """
        Structure call notes with metadata for searchability.

        Args:
            notes: Raw call notes text
            contact: Contact name
            date: Date of call (any format)
            program: Associated program (optional)
            output_name: Custom output filename
        """
        # Structure the notes
        sections = {
            "key_points": [],
            "action_items": [],
            "follow_ups": [],
            "quotes": [],
            "general": [],
        }

        lines = notes.split("\n")
        current_section = "general"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Detect section changes
            if any(kw in line_lower for kw in ["key point", "takeaway", "insight"]):
                current_section = "key_points"
            elif any(kw in line_lower for kw in ["action", "todo", "next step"]):
                current_section = "action_items"
            elif any(kw in line_lower for kw in ["follow up", "follow-up"]):
                current_section = "follow_ups"
            elif line.startswith('"') or line.startswith("'") or "said" in line_lower:
                sections["quotes"].append(line)
                continue

            # Add to current section
            if line.startswith(("-", "•", "*", "1", "2", "3")):
                sections[current_section].append(line.lstrip("-•*0123456789.) "))
            else:
                sections[current_section].append(line)

        # Build structured output
        output = f"""---
document_type: call_notes
contact: {contact}
date: {date}
program: {program or "General"}
preprocessed_at: {datetime.now().isoformat()}
---

# Call Notes: {contact}
**Date:** {date}
"""
        if program:
            output += f"**Program:** {program}\n"

        if sections["key_points"]:
            output += "\n## Key Points\n"
            for point in sections["key_points"]:
                output += f"- {point}\n"

        if sections["action_items"]:
            output += "\n## Action Items\n"
            for item in sections["action_items"]:
                output += f"- [ ] {item}\n"

        if sections["follow_ups"]:
            output += "\n## Follow-Ups Required\n"
            for item in sections["follow_ups"]:
                output += f"- {item}\n"

        if sections["quotes"]:
            output += "\n## Direct Quotes\n"
            for quote in sections["quotes"]:
                output += f"> {quote}\n"

        if sections["general"]:
            output += "\n## Notes\n"
            output += "\n".join(sections["general"])

        # Write output
        if output_name:
            filename = f"{output_name}.md"
        else:
            safe_contact = re.sub(r"[^\w\s-]", "", contact).replace(" ", "_")
            safe_date = re.sub(r"[^\w-]", "", date)
            filename = f"call_notes_{safe_contact}_{safe_date}.md"

        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)

        return PreprocessedDocument(
            original_path="inline",
            processed_path=str(output_path),
            document_type="call_notes",
            metadata={"contact": contact, "date": date, "program": program},
            sections=list(sections.keys()),
            processing_notes="Structured call notes with sections",
        )

    # =========================================================================
    # Batch Processing
    # =========================================================================

    async def batch_preprocess(
        self, folder: str, recursive: bool = True
    ) -> List[PreprocessedDocument]:
        """
        Preprocess all supported files in folder.

        Supports: .docx, .pdf, .csv, .md, .txt

        Args:
            folder: Directory to scan
            recursive: Include subdirectories

        Returns:
            List of PreprocessedDocument results
        """
        folder_path = Path(folder)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        results = []

        # File type handlers
        handlers = {
            ".docx": self.preprocess_playbook,
            ".csv": self.preprocess_contact_csv,
            ".pdf": self.preprocess_rfp,
        }

        # Find files
        if recursive:
            files = list(folder_path.rglob("*"))
        else:
            files = list(folder_path.glob("*"))

        files = [f for f in files if f.is_file() and f.suffix.lower() in handlers]

        logger.info(f"Found {len(files)} files to preprocess")

        for file_path in files:
            handler = handlers.get(file_path.suffix.lower())
            if not handler:
                continue

            try:
                result = await handler(str(file_path))
                results.append(result)
                logger.info(f"Preprocessed: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to preprocess {file_path}: {e}")
                results.append(
                    PreprocessedDocument(
                        original_path=str(file_path),
                        processed_path="",
                        document_type="error",
                        metadata={"error": str(e)},
                        processing_notes=f"Failed: {e}",
                    )
                )

        return results

    # =========================================================================
    # Fallback Processing
    # =========================================================================

    def _fallback_preprocess(
        self, file_path: str, doc_type: str
    ) -> PreprocessedDocument:
        """
        Fallback when specialized libraries aren't available.

        Simply copies the file with metadata header if possible.
        """
        path = Path(file_path)

        # For text-based files, we can add metadata
        text_extensions = {".txt", ".md", ".csv"}

        if path.suffix.lower() in text_extensions:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                output_path = self.output_dir / f"{path.stem}_preprocessed.md"
                header = f"""---
document_type: {doc_type}
original_file: {path.name}
preprocessed_at: {datetime.now().isoformat()}
note: Basic preprocessing (install python-docx/PyPDF2/pandas for full features)
---

"""
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(header + content)

                return PreprocessedDocument(
                    original_path=file_path,
                    processed_path=str(output_path),
                    document_type=doc_type,
                    metadata={"fallback": True},
                    processing_notes="Basic preprocessing - libraries not available",
                )
            except Exception:
                pass

        # Can't preprocess, return original
        return PreprocessedDocument(
            original_path=file_path,
            processed_path=file_path,
            document_type=doc_type,
            metadata={"preprocessed": False},
            processing_notes="No preprocessing available for this file type",
        )
