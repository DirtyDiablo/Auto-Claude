"""
Dify External Tools Configuration

Register your existing tools as Dify external tools.
These tools allow Dify apps to access your BD infrastructure.

Tools connect to:
- Knowledge API (http://127.0.0.1:8100) - Your existing FastAPI server
- n8n webhooks - Your automation workflows
- MCP servers - Notion, Apify, etc.
"""

import os

# Base URLs from environment or defaults
KNOWLEDGE_API_URL = os.getenv("KNOWLEDGE_API_URL", "http://127.0.0.1:8100")
N8N_API_URL = os.getenv("N8N_API_URL", "https://primetech.app.n8n.cloud")

# ============================================
# DIFY EXTERNAL TOOLS CONFIGURATION
# ============================================

DIFY_EXTERNAL_TOOLS = [
    # ----------------------------------------
    # SEARCH & RAG TOOLS (via Knowledge API)
    # ----------------------------------------
    {
        "name": "qdrant_search",
        "type": "api",
        "description": "Search your 8,447+ indexed BD documents across all collections (contacts, programs, jobs, documents, activities)",
        "endpoint": f"{KNOWLEDGE_API_URL}/search",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Search query in natural language",
            },
            "collection": {
                "type": "string",
                "required": False,
                "enum": ["contacts", "programs", "jobs", "documents", "activities"],
                "description": "Collection to search (default: all)",
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "description": "Maximum results to return",
            },
        },
    },
    {
        "name": "qdrant_smart_query",
        "type": "api",
        "description": "Intelligent query that routes to optimal retrieval systems (vector, graph, BM25)",
        "endpoint": f"{KNOWLEDGE_API_URL}/ask/smart",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Your BD question",
            },
            "use_cache": {
                "type": "boolean",
                "default": True,
                "description": "Use semantic cache for faster responses",
            },
        },
    },
    {
        "name": "qdrant_hybrid_search",
        "type": "api",
        "description": "Hybrid search combining semantic vectors and BM25 keyword matching with reranking",
        "endpoint": f"{KNOWLEDGE_API_URL}/search/hybrid",
        "method": "GET",
        "parameters": {
            "q": {"type": "string", "required": True, "description": "Search query"},
            "collection": {
                "type": "string",
                "default": "bd_knowledge",
                "description": "Collection to search",
            },
            "limit": {"type": "integer", "default": 10},
            "use_rerank": {
                "type": "boolean",
                "default": True,
                "description": "Apply cross-encoder reranking",
            },
        },
    },
    {
        "name": "qdrant_rag",
        "type": "api",
        "description": "RAG-powered question answering with source citations",
        "endpoint": f"{KNOWLEDGE_API_URL}/ask",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Question to answer",
            },
            "collection": {
                "type": "string",
                "required": False,
                "description": "Collection to search",
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "description": "Number of sources to retrieve",
            },
        },
    },
    # ----------------------------------------
    # SPECIALIZED SEARCH TOOLS
    # ----------------------------------------
    {
        "name": "qdrant_contacts",
        "type": "api",
        "description": "Search contacts by company, tier, program, or role",
        "endpoint": f"{KNOWLEDGE_API_URL}/contacts/at",
        "method": "GET",
        "parameters": {
            "company_name": {
                "type": "string",
                "required": True,
                "description": "Company to find contacts at",
            },
            "limit": {"type": "integer", "default": 20},
        },
    },
    {
        "name": "qdrant_programs",
        "type": "api",
        "description": "Get intelligence about a federal program",
        "endpoint": f"{KNOWLEDGE_API_URL}/program",
        "method": "GET",
        "parameters": {
            "program_name": {
                "type": "string",
                "required": True,
                "description": "Program name (e.g., AF DCGS, DCGS-A, GBSD)",
            }
        },
    },
    {
        "name": "qdrant_jobs",
        "type": "api",
        "description": "Find jobs associated with a program",
        "endpoint": f"{KNOWLEDGE_API_URL}/jobs/for",
        "method": "GET",
        "parameters": {
            "program_name": {
                "type": "string",
                "required": True,
                "description": "Program name to search jobs for",
            },
            "limit": {"type": "integer", "default": 20},
        },
    },
    # ----------------------------------------
    # KNOWLEDGE GRAPH TOOLS
    # ----------------------------------------
    {
        "name": "graph_query",
        "type": "api",
        "description": "Query the BD knowledge graph for relationships and paths",
        "endpoint": f"{KNOWLEDGE_API_URL}/graph/query",
        "method": "GET",
        "parameters": {
            "q": {"type": "string", "required": True, "description": "Graph query"},
            "mode": {
                "type": "string",
                "default": "hybrid",
                "enum": ["naive", "local", "global", "hybrid"],
                "description": "Query mode",
            },
        },
    },
    {
        "name": "graph_program_ecosystem",
        "type": "api",
        "description": "Get full ecosystem for a program (primes, subs, contacts, jobs)",
        "endpoint": f"{KNOWLEDGE_API_URL}/bdgraph/program",
        "method": "GET",
        "parameters": {
            "program_name": {
                "type": "string",
                "required": True,
                "description": "Program name",
            }
        },
    },
    {
        "name": "graph_contact_network",
        "type": "api",
        "description": "Get a contact's professional network and relationships",
        "endpoint": f"{KNOWLEDGE_API_URL}/bdgraph/contact",
        "method": "GET",
        "parameters": {
            "contact_name": {
                "type": "string",
                "required": True,
                "description": "Contact name",
            }
        },
    },
    {
        "name": "graph_teaming_path",
        "type": "api",
        "description": "Find teaming path from a contractor to a program",
        "endpoint": f"{KNOWLEDGE_API_URL}/bdgraph/teaming",
        "method": "GET",
        "parameters": {
            "from_contractor": {
                "type": "string",
                "required": True,
                "description": "Source contractor",
            },
            "to_program": {
                "type": "string",
                "required": True,
                "description": "Target program",
            },
            "max_depth": {"type": "integer", "default": 4},
        },
    },
    # ----------------------------------------
    # MEMORY TOOLS
    # ----------------------------------------
    {
        "name": "memory_search",
        "type": "api",
        "description": "Search conversation memories and past interactions",
        "endpoint": f"{KNOWLEDGE_API_URL}/memory/search",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Memory search query",
            },
            "limit": {"type": "integer", "default": 10},
        },
    },
    {
        "name": "memory_contact_context",
        "type": "api",
        "description": "Get full context for a contact (interactions, memories, history)",
        "endpoint": f"{KNOWLEDGE_API_URL}/memory/contact",
        "method": "GET",
        "parameters": {
            "contact_name": {
                "type": "string",
                "required": True,
                "description": "Contact name",
            }
        },
    },
    # ----------------------------------------
    # AGENT TOOLS
    # ----------------------------------------
    {
        "name": "bd_strategy_agent",
        "type": "api",
        "description": "BD Strategy Agent - Synthesizes intelligence into capture plans, win themes, and action plans",
        "endpoint": f"{KNOWLEDGE_API_URL}/agent/strategy",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Strategy request (e.g., 'Develop capture plan for AF DCGS')",
            }
        },
    },
    {
        "name": "company_research_agent",
        "type": "api",
        "description": "Company Research Agent - Gathers competitive intelligence about contractors",
        "endpoint": f"{KNOWLEDGE_API_URL}/agent/company",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Company to research",
            }
        },
    },
    {
        "name": "contact_finder_agent",
        "type": "api",
        "description": "Contact Finder Agent - Discovers contacts based on program, company, or role criteria",
        "endpoint": f"{KNOWLEDGE_API_URL}/agent/contact",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Contact search criteria",
            }
        },
    },
    {
        "name": "program_intel_agent",
        "type": "api",
        "description": "Program Intel Agent - Analyzes federal programs for BD opportunities",
        "endpoint": f"{KNOWLEDGE_API_URL}/agent/program",
        "method": "GET",
        "parameters": {
            "q": {
                "type": "string",
                "required": True,
                "description": "Program to analyze",
            }
        },
    },
    # ----------------------------------------
    # CREWAI WORKFLOW TOOLS
    # ----------------------------------------
    {
        "name": "crewai_analyze_program",
        "type": "api",
        "description": "Run multi-agent program analysis workflow (4 agents → BD playbook)",
        "endpoint": f"{KNOWLEDGE_API_URL}/agents/analyze-program",
        "method": "POST",
        "parameters": {
            "program_name": {
                "type": "string",
                "required": True,
                "description": "Program to analyze",
            }
        },
    },
    {
        "name": "crewai_prepare_outreach",
        "type": "api",
        "description": "Run multi-agent outreach preparation (4 agents → call script, email, LinkedIn)",
        "endpoint": f"{KNOWLEDGE_API_URL}/agents/prepare-outreach",
        "method": "POST",
        "parameters": {
            "contact_name": {
                "type": "string",
                "required": True,
                "description": "Contact to prepare outreach for",
            }
        },
    },
    {
        "name": "crewai_weekly_intel",
        "type": "api",
        "description": "Generate weekly BD intelligence report with multi-agent workflow",
        "endpoint": f"{KNOWLEDGE_API_URL}/agents/weekly-intel",
        "method": "POST",
        "parameters": {},
    },
    # ----------------------------------------
    # N8N WORKFLOW TOOLS
    # ----------------------------------------
    {
        "name": "n8n_job_scraper",
        "type": "webhook",
        "description": "Trigger job scraping from ClearanceJobs, LinkedIn, and competitor sites",
        "endpoint": f"{N8N_API_URL}/webhook/job-scraper-trigger",
        "method": "POST",
        "parameters": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Search keywords",
            },
            "max_results": {"type": "integer", "default": 100},
        },
    },
    {
        "name": "n8n_hot_lead_alert",
        "type": "webhook",
        "description": "Send hot lead alert notification",
        "endpoint": f"{N8N_API_URL}/webhook/hot-lead",
        "method": "POST",
        "parameters": {
            "contact_name": {"type": "string", "required": True},
            "company": {"type": "string"},
            "program": {"type": "string"},
            "score": {"type": "integer"},
            "reason": {"type": "string"},
        },
    },
    {
        "name": "n8n_weekly_report",
        "type": "webhook",
        "description": "Generate and send weekly BD intelligence report",
        "endpoint": f"{N8N_API_URL}/webhook/weekly-report",
        "method": "POST",
        "parameters": {
            "recipients": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Email recipients",
            }
        },
    },
    {
        "name": "n8n_master_pipeline",
        "type": "webhook",
        "description": "Trigger master BD orchestration pipeline",
        "endpoint": f"{N8N_API_URL}/webhook/master-pipeline",
        "method": "POST",
        "parameters": {
            "stage": {
                "type": "string",
                "enum": ["scrape", "enrich", "score", "full"],
                "default": "full",
            }
        },
    },
    # ----------------------------------------
    # MCP TOOLS (via MCP servers)
    # ----------------------------------------
    {
        "name": "notion_query",
        "type": "mcp",
        "description": "Query Notion databases (contacts, programs, opportunities)",
        "mcp_server": "notion",
        "note": "Requires Notion MCP server to be running",
    },
    {
        "name": "apify_scrape",
        "type": "mcp",
        "description": "Run Apify actors for web scraping",
        "mcp_server": "apify",
        "note": "Requires Apify MCP server to be running",
    },
]


# ============================================
# TOOL CATEGORIES FOR DIFY UI
# ============================================

TOOL_CATEGORIES = {
    "Search & RAG": [
        "qdrant_search",
        "qdrant_smart_query",
        "qdrant_hybrid_search",
        "qdrant_rag",
    ],
    "Contacts & Companies": [
        "qdrant_contacts",
        "qdrant_programs",
        "qdrant_jobs",
        "graph_contact_network",
    ],
    "Knowledge Graph": ["graph_query", "graph_program_ecosystem", "graph_teaming_path"],
    "Memory": ["memory_search", "memory_contact_context"],
    "AI Agents": [
        "bd_strategy_agent",
        "company_research_agent",
        "contact_finder_agent",
        "program_intel_agent",
    ],
    "Multi-Agent Workflows": [
        "crewai_analyze_program",
        "crewai_prepare_outreach",
        "crewai_weekly_intel",
    ],
    "Automation (n8n)": [
        "n8n_job_scraper",
        "n8n_hot_lead_alert",
        "n8n_weekly_report",
        "n8n_master_pipeline",
    ],
    "External (MCP)": ["notion_query", "apify_scrape"],
}


def get_tools_for_dify() -> list:
    """Get tool configurations formatted for Dify import."""
    return DIFY_EXTERNAL_TOOLS


def get_tools_by_category(category: str) -> list:
    """Get tools in a specific category."""
    tool_names = TOOL_CATEGORIES.get(category, [])
    return [t for t in DIFY_EXTERNAL_TOOLS if t["name"] in tool_names]


def print_tools_summary():
    """Print a summary of all available tools."""
    print("\n" + "=" * 60)
    print("DIFY EXTERNAL TOOLS CONFIGURATION")
    print("=" * 60)

    for category, tool_names in TOOL_CATEGORIES.items():
        print(f"\n{category}:")
        for name in tool_names:
            tool = next((t for t in DIFY_EXTERNAL_TOOLS if t["name"] == name), None)
            if tool:
                print(f"  • {name}: {tool['description'][:60]}...")

    print("\n" + "=" * 60)
    print(f"Total Tools: {len(DIFY_EXTERNAL_TOOLS)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_tools_summary()
