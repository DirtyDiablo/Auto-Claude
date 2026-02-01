#!/usr/bin/env node

/**
 * Enhanced MCP Server for BD Intelligence Hub
 * 30+ tools for comprehensive BD operations
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

const API_URL = process.env.KNOWLEDGE_API_URL || "http://127.0.0.1:8100";

// Helper to call API
async function callAPI(endpoint: string, method: string = "GET", body?: any) {
  const options: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) options.body = JSON.stringify(body);

  try {
    const response = await fetch(`${API_URL}${endpoint}`, options);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error (${response.status}): ${errorText}`);
    }
    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Cannot connect to BD Intelligence Hub API at ${API_URL}. ` +
        `Make sure the API is running: python Engine8_Knowledge/api.py`
      );
    }
    throw error;
  }
}

// Create server
const server = new Server(
  { name: "bd-intelligence-hub", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // ==================== SMART QUERY ====================
    {
      name: "smart_ask",
      description: "Intelligent query that routes to optimal system(s). Use for any BD question.",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string", description: "Your BD question" },
          use_cache: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },

    // ==================== SEARCH TOOLS ====================
    {
      name: "search_knowledge",
      description: `Search the BD knowledge base for jobs, contacts, programs, documents, or activities.
Collections: jobs, contacts, programs, documents, activities`,
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string", description: "Search query" },
          collection: { type: "string", enum: ["jobs", "contacts", "programs", "documents", "activities"] },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "semantic_search",
      description: "Search using semantic similarity",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "keyword_search",
      description: "Search using exact keyword matching (BM25)",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "hybrid_search",
      description: "Combined semantic + keyword search with reranking",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          collection: { type: "string", default: "bd_knowledge" },
          limit: { type: "number", default: 10 },
          use_rerank: { type: "boolean", default: true }
        },
        required: ["query"]
      }
    },

    // ==================== RAG TOOLS ====================
    {
      name: "ask_knowledge",
      description: "Ask a natural language question (RAG)",
      inputSchema: {
        type: "object" as const,
        properties: {
          question: { type: "string" },
          collection: { type: "string" },
          limit: { type: "number", default: 5 }
        },
        required: ["question"]
      }
    },

    // ==================== GRAPH TOOLS ====================
    {
      name: "query_knowledge_graph",
      description: "Query entity relationships and networks",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          mode: { type: "string", enum: ["local", "global", "hybrid"], default: "hybrid" }
        },
        required: ["query"]
      }
    },
    {
      name: "find_relationships",
      description: "Find all relationships for a company/program/contact",
      inputSchema: {
        type: "object" as const,
        properties: {
          entity: { type: "string", description: "Entity name" }
        },
        required: ["entity"]
      }
    },
    {
      name: "analyze_network",
      description: "Analyze a company's partner/competitor network",
      inputSchema: {
        type: "object" as const,
        properties: {
          company: { type: "string" }
        },
        required: ["company"]
      }
    },

    // ==================== MEMORY TOOLS ====================
    {
      name: "memory_add",
      description: "Add information to memory for future reference",
      inputSchema: {
        type: "object" as const,
        properties: {
          content: { type: "string" },
          memory_type: { type: "string", default: "interaction" }
        },
        required: ["content"]
      }
    },
    {
      name: "memory_add_entity",
      description: "Add a fact about a company/program/contact",
      inputSchema: {
        type: "object" as const,
        properties: {
          entity_name: { type: "string" },
          entity_type: { type: "string", enum: ["company", "program", "contact", "contract"] },
          fact: { type: "string" }
        },
        required: ["entity_name", "entity_type", "fact"]
      }
    },
    {
      name: "memory_add_insight",
      description: "Add a BD insight (opportunity, risk, relationship)",
      inputSchema: {
        type: "object" as const,
        properties: {
          insight_type: { type: "string", enum: ["opportunity", "risk", "relationship", "strategy"] },
          insight: { type: "string" },
          source: { type: "string", default: "user" },
          confidence: { type: "number", default: 0.8 }
        },
        required: ["insight_type", "insight"]
      }
    },
    {
      name: "memory_search",
      description: "Search past memories and interactions",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          limit: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "memory_get_entity",
      description: "Get all facts about a specific entity",
      inputSchema: {
        type: "object" as const,
        properties: {
          entity_name: { type: "string" }
        },
        required: ["entity_name"]
      }
    },
    {
      name: "memory_get_insights",
      description: "Get BD insights",
      inputSchema: {
        type: "object" as const,
        properties: {
          insight_type: { type: "string" },
          limit: { type: "number", default: 10 }
        }
      }
    },

    // ==================== INGEST TOOLS ====================
    {
      name: "ingest_program",
      description: "Add a federal program to the knowledge base",
      inputSchema: {
        type: "object" as const,
        properties: {
          name: { type: "string" },
          description: { type: "string" },
          agency: { type: "string" },
          primes: { type: "array", items: { type: "string" } },
          value: { type: "string" },
          clearance: { type: "string" },
          technologies: { type: "array", items: { type: "string" } }
        },
        required: ["name"]
      }
    },
    {
      name: "ingest_company",
      description: "Add a company to the knowledge base",
      inputSchema: {
        type: "object" as const,
        properties: {
          name: { type: "string" },
          type: { type: "string" },
          capabilities: { type: "array", items: { type: "string" } },
          programs: { type: "array", items: { type: "string" } },
          partners: { type: "array", items: { type: "string" } }
        },
        required: ["name"]
      }
    },
    {
      name: "ingest_contact",
      description: "Add a contact to the knowledge base",
      inputSchema: {
        type: "object" as const,
        properties: {
          name: { type: "string" },
          company: { type: "string" },
          title: { type: "string" },
          programs: { type: "array", items: { type: "string" } },
          clearance: { type: "string" }
        },
        required: ["name"]
      }
    },

    // ==================== AGENT TOOLS ====================
    {
      name: "agent_program_intel",
      description: "Use Program Intelligence Agent for program analysis",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_company_research",
      description: "Use Company Research Agent for competitor/partner analysis",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_contact_finder",
      description: "Use Contact Finder Agent to identify key personnel",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },
    {
      name: "agent_bd_strategy",
      description: "Use BD Strategy Agent for strategy development",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    },

    // ==================== WORKFLOW TOOLS ====================
    {
      name: "workflow_capture_strategy",
      description: "Run capture strategy workflow for an opportunity",
      inputSchema: {
        type: "object" as const,
        properties: {
          opportunity: { type: "string" }
        },
        required: ["opportunity"]
      }
    },
    {
      name: "workflow_competitor_analysis",
      description: "Run competitor analysis workflow for a company",
      inputSchema: {
        type: "object" as const,
        properties: {
          company: { type: "string" }
        },
        required: ["company"]
      }
    },

    // ==================== PAGEINDEX TOOLS ====================
    {
      name: "index_document_audit",
      description: "Index document for audit trail queries",
      inputSchema: {
        type: "object" as const,
        properties: {
          doc_id: { type: "string" },
          content: { type: "string" }
        },
        required: ["doc_id", "content"]
      }
    },
    {
      name: "query_with_audit",
      description: "Query with audit trail for compliance",
      inputSchema: {
        type: "object" as const,
        properties: {
          query: { type: "string" },
          doc_ids: { type: "string", description: "Comma-separated doc IDs" }
        },
        required: ["query"]
      }
    },

    // ==================== SPECIALIZED TOOLS ====================
    {
      name: "get_program_intel",
      description: "Get comprehensive intelligence about a program",
      inputSchema: {
        type: "object" as const,
        properties: {
          program_name: { type: "string" }
        },
        required: ["program_name"]
      }
    },
    {
      name: "get_company_contacts",
      description: "Find contacts at a specific company",
      inputSchema: {
        type: "object" as const,
        properties: {
          company_name: { type: "string" },
          limit: { type: "number", default: 20 }
        },
        required: ["company_name"]
      }
    },

    // ==================== SYSTEM TOOLS ====================
    {
      name: "get_system_stats",
      description: "Get system statistics",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "get_cache_stats",
      description: "Get cache statistics",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "clear_cache",
      description: "Clear query cache",
      inputSchema: { type: "object" as const, properties: {} }
    },
    {
      name: "reindex_knowledge",
      description: "Trigger re-indexing of the knowledge base",
      inputSchema: {
        type: "object" as const,
        properties: {
          collection: { type: "string", enum: ["jobs", "contacts", "programs", "documents", "activities", "all"], default: "all" }
        }
      }
    }
  ]
}));

// Tool handlers
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      // Smart Query
      case "smart_ask":
        result = await callAPI(`/ask/smart?q=${encodeURIComponent((args as any).query)}&use_cache=${(args as any).use_cache ?? true}`);
        break;

      // Search
      case "search_knowledge":
        result = await callAPI("/search", "POST", {
          query: (args as any).query,
          collection: (args as any).collection,
          limit: (args as any).limit || 10
        });
        break;
      case "semantic_search":
        result = await callAPI(`/search/semantic?q=${encodeURIComponent((args as any).query)}&collection=${(args as any).collection || 'bd_knowledge'}&limit=${(args as any).limit || 10}`);
        break;
      case "keyword_search":
        result = await callAPI(`/search/keyword?q=${encodeURIComponent((args as any).query)}&collection=${(args as any).collection || 'bd_knowledge'}&limit=${(args as any).limit || 10}`);
        break;
      case "hybrid_search":
        result = await callAPI(`/search/hybrid?q=${encodeURIComponent((args as any).query)}&collection=${(args as any).collection || 'bd_knowledge'}&limit=${(args as any).limit || 10}&use_rerank=${(args as any).use_rerank ?? true}`);
        break;

      // RAG
      case "ask_knowledge":
        result = await callAPI("/ask", "POST", {
          question: (args as any).question,
          collection: (args as any).collection,
          limit: (args as any).limit || 5,
          include_sources: true
        });
        break;

      // Graph
      case "query_knowledge_graph":
        result = await callAPI(`/graph/query?q=${encodeURIComponent((args as any).query)}&mode=${(args as any).mode || 'hybrid'}`);
        break;
      case "find_relationships":
        result = await callAPI(`/graph/relationships?entity=${encodeURIComponent((args as any).entity)}`);
        break;
      case "analyze_network":
        result = await callAPI(`/graph/network?company=${encodeURIComponent((args as any).company)}`);
        break;

      // Memory
      case "memory_add":
        result = await callAPI("/memory/add", "POST", { content: (args as any).content, metadata: { memory_type: (args as any).memory_type } });
        break;
      case "memory_add_entity":
        result = await callAPI(`/memory/entity?entity_name=${encodeURIComponent((args as any).entity_name)}&entity_type=${(args as any).entity_type}&fact=${encodeURIComponent((args as any).fact)}`, "POST");
        break;
      case "memory_add_insight":
        result = await callAPI("/memory/insight", "POST", args);
        break;
      case "memory_search":
        result = await callAPI(`/memory/search?q=${encodeURIComponent((args as any).query)}&limit=${(args as any).limit || 10}`);
        break;
      case "memory_get_entity":
        result = await callAPI(`/memory/entity/${encodeURIComponent((args as any).entity_name)}`);
        break;
      case "memory_get_insights":
        result = await callAPI(`/memory/insights?${(args as any).insight_type ? `insight_type=${(args as any).insight_type}&` : ''}limit=${(args as any).limit || 10}`);
        break;

      // Ingest
      case "ingest_program":
        result = await callAPI("/ingest/program", "POST", args);
        break;
      case "ingest_company":
        result = await callAPI("/ingest/company", "POST", args);
        break;
      case "ingest_contact":
        result = await callAPI("/ingest/contact", "POST", args);
        break;

      // Agents
      case "agent_program_intel":
        result = await callAPI(`/agent/program?q=${encodeURIComponent((args as any).query)}`);
        break;
      case "agent_company_research":
        result = await callAPI(`/agent/company?q=${encodeURIComponent((args as any).query)}`);
        break;
      case "agent_contact_finder":
        result = await callAPI(`/agent/contact?q=${encodeURIComponent((args as any).query)}`);
        break;
      case "agent_bd_strategy":
        result = await callAPI(`/agent/strategy?q=${encodeURIComponent((args as any).query)}`);
        break;

      // Workflows
      case "workflow_capture_strategy":
        result = await callAPI(`/workflow/capture?opportunity=${encodeURIComponent((args as any).opportunity)}`);
        break;
      case "workflow_competitor_analysis":
        result = await callAPI(`/workflow/competitor?company=${encodeURIComponent((args as any).company)}`);
        break;

      // PageIndex
      case "index_document_audit":
        result = await callAPI(`/pageindex/index?doc_id=${encodeURIComponent((args as any).doc_id)}&content=${encodeURIComponent((args as any).content)}`, "POST");
        break;
      case "query_with_audit":
        result = await callAPI(`/pageindex/query?q=${encodeURIComponent((args as any).query)}${(args as any).doc_ids ? `&doc_ids=${(args as any).doc_ids}` : ''}`);
        break;

      // Specialized
      case "get_program_intel":
        result = await callAPI(`/program/${encodeURIComponent((args as any).program_name)}`);
        break;
      case "get_company_contacts":
        result = await callAPI(`/contacts/at/${encodeURIComponent((args as any).company_name)}?limit=${(args as any).limit || 20}`);
        break;

      // System
      case "get_system_stats":
        result = await callAPI("/stats");
        break;
      case "get_cache_stats":
        result = await callAPI("/cache/stats");
        break;
      case "clear_cache":
        result = await callAPI("/cache/clear", "DELETE");
        break;
      case "reindex_knowledge":
        const collection = (args as any).collection || "all";
        const endpoint = collection === "all" ? "/index/all" : `/index/${collection}`;
        result = await callAPI(endpoint, "POST");
        break;

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }

    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text" as const, text: `Error: ${message}` }], isError: true };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("BD Intelligence Hub MCP Server running (30+ tools)");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
