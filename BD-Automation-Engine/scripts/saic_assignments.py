"""Find all SAIC contracts/programs that are assigned to someone."""
import sqlite3
import csv
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "master_federal_contracts.db"
CONTACTS_PATH = Path(__file__).parent.parent / "data" / "enriched" / "contacts" / "by_company" / "SAIC_Contacts_Enriched.csv"

def fmt(val):
    if not val: return "N/A"
    if val > 1e9: return f"${val/1e9:.2f}B"
    if val > 1e6: return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"

def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Programs with pts_involvement set
    print("=" * 100)
    print("SAIC PROGRAMS WITH PTS INVOLVEMENT/ASSIGNMENT")
    print("=" * 100)
    c.execute("""
        SELECT program_name, acronym, prime_contractor, pts_involvement,
               priority_level, program_manager, cor_cotr, total_contract_value,
               agency_owner, key_locations
        FROM programs
        WHERE (prime_contractor LIKE '%SAIC%' OR prime_contractor_1 LIKE '%SAIC%'
               OR prime_contractor_consolidated LIKE '%SAIC%' OR recipient_name LIKE '%SAIC%')
        AND pts_involvement IS NOT NULL AND pts_involvement != ''
    """)
    rows = c.fetchall()
    print(f"\nPrograms with pts_involvement: {len(rows)}")
    for r in rows:
        print(f"  {(r['program_name'] or '')[:55]:55s} | {r['acronym'] or '':15s} | involvement={r['pts_involvement']}")
        print(f"    PM: {r['program_manager'] or 'N/A'} | COR: {r['cor_cotr'] or 'N/A'} | Value: {fmt(r['total_contract_value'])}")

    # 2. Jobs with SAIC - these have owners
    print("\n" + "=" * 100)
    print("SAIC JOBS IN PIPELINE (with owner assignments)")
    print("=" * 100)
    c.execute("""
        SELECT title, company, prime, matched_program, owner, contact,
               status, location, clearance, date_posted, pay_rate, bill_rate
        FROM jobs
        WHERE company LIKE '%SAIC%' OR prime LIKE '%SAIC%'
        ORDER BY date_posted DESC
    """)
    rows = c.fetchall()
    print(f"\nTotal SAIC jobs: {len(rows)}")
    for r in rows:
        title = (r['title'] or '')[:40]
        owner = r['owner'] or 'UNASSIGNED'
        contact = r['contact'] or ''
        prog = r['matched_program'] or ''
        status = r['status'] or ''
        loc = r['location'] or ''
        clear = r['clearance'] or ''
        bill = r['bill_rate'] or 0
        pay = r['pay_rate'] or 0
        print(f"  {title:40s} | OWNER: {owner:18s} | contact: {contact[:20]:20s}")
        print(f"    program: {prog[:30]:30s} | status: {status:10s} | loc: {loc[:25]} | clear: {clear[:15]} | bill=${bill:.0f} pay=${pay:.0f}")
        print()

    # 3. Placements at SAIC
    print("=" * 100)
    print("SAIC PLACEMENTS (active revenue)")
    print("=" * 100)
    c.execute("""
        SELECT job_title, program_name, candidate_name, owner, client_name,
               start_date, end_date, status, bill_rate, pay_rate, spread,
               estimated_revenue
        FROM placements
        WHERE client_name LIKE '%SAIC%'
        ORDER BY start_date DESC
    """)
    rows = c.fetchall()
    print(f"\nTotal SAIC placements: {len(rows)}")
    for r in rows:
        print(f"  {r['job_title'] or '':30s} | owner: {r['owner'] or 'N/A':15s} | program: {r['program_name'] or '':20s} | status: {r['status'] or ''}")
        print(f"    candidate: {r['candidate_name'] or ''} | bill=${r['bill_rate'] or 0:.0f} pay=${r['pay_rate'] or 0:.0f} spread=${r['spread'] or 0:.0f} | start: {r['start_date'] or ''}")

    # 4. Who is working SAIC contacts - from activities
    print("\n" + "=" * 100)
    print("PTS RECRUITERS WORKING SAIC CONTACTS (from call notes)")
    print("=" * 100)

    # Get SAIC contact names from enriched file
    saic_names = set()
    if CONTACTS_PATH.exists():
        with open(CONTACTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Name', '').strip()
                if name:
                    saic_names.add(name)

    print(f"\nSAIC contacts in enriched file: {len(saic_names)}")

    # Check who authored notes about SAIC contacts
    if saic_names:
        # Build query with parameterized IN clause
        placeholders = ','.join(['?' for _ in saic_names])
        c.execute(f"""
            SELECT actor, COUNT(*) as note_count,
                   COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring_signals,
                   COUNT(CASE WHEN traction = 1 THEN 1 END) as traction_count,
                   COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive_count,
                   MAX(activity_date) as last_activity,
                   GROUP_CONCAT(DISTINCT about) as contacts_worked
            FROM activities
            WHERE about IN ({placeholders})
            GROUP BY actor
            ORDER BY note_count DESC
        """, list(saic_names))
        rows = c.fetchall()
        print(f"\nRecruiters with notes on SAIC contacts: {len(rows)}")
        for r in rows:
            actor = r['actor'] or 'UNKNOWN'
            contacts_list = (r['contacts_worked'] or '')[:80]
            print(f"\n  {actor:20s} | {r['note_count']:4d} notes | hiring={r['hiring_signals']} | traction={r['traction_count']} | positive={r['positive_count']} | last={r['last_activity'] or ''}")
            print(f"    Contacts worked: {contacts_list}")

    # 5. Enriched contacts - who are the Authors (recruiters who own the relationship)
    print("\n" + "=" * 100)
    print("SAIC CONTACT OWNERSHIP (from enriched contacts 'Authors' field)")
    print("=" * 100)

    author_map = {}  # author -> list of contacts
    if CONTACTS_PATH.exists():
        with open(CONTACTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                authors = row.get('Authors', '').strip()
                name = row.get('Name', '').strip()
                tier = row.get('Tier', '')
                prog = row.get('Programs', '')
                if authors:
                    for author in authors.split(','):
                        author = author.strip()
                        if author:
                            if author not in author_map:
                                author_map[author] = []
                            author_map[author].append({
                                'name': name,
                                'tier': tier,
                                'programs': prog,
                                'title': row.get('Primary Title', ''),
                                'notes': row.get('Note Count', '0'),
                                'last': row.get('Last Activity', ''),
                                'hm': row.get('Is Hiring Manager', ''),
                                'dm': row.get('Is Decision Maker', ''),
                            })

    print(f"\nRecruiters assigned to SAIC contacts: {len(author_map)}")
    for author in sorted(author_map.keys(), key=lambda a: -len(author_map[a])):
        contacts = author_map[author]
        t1 = sum(1 for c in contacts if 'Tier 1' in c['tier'])
        t2 = sum(1 for c in contacts if 'Tier 2' in c['tier'])
        hms = sum(1 for c in contacts if c['hm'].lower() in ('yes', 'true', '1'))
        dms = sum(1 for c in contacts if c['dm'].lower() in ('yes', 'true', '1'))
        progs = set()
        for c in contacts:
            for p in c['programs'].split(','):
                p = p.strip()
                if p:
                    progs.add(p)

        print(f"\n  {author:25s} | {len(contacts):3d} contacts | T1={t1:2d} T2={t2:2d} | HMs={hms:3d} DMs={dms:2d}")
        print(f"    Programs: {', '.join(sorted(progs)[:8])}")

        # Show their top 5 contacts
        top = sorted(contacts, key=lambda c: -int(c['notes'] or 0))[:5]
        for c in top:
            print(f"      -> {c['name'][:25]:25s} | {c['tier'][:20]:20s} | {c['title'][:25]:25s} | {c['programs'][:30]} | notes={c['notes']}")

    conn.close()

if __name__ == "__main__":
    run()
