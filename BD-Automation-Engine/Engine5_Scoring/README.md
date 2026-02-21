# Engine 5 — BD Priority Scoring

Calculates BD Priority Scores (0-100) and tier classifications (Hot/Warm/Cold) using a 6-factor algorithm.

## Scripts

| Script | Purpose |
|--------|---------|
| `bd_scoring.py` | 6-factor scoring with clearance, program, location, contact tier, confidence, and recency boosts |

## Scoring Algorithm

| Factor | Boost Range | Details |
|--------|-------------|---------|
| **Base Score** | 50 | Starting point for all jobs |
| **Clearance** | 0–35 | TS/SCI w/ Poly: +35, TS/SCI: +25, Top Secret: +15, Secret: +5 |
| **Program** | 0–15 | AF DCGS-PACAF: +15, Navy/Army DCGS: +8 |
| **Location** | 0–10 | San Diego: +10, Hampton/Dayton: +5 |
| **Contact Tier** | 0.9–1.3x | Multiplier based on tier (1=1.3x, 5=1.0x) |
| **Confidence** | 0–20 | Match confidence weighted to 20 points |
| **Recency** | 0–10 | Last 7 days: +10, Last 30: +5, Last 90: +2 |

## Tier Classification

| Tier | Score | Action |
|------|-------|--------|
| Hot 🔥 | ≥80 | Generate playbook, notify team |
| Warm 🟡 | 50–79 | Add to watchlist |
| Cold ❄️ | <50 | Archive |

## Configuration

`Configurations/Scoring_Config.json`:
- DCGS focus programs (AF DCGS-PACAF, Langley, Wright-Patt, Navy DCGS-N, Army DCGS-A)
- Critical locations (San Diego, Hampton, Dayton)
- Top 20 strategic programs boost (+10): GBSD, F-35, GPS III, JADC2, etc.

## Running

```python
from Engine5_Scoring.scripts.bd_scoring import calculate_bd_score

result = calculate_bd_score(
    job_data,
    contact_tier=3,
    match_confidence=0.85,
    program_name="AF DCGS - PACAF"
)
# Returns: ScoringResult(bd_score=89, tier="hot", ...)
```

## Dependencies

- **Input from:** Engine 2 (standardized jobs), Engine 3 (contact tier)
- **Feeds into:** Engine 4 (playbooks/briefings), Engine 6 (QA/alerts)
