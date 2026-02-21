# Engine 4 — BD Playbook & Briefing Generator

Generates BD playbooks for Hot-tier opportunities (score ≥80) and briefing documents for all scored opportunities.

## Components

### Playbook Generator (`Engine4_Playbook/`)

| Script | Purpose |
|--------|---------|
| `bd_playbook_generator.py` | Full playbook generation: 5 sections + 4 output formats |

**5 Sections:** Program Intel, Org Intel, Pain Points, Competitive Landscape, Action Plan

**4 Output Formats:**
1. Full Playbook — Markdown briefing (all 5 sections)
2. Intro Email — Personalized outreach email
3. Call Script — Phone conversation guide
4. Talking Points — Key discussion topics

**Config:** `Configurations/Playbook_Config.json` — trigger threshold (score ≥80, confidence ≥0.70)

**Templates:** `Templates/` — output format templates

### Briefing Generator (`Engine4_Briefing/`)

| Script | Purpose |
|--------|---------|
| `briefing_generator.py` | Creates markdown briefings with 4 sections |

**4 Sections:** Opportunity Overview, Program Background, Key Contacts, Recommendations

## Running

```python
# Playbooks (Hot tier only)
from Engine4_Playbook.scripts.bd_playbook_generator import generate_playbooks_batch
results = generate_playbooks_batch(jobs_data, output_dir="outputs/playbooks", min_score=80)

# Briefings (broader coverage)
from Engine4_Briefing.scripts.briefing_generator import generate_briefings_batch
results = generate_briefings_batch(jobs, output_dir="data/deliverables/briefings", min_score=50)
```

## Dependencies

- **Input from:** Engine 2 (standardized jobs), Engine 3 (contact lookup), Engine 5 (scores)
- **Requires:** Claude API or OpenAI API
