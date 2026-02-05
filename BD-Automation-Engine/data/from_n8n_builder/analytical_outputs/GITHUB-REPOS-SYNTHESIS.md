# GitHub Repos Analysis - All-In-One Federal Programs Scraper

**Date:** 2026-01-20
**Repos Analyzed:** 7 key repositories
**Purpose:** Extract best practices to build ultimate federal programs discovery engine

---

## Repos Cloned & Analyzed

### 1. ✅ blencorp/capture-mcp-server (PRIORITY 1)
- **Stars:** 12
- **Language:** TypeScript
- **Value:** Tango API production implementation
- **Key Learning:** Correct Tango API parameter names, field fallback patterns

### 2. ✅ pretorin-ai/govbizops (PRIORITY 1)
- **Stars:** 12
- **Language:** Python
- **Value:** Comprehensive SAM.gov library with compliance features
- **Key Learning:** Rate limiting, validation, daily collection limits

### 3. ✅ jjwprotozoa/SAM.gov-Scripts (PRIORITY 2)
- **Stars:** 15
- **Language:** Python
- **Value:** Multiple automation scripts and tools
- **Key Learning:** Various scraping approaches

### 4. ✅ tommycolitsas/sam (PRIORITY 1)
- **Stars:** 3
- **Updated:** Jan 2026 (very recent!)
- **Language:** Python (async)
- **Value:** Bulk URL scraping with async/concurrency
- **Key Learning:** Async patterns, Supabase integration, failed request tracking

### 5. ✅ IncrediblyHungie/sam-gov-scraper (PRIORITY 1)
- **Stars:** 0
- **Language:** Python (Apify Actor)
- **Value:** NO API KEY REQUIRED - uses internal SAM.gov endpoints
- **Key Learning:** Bypass API limits, download attachments, Playwright integration

### 6. ✅ ramfrancis0x1/Beacon (PRIORITY 2)
- **Stars:** 2
- **Updated:** May 2025
- **Language:** Python
- **Value:** Continuous monitoring by NAICS, Linear integration, OpenAI enhancement
- **Key Learning:** Monitoring patterns, AI title generation, project management integration

### 7. ✅ ataddesse/govConDiscovery (PRIORITY 3)
- **Stars:** 5
- **Language:** Python
- **Value:** AI-powered semantic search and recommendations
- **Key Learning:** Semantic search, recommendation algorithms

---

## KEY DISCOVERIES

### Discovery 1: Multiple API Access Methods

| Method | Repo | API Key Required | Rate Limit | Reliability |
|--------|------|------------------|-----------|-------------|
| **Tango API** | capture-mcp-server | ✅ Yes | 25,000/day | HIGH |
| **SAM.gov Official API** | govbizops | ✅ Yes | 100/day | MEDIUM |
| **SAM.gov Internal API** | IncrediblyHungie | ❌ No | Unknown | HIGH |
| **Web Scraping** | tommycolitsas | ❌ No | Self-limited | MEDIUM |

**Best Approach:** Hybrid - Use Tango as primary, Internal API as backup

---

### Discovery 2: Async/Concurrency Patterns (tommycolitsas/sam)

**Technique:** Asyncio + aiohttp for massive parallel requests

```python
class SamScraper:
    def __init__(self, max_concurrent_requests: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def fetch_page(self, page: int):
        async with self.semaphore:  # Rate limiting via semaphore
            async with self.session.get(url, headers=headers) as response:
                return await response.json()
```

**Benefits:**
- 10x faster than sequential requests
- Built-in concurrency control via semaphore
- Automatic retry on failure

**Application to Our Engine:**
```python
# Instead of:
for piid in piids:
    data = query_tango_api(piid)  # Sequential - slow

# Use:
tasks = [query_tango_api_async(piid) for piid in piids]
results = await asyncio.gather(*tasks, return_exceptions=True)  # Parallel - fast
```

---

### Discovery 3: NO API KEY Method (IncrediblyHungie-sam-gov-scraper)

**Critical Finding:** SAM.gov has internal JSON endpoints that don't require API keys!

```python
# Internal API endpoints (NO API KEY REQUIRED):
SAM_SEARCH_URL = "https://sam.gov/api/prod/sgs/v1/search/"
SAM_DETAILS_URL = "https://sam.gov/api/prod/opps/v2/opportunities"
SAM_RESOURCES_URL = "https://sam.gov/api/prod/opps/v3/opportunities"
SAM_DOWNLOAD_URL = "https://sam.gov/api/prod/opps/v3/opportunities/resources/files"

# Headers mimic browser:
JSON_HEADERS = {
    "Accept": "application/hal+json, application/json",
    "Referer": "https://sam.gov/search/",
    "Origin": "https://sam.gov",
    "User-Agent": "Mozilla/5.0..."
}
```

**Benefits:**
- ✅ No API key registration
- ✅ No rate limits (self-imposed only)
- ✅ Downloads attachments (RFPs, SOWs, documents)
- ✅ Real-time data

**Application:** Backup method when Tango API hits limits or for attachment downloads

---

### Discovery 4: Failed Request Tracking (tommycolitsas/sam)

**Pattern:** SQLite database to track and retry failed requests

```python
# Track failures:
cursor.execute('''
    INSERT INTO failed_requests (date_from, date_to, page, error)
    VALUES (?, ?, ?, ?)
''', (date_from, date_to, page, error_msg))

# Retry later:
cursor.execute('''
    SELECT date_from, date_to, page
    FROM failed_requests
    WHERE retry_count < 3
''')
for date_from, date_to, page in failed_requests:
    result = await self.fetch_page(page, date_from, date_to)
    if result:
        # Mark as successful
        cursor.execute('DELETE FROM failed_requests WHERE ...')
```

**Benefits:**
- Never lose data due to transient errors
- Automatic retry with exponential backoff
- Audit trail of issues

**Application to Our Engine:**
```python
# Add failed_requests table:
CREATE TABLE failed_requests (
    piid TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

# Retry after main run:
def retry_failed():
    for piid in get_failed_piids():
        try:
            data = query_tango_api(piid)
            mark_successful(piid)
        except:
            increment_retry_count(piid)
```

---

### Discovery 5: Compliance & Rate Limiting (govbizops/client.py)

**Best Practice:** Built-in compliance checking

```python
class SAMGovClient:
    # Compliance limits
    MAX_NAICS_CODES = 50
    MAX_DAYS_RANGE = 90
    MAX_DAILY_COLLECTIONS = 100

    def _check_daily_limit(self):
        today = datetime.now().date()
        if self._last_collection_date != today:
            self._daily_collections = 0  # Reset
        if self._daily_collections >= self.MAX_DAILY_COLLECTIONS:
            raise ValueError("Daily limit reached")
        self._daily_collections += 1

    def _validate_naics_codes(self, naics_codes):
        if len(naics_codes) > self.MAX_NAICS_CODES:
            raise ValueError(f"Max {self.MAX_NAICS_CODES} NAICS codes")
```

**Benefits:**
- Prevents accidental API abuse
- Self-documenting limits
- Automatic daily reset

**Application to Our Engine:**
```python
class TangoClient:
    MAX_REQUESTS_PER_DAY = 25000  # Large plan
    MAX_REQUESTS_PER_MINUTE = 100

    def __init__(self):
        self.request_counter = 0
        self.minute_counter = 0
        self.minute_start = time.time()

    def _check_rate_limits(self):
        # Per-minute check
        if time.time() - self.minute_start > 60:
            self.minute_counter = 0
            self.minute_start = time.time()

        if self.minute_counter >= self.MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (time.time() - self.minute_start)
            logger.info(f"Rate limit pause: {sleep_time:.1f}s")
            time.sleep(sleep_time)
            self.minute_counter = 0
            self.minute_start = time.time()

        self.minute_counter += 1
        self.request_counter += 1
```

---

### Discovery 6: AI Enhancement (Beacon/main.py)

**Pattern:** OpenAI to improve data quality

```python
def generate_ai_issue_title(listing):
    """Use OpenAI to make titles more actionable"""
    prompt = f"""
    Create actionable title for project management:

    Original: {listing['title']}
    Notice Type: {listing['type']}
    NAICS: {listing['naicsCode']}

    Make it:
    - Clear and actionable
    - Under 80 chars
    - Professional but direct
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

**Application to Our Engine:**
```python
# Enhance program names:
def enhance_program_name(contract: Dict) -> str:
    """Use AI to create better program names from descriptions"""
    description = contract.get('description', '')
    value = contract.get('total_contract_value', 0)
    contractor = contract.get('recipient', {}).get('display_name', '')

    prompt = f"""
    Create a concise program name (max 100 chars) from this federal contract:

    Description: {description}
    Value: ${value:,.0f}
    Prime: {contractor}

    Focus on: What service/capability is being provided
    """

    return call_openai(prompt)
```

---

### Discovery 7: Attachment Download (IncrediblyHungie)

**Critical Capability:** Download actual RFP documents using Playwright

```python
async def download_attachment(browser_context, file_url, file_name):
    """Download attachment via Playwright browser"""
    page = await browser_context.new_page()

    # Start waiting for download
    async with page.expect_download() as download_info:
        await page.goto(file_url)

    download = await download_info.value
    file_bytes = await download.read_all_bytes()

    # Upload to storage or save locally
    await Actor.set_value(f"attachments/{file_name}", file_bytes, 'BINARY')
```

**Application:** Download contract SOWs, PWS, attachments for deeper analysis

---

### Discovery 8: Supabase Integration (tommycolitsas)

**Pattern:** Real-time database sync

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Insert opportunities in batches:
supabase.table('opportunities').upsert(
    [
        {
            'id': opp['_id'],
            'title': opp['title'],
            'posted_date': opp['postedDate'],
            'naics_code': opp['naics'],
            'url': opp['url']
        }
        for opp in opportunities
    ]
).execute()
```

**Benefits:**
- Real-time updates
- Web dashboard can query directly
- Collaborative access

**Application to Our Engine:**
```python
# Replace CSV exports with Supabase:
def save_programs_to_supabase(programs: List[Dict]):
    supabase.table('federal_programs').upsert(programs).execute()

# Enable real-time queries from web app:
SELECT * FROM federal_programs
WHERE contractor_count >= 100
ORDER BY total_value DESC
```

---

## UNIFIED SCRAPER ARCHITECTURE

### Layer 1: Multi-Source Data Acquisition

```python
class FederalProgramsUnifiedScraper:
    def __init__(self):
        self.tango_client = TangoClient(api_key)
        self.sam_internal_client = SAMInternalClient()
        self.sam_api_client = SAMGovClient(api_key)

    async def discover_programs(self, naics_codes: List[str]):
        """Try Tango first, fallback to internal API"""
        try:
            # Primary: Tango API (fast, reliable, 25k/day)
            programs = await self.tango_client.discover(naics_codes)
        except RateLimitError:
            # Fallback: SAM.gov internal API (no limits)
            programs = await self.sam_internal_client.discover(naics_codes)

        return programs
```

### Layer 2: Async Processing Pipeline

```python
async def process_programs_async(piids: List[str]):
    """Process thousands of PIIDs concurrently"""
    semaphore = asyncio.Semaphore(50)  # 50 concurrent requests

    async def fetch_with_limit(piid):
        async with semaphore:
            try:
                return await tango_client.get_contract_async(piid)
            except Exception as e:
                track_failed_request(piid, str(e))
                return None

    tasks = [fetch_with_limit(piid) for piid in piids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failures:
    programs = [r for r in results if r and not isinstance(r, Exception)]

    return programs
```

### Layer 3: Enhanced Data Processing

```python
def enhance_program_data(program: Dict) -> Dict:
    """Enhance with AI, attachments, and enrichment"""

    # 1. AI-enhanced program name:
    program['enhanced_name'] = generate_ai_program_name(program)

    # 2. Download attachments (if available):
    if program.get('has_attachments'):
        program['attachments'] = download_attachments(program['piid'])

    # 3. Get actual subcontractor data:
    program['subcontractors'] = get_subcontractor_details(program['piid'])

    # 4. Identify staffing firms:
    program['staffing_firms'] = identify_staffing_firms(program['subcontractors'])

    return program
```

### Layer 4: Smart Storage

```python
def save_programs(programs: List[Dict], method: str = 'hybrid'):
    """Save to multiple formats"""

    if method in ['hybrid', 'csv']:
        # CSV for Excel users:
        pd.DataFrame(programs).to_csv('programs.csv', index=False)

    if method in ['hybrid', 'database']:
        # Supabase for real-time access:
        supabase.table('federal_programs').upsert(programs).execute()

    if method in ['hybrid', 'json']:
        # JSON for API access:
        with open('programs.json', 'w') as f:
            json.dump(programs, f, indent=2)
```

### Layer 5: Monitoring & Retry

```python
class MonitoringEngine:
    """Continuous monitoring with retry logic"""

    def __init__(self):
        self.db = sqlite3.connect('monitoring.db')
        self.setup_tables()

    def setup_tables(self):
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS failed_requests (
                piid TEXT PRIMARY KEY,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    async def retry_failed_requests(self):
        """Retry failed requests with exponential backoff"""
        cursor = self.db.execute('''
            SELECT piid, retry_count
            FROM failed_requests
            WHERE retry_count < 5
            ORDER BY last_attempt ASC
        ''')

        for piid, retry_count in cursor.fetchall():
            wait_time = 2 ** retry_count  # Exponential backoff
            await asyncio.sleep(wait_time)

            try:
                data = await tango_client.get_contract_async(piid)
                # Success - remove from failed list:
                self.db.execute('DELETE FROM failed_requests WHERE piid = ?', (piid,))
                self.db.commit()
            except Exception as e:
                # Update retry count:
                self.db.execute('''
                    UPDATE failed_requests
                    SET retry_count = retry_count + 1,
                        last_attempt = CURRENT_TIMESTAMP,
                        error = ?
                    WHERE piid = ?
                ''', (str(e), piid))
                self.db.commit()
```

---

## RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Core Engine (Week 1)

```python
# File: unified_federal_programs_scraper.py

class UnifiedScraper:
    """All-in-one federal programs discovery engine"""

    def __init__(self, tango_api_key: str, sam_api_key: Optional[str] = None):
        # Primary: Tango API
        self.tango = TangoClient(tango_api_key)

        # Backup: SAM.gov internal API (no key needed)
        self.sam_internal = SAMInternalClient()

        # Optional: SAM.gov official API
        if sam_api_key:
            self.sam_official = SAMGovClient(sam_api_key)

        # Monitoring & retry
        self.monitoring = MonitoringEngine()

    async def discover_all_programs(
        self,
        naics_codes: List[str],
        min_value: float = 10_000_000,
        min_contractors: int = 100
    ) -> List[Dict]:
        """Discover all qualifying federal programs"""

        # Step 1: Bulk discovery (async)
        contracts = await self.discover_contracts_async(naics_codes)

        # Step 2: Filter by criteria
        qualified = [
            c for c in contracts
            if self.qualifies(c, min_value, min_contractors)
        ]

        # Step 3: Enrich with details (async)
        enriched = await self.enrich_programs_async(qualified)

        # Step 4: Retry any failures
        await self.monitoring.retry_failed_requests()

        return enriched
```

### Phase 2: Advanced Features (Week 2)

1. **AI Enhancement**
   - Program name generation
   - Categorization
   - Opportunity scoring

2. **Attachment Download**
   - SOWs, PWS, RFPs
   - Extract requirements
   - Store in cloud

3. **Monitoring Dashboard**
   - Supabase real-time DB
   - Web interface
   - Alerts on new opportunities

---

## SYNTHESIS: Best Practices Extracted

| Feature | Source Repo | Implementation Priority |
|---------|-------------|------------------------|
| Async/concurrent requests | tommycolitsas/sam | **HIGH** - 10x speed improvement |
| Tango API patterns | capture-mcp-server | **HIGH** - Correct parameters |
| Internal SAM.gov API | IncrediblyHungie | **MEDIUM** - Backup method |
| Failed request tracking | tommycolitsas/sam | **HIGH** - Data integrity |
| Rate limit compliance | govbizops | **HIGH** - Prevent bans |
| AI enhancement | Beacon | **LOW** - Nice to have |
| Attachment download | IncrediblyHungie | **MEDIUM** - Deep analysis |
| Supabase integration | tommycolitsas/sam | **MEDIUM** - Real-time access |

---

## NEXT STEPS

1. **Integrate async patterns** into Discovery Engine V2
2. **Add failed request tracking** with SQLite
3. **Implement dual-source strategy** (Tango + SAM internal)
4. **Add rate limit protection** class
5. **Build monitoring engine** for retries
6. **Optional:** Add AI enhancement layer
7. **Optional:** Add attachment download capability

---

**Status:** Analysis complete
**Repos Cloned:** 7
**Patterns Extracted:** 8 major discoveries
**Next Action:** Build unified scraper incorporating best practices
