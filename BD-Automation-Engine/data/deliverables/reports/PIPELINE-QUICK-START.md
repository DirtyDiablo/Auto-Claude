# Program Intelligence Pipeline - Quick Start Guide

## Overview

This pipeline collects comprehensive BD intelligence on federal programs from USASpending.gov. It implements a 7-phase data collection strategy to gather:

- **500+ data fields** per contract
- Prime contractor details with executives
- All subcontractors and their locations
- Task orders under IDV contracts
- Technology and skills intelligence
- BD scoring and prioritization

## Installation

```bash
# Ensure you're in the project directory
cd "C:\N8N Builder"

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Run Full Pipeline

```bash
# Run full pipeline for DoD contracts > $100M
python -m src.pipelines.program_intelligence_pipeline

# With custom parameters
python -m src.pipelines.program_intelligence_pipeline \
    --min-amount 500000000 \
    --max-contracts 100 \
    --naics 541512 541519
```

### Run Individual Phases

```bash
# Phase 1: Discover contracts
python -m src.pipelines.program_intelligence_pipeline --phase 1

# Phase 2: Enrich with full details
python -m src.pipelines.program_intelligence_pipeline --phase 2

# Phase 3: Collect subawards
python -m src.pipelines.program_intelligence_pipeline --phase 3

# Phase 4: Collect task orders
python -m src.pipelines.program_intelligence_pipeline --phase 4

# Phase 7: Synthesize and score
python -m src.pipelines.program_intelligence_pipeline --phase 7
```

### Programmatic Usage

```python
from src.pipelines import ProgramIntelligencePipeline

# Initialize pipeline
pipeline = ProgramIntelligencePipeline()

# Run full pipeline
programs = pipeline.run_full_pipeline(
    min_amount=100_000_000,
    max_contracts=50,
    naics_codes=['541512', '541519'],  # IT Services
)

# Or run phases individually
contracts = pipeline.run_phase_1_discovery()
programs = pipeline.run_phase_2_enrichment(contracts)
programs = pipeline.run_phase_3_subawards(programs)
programs = pipeline.run_phase_4_task_orders(programs)
programs = pipeline.run_phase_7_synthesis(programs)
```

## Output Files

After running the pipeline, find results in `output/program_intelligence/`:

| File | Description |
|------|-------------|
| `master_program_intelligence.json` | Full data with all 500+ fields |
| `master_program_intelligence.csv` | Flat CSV for Excel/analysis |
| `tier1_high_priority.csv` | Top BD targets (score >= 70) |
| `tier2_medium_priority.csv` | Medium priority targets |
| `tier3_standard.csv` | Standard targets |
| `phase3_all_subawards.csv` | All subcontractor data |
| `phase4_all_task_orders.csv` | All task order data |
| `pipeline_stats.json` | Execution statistics |

## Data Model

The pipeline uses the `FederalProgramIntelligence` model with these key sections:

### Identifiers
- `award_id` - USASpending award ID
- `piid` - Procurement Instrument Identifier
- `parent_award_id` - Parent IDV (if applicable)

### Financial
- `contract_ceiling` - Total potential value
- `obligated_amount` - Current obligations
- `utilization_rate` - % of ceiling used

### Prime Contractor
- `prime_contractor` - Company name
- `prime_uei` - Unique Entity ID
- `prime_executives` - Top 5 executives with compensation
- `prime_business_types` - Small business flags

### Subcontractors
- `subcontractors` - List of all subs
- `sub_count` - Number of subcontractors
- `total_sub_spend` - Total subaward value
- `team_locations` - All work sites

### Task Orders
- `task_orders` - List of task orders (for IDVs)
- `task_order_count` - Number of TOs
- `total_task_order_value` - Combined TO value

### Classification
- `naics_code` / `naics_description`
- `psc_code` / `psc_description`
- `contract_type` / `pricing_type`

### Dates
- `start_date` / `current_end_date`
- `potential_end_date` / `ordering_end_date`
- `days_until_end` - Days to contract end

### BD Scoring
- `bd_score` - Overall target score (0-100)
- `priority_tier` - 1 (High), 2 (Medium), 3 (Standard)
- `recompete_risk` - High/Medium/Low
- `strategic_value` - High/Medium/Low

## BD Score Calculation

The BD score is calculated based on:

| Factor | Max Points | Criteria |
|--------|------------|----------|
| Contract Value | 30 | $10B+=30, $1B+=25, $500M+=20, $100M+=15 |
| Recompete Timing | 25 | <1yr=25, 1-2yr=15, >2yr=5 |
| Sub Activity | 15 | 20+ subs=15, 10+=10, 5+=5 |
| Hiring Activity | 15 | Hot hiring=15, 3+ jobs=10 |
| Tech Match | 15 | 10+ techs=15, 5+=10, 1+=5 |

**Priority Tiers:**
- Tier 1 (High): Score >= 70
- Tier 2 (Medium): Score >= 50
- Tier 3 (Standard): Score < 50

## API Rate Limiting

The pipeline implements automatic rate limiting:
- Default: 60 requests/minute
- Automatic retries on 429/500 errors
- Exponential backoff

## Example: Finding Teaming Opportunities

```python
from src.pipelines import ProgramIntelligencePipeline

pipeline = ProgramIntelligencePipeline()

# Get high-priority programs
programs = pipeline.run_full_pipeline(max_contracts=100)

# Find programs with significant subcontracting
teaming_opportunities = [
    p for p in programs
    if p.sub_count >= 10 and p.recompete_risk in ['High', 'Medium']
]

# Get competitor subcontractors
for program in teaming_opportunities:
    print(f"\n{program.program_name or program.piid}")
    print(f"Prime: {program.prime_contractor}")
    print(f"Contract: ${program.contract_ceiling:,.0f}")
    print(f"Recompete: {program.recompete_risk}")
    print(f"Subcontractors ({program.sub_count}):")
    for sub in program.subcontractors[:5]:
        print(f"  - {sub.name}: ${sub.subaward_amount:,.0f}")
```

## Extending the Pipeline

### Add Custom Phases

```python
class CustomPipeline(ProgramIntelligencePipeline):

    def run_phase_5_entity_enrichment(self, programs):
        """Custom phase: Enrich with SAM.gov data."""
        for program in programs:
            # Add SAM entity lookup here
            pass
        return programs

    def run_phase_6_job_intelligence(self, programs):
        """Custom phase: Collect job postings."""
        for program in programs:
            # Add job scraping here
            pass
        return programs
```

### Add Custom Scoring

```python
class CustomProgram(FederalProgramIntelligence):

    def calculate_custom_score(self):
        """Custom scoring based on company capabilities."""
        score = 0

        # Add points for matching NAICS
        target_naics = ['541512', '541519', '541511']
        if self.naics_code in target_naics:
            score += 20

        # Add points for matching clearance requirements
        if 'TS/SCI' in self.clearances:
            score += 15

        return score
```

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: The pipeline handles this automatically, but if you see many 429 errors, reduce the rate limit:
   ```python
   pipeline = ProgramIntelligencePipeline(rate_limit_per_min=30)
   ```

2. **Memory Issues**: For large datasets, process in batches:
   ```python
   pipeline.run_full_pipeline(max_contracts=50)  # Smaller batches
   ```

3. **Missing Data**: Some fields may be empty in USASpending. The pipeline handles null values gracefully.

### Logging

Enable debug logging:
```python
import logging
logging.getLogger('ProgramIntelligencePipeline').setLevel(logging.DEBUG)
```

## Next Steps

1. **Run the pipeline** for your target NAICS codes
2. **Review Tier 1 targets** in `tier1_high_priority.csv`
3. **Analyze subcontractor teams** in `phase3_all_subawards.csv`
4. **Track task orders** in `phase4_all_task_orders.csv`
5. **Export to your CRM** or BD tracking system

---

For the complete data field reference, see: `docs/COMPREHENSIVE-BD-INTELLIGENCE-STRATEGY.md`
