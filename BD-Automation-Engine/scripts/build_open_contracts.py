"""
Build Open Contracts Spreadsheet
---------------------------------
Cross-references ALL federal contract data sources against the master target list
to find unassigned open opportunities.

Data sources:
1. master_federal_contracts.db (8,813 programs)
2. WARM_GREENFIELD_ENRICHED.csv (50 warm/greenfield opportunities)
3. bd_targets.csv (260 BD targets with recompete dates)
4. contract_timeline.csv (254 contracts with PoP dates)
5. programs_with_contracts.csv (257 programs with contract numbers)
6. Bullhorn placement_program_links (1,611 links)
7. Bullhorn gap_analysis (from bullhorn_master.db)
8. PROGRAM_PLACEMENT_GAP_ANALYSIS_20260122.csv (41 gap programs)
9. Federal Programs MASTER V4.csv (257 programs)

Output: outputs/open_contracts_UNASSIGNED.csv
"""

import csv
import logging
import sqlite3
import os
import re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 1. Load the master target list (all assigned programs) ──────────────
assigned_acronyms = set()
assigned_names = set()
assigned_entries = []  # (person, acronym, full_name, prime)

roster_path = os.path.join(BASE, 'outputs', 'contract_assignments_CORRECTED.csv')
with open(roster_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        acr = (row.get('Corrected Acronym') or '').strip()
        full = (row.get('Full Program Name') or '').strip()
        prime = (row.get('Prime Contractor') or '').strip()
        person = (row.get('Person') or '').strip()
        if acr:
            assigned_acronyms.add(acr.upper())
            # Add normalized variants
            assigned_acronyms.add(acr.upper().replace(' ', ''))
            assigned_acronyms.add(acr.upper().replace('-', ''))
            assigned_acronyms.add(acr.upper().replace(' ', '-'))
        if full:
            assigned_names.add(full.upper())
        assigned_entries.append((person, acr, full, prime))

# Add known aliases for assigned programs
aliases = {
    'GBSD': 'SENTINEL',           # Ground-Based Strategic Deterrent = Sentinel
    'GBSD / SENTINEL': 'SENTINEL',
    'MQ-25': 'MQ-25 STINGRAY',    # MQ-25 is assigned as MQ-25 STINGRAY
    'SLS': 'BOEING ESS',          # SLS overlap with Boeing ESS
    'F-35': 'F-35 CYBER',         # F-35 general overlaps with F-35 Cyber assigned
}
for alias in aliases:
    assigned_acronyms.add(alias.upper())

print(f"Loaded {len(assigned_entries)} assigned entries, {len(assigned_acronyms)} unique acronym variants")


def normalize(s):
    """Normalize a string for matching."""
    if not s:
        return ''
    return re.sub(r'[^A-Z0-9]', '', s.upper())


def is_assigned(acronym, program_name='', prime=''):
    """Check if a program is already on someone's target list."""
    acr_up = (acronym or '').strip().upper()
    name_up = (program_name or '').strip().upper()

    # Direct acronym match
    if acr_up and acr_up in assigned_acronyms:
        return True

    # Normalized acronym match
    acr_norm = normalize(acronym)
    if acr_norm and any(normalize(a) == acr_norm for a in assigned_acronyms):
        return True

    # Full name match
    if name_up and name_up in assigned_names:
        return True

    # Check if acronym is a substring of any assigned entry or vice versa
    # e.g. "GSMO" matches "GSMO TN01"
    for aa in assigned_acronyms:
        if len(acr_up) >= 3 and len(aa) >= 3:
            if acr_up == aa:
                return True
            # Check if the base program is assigned (e.g., GSMO covers GSMO TN01)
            # But don't match overly generic ones

    # Check combined prime+program match for things like "GDIT ADCS"
    if prime and acr_up:
        combo = f"{prime.upper()} {acr_up}"
        for aa in assigned_acronyms:
            if aa == combo or combo == aa:
                return True

    # Check if open program is a variant/extension of assigned program
    # e.g., "SENTINEL CYBER" should match assigned "SENTINEL"
    #        "BICES-X" should match assigned "BICES"
    #        "DLA JETS 2.0" should match assigned "DLA JETS"
    #        "GENMOD/VMOD" matches assigned "GENMOD" or "VMOD"
    if acr_up:
        for aa in assigned_acronyms:
            if len(aa) >= 3:
                # Assigned is a prefix of open (SENTINEL -> SENTINEL CYBER)
                if acr_up.startswith(aa + ' ') or acr_up.startswith(aa + '-') or acr_up.startswith(aa + '/'):
                    return True
                # Open contains assigned as a component (GENMOD/VMOD -> GENMOD)
                if '/' in acr_up:
                    parts = [p.strip() for p in acr_up.split('/')]
                    if aa in parts:
                        return True
                # Assigned is the base and open adds a version/TO (JETS -> JETS 2.0, BIM -> BIM TO2)
                if acr_up.startswith(aa) and len(acr_up) > len(aa):
                    suffix = acr_up[len(aa):].strip()
                    if suffix and (suffix[0].isdigit() or suffix.startswith('TO') or
                                   suffix.startswith('II') or suffix.startswith('2') or
                                   suffix.startswith('3') or suffix.startswith('CYBER')):
                        return True

    # Check if program_name contains an assigned acronym in a meaningful way
    if name_up:
        for aa in assigned_acronyms:
            if len(aa) >= 4:
                # Full word boundary match in name
                import re
                if re.search(r'\b' + re.escape(aa) + r'\b', name_up):
                    return True

    return False


# ── 2. Gather ALL federal contracts from all sources ────────────────────

all_opportunities = {}  # key -> dict of program details


def make_key(acronym, program_name, prime=''):
    """Create a dedup key."""
    acr = normalize(acronym)
    if acr and len(acr) >= 2:
        return acr
    name = normalize(program_name)
    if name:
        return name[:40]
    return None


def parse_money(val):
    """Parse dollar strings to float."""
    if not val:
        return 0.0
    val = str(val).replace('$', '').replace(',', '').replace(' ', '')
    # Handle "261M" format
    m = re.match(r'^([\d.]+)([BMKbmk]?)$', val)
    if m:
        num = float(m.group(1))
        suffix = m.group(2).upper()
        if suffix == 'B':
            return num * 1_000_000_000
        elif suffix == 'M':
            return num * 1_000_000
        elif suffix == 'K':
            return num * 1_000
        return num
    try:
        return float(val)
    except (ValueError, TypeError):
        logging.warning(f"Could not parse dollar value: {val!r} — returning None")
        return None


def merge_opp(key, data):
    """Merge opportunity data, preferring non-empty values."""
    if key not in all_opportunities:
        all_opportunities[key] = data
        return
    existing = all_opportunities[key]
    for k, v in data.items():
        if v and (not existing.get(k) or existing[k] in ('', 'Unknown', '0', '$0', None)):
            existing[k] = v


# ── Source 1: master_federal_contracts.db ──────────────────────────────
print("\n[1] Loading master_federal_contracts.db...")
db_path = os.path.join(BASE, 'data', 'master_federal_contracts.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''SELECT program_name, acronym, agency_owner, prime_contractor_consolidated,
             contract_number, contract_value_consolidated, total_contract_value,
             pop_start_consolidated, pop_end_consolidated, ultimate_completion_consolidated,
             recompete_date, clearance_requirements, key_locations, typical_roles,
             naics_code_consolidated, set_aside, priority_level, confidence_level,
             pts_involvement, subawards_total, subawards_count, obligated,
             functional_areas, match_confidence, contract_vehicle_type, recipient_name
             FROM programs''')

db_count = 0
db_skipped = 0
for row in c.fetchall():
    (name, acr, agency, prime, contract_num, value_consol, total_value,
     pop_start, pop_end, ultimate_end, recompete, clearance, locations, roles,
     naics, set_aside, priority, confidence, pts_inv, sub_total, sub_count,
     obligated, func_areas, match_conf, vehicle_type, recipient) = row

    # Use best available value
    value = value_consol or total_value or 0
    if isinstance(value, str):
        value = parse_money(value)

    # Skip programs with no real data
    if not name and not acr:
        continue

    key = make_key(acr, name)
    if not key:
        continue

    if is_assigned(acr, name, prime):
        db_skipped += 1
        continue

    db_count += 1
    merge_opp(key, {
        'acronym': acr or '',
        'program_name': name or '',
        'agency': agency or '',
        'prime_contractor': prime or recipient or '',
        'contract_number': contract_num or '',
        'contract_value': value,
        'obligated_amount': obligated or 0,
        'pop_start': pop_start or '',
        'pop_end': pop_end or '',
        'ultimate_completion': ultimate_end or '',
        'recompete_date': recompete or '',
        'clearance': clearance or '',
        'locations': locations or '',
        'typical_roles': roles or '',
        'naics': naics or '',
        'set_aside': set_aside or '',
        'priority': priority or '',
        'confidence': confidence or match_conf or '',
        'pts_involvement': pts_inv or '',
        'subaward_total': sub_total or 0,
        'subaward_count': sub_count or 0,
        'vehicle_type': vehicle_type or '',
        'source': 'master_db',
    })

print(f"  {db_count} unassigned programs loaded, {db_skipped} already assigned")


# ── Source 2: WARM_GREENFIELD_ENRICHED.csv ─────────────────────────────
print("\n[2] Loading WARM_GREENFIELD_ENRICHED.csv...")
wg_path = os.path.join(BASE, 'WARM_GREENFIELD_ENRICHED.csv')
wg_count = 0
with open(wg_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        acr = row.get('acronym', '')
        name = row.get('program_name', '')
        prime = row.get('prime_contractor', '')

        if is_assigned(acr, name, prime):
            continue

        key = make_key(acr, name)
        if not key:
            continue

        wg_count += 1
        merge_opp(key, {
            'acronym': acr,
            'program_name': name,
            'agency': row.get('agency', ''),
            'prime_contractor': prime,
            'contract_number': row.get('piid', ''),
            'contract_value': parse_money(row.get('total_contract_value', '')),
            'obligated_amount': parse_money(row.get('obligated_amount', '')),
            'pop_start': row.get('pop_start', ''),
            'pop_end': row.get('pop_current_end', ''),
            'ultimate_completion': row.get('pop_ultimate_end', ''),
            'recompete_date': row.get('recompete_date', ''),
            'clearance': row.get('clearance_requirements', ''),
            'locations': row.get('performance_location', '') or row.get('key_locations', ''),
            'typical_roles': row.get('typical_roles', ''),
            'bd_score': row.get('bd_score', ''),
            'greenfield_type': row.get('greenfield_type', ''),
            'source': 'warm_greenfield',
        })

print(f"  {wg_count} unassigned greenfield opportunities")


# ── Source 3: bd_targets.csv ───────────────────────────────────────────
print("\n[3] Loading bd_targets.csv...")
bd_path = os.path.join(BASE, 'docs', 'N8N-Builder.Capture-MCP-server', 'bd_targets.csv')
bd_count = 0
with open(bd_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        acr = row.get('Acronym', '')
        name = row.get('Program Name', '')
        prime = row.get('Prime Contractor', '')

        if is_assigned(acr, name, prime):
            continue

        key = make_key(acr, name)
        if not key:
            continue

        bd_count += 1
        merge_opp(key, {
            'acronym': acr,
            'program_name': name,
            'agency': row.get('Agency', ''),
            'prime_contractor': prime,
            'contract_value': parse_money(row.get('Contract Value', '')),
            'recompete_date': row.get('Recompete Date', ''),
            'pop_end': row.get('Period of Performance', ''),
            'bd_priority': row.get('BD Priority', ''),
            'source': 'bd_targets',
        })

print(f"  {bd_count} unassigned BD targets")


# ── Source 4: contract_timeline.csv ────────────────────────────────────
print("\n[4] Loading contract_timeline.csv...")
ct_path = os.path.join(BASE, 'docs', 'N8N-Builder.Capture-MCP-server', 'contract_timeline.csv')
ct_count = 0
with open(ct_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        acr = row.get('Acronym', '')
        name = row.get('Program Name', '')

        key = make_key(acr, name)
        if not key or key not in all_opportunities:
            continue

        # Enrich existing entries with timeline data
        ct_count += 1
        opp = all_opportunities[key]
        if not opp.get('pop_start') and row.get('Period Start'):
            opp['pop_start'] = row['Period Start']
        if not opp.get('pop_end') and row.get('Period End'):
            opp['pop_end'] = row['Period End']
        if not opp.get('ultimate_completion') and row.get('Ultimate Completion'):
            opp['ultimate_completion'] = row['Ultimate Completion']
        if not opp.get('contract_number') and row.get('Contract Number'):
            opp['contract_number'] = row['Contract Number']

print(f"  Enriched {ct_count} entries with timeline data")


# ── Source 5: Bullhorn placement_program_links ─────────────────────────
print("\n[5] Loading Bullhorn placement data...")
bh_path = os.path.join(BASE, 'Engine7_BullhornETL', 'data', 'bullhorn_master.db')
bh_conn = sqlite3.connect(bh_path)
bh_c = bh_conn.cursor()

# Get placement counts by program
bh_c.execute('''SELECT program_acronym, program_name, COUNT(*) as cnt
                FROM placement_program_links
                GROUP BY program_acronym, program_name''')

bh_placements = {}
for acr, name, cnt in bh_c.fetchall():
    key = make_key(acr, name)
    if key:
        bh_placements[key] = (acr, name, cnt)

# Get call note counts by program mention
bh_c.execute('''SELECT programs_mentioned, COUNT(*) as cnt
                FROM call_notes
                WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''
                GROUP BY programs_mentioned''')

bh_mentions = defaultdict(int)
for prog, cnt in bh_c.fetchall():
    if prog:
        for p in prog.split(','):
            p = p.strip()
            if p:
                bh_mentions[normalize(p)] += cnt

bh_conn.close()

# Annotate opportunities with Bullhorn data
bh_enriched = 0
for key, opp in all_opportunities.items():
    if key in bh_placements:
        _, _, cnt = bh_placements[key]
        opp['bullhorn_placements'] = cnt
        bh_enriched += 1

    mention_count = bh_mentions.get(key, 0)
    if mention_count:
        opp['bullhorn_mentions'] = mention_count

print(f"  Enriched {bh_enriched} opportunities with Bullhorn placement data")


# ── Source 6: Gap analysis ─────────────────────────────────────────────
print("\n[6] Loading gap analysis...")
gap_path = os.path.join(BASE, 'outputs', 'PROGRAM_PLACEMENT_GAP_ANALYSIS_20260122.csv')
gap_count = 0
with open(gap_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        prog = row.get('Program', '')
        prime = row.get('Prime', '')

        key = make_key(prog, prog)
        if key and key in all_opportunities:
            opp = all_opportunities[key]
            opp['gap_status'] = row.get('Gap_Status', '')
            opp['gap_placements'] = row.get('Placements', '')
            opp['gap_revenue_est'] = row.get('Revenue_Est', '')
            opp['gap_call_mentions'] = row.get('Call_Mentions', '')
            gap_count += 1

print(f"  Enriched {gap_count} entries with gap analysis data")


# ── Source 7: Contracts table for extra PIID/value data ────────────────
print("\n[7] Loading contracts table for extra enrichment...")
c.execute('''SELECT program_name, piid, award_amount, obligated, recipient_name,
             award_date, pop_start, pop_end
             FROM contracts
             WHERE award_amount > 0
             ORDER BY award_amount DESC''')

contracts_enriched = 0
for name, piid, amount, oblig, recipient, award_date, p_start, p_end in c.fetchall():
    key = make_key('', name)
    if key and key in all_opportunities:
        opp = all_opportunities[key]
        if amount and (not opp.get('contract_value') or opp['contract_value'] == 0):
            opp['contract_value'] = amount
        contracts_enriched += 1

print(f"  Enriched {contracts_enriched} entries from contracts table")

# ── Source 8: Scoring table for BD scores ──────────────────────────────
print("\n[8] Loading BD scoring data...")
c.execute('''SELECT entity_name, bd_score, priority_tier, engagement_score,
             contract_score, recompete_proximity_score
             FROM scoring
             WHERE entity_type = 'program' AND bd_score > 0
             ORDER BY bd_score DESC''')

scores_enriched = 0
for name, bd_score, tier, engage, contract_sc, recompete_sc in c.fetchall():
    key = make_key('', name)
    if key and key in all_opportunities:
        opp = all_opportunities[key]
        opp['bd_score'] = opp.get('bd_score') or bd_score
        opp['priority_tier'] = opp.get('priority_tier') or tier
        scores_enriched += 1

print(f"  Enriched {scores_enriched} entries with BD scores")

conn.close()


# ── Filter and rank ────────────────────────────────────────────────────
print(f"\n[TOTAL] {len(all_opportunities)} unique unassigned opportunities found")

# Filter to actionable opportunities only
# Must have at least ONE of: contract value, PoP dates, Bullhorn activity, BD score
filtered = {}
for key, opp in all_opportunities.items():
    # Must have at least a name or acronym
    if not opp.get('acronym') and not opp.get('program_name'):
        continue

    # Skip if name is just a generic description
    name = opp.get('program_name', '')
    acr_check = opp.get('acronym', '')
    if len(name) > 100 and not acr_check:
        continue

    # Filter out junk/noise entries - common English words, fragments
    junk_words = {'best', 'missile', 'nasa', 'idiq', 'vehicle', 'term', 'year',
                  'their', 'these', 'that', 'for the', 'cloud', 'the', 'and',
                  'this', 'with', 'from', 'will', 'have', 'been', 'also', 'each',
                  'other', 'more', 'than', 'about', 'only', 'some', 'into',
                  'over', 'such', 'make', 'like', 'just', 'its', 'our', 'his',
                  'her', 'not', 'but', 'all', 'can', 'had', 'one', 'may', 'was',
                  'are', 'who', 'did', 'get', 'has', 'him', 'how', 'man', 'new',
                  'now', 'old', 'see', 'way', 'day', 'too', 'use', 'end',
                  'key', 'per', 'based', 'sls', 'orion'}
    check_val = (acr_check or name).strip().lower()
    if check_val in junk_words:
        continue
    # Skip entries that are just 1-3 character generic strings without an acronym
    if not acr_check and len(name.strip()) <= 3:
        continue

    # Must have at least ONE signal of being a real actionable opportunity
    has_value = (opp.get('contract_value') or 0) > 0
    has_pop = bool(opp.get('pop_end') or opp.get('ultimate_completion') or opp.get('recompete_date'))
    has_bullhorn = bool(opp.get('bullhorn_placements') or opp.get('bullhorn_mentions'))
    has_bd = bool(opp.get('bd_score') or opp.get('bd_priority') or opp.get('priority'))
    has_greenfield = bool(opp.get('greenfield_type'))
    has_gap = bool(opp.get('gap_status'))
    has_roles = bool(opp.get('typical_roles'))
    has_clearance = bool(opp.get('clearance'))
    has_locations = bool(opp.get('locations'))

    # Need at least 2 signals, OR a contract value, OR Bullhorn placements
    signals = sum([has_value, has_pop, has_bullhorn, has_bd, has_greenfield,
                   has_gap, has_roles, has_clearance, has_locations])

    if has_value or has_bullhorn or has_greenfield or has_gap or signals >= 2:
        filtered[key] = opp

print(f"After filtering to actionable opportunities: {len(filtered)}")

# Sort by contract value descending, then by BD score
sorted_opps = sorted(
    filtered.values(),
    key=lambda x: (
        -(x.get('contract_value') or 0),
        -(float(x.get('bd_score') or 0) if str(x.get('bd_score', '')).replace('.','').isdigit() else 0),
        -(x.get('bullhorn_placements') or 0),
    )
)


# ── Write output CSV ──────────────────────────────────────────────────
def fmt_money(val):
    """Format a dollar amount."""
    if not val or val == 0:
        return ''
    try:
        val = float(val)
        if val >= 1_000_000_000:
            return f"${val/1_000_000_000:.2f}B"
        elif val >= 1_000_000:
            return f"${val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val/1_000:.0f}K"
        else:
            return f"${val:.0f}"
    except:
        return str(val)


output_path = os.path.join(BASE, 'outputs', 'open_contracts_UNASSIGNED.csv')
os.makedirs(os.path.dirname(output_path), exist_ok=True)

headers = [
    'Rank',
    'Acronym',
    'Program Name',
    'Prime Contractor',
    'Agency',
    'Contract Value',
    'Obligated Amount',
    'Contract Number',
    'PoP Start',
    'PoP End',
    'Ultimate Completion',
    'Recompete Date',
    'Clearance',
    'Locations',
    'Typical Roles',
    'BD Score',
    'BD Priority',
    'Greenfield Type',
    'Bullhorn Placements',
    'Bullhorn Mentions',
    'Gap Status',
    'NAICS',
    'Set Aside',
    'Vehicle Type',
    'Subaward Total',
    'Subaward Count',
    'Data Source',
]

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)

    for i, opp in enumerate(sorted_opps, 1):
        writer.writerow([
            i,
            opp.get('acronym', ''),
            opp.get('program_name', ''),
            opp.get('prime_contractor', ''),
            opp.get('agency', ''),
            fmt_money(opp.get('contract_value', 0)),
            fmt_money(opp.get('obligated_amount', 0)),
            opp.get('contract_number', ''),
            opp.get('pop_start', ''),
            opp.get('pop_end', ''),
            opp.get('ultimate_completion', ''),
            opp.get('recompete_date', ''),
            opp.get('clearance', ''),
            opp.get('locations', ''),
            opp.get('typical_roles', ''),
            opp.get('bd_score', ''),
            opp.get('bd_priority', '') or opp.get('priority', ''),
            opp.get('greenfield_type', ''),
            opp.get('bullhorn_placements', ''),
            opp.get('bullhorn_mentions', ''),
            opp.get('gap_status', ''),
            opp.get('naics', ''),
            opp.get('set_aside', ''),
            opp.get('vehicle_type', ''),
            fmt_money(opp.get('subaward_total', 0)),
            opp.get('subaward_count', ''),
            opp.get('source', ''),
        ])

print(f"\nOutput written to: {output_path}")
print(f"Total open opportunities: {len(sorted_opps)}")

# Print summary stats
has_value = sum(1 for o in sorted_opps if (o.get('contract_value') or 0) > 0)
has_pop = sum(1 for o in sorted_opps if o.get('pop_end') or o.get('ultimate_completion'))
has_bh = sum(1 for o in sorted_opps if o.get('bullhorn_placements'))
total_value = sum(o.get('contract_value', 0) or 0 for o in sorted_opps)
print(f"\nWith contract value: {has_value}")
print(f"With PoP dates: {has_pop}")
print(f"With Bullhorn placements: {has_bh}")
print(f"Total addressable value: {fmt_money(total_value)}")

# Print top 25
print(f"\n{'='*100}")
print(f"TOP 25 UNASSIGNED OPEN OPPORTUNITIES BY CONTRACT VALUE")
print(f"{'='*100}")
print(f"{'#':<4} {'Acronym':<20} {'Prime':<25} {'Agency':<20} {'Value':<15} {'PoP End':<12} {'BH Place':<10}")
print(f"{'-'*4} {'-'*20} {'-'*25} {'-'*20} {'-'*15} {'-'*12} {'-'*10}")
for i, opp in enumerate(sorted_opps[:25], 1):
    acr = (opp.get('acronym') or opp.get('program_name', ''))[:19]
    prime = (opp.get('prime_contractor') or '')[:24]
    agency = (opp.get('agency') or '')[:19]
    val = fmt_money(opp.get('contract_value', 0))
    pop = (opp.get('ultimate_completion') or opp.get('pop_end') or '')[:11]
    bh = opp.get('bullhorn_placements', '')
    print(f"{i:<4} {acr:<20} {prime:<25} {agency:<20} {val:<15} {pop:<12} {bh:<10}")
