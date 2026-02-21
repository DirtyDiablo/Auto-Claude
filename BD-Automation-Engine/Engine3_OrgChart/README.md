# Engine 3 — OrgChart Contact Classification

Classifies contacts into a 6-tier organizational hierarchy with BD priority and outreach sequence assignment.

## Scripts

| Script | Purpose |
|--------|---------|
| `contact_classifier.py` | Title-pattern classification into 6 tiers; assigns BD priority and outreach sequence |
| `contact_lookup.py` | Searches contact database and formats results for briefings/playbooks |

## 6-Tier Hierarchy

| Tier | Name | BD Priority | Outreach |
|------|------|------------|----------|
| 1 | Executive (CEO, CTO, President, EVP) | Critical | D — Strategic Engagement |
| 2 | Director (VP, Division Head) | Critical | D — Strategic Engagement |
| 3 | Program Leadership (PM, PjM, Site Lead) | High | C — Program Engagement |
| 4 | Management (Manager, Team Lead, Section Chief) | High | B — Validation Approach |
| 5 | Senior IC (Senior Engineer, Lead, Architect) | Medium | A — Discovery Approach |
| 6 | Individual Contributor (Engineer, Analyst) | Low | Tactical |

## Configuration

`Configurations/OrgChart_Config.json`:
- Target programs (GBSD Sentinel, F-35, etc.)
- Priority roles (Program Manager, VP, Director, Technical Lead, Capture Manager)
- Data sources and search strategies

## Data

- `DCGS_Contacts.csv` — 10K+ DCGS contacts
- `GDIT PTS Contacts.csv`, `GDIT_Other_Contacts.csv` — GDIT contacts
- `Lockheed Contact.csv` — Lockheed Martin contacts
- `Bullhorn_Contact_Search.csv` — CRM export
- `Prime_Contacts_Enriched/` — enriched output directory

## Running

```python
from Engine3_OrgChart.scripts.contact_classifier import classify_contact

result = classify_contact(title="Senior Program Manager", company="Lockheed Martin")
# Returns: tier=3, name="Program Leadership", bd_priority="High", outreach="C"

from Engine3_OrgChart.scripts.contact_lookup import lookup_contacts
contacts = lookup_contacts(program_name="DCGS", company="GDIT")
```

## Dependencies

- **Input:** Local CSV files (Bullhorn, LinkedIn exports)
- **Used by:** Engine 4 (playbooks/briefings), Engine 8 (knowledge indexing)
