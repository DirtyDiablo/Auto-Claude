# Federal Programs Intelligence Engine - Quick Start Guide

## Prerequisites

- Python 3.9+
- pip (Python package manager)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
TANGO_API_KEY=your_tango_key_here
SAM_GOV_API_KEY=your_sam_gov_key_here
```

### 3. Initialize Database

```bash
python -m src.cli init
```

This creates:
- SQLite database at `data/federal_programs.db`
- Required directories (data, exports, logs, cache)

### 4. Migrate Existing Data (Optional)

If you have existing CSV data:

```bash
python -m src.cli migrate --source csv
```

## Usage

### Discover High Subaward Programs

Find programs with $100M+ subaward spend:

```bash
python -m src.cli discover --high-subaward --min-amount 100000000 --save
```

### Export BD Targets

Export programs to CSV:

```bash
python -m src.cli export --format csv --output bd_targets.csv
```

Export critical priority only:

```bash
python -m src.cli export --format csv --priority Critical --output critical_targets.csv
```

### View Statistics

```bash
python -m src.cli stats
```

### Validate Configuration

```bash
python -m src.cli validate
```

## Project Structure

```
C:\N8N Builder\
├── src/                    # Refactored source code
│   ├── config/            # Configuration management
│   ├── api_clients/       # Unified API clients
│   ├── database/          # SQLAlchemy models
│   ├── utils/             # Logging, helpers
│   ├── discovery_engine.py
│   └── cli.py             # Command-line interface
├── docs/                   # Documentation
├── data/                   # Database files
├── exports/               # Exported data
├── logs/                  # Log files
└── cache/                 # API cache
```

## Common Commands

| Command | Description |
|---------|-------------|
| `python -m src.cli init` | Initialize database |
| `python -m src.cli discover --high-subaward` | Find high subaward programs |
| `python -m src.cli migrate --source csv` | Import CSV data |
| `python -m src.cli export --format csv` | Export to CSV |
| `python -m src.cli stats` | Show statistics |
| `python -m src.cli validate` | Check configuration |

## Getting Help

```bash
python -m src.cli --help
python -m src.cli discover --help
```

## Next Steps

1. Review `docs/UI-UX-IDEATION.md` for dashboard concepts
2. Review `docs/AUTONOMOUS-AUDIT-FINAL-SUMMARY.md` for full audit results
3. Consider building the dashboard with Next.js + FastAPI
