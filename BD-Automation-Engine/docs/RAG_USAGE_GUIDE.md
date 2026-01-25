# RAG (Retrieval Augmented Generation) Usage Guide

## Overview

This guide explains how to use the BD Knowledge System's RAG capabilities to retrieve contextual information and generate AI-powered answers for any future work in this project.

---

## What is RAG?

RAG combines:
1. **Retrieval** - Finding relevant documents/data via semantic search
2. **Augmentation** - Adding retrieved context to AI prompts
3. **Generation** - Using Claude to synthesize answers with citations

```
Query → Semantic Search → Retrieve Top K → Augment Prompt → Claude → Answer + Sources
```

---

## Quick Reference

### For Claude Code Sessions

When working in Claude Code, you can reference the knowledge base:

```bash
# Search for relevant information
python Engine8_Knowledge/scripts/vector_store.py --search "your query" --collection all

# Ask a question with RAG
python Engine8_Knowledge/scripts/rag_engine.py "What contacts do we have at Leidos?"
```

### Common Query Patterns

| Use Case | Query Example | Collection |
|----------|---------------|------------|
| Find contacts at company | "contacts at Leidos" | contacts |
| Find program experts | "DCGS program manager" | contacts |
| Research a program | "DCGS contract details" | programs |
| Find job opportunities | "cybersecurity analyst TS/SCI" | jobs |
| Past performance | "Leidos past performance" | documents |
| Call notes history | "meeting notes with GDIT" | activities |

---

## RAG Engine Usage

### Python API

```python
from Engine8_Knowledge.scripts.rag_engine import BDRAGEngine
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

# Initialize
store = BDKnowledgeStore()
rag = BDRAGEngine(store)

# Simple question
answer = rag.ask("What contacts do we have at Leidos?")
print(answer)

# Question with sources
result = rag.ask_with_sources("What is the DCGS program?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")

# Program-specific question
intel = rag.ask_about_program("DCGS", "Who are the key contacts?")

# Company-specific question
info = rag.ask_about_company("Leidos", "What programs are they on?")
```

### CLI Usage

```bash
# Ask a question
python Engine8_Knowledge/scripts/rag_engine.py "What contacts do we have at Leidos?"

# Ask about a specific program
python Engine8_Knowledge/scripts/rag_engine.py --program DCGS "Who are the key decision makers?"

# Ask about a specific company
python Engine8_Knowledge/scripts/rag_engine.py --company Leidos "What contracts do they hold?"
```

### REST API

```bash
# Start the API server first
python Engine8_Knowledge/api.py

# Ask endpoint
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What contacts do we have at Leidos working on DCGS?",
    "limit": 5
  }'

# Program intelligence
curl http://localhost:8100/program/DCGS

# Company intelligence
curl http://localhost:8100/company/Leidos
```

---

## Best Practices for Queries

### 1. Be Specific
```
# Good
"TS/SCI cleared systems engineers at Northrop Grumman"

# Too vague
"engineers"
```

### 2. Include Context
```
# Good
"DCGS program contacts who work on ISR systems"

# Less effective
"DCGS contacts"
```

### 3. Use Domain Terms
```
# Good (uses BD terminology)
"Tier 1 contacts at prime contractors for JADC2"

# Generic
"important people at big companies"
```

### 4. Combine Filters
```python
# Search with filters
results = store.search(
    query="program manager",
    collection="contacts",
    filters={
        "company": "Leidos",
        "tier": [1, 2]  # Tier 1 or 2 only
    }
)
```

---

## Common Workflows

### 1. Research a New Program
```python
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

store = BDKnowledgeStore()

# Step 1: Find program info
programs = store.search("GBSD missile defense", "programs", limit=5)

# Step 2: Find related contacts
contacts = store.find_contacts_for_program("GBSD")

# Step 3: Find related jobs
jobs = store.find_jobs_for_program("GBSD")

# Step 4: Get full intelligence
intel = store.get_program_intelligence("GBSD")
```

### 2. Prepare for Company Meeting
```python
# Find all contacts at company
contacts = store.find_contacts_at_company("Leidos")

# Find programs they're involved in
programs = store.search("Leidos prime contractor", "programs")

# Find recent activities
activities = store.search("Leidos meeting call", "activities")
```

### 3. Find BD Opportunities
```python
# Find hot opportunities
jobs = store.search("hot priority", "jobs",
                    filters={"bd_priority": "hot"})

# Find programs needing coverage
programs = store.search("no contacts warm priority", "programs")
```

### 4. Cross-Reference Analysis
```python
# For a contact, find related items
contact_name = "John Smith"

# Find their activities
activities = store.search(contact_name, "activities")

# Find their company's programs
company_programs = store.search(contact_company, "programs")

# Find similar contacts
similar = store.find_similar(contact_id, "contacts")
```

---

## Integration with Claude Code

### MCP Server Tools

When the MCP server is running, Claude Code has these tools:

| Tool | Description |
|------|-------------|
| `search_knowledge` | Semantic search across collections |
| `ask_knowledge` | RAG-powered Q&A |
| `find_similar` | Find similar items |
| `get_program_intel` | Full program intelligence |
| `get_company_contacts` | Contacts at a company |
| `get_knowledge_stats` | Index statistics |
| `reindex_knowledge` | Trigger reindexing |

### Example Claude Code Prompts

```
"Search the knowledge base for contacts at Leidos who work on DCGS"
→ Uses search_knowledge tool

"What do we know about the GBSD program?"
→ Uses ask_knowledge tool

"Find contacts similar to this Tier 1 program manager"
→ Uses find_similar tool

"Give me a full intelligence report on the DCGS program"
→ Uses get_program_intel tool
```

---

## Sharing Context Across Projects

### For Cross-Project Learning

This knowledge system can be referenced by other Auto-Claude projects:

1. **Export Knowledge**
```bash
# Export search results to JSON
python -c "
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
import json

store = BDKnowledgeStore()
results = store.search_all('your query', limit_per_collection=10)

# Convert to shareable format
export = {coll: [r.to_dict() for r in items] for coll, items in results.items()}
print(json.dumps(export, indent=2))
"
```

2. **Reference Patterns**
Other projects can learn from:
- `Engine8_Knowledge/scripts/vector_store.py` - Qdrant integration patterns
- `Engine8_Knowledge/scripts/indexer.py` - Data pipeline patterns
- `Engine8_Knowledge/scripts/rag_engine.py` - RAG implementation

3. **Shared Taxonomy**
The auto-tagging taxonomy in `auto_tagger.py` can be reused:
- Program categories
- Contractor names
- Clearance levels
- Priority classifications

---

## Troubleshooting

### Empty Results
```bash
# Check if collection has data
python Engine8_Knowledge/scripts/vector_store.py --stats

# Reindex if needed
python Engine8_Knowledge/scripts/indexer.py --all
```

### Poor Relevance
- Try more specific queries
- Use domain terminology
- Add filters to narrow results

### API Not Responding
```bash
# Check if server is running
curl http://localhost:8100/stats

# Start server
python Engine8_Knowledge/api.py
```

---

## Performance Tips

1. **Limit Results**: Use `limit` parameter to reduce processing
2. **Score Threshold**: Set `score_threshold=0.3` to filter low-relevance
3. **Specific Collections**: Search specific collections vs. `all`
4. **Batch Queries**: Use `search_all()` for multi-collection searches

---

## Future Enhancements

See `docs/KNOWLEDGE_SYSTEM_ROADMAP.md` for planned features:
- Hybrid search (semantic + keyword)
- Query caching
- Incremental indexing
- Real-time sync with external systems
