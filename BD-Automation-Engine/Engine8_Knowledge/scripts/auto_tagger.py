"""
BD Auto Tagger - LLM-powered document classification and tagging.
Automatically categorizes documents by program, contractor, data type, clearance, and priority.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from utils.llm_retry import anthropic_retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDAutoTagger')

# Check for optional dependencies
ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic not installed. Using rule-based tagging only.")

# =========================================
# TAXONOMY DEFINITIONS
# =========================================

# BD-specific taxonomy for classification
TAXONOMY = {
    'program': [
        'DCGS', 'DCGS-A', 'DCGS-N', 'DCGS-MC',
        'GBSD', 'Sentinel',
        'NGI', 'Next Generation Interceptor',
        'Defense Enclave Services', 'DES',
        'JADC2',
        'ABMS',
        'Space Force',
        'MDA', 'Missile Defense Agency',
        'DISA',
        'Navy', 'Air Force', 'Army', 'SOCOM',
        'DIA', 'NGA', 'NSA', 'CIA',
        'PAC-3', 'THAAD', 'Aegis',
    ],
    'contractor': [
        'Leidos', 'GDIT', 'General Dynamics',
        'CACI', 'Peraton', 'Northrop Grumman', 'Northrop',
        'Lockheed Martin', 'Lockheed',
        'Raytheon', 'RTX',
        'Boeing', 'BAE Systems', 'BAE',
        'SAIC', 'ManTech', 'Booz Allen', 'BAH',
        'L3Harris', 'L3',
        'Parsons', 'Jacobs', 'KBR',
        'Accenture Federal', 'Deloitte',
        'Microsoft', 'Amazon', 'AWS', 'Google', 'Oracle',
    ],
    'data_type': [
        'job_posting', 'contact', 'contract',
        'past_performance', 'briefing', 'playbook',
        'call_note', 'activity', 'proposal',
        'org_chart', 'intelligence_report',
    ],
    'clearance': [
        'TS/SCI', 'TS/SCI CI Poly', 'TS/SCI Full Scope',
        'Top Secret', 'TS',
        'Secret',
        'Public Trust',
        'None', 'Unclassified',
    ],
    'priority': [
        'hot', 'high',
        'warm', 'medium',
        'cold', 'low',
    ],
    'location': [
        'Washington DC', 'DC Metro', 'Northern Virginia', 'NoVA',
        'Arlington', 'McLean', 'Reston', 'Tysons',
        'Fort Belvoir', 'Fort Meade', 'Pentagon',
        'San Diego', 'Colorado Springs', 'Huntsville',
        'Remote', 'Hybrid',
    ],
    'skill': [
        'Cloud', 'AWS', 'Azure', 'DevOps', 'DevSecOps',
        'Cybersecurity', 'SIEM', 'SOC',
        'Data Analytics', 'Machine Learning', 'AI',
        'Software Development', 'Full Stack',
        'Systems Engineering', 'Integration',
        'Program Management', 'Capture Management',
        'Intelligence Analysis', 'SIGINT', 'GEOINT',
    ],
}

# Compile regex patterns for each taxonomy
TAXONOMY_PATTERNS = {}
for category, terms in TAXONOMY.items():
    patterns = []
    for term in terms:
        # Escape special characters and create word boundary pattern
        escaped = re.escape(term)
        patterns.append(rf'\b{escaped}\b')
    TAXONOMY_PATTERNS[category] = re.compile('|'.join(patterns), re.IGNORECASE)


@dataclass
class TagResult:
    """Result of auto-tagging operation."""
    tags: Dict[str, List[str]]
    confidence: float
    method: str  # 'llm' or 'rules'
    raw_text_sample: str = ""

    def to_dict(self) -> Dict:
        return {
            'tags': self.tags,
            'confidence': self.confidence,
            'method': self.method
        }

    def all_tags(self) -> List[str]:
        """Get flattened list of all tags."""
        all_tags = []
        for category_tags in self.tags.values():
            all_tags.extend(category_tags)
        return list(set(all_tags))


# =========================================
# RULE-BASED TAGGER
# =========================================

class RuleBasedTagger:
    """
    Rule-based document tagger using pattern matching.
    Fast and deterministic, good for structured data.
    """

    def __init__(self, taxonomy: Dict[str, List[str]] = None):
        self.taxonomy = taxonomy or TAXONOMY
        self.patterns = TAXONOMY_PATTERNS

    def classify(self, text: str, metadata: Optional[Dict] = None) -> TagResult:
        """
        Extract tags from text using pattern matching.

        Args:
            text: Document text to classify.
            metadata: Optional metadata dict with additional context.

        Returns:
            TagResult with extracted tags.
        """
        text = text or ""
        metadata = metadata or {}

        tags = {}
        match_counts = 0
        total_terms = 0

        for category, pattern in self.patterns.items():
            matches = set(m.group() for m in pattern.finditer(text))

            # Also check metadata
            for key, value in metadata.items():
                if isinstance(value, str):
                    meta_matches = set(m.group() for m in pattern.finditer(value))
                    matches.update(meta_matches)

            if matches:
                # Normalize matches to canonical form
                normalized = self._normalize_matches(category, matches)
                tags[category] = normalized
                match_counts += len(matches)

            total_terms += len(self.taxonomy[category])

        # Calculate confidence based on match density
        confidence = min(1.0, match_counts / max(1, len(text.split()) / 100))

        return TagResult(
            tags=tags,
            confidence=confidence,
            method='rules',
            raw_text_sample=text[:200]
        )

    def _normalize_matches(self, category: str, matches: Set[str]) -> List[str]:
        """Normalize matched terms to canonical form."""
        normalized = set()

        for match in matches:
            match_lower = match.lower()

            # Check against canonical terms
            for canonical in self.taxonomy[category]:
                if canonical.lower() == match_lower:
                    normalized.add(canonical)
                    break
            else:
                # Keep original if no canonical found
                normalized.add(match)

        return sorted(normalized)

    def suggest_tags(self, text: str) -> List[str]:
        """Get simple list of suggested tags."""
        result = self.classify(text)
        return result.all_tags()


# =========================================
# LLM-BASED TAGGER
# =========================================

class LLMTagger:
    """
    LLM-powered document tagger using Claude.
    Better at understanding context and nuance.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"LLM Tagger initialized with Claude: {model}")
        else:
            self.client = None
            logger.warning("Claude client not available")

    @anthropic_retry
    def classify(self, text: str, metadata: Optional[Dict] = None) -> TagResult:
        """
        Extract tags using Claude LLM.

        Args:
            text: Document text to classify.
            metadata: Optional metadata dict.

        Returns:
            TagResult with extracted tags.
        """
        if not self.client:
            logger.warning("LLM client not available, falling back to rules")
            return RuleBasedTagger().classify(text, metadata)

        # Prepare context
        meta_text = json.dumps(metadata, indent=2) if metadata else "None"

        prompt = f"""Classify this document for a federal defense BD (Business Development) intelligence system.

TAXONOMY CATEGORIES:
- program: Federal programs (DCGS, GBSD, NGI, Defense Enclave Services, etc.)
- contractor: Prime contractors (Leidos, GDIT, Northrop Grumman, CACI, etc.)
- data_type: Document type (job_posting, contact, contract, past_performance, briefing, etc.)
- clearance: Security clearance (TS/SCI, Top Secret, Secret, Public Trust, None)
- priority: BD priority level (hot, warm, cold)
- location: Work location (DC Metro, Arlington, Remote, etc.)
- skill: Technical skills (Cloud, DevOps, Cybersecurity, etc.)

DOCUMENT TEXT:
{text[:2000]}

METADATA:
{meta_text}

Return a JSON object with tags for each relevant category. Only include categories where you find clear matches.
Example: {{"program": ["DCGS"], "contractor": ["Leidos", "GDIT"], "clearance": ["TS/SCI"], "priority": ["warm"]}}

JSON:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from response
            tags = self._parse_json_response(response_text)

            return TagResult(
                tags=tags,
                confidence=0.85,  # LLM generally higher confidence
                method='llm',
                raw_text_sample=text[:200]
            )

        except Exception as e:
            logger.error(f"LLM tagging error: {e}")
            # Fallback to rules
            return RuleBasedTagger().classify(text, metadata)

    def _parse_json_response(self, text: str) -> Dict[str, List[str]]:
        """Parse JSON from LLM response."""
        # Try to find JSON in response
        try:
            # Look for JSON object
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        logger.warning(f"Could not parse LLM response: {text[:100]}")
        return {}


# =========================================
# AUTO TAGGER (COMBINED)
# =========================================

class AutoTagger:
    """
    Combined auto-tagger using both rules and LLM.
    Uses rules for fast processing, LLM for complex cases.
    """

    def __init__(
        self,
        use_llm: bool = True,
        llm_threshold: float = 0.5,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize auto-tagger.

        Args:
            use_llm: Whether to use LLM for complex cases.
            llm_threshold: Rule confidence threshold below which to use LLM.
            model: Claude model for LLM tagging.
        """
        self.rule_tagger = RuleBasedTagger()
        self.llm_tagger = LLMTagger(model=model) if use_llm else None
        self.llm_threshold = llm_threshold

    def classify(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        force_llm: bool = False
    ) -> TagResult:
        """
        Classify document, using LLM if rules are uncertain.

        Args:
            text: Document text.
            metadata: Optional metadata.
            force_llm: Force LLM even if rules are confident.

        Returns:
            TagResult with tags.
        """
        # Start with rule-based
        rule_result = self.rule_tagger.classify(text, metadata)

        # Use LLM if rules uncertain or forced
        if force_llm or (self.llm_tagger and rule_result.confidence < self.llm_threshold):
            llm_result = self.llm_tagger.classify(text, metadata)

            # Merge results (LLM takes precedence for overlapping categories)
            merged_tags = {**rule_result.tags}
            for category, tags in llm_result.tags.items():
                if category in merged_tags:
                    # Combine unique tags
                    merged_tags[category] = list(set(merged_tags[category] + tags))
                else:
                    merged_tags[category] = tags

            return TagResult(
                tags=merged_tags,
                confidence=max(rule_result.confidence, llm_result.confidence),
                method='hybrid',
                raw_text_sample=text[:200]
            )

        return rule_result

    def suggest_tags(self, text: str) -> List[str]:
        """Get simple list of suggested tags."""
        result = self.classify(text)
        return result.all_tags()

    def batch_classify(
        self,
        documents: List[Dict],
        text_field: str = 'content'
    ) -> List[Tuple[Dict, TagResult]]:
        """
        Classify multiple documents.

        Args:
            documents: List of document dicts.
            text_field: Field containing text to classify.

        Returns:
            List of (document, TagResult) tuples.
        """
        results = []

        for doc in documents:
            text = doc.get(text_field, '')

            # Use other fields as metadata
            metadata = {k: v for k, v in doc.items() if k != text_field}

            result = self.classify(text, metadata)
            results.append((doc, result))

        return results


# =========================================
# INTEGRATION WITH INDEXER
# =========================================

def enrich_with_tags(data: Dict, tagger: Optional[AutoTagger] = None) -> Dict:
    """
    Enrich a data record with auto-generated tags.

    Args:
        data: Data record to enrich.
        tagger: AutoTagger instance (creates one if None).

    Returns:
        Data record with 'auto_tags' field added.
    """
    tagger = tagger or AutoTagger(use_llm=False)  # Use rules for speed

    # Build text from common fields
    text_parts = []
    for field in ['title', 'name', 'content', 'summary', 'notes', 'description']:
        if field in data and data[field]:
            text_parts.append(str(data[field]))

    text = ' '.join(text_parts)

    # Classify
    result = tagger.classify(text, data)

    # Add tags to data
    enriched = {**data}
    enriched['auto_tags'] = result.all_tags()
    enriched['auto_tags_detail'] = result.tags

    return enriched


# =========================================
# CLI INTERFACE
# =========================================

def main():
    """CLI for the BD Auto Tagger."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Auto Tagger')
    parser.add_argument('text', nargs='?', help='Text to classify')
    parser.add_argument('--file', '-f', help='File to classify')
    parser.add_argument('--llm', action='store_true', help='Force LLM classification')
    parser.add_argument('--rules-only', action='store_true', help='Use only rule-based tagging')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Get text to classify
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Enter text to classify (Ctrl+D when done):")
        text = sys.stdin.read()

    # Create tagger
    tagger = AutoTagger(use_llm=not args.rules_only)

    # Classify
    result = tagger.classify(text, force_llm=args.llm)

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\nClassification Result (method: {result.method}, confidence: {result.confidence:.2f})")
        print("=" * 50)

        for category, tags in sorted(result.tags.items()):
            print(f"\n{category.upper()}:")
            for tag in tags:
                print(f"  - {tag}")

        print(f"\nAll tags: {', '.join(result.all_tags())}")


if __name__ == '__main__':
    main()
