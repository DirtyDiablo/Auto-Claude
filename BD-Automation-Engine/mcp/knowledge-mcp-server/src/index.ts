#!/usr/bin/env node
/**
 * BD Knowledge MCP Server
 *
 * Provides semantic search and RAG capabilities for BD intelligence data.
 * Connects to the BD Knowledge API for actual search/RAG operations.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

// Configuration
const KNOWLEDGE_API_URL = process.env.KNOWLEDGE_API_URL || "http://127.0.0.1:8100";

// Types
interface SearchParams {
  query: string;
  collection?: string;
  limit?: number;
  score_threshold?: number;
}

interface AskParams {
  question: string;
  collection?: string;
  limit?: number;
}

interface SimilarParams {
  item_id: string;
  collection: string;
  limit?: number;
}

interface ApiResponse {
  [key: string]: unknown;
}

// Helper function for API calls
async function callKnowledgeAPI(
  endpoint: string,
  method: "GET" | "POST" = "GET",
  body?: Record<string, unknown>
): Promise<ApiResponse> {
  const url = `${KNOWLEDGE_API_URL}${endpoint}`;

  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (body && method === "POST") {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error (${response.status}): ${errorText}`);
    }

    return await response.json() as ApiResponse;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Cannot connect to Knowledge API at ${KNOWLEDGE_API_URL}. ` +
        `Make sure the API is running: python Engine8_Knowledge/api.py`
      );
    }
    throw error;
  }
}

// Create MCP server
const server = new Server(
  {
    name: "bd-knowledge",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_knowledge",
        description: `Search the BD knowledge base for jobs, contacts, programs, documents, or activities.

Collections available:
- jobs: Job postings with program mappings and BD scores
- contacts: Contacts with tier classification (1-6) and company affiliation
- programs: Federal programs and contracts
- documents: Processed documents, briefings, past performance
- activities: Call notes and interaction records

Examples:
- "DCGS analyst" in jobs collection
- "Leidos program manager" in contacts
- "TS/SCI cleared positions"`,
        inputSchema: {
          type: "object" as const,
          properties: {
            query: {
              type: "string",
              description: "Natural language search query",
            },
            collection: {
              type: "string",
              enum: ["jobs", "contacts", "programs", "documents", "activities"],
              description: "Collection to search (searches all if not specified)",
            },
            limit: {
              type: "number",
              default: 10,
              description: "Maximum results to return (1-50)",
            },
            score_threshold: {
              type: "number",
              default: 0.3,
              description: "Minimum relevance score (0-1)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "ask_knowledge",
        description: `Ask a natural language question about BD intelligence data.
Uses RAG (Retrieval Augmented Generation) to find relevant context and generate a comprehensive answer.

Great for questions like:
- "What contacts do we have at Leidos working on DCGS?"
- "What past performance do we have with GDIT?"
- "Summarize job opportunities requiring TS/SCI clearance"
- "Who should we contact about GBSD opportunities?"`,
        inputSchema: {
          type: "object" as const,
          properties: {
            question: {
              type: "string",
              description: "Natural language question to answer",
            },
            collection: {
              type: "string",
              enum: ["jobs", "contacts", "programs", "documents", "activities"],
              description: "Specific collection to search (searches all if not specified)",
            },
            limit: {
              type: "number",
              default: 5,
              description: "Number of sources to use for context (1-20)",
            },
          },
          required: ["question"],
        },
      },
      {
        name: "find_similar",
        description: `Find items similar to a specific item in the knowledge base.

Use this to discover related jobs, contacts, or programs based on semantic similarity.`,
        inputSchema: {
          type: "object" as const,
          properties: {
            item_id: {
              type: "string",
              description: "ID of the item to find similar items for",
            },
            collection: {
              type: "string",
              enum: ["jobs", "contacts", "programs", "documents", "activities"],
              description: "Collection containing the item",
            },
            limit: {
              type: "number",
              default: 10,
              description: "Maximum similar items to return",
            },
          },
          required: ["item_id", "collection"],
        },
      },
      {
        name: "get_program_intel",
        description: `Get comprehensive intelligence about a federal program.

Returns related jobs, contacts, past performance, and other relevant information.`,
        inputSchema: {
          type: "object" as const,
          properties: {
            program_name: {
              type: "string",
              description: "Name of the program (e.g., 'DCGS', 'GBSD', 'Defense Enclave Services')",
            },
          },
          required: ["program_name"],
        },
      },
      {
        name: "get_company_contacts",
        description: `Find contacts at a specific company/contractor.`,
        inputSchema: {
          type: "object" as const,
          properties: {
            company_name: {
              type: "string",
              description: "Name of the company (e.g., 'Leidos', 'GDIT', 'Northrop Grumman')",
            },
            limit: {
              type: "number",
              default: 20,
              description: "Maximum contacts to return",
            },
          },
          required: ["company_name"],
        },
      },
      {
        name: "get_knowledge_stats",
        description: `Get statistics about the knowledge base collections.

Shows number of indexed items in each collection.`,
        inputSchema: {
          type: "object" as const,
          properties: {},
        },
      },
      {
        name: "reindex_knowledge",
        description: `Trigger re-indexing of the knowledge base.

Use this after data updates to refresh the search index.`,
        inputSchema: {
          type: "object" as const,
          properties: {
            collection: {
              type: "string",
              enum: ["jobs", "contacts", "programs", "documents", "activities", "all"],
              default: "all",
              description: "Collection to reindex (or 'all' for everything)",
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "search_knowledge": {
        const params = args as unknown as SearchParams;
        const response = await callKnowledgeAPI("/search", "POST", {
          query: params.query,
          collection: params.collection,
          limit: params.limit || 10,
          score_threshold: params.score_threshold || 0.3,
        });

        return {
          content: [
            {
              type: "text" as const,
              text: formatSearchResults(response),
            },
          ],
        };
      }

      case "ask_knowledge": {
        const params = args as unknown as AskParams;
        const response = await callKnowledgeAPI("/ask", "POST", {
          question: params.question,
          collection: params.collection,
          limit: params.limit || 5,
          include_sources: true,
        });

        return {
          content: [
            {
              type: "text" as const,
              text: formatAskResponse(response),
            },
          ],
        };
      }

      case "find_similar": {
        const params = args as unknown as SimilarParams;
        const response = await callKnowledgeAPI("/similar", "POST", {
          item_id: params.item_id,
          collection: params.collection,
          limit: params.limit || 10,
        });

        return {
          content: [
            {
              type: "text" as const,
              text: formatSearchResults(response),
            },
          ],
        };
      }

      case "get_program_intel": {
        const programName = (args as { program_name: string }).program_name;
        const response = await callKnowledgeAPI(
          `/program/${encodeURIComponent(programName)}`
        );

        return {
          content: [
            {
              type: "text" as const,
              text: formatAskResponse(response),
            },
          ],
        };
      }

      case "get_company_contacts": {
        const params = args as { company_name: string; limit?: number };
        const response = await callKnowledgeAPI(
          `/contacts/at/${encodeURIComponent(params.company_name)}?limit=${params.limit || 20}`
        );

        return {
          content: [
            {
              type: "text" as const,
              text: formatContactsResponse(response),
            },
          ],
        };
      }

      case "get_knowledge_stats": {
        const response = await callKnowledgeAPI("/stats");
        return {
          content: [
            {
              type: "text" as const,
              text: formatStatsResponse(response),
            },
          ],
        };
      }

      case "reindex_knowledge": {
        const collection = (args as { collection?: string }).collection || "all";
        const endpoint = collection === "all" ? "/index/all" : `/index/${collection}`;
        const response = await callKnowledgeAPI(endpoint, "POST");

        return {
          content: [
            {
              type: "text" as const,
              text: formatIndexResponse(response),
            },
          ],
        };
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: "text" as const,
          text: `Error: ${message}`,
        },
      ],
      isError: true,
    };
  }
});

// Format helpers
function formatSearchResults(response: ApiResponse): string {
  const results = response.results as Array<{
    id: string;
    score: number;
    payload: Record<string, unknown>;
    collection: string;
  }>;

  if (!results || results.length === 0) {
    return "No results found.";
  }

  const lines = [`Found ${results.length} results:\n`];

  for (const result of results) {
    const payload = result.payload;
    const name = (payload.name as string) || (payload.title as string) || result.id;
    const collection = result.collection;

    lines.push(`[${result.score.toFixed(2)}] ${name} (${collection})`);

    // Add relevant details based on collection
    if (collection === "jobs") {
      if (payload.company) lines.push(`  Company: ${payload.company}`);
      if (payload.location) lines.push(`  Location: ${payload.location}`);
      if (payload.clearance) lines.push(`  Clearance: ${payload.clearance}`);
    } else if (collection === "contacts") {
      if (payload.title) lines.push(`  Title: ${payload.title}`);
      if (payload.company) lines.push(`  Company: ${payload.company}`);
      if (payload.email) lines.push(`  Email: ${payload.email}`);
      if (payload.tier) lines.push(`  Tier: ${payload.tier}`);
    } else if (collection === "programs") {
      if (payload.prime_contractor) lines.push(`  Prime: ${payload.prime_contractor}`);
      if (payload.contract_value) lines.push(`  Value: ${payload.contract_value}`);
    }

    lines.push("");
  }

  return lines.join("\n");
}

function formatAskResponse(response: ApiResponse): string {
  const answer = response.answer as string;
  const sources = response.sources as Array<{
    id: string;
    score: number;
    payload: Record<string, unknown>;
    collection: string;
  }>;
  const confidence = response.confidence as number;

  const lines = [answer, "", "---", `Confidence: ${((confidence || 0) * 100).toFixed(0)}%`, "", "Sources:"];

  if (sources) {
    for (let i = 0; i < sources.length; i++) {
      const source = sources[i];
      const name = (source.payload.name as string) || (source.payload.title as string) || source.id;
      lines.push(`  [${i + 1}] ${name} (${source.collection}, score: ${source.score.toFixed(2)})`);
    }
  }

  return lines.join("\n");
}

function formatContactsResponse(response: ApiResponse): string {
  const company = response.company as string;
  const contacts = response.contacts as Array<{
    payload: Record<string, unknown>;
    score: number;
  }>;
  const count = response.count as number;

  const lines = [`Contacts at ${company}: ${count} found\n`];

  for (const contact of contacts) {
    const payload = contact.payload;
    const name = `${payload.first_name || ""} ${payload.last_name || ""}`.trim() || (payload.name as string);
    lines.push(`- ${name}`);
    if (payload.title) lines.push(`  Title: ${payload.title}`);
    if (payload.email) lines.push(`  Email: ${payload.email}`);
    if (payload.phone) lines.push(`  Phone: ${payload.phone}`);
    if (payload.tier) lines.push(`  Tier: ${payload.tier}`);
    lines.push("");
  }

  return lines.join("\n");
}

function formatStatsResponse(response: ApiResponse): string {
  const collections = response.collections as Record<string, { points_count?: number; status?: string; error?: string }>;
  const totalVectors = response.total_vectors as number;

  const lines = ["Knowledge Base Statistics\n", "=".repeat(30)];

  for (const [name, stats] of Object.entries(collections)) {
    if (stats.error) {
      lines.push(`${name}: ERROR - ${stats.error}`);
    } else {
      lines.push(`${name}: ${stats.points_count || 0} items (${stats.status || "unknown"})`);
    }
  }

  lines.push("=".repeat(30));
  lines.push(`Total vectors: ${totalVectors}`);

  return lines.join("\n");
}

function formatIndexResponse(response: ApiResponse): string {
  const success = response.success as boolean;
  const message = response.message as string;
  const indexed = response.indexed as number;
  const errors = response.errors as number;
  const duration = response.duration_seconds as number;

  const status = success ? "SUCCESS" : "COMPLETED WITH ERRORS";
  return [
    `Indexing ${status}`,
    "",
    `Message: ${message}`,
    `Indexed: ${indexed}`,
    `Errors: ${errors}`,
    `Duration: ${duration.toFixed(1)}s`,
  ].join("\n");
}

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("BD Knowledge MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
