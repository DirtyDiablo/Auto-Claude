# DATA ARCHITECTURE EXTRACTION — JSON OUTPUT TEMPLATES

Use these templates as the exact structure for your JSON output files.

---

## TEMPLATE 1: BD-AUTOMATION-ENGINE JSON Structure

**File:** `data_architecture_bd_engine.json`

```json
{
  "project_id": "BD_ENGINE",
  "scan_date": "2026-02-12",
  "project_info": {
    "path": "bd-automation-engine/",
    "files_scanned": 0,
    "file_types_found": {
      "python": 0,
      "typescript": 0,
      "csv": 0,
      "json": 0,
      "sql": 0,
      "other": 0
    }
  },
  "scan_stats": {
    "files_scanned": 0,
    "entities_found": 0,
    "properties_found": 0,
    "relationships_found": 0,
    "aliases_found": 0,
    "data_flows_found": 0,
    "qdrant_collections_documented": 0,
    "bullhorn_tables_documented": 0,
    "dashboard_feeds_documented": 0,
    "api_endpoints_documented": 0
  },
  "entities": [
    {
      "name": "EntityName",
      "pk": "primary_key_field",
      "records": "count or 'estimate: ~X' or 'unknown'",
      "category": "BD Intelligence",
      "desc": "One sentence description of what this entity represents",
      "sources": [
        "Engine3_OrgChart/data/Prime_Contacts_Enriched/",
        "Bullhorn candidate table",
        "Qdrant bd_contacts collection"
      ],
      "storage": "csv:Engine3_OrgChart/data/Prime_Contacts_Enriched/ | sqlite:bullhorn_master.db:candidates | qdrant:bd_contacts",
      "properties": [
        {
          "name": "contact_id",
          "type": "string",
          "note": "Unique identifier for contact",
          "source": "Bullhorn API or generated UUID",
          "nullable": false,
          "example": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
          "name": "first_name",
          "type": "string",
          "note": "Contact's first name",
          "source": "ZoomInfo export or Bullhorn candidate",
          "nullable": true,
          "example": "John"
        }
      ],
      "aliases": [
        {
          "canonical": "contact_id",
          "alias": "bullhorn_candidate_id",
          "source": "Bullhorn database candidates table"
        },
        {
          "canonical": "current_employer",
          "alias": "company_name",
          "source": "ZoomInfo export"
        }
      ]
    }
  ],
  "relationships": [
    {
      "from": "CONTACT",
      "to": "PROGRAM",
      "label": "WORKS_ON",
      "type": "many-many",
      "field": "contact_program_mapping (join table)",
      "note": "Contact assigned to work on a federal program at their contractor"
    },
    {
      "from": "JOB",
      "to": "PROGRAM",
      "label": "POSTED_FOR",
      "type": "many-one",
      "field": "job.program_id",
      "note": "Job posting is for a specific federal program"
    }
  ],
  "data_flows": [
    {
      "name": "Job Scrape → Program Mapping → BD Scoring",
      "source": "Engine1 job scraper output (531 jobs)",
      "target": "Engine5 BD scoring output",
      "stages": [
        "Stage 1: Apify scraper collects raw jobs",
        "Stage 2: Engine2 enriches with program matching",
        "Stage 3: Engine3 classifies contacts",
        "Stage 4: Engine5 scores opportunities",
        "Stage 5: Engine4 generates briefings"
      ],
      "entities_touched": [
        "JOB",
        "PROGRAM",
        "CONTRACTOR",
        "LOCATION",
        "OPPORTUNITY"
      ],
      "data_volume": "~500 jobs/month"
    }
  ],
  "databases": {
    "qdrant_collections": [
      {
        "name": "bd_contacts",
        "vector_size": 1536,
        "embedding_model": "text-embedding-3-small",
        "record_count": 0,
        "indexed": true,
        "payload_fields": [
          {
            "name": "contact_id",
            "type": "string",
            "example": ""
          },
          {
            "name": "full_name",
            "type": "string",
            "example": ""
          }
        ]
      }
    ],
    "sqlite_tables": [
      {
        "database": "bullhorn_master.db",
        "table": "candidates",
        "row_count": 0,
        "columns": [
          {
            "name": "id",
            "type": "INTEGER",
            "pk": true,
            "nullable": false
          },
          {
            "name": "first_name",
            "type": "TEXT",
            "pk": false,
            "nullable": true
          }
        ]
      }
    ],
    "dashboard_feeds": [
      {
        "file": "dashboard/public/data/contacts.json",
        "record_count": 0,
        "fields": [
          {
            "name": "id",
            "type": "string"
          },
          {
            "name": "name",
            "type": "string"
          }
        ]
      }
    ],
    "api_endpoints": [
      {
        "method": "GET",
        "path": "/api/v1/contacts",
        "description": "List all contacts",
        "request_params": [
          {
            "name": "program",
            "type": "string",
            "required": false,
            "example": "AF_DCGS_Langley"
          }
        ],
        "response_model": "ContactResponse",
        "response_fields": [
          {
            "name": "id",
            "type": "string"
          },
          {
            "name": "name",
            "type": "string"
          }
        ]
      }
    ]
  },
  "engines": [
    {
      "name": "Engine1_Scraper",
      "description": "Web scraping for job postings",
      "input_schema": {
        "job_board_url": "string",
        "filters": "object"
      },
      "output_schema": {
        "jobs": "array[Job]"
      }
    }
  ],
  "ai_agents": [
    {
      "name": "OutreachComposer",
      "description": "Generates personalized BD outreach messages",
      "tools": ["past_performance_lookup", "program_matcher"],
      "input_schema": {
        "contact": "Contact",
        "program": "Program"
      },
      "output_schema": {
        "message": "string",
        "subject": "string"
      }
    }
  ],
  "new_discoveries": [
    {
      "entity": "NEW_ENTITY_NAME",
      "description": "Description of what this is and where found",
      "properties": [
        "field1",
        "field2"
      ],
      "source": "Which file/database"
    }
  ],
  "scan_notes": "Any issues, gaps, or observations during scanning",
  "verified_against_known": {
    "known_20_node_types": "Verified all 20 exist in code",
    "known_35_relationships": "Verified XX exist, added Y new ones",
    "new_entities_beyond_20": "Found 2 new entity types not in prior audit"
  }
}
```

---

## TEMPLATE 2: DATA-SCRAPER JSON Structure

**File:** `data_architecture_data_scraper.json`

```json
{
  "project_id": "DATA_SCRAPER",
  "scan_date": "2026-02-12",
  "project_info": {
    "path": "data-scraper/",
    "files_scanned": 0,
    "file_types_found": {
      "python": 0,
      "sql": 0,
      "csv": 0,
      "json": 0,
      "other": 0
    }
  },
  "scan_stats": {
    "files_scanned": 0,
    "entities_found": 0,
    "properties_found": 0,
    "relationships_found": 0,
    "aliases_found": 0,
    "data_flows_found": 0,
    "tango_sql_schemas_extracted": 0,
    "scraper_output_columns": 0,
    "federal_api_endpoints": 0,
    "src_domains_sampled": 0
  },
  "entities": [
    {
      "name": "CONTRACT",
      "pk": "piid",
      "records": "100000+",
      "category": "Federal Awards",
      "desc": "Federal contract from SAM.gov, FPDS, or Tango API",
      "sources": [
        "Tango API",
        "FPDS XML feeds",
        "SAM.gov contract API"
      ],
      "storage": "qdrant:contracts | csv:data/output/Federal_Programs_Contracts.csv",
      "properties": [
        {
          "name": "piid",
          "type": "string",
          "note": "Procurement Instrument Identifier",
          "source": "FPDS or SAM.gov API",
          "nullable": false,
          "example": "FA8722-21-C-0001"
        },
        {
          "name": "contract_value",
          "type": "float",
          "note": "Total contract value in dollars",
          "source": "FPDS or SAM.gov",
          "nullable": true,
          "example": 5000000.0
        }
      ],
      "aliases": [
        {
          "canonical": "piid",
          "alias": "contract_number",
          "source": "FPDS variable name"
        }
      ]
    }
  ],
  "relationships": [
    {
      "from": "CONTRACT",
      "to": "PRIME",
      "label": "AWARDED_TO",
      "type": "many-one",
      "field": "contract.contractor_id",
      "note": "Contract awarded to a prime contractor"
    }
  ],
  "data_flows": [
    {
      "name": "USASpending API → Contract Enrichment → BD Database",
      "source": "USASpending API (award search)",
      "target": "BD Target Database",
      "stages": [
        "Query USASpending for GDIT contracts",
        "Extract award details and subawards",
        "Match to programs using keywords/location",
        "Calculate staffing needs",
        "Sync to bd_database"
      ],
      "entities_touched": [
        "CONTRACT",
        "SUBAWARD",
        "PRIME",
        "PROGRAM"
      ],
      "data_volume": "~100K contracts/update"
    }
  ],
  "tango_api": {
    "sql_schemas_found": 0,
    "database_name": "Tango federal procurement database",
    "tables": [
      {
        "table": "awards",
        "row_count": 0,
        "columns": [
          {
            "name": "piid",
            "type": "VARCHAR(100)",
            "pk": true
          }
        ]
      }
    ]
  },
  "scraper_outputs": [
    {
      "scraper": "insight_global",
      "description": "Jobs scraped from Insight Global staffing board",
      "output_format": "CSV",
      "column_count": 64,
      "columns": [
        {
          "name": "job_title",
          "position": 1,
          "type": "string",
          "example": "Network Engineer"
        },
        {
          "name": "required_clearance",
          "position": 15,
          "type": "enum",
          "values": [
            "None",
            "Secret",
            "TS/SCI",
            "TS/SCI/Poly"
          ],
          "example": "Secret"
        }
      ],
      "record_count": 0,
      "sample_file": "data/output/ig_jobs_stage1_enriched.csv"
    },
    {
      "scraper": "apex_systems",
      "description": "Jobs from Apex Systems portal",
      "output_format": "CSV",
      "column_count": 64,
      "columns": []
    }
  ],
  "federal_api_shapes": {
    "tango": {
      "search_awards": {
        "request": {
          "q": "string search query",
          "page_size": "integer",
          "filters": "object"
        },
        "response_fields": [
          {
            "name": "piid",
            "type": "string",
            "description": "Procurement Instrument Identifier"
          }
        ]
      },
      "search_entities": {
        "request": {
          "q": "string",
          "entity_type": "string"
        },
        "response_fields": [
          {
            "name": "entity_id",
            "type": "string"
          }
        ]
      },
      "search_opportunities": {
        "request": {
          "q": "string"
        },
        "response_fields": []
      }
    },
    "usaspending": {
      "search_awards": {
        "endpoint": "/api/v2/awards/search/",
        "response_fields": [
          {
            "name": "piid",
            "type": "string"
          }
        ]
      }
    },
    "fpds": {
      "atom_feed": {
        "response_fields": [
          {
            "name": "transaction_number",
            "type": "string"
          }
        ]
      }
    },
    "sam_gov": {
      "entity_search": {
        "response_fields": [
          {
            "name": "sam_entity_id",
            "type": "string"
          }
        ]
      }
    }
  },
  "pydantic_models": [
    {
      "file": "models/contract.py",
      "class": "ContractModel",
      "fields": [
        {
          "name": "piid",
          "type": "str",
          "required": true,
          "description": ""
        }
      ]
    }
  ],
  "src_domains_sampled": [
    {
      "domain": "agents",
      "classes_found": 0,
      "sample_classes": [
        "ResearchAgent",
        "EnrichmentAgent"
      ]
    },
    {
      "domain": "enrichment",
      "classes_found": 0,
      "sample_classes": []
    }
  ],
  "hub_client_sync": {
    "endpoint": "/api/v1/sync/jobs",
    "method": "POST",
    "request_schema": {
      "jobs": "array[Job]",
      "timestamp": "datetime",
      "run_id": "string"
    },
    "response_schema": {
      "success": "boolean",
      "inserted": "integer",
      "updated": "integer"
    }
  },
  "bd_target_databases": [
    {
      "file": "data/output/bd_databases/db1.csv",
      "row_count": 0,
      "column_count": 0,
      "columns": [
        "column1",
        "column2"
      ]
    }
  ],
  "knowledge_base": {
    "company_manifest_schema": {
      "name": "string",
      "headquarters": "string",
      "past_performance": "array"
    },
    "program_folder_structure": {
      "index_file": "index.json",
      "data_files": [
        "contracts.csv",
        "staffing.csv"
      ]
    }
  },
  "new_discoveries": [],
  "scan_notes": ""
}
```

---

## TEMPLATE 3: N8N-BUILDER JSON Structure

**File:** `data_architecture_n8n_builder.json`

```json
{
  "project_id": "N8N_BUILDER",
  "scan_date": "2026-02-12",
  "project_info": {
    "path": "n8n-builder/",
    "workflow_files_found": 0,
    "total_nodes": 0,
    "api_integrations": 0
  },
  "scan_stats": {
    "files_scanned": 0,
    "workflows_found": 0,
    "nodes_found": 0,
    "api_integrations": 0,
    "data_flows_found": 0,
    "contact_fields_extracted": 0,
    "webhook_triggers": 0
  },
  "workflows": [
    {
      "name": "Job_Scrape_Enrichment_Notion_Sync",
      "file": "workflows/job_scrape_enrichment.n8n.json",
      "description": "Scrapes job boards, enriches with program matching, syncs to Notion",
      "triggers": [
        "webhook",
        "schedule"
      ],
      "trigger_schedule": "daily at 6 AM",
      "node_count": 0,
      "nodes": [
        {
          "name": "Webhook Trigger",
          "type": "n8n-nodes-base.webhook",
          "position": [0, 0],
          "parameters": {
            "httpMethod": "POST",
            "path": "job-scrape-trigger"
          },
          "outputs": [
            "job_url",
            "scraper_type"
          ]
        },
        {
          "name": "Call Apify Actor",
          "type": "n8n-nodes-base.httpRequest",
          "position": [200, 0],
          "parameters": {
            "method": "POST",
            "url": "https://api.apify.com/v2/acts/...",
            "headers": {
              "Authorization": "Bearer $APIFY_TOKEN"
            }
          },
          "input_fields": [
            "actor_id",
            "input_data"
          ],
          "output_fields": [
            "status",
            "result_url"
          ]
        },
        {
          "name": "Enrich Job Data",
          "type": "n8n-nodes-base.code",
          "language": "javascript",
          "code_snippet": "return items.map(item => ({...item, enriched: true}))"
        },
        {
          "name": "Update Notion Database",
          "type": "n8n-nodes-base.httpRequest",
          "parameters": {
            "method": "POST",
            "url": "https://api.notion.com/v1/pages"
          }
        }
      ],
      "connections": [
        {
          "from": "Webhook Trigger",
          "to": "Call Apify Actor"
        },
        {
          "from": "Call Apify Actor",
          "to": "Enrich Job Data"
        },
        {
          "from": "Enrich Job Data",
          "to": "Update Notion Database"
        }
      ],
      "data_flow": "Webhook receives job scrape request → Apify actor scrapes jobs → JavaScript enriches with program matching → POST to Notion",
      "output_schema": {
        "jobs_processed": "integer",
        "records_created": "integer",
        "records_updated": "integer"
      }
    }
  ],
  "api_integrations": [
    {
      "service": "Bullhorn",
      "endpoints_called": [
        "/search",
        "/entity/Candidate",
        "/entity/ClientCorporation"
      ],
      "workflows_using": [
        "Contact_Enrichment",
        "Bullhorn_Export_Analysis"
      ],
      "authentication": "API token in header",
      "request_sample": {
        "method": "GET",
        "params": {
          "where": "status = 'Active'",
          "count": 100
        }
      },
      "response_sample": {
        "data": [
          {
            "id": "12345",
            "firstName": "John",
            "email": "john@gdit.com"
          }
        ]
      }
    },
    {
      "service": "Notion",
      "operations": [
        "query_database",
        "create_page",
        "update_page",
        "delete_page"
      ],
      "databases_touched": [
        {
          "name": "DCGS Contacts Full",
          "collection_id": "2ccdef65-baa5-8087-a53b-000ba596128e",
          "operations": ["query", "update"]
        },
        {
          "name": "Program Mapping Hub",
          "collection_id": "f57792c1-605b-424c-8830-23ab41c47137",
          "operations": ["query", "create", "update"]
        }
      ]
    },
    {
      "service": "ZoomInfo",
      "endpoints_called": [
        "/search/people",
        "/person/{id}"
      ],
      "request_params": [
        {
          "name": "query",
          "type": "string",
          "example": "John Doe GDIT"
        }
      ],
      "response_fields": [
        {
          "name": "person_id",
          "type": "string"
        },
        {
          "name": "email",
          "type": "string"
        }
      ]
    },
    {
      "service": "Apify",
      "actors_called": [
        "insightglobal_scraper",
        "apexsystems_scraper"
      ],
      "request_schema": {
        "actor_id": "string",
        "input": "object"
      },
      "response_schema": {
        "status": "string",
        "result_url": "string"
      }
    }
  ],
  "contact_enrichment_workflow": {
    "workflow_name": "Contact_Enrichment_Master",
    "description": "Merges ZoomInfo, Bullhorn, DCGS Notion data into enriched contact",
    "input_schema": {
      "contact_name": "string",
      "company": "string",
      "title": "string (optional)"
    },
    "enrichment_sources": [
      {
        "source": "ZoomInfo API",
        "fields_provided": [
          "email",
          "phone",
          "mobile",
          "linkedin_url",
          "company_id"
        ]
      },
      {
        "source": "Bullhorn API",
        "fields_provided": [
          "candidate_id",
          "all_titles",
          "last_activity",
          "note_count"
        ]
      },
      {
        "source": "DCGS Contacts Notion",
        "fields_provided": [
          "program",
          "hierarchy_tier",
          "bd_priority",
          "location_hub",
          "functional_area"
        ]
      },
      {
        "source": "Program Mapping",
        "fields_provided": [
          "matched_program",
          "confidence_score",
          "labor_gap_identified"
        ]
      }
    ],
    "output_schema": [
      {
        "name": "enriched_contact_id",
        "type": "string",
        "source": "Bullhorn or generated UUID"
      },
      {
        "name": "full_name",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "email",
        "type": "string",
        "source": "ZoomInfo + Bullhorn"
      },
      {
        "name": "phone",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "mobile",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "linkedin_url",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "current_employer",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "job_title",
        "type": "string",
        "source": "ZoomInfo or Bullhorn"
      },
      {
        "name": "program",
        "type": "enum",
        "source": "Program matching or DCGS Notion",
        "possible_values": [
          "AF DCGS - Langley",
          "AF DCGS - PACAF",
          "Army DCGS-A",
          "Navy DCGS-N"
        ]
      },
      {
        "name": "hierarchy_tier",
        "type": "enum",
        "source": "Contact classification logic",
        "possible_values": [
          "Tier 1 - Executive",
          "Tier 2 - Director",
          "Tier 3 - Program Leadership",
          "Tier 4 - Management",
          "Tier 5 - Senior IC",
          "Tier 6 - Individual Contributor"
        ]
      },
      {
        "name": "bd_priority",
        "type": "enum",
        "source": "BD scoring algorithm",
        "possible_values": [
          "🔴 Critical",
          "🟠 High",
          "🟡 Medium",
          "⚪ Standard"
        ]
      },
      {
        "name": "functional_area",
        "type": "array[string]",
        "source": "Job title parsing or Bullhorn"
      },
      {
        "name": "city",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "state",
        "type": "string",
        "source": "ZoomInfo"
      },
      {
        "name": "location_hub",
        "type": "enum",
        "source": "Location mapping",
        "possible_values": [
          "Hampton Roads",
          "San Diego Metro",
          "DC Metro",
          "Dayton/Wright-Patt",
          "Other CONUS",
          "OCONUS"
        ]
      }
    ]
  },
  "code_node_transformations": [
    {
      "workflow": "Job_Scrape_Enrichment",
      "node_name": "Normalize Contact Fields",
      "language": "javascript",
      "input_schema": {
        "zoominfo_contact": "object",
        "bullhorn_contact": "object"
      },
      "output_schema": {
        "normalized_contact": "object with standardized field names"
      },
      "transformation_logic": "Merges ZoomInfo and Bullhorn contacts, choosing best value for each field"
    }
  ],
  "notion_operations": [
    {
      "database": "DCGS Contacts Full",
      "collection_id": "2ccdef65-baa5-8087-a53b-000ba596128e",
      "operations": [
        {
          "operation": "update",
          "fields_touched": [
            "Program",
            "Hierarchy Tier",
            "BD Priority",
            "Location Hub"
          ],
          "workflow": "Contact_Classification"
        }
      ]
    },
    {
      "database": "Program Mapping Hub",
      "collection_id": "f57792c1-605b-424c-8830-23ab41c47137",
      "operations": [
        {
          "operation": "create",
          "fields_set": [
            "job_title",
            "company",
            "program",
            "confidence_score"
          ],
          "workflow": "Job_Scrape_Enrichment"
        }
      ]
    }
  ],
  "webhooks": [
    {
      "path": "job-scrape-trigger",
      "method": "POST",
      "authentication": "API key in header",
      "payload_schema": {
        "job_url": "string",
        "scraper_type": "enum: insightglobal | apex | teksystems",
        "timestamp": "datetime"
      },
      "triggers_workflow": "Job_Scrape_Enrichment_Notion_Sync",
      "sample_payload": {
        "job_url": "https://insightglobal.com/job/12345",
        "scraper_type": "insightglobal"
      }
    }
  ],
  "new_discoveries": [],
  "scan_notes": ""
}
```

---

## KEY FIELD DEFINITIONS FOR ALL TEMPLATES

### Type Values (Use Exact Strings)
```
"string" | "integer" | "int" | "float" | "boolean" | "bool" | 
"date" | "datetime" | "timestamp" |
"enum" | "list[string]" | "list[int]" | "array" | 
"object" | "dict" | "UUID" | "FK" | "PK"
```

### Category Values (Use Exact Strings)
```
"Federal Awards" | "Procurement" | "Organizations" | 
"BD Intelligence" | "Reference" | "Meta/Ops"
```

### Storage Format (Use Exact Pattern)
```
"csv:path/to/file.csv" |
"sqlite:database.db:table_name" |
"qdrant:collection_name" |
"api:endpoint_path" |
"json:path/to/file.json" |
"notion:collection_id"
```

### Relationship Type Values
```
"FK" | "one-one" | "one-many" | "many-many" | "many-one" | "derived"
```

---

## VALIDATION CHECKLIST FOR OUTPUT

Before saving, verify your JSON:

- [ ] Top-level keys present: project_id, scan_date, scan_stats, entities, relationships
- [ ] All entities have: name, pk, records, category, desc, sources, storage, properties
- [ ] All properties have: name, type, note, source, nullable, example
- [ ] All relationships have: from, to, label, type, field, note
- [ ] scan_stats numbers match actual content (entity count, etc.)
- [ ] Type values are from the predefined list above
- [ ] Category values are from the predefined list above
- [ ] JSON is valid (use `python3 -m json.tool <file>` to validate)
- [ ] No circular references
- [ ] No placeholder values like "TODO" or "unknown"

---

*JSON templates generated 2026-02-12 | Use exact structure shown above*
