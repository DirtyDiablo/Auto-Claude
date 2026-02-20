"""SAIC Navy/Air Force/Army Opportunity Analysis"""
import sqlite3
import csv
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "master_federal_contracts.db"

def format_value(val):
    if not val: return "N/A"
    if val > 1e9: return f"${val/1e9:.2f}B"
    if val > 1e6: return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"

def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    branches = {
        "NAVY": ["%Navy%", "%Naval%", "%NAWC%", "%NAVSEA%", "%NAVAIR%", "%NGEN%", "%SPAWAR%", "%NIWC%", "%ONR%", "%USMC%", "%Marine%"],
        "AIR_FORCE": ["%Air Force%", "%USAF%", "%AFLCMC%", "%AFMC%", "%ACC%", "%AFSOC%", "%AFGSC%", "%AFNCR%", "%AETC%", "%Eglin%", "%Wright-Patterson%", "%Langley%", "%Hanscom%"],
        "ARMY": ["%Army%", "%INSCOM%", "%CECOM%", "%PEO%", "%FORSCOM%", "%TRADOC%", "%AMC%", "%ARCYBER%", "%Fort%", "%Aberdeen%"],
    }

    all_results = {}

    # 1. PROGRAMS BY BRANCH
    print("=" * 100)
    print("SAIC PROGRAMS BY MILITARY BRANCH")
    print("=" * 100)

    for branch, patterns in branches.items():
        # Search across agency, description, program name, and locations
        conditions = []
        params = []
        for p in patterns:
            conditions.append("p.agency_owner LIKE ?")
            params.append(p)
        for p in patterns:
            conditions.append("p.program_name LIKE ?")
            params.append(p)
        for p in patterns:
            conditions.append("p.description LIKE ?")
            params.append(p)
        for p in patterns:
            conditions.append("p.key_locations LIKE ?")
            params.append(p)

        where = " OR ".join(conditions)

        q = f"""
            SELECT p.id, p.program_name, p.acronym, p.agency_owner, p.prime_contractor,
                   p.total_contract_value, p.contract_value_consolidated,
                   p.pop_start_consolidated, p.pop_end_consolidated,
                   p.recompete_date, p.ultimate_completion,
                   p.clearance_requirements, p.key_locations,
                   p.priority_level, p.pts_involvement,
                   p.functional_areas, p.typical_roles,
                   p.naics_code, p.technical_stack, p.description
            FROM programs p
            WHERE (p.prime_contractor LIKE '%SAIC%' OR p.prime_contractor_1 LIKE '%SAIC%'
                   OR p.prime_contractor_consolidated LIKE '%SAIC%' OR p.recipient_name LIKE '%SAIC%')
            AND ({where})
            ORDER BY COALESCE(p.total_contract_value, p.contract_value_consolidated, 0) DESC
        """

        c.execute(q, params)
        rows = c.fetchall()
        all_results[branch] = rows

        print(f"\n--- {branch}: {len(rows)} SAIC programs ---")
        for r in rows:
            val = r["total_contract_value"] or r["contract_value_consolidated"] or 0
            name = (r["program_name"] or "")[:60]
            acr = (r["acronym"] or "")[:15]
            agency = (r["agency_owner"] or "")[:20]
            pri = r["priority_level"] or ""
            loc = str(r["key_locations"] or "")[:35]
            roles = str(r["typical_roles"] or "")[:40]
            clear = str(r["clearance_requirements"] or "")[:15]
            print(f"  {name:60s} | {acr:15s} | {format_value(val):>12s} | {agency:20s} | pri={pri:6s} | {clear:15s} | {loc}")

    # 2. SAIC CONTACTS
    print("\n" + "=" * 100)
    print("SAIC CONTACTS IN CRM")
    print("=" * 100)

    c.execute("SELECT COUNT(*) FROM contacts WHERE company LIKE '%SAIC%'")
    total = c.fetchone()[0]
    print(f"\nTotal SAIC contacts: {total}")

    c.execute("SELECT tier, COUNT(*) FROM contacts WHERE company LIKE '%SAIC%' GROUP BY tier ORDER BY tier")
    for r in c.fetchall():
        print(f"  Tier {r[0]}: {r[1]}")

    c.execute("""
        SELECT full_name, title, tier, program, bd_priority, relationship_status,
               note_count, last_activity, is_hiring_manager, is_decision_maker, email
        FROM contacts
        WHERE company LIKE '%SAIC%'
        ORDER BY COALESCE(tier, 99), COALESCE(note_count, 0) DESC
        LIMIT 40
    """)
    print("\nTop 40 SAIC contacts by tier + activity:")
    for r in c.fetchall():
        name = (r["full_name"] or "")[:25]
        title = (r["title"] or "")[:35]
        prog = (r["program"] or "")[:20]
        tier = r["tier"] or "?"
        notes = r["note_count"] or 0
        hm = "HM" if r["is_hiring_manager"] else "  "
        dm = "DM" if r["is_decision_maker"] else "  "
        last = (r["last_activity"] or "")[:10]
        print(f"  T{tier} | {name:25s} | {title:35s} | {prog:20s} | notes={notes:3d} | {hm} {dm} | last={last}")

    # 3. SAIC CONTRACTS (FPDS)
    print("\n" + "=" * 100)
    print("SAIC FEDERAL CONTRACTS BY BRANCH")
    print("=" * 100)

    for branch, patterns in branches.items():
        conditions = []
        params = []
        for p in patterns:
            conditions.append("c.awarding_agency LIKE ?")
            params.append(p)
        for p in patterns:
            conditions.append("c.funding_agency LIKE ?")
            params.append(p)
        for p in patterns:
            conditions.append("c.description LIKE ?")
            params.append(p)
        where = " OR ".join(conditions)

        c.execute(f"""
            SELECT c.piid, c.description, c.awarding_agency, c.award_amount,
                   c.total_contract_value, c.start_date, c.end_date,
                   c.pop_city, c.pop_state, c.naics_code
            FROM contracts c
            WHERE (c.recipient_name LIKE '%SAIC%' OR c.prime_search LIKE '%SAIC%')
            AND ({where})
            ORDER BY COALESCE(c.total_contract_value, c.award_amount, 0) DESC
            LIMIT 25
        """, params)
        rows = c.fetchall()
        print(f"\n--- {branch}: {len(rows)} SAIC contracts ---")
        for r in rows:
            val = r["total_contract_value"] or r["award_amount"] or 0
            piid = (r["piid"] or "")[:22]
            desc = (r["description"] or "")[:55]
            agency = (r["awarding_agency"] or "")[:25]
            end = r["end_date"] or ""
            loc = f"{r['pop_city'] or ''}, {r['pop_state'] or ''}"[:20]
            print(f"  {piid:22s} | {desc:55s} | {format_value(val):>10s} | {agency:25s} | end={end} | {loc}")

    # 4. SAIC PLACEMENTS
    print("\n" + "=" * 100)
    print("SAIC PLACEMENTS (Revenue History)")
    print("=" * 100)

    c.execute("SELECT COUNT(*) FROM placements WHERE client_name LIKE '%SAIC%'")
    print(f"\nTotal SAIC placements: {c.fetchone()[0]}")

    c.execute("""
        SELECT job_title, program_name, start_date, end_date, status,
               bill_rate, pay_rate, spread, estimated_revenue
        FROM placements WHERE client_name LIKE '%SAIC%'
        ORDER BY start_date DESC LIMIT 20
    """)
    for r in c.fetchall():
        title = (r["job_title"] or "")[:30]
        prog = (r["program_name"] or "")[:25]
        start = (r["start_date"] or "")[:10]
        bill = r["bill_rate"] or 0
        pay = r["pay_rate"] or 0
        spread = r["spread"] or 0
        print(f"  {title:30s} | {prog:25s} | {start} | bill=${bill:.0f} pay=${pay:.0f} spread=${spread:.0f}")

    # 5. SAIC ACTIVITY NOTES WITH HIRING SIGNALS
    print("\n" + "=" * 100)
    print("SAIC ACTIVITY INTELLIGENCE (BACKFILLED)")
    print("=" * 100)

    # Count by match type
    c.execute("SELECT COUNT(*) FROM activities WHERE primes_mentioned LIKE '%SAIC%'")
    primes_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activities WHERE note_text LIKE '%SAIC%'")
    text_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activities WHERE about LIKE '%SAIC%'")
    about_count = c.fetchone()[0]
    c.execute("""SELECT COUNT(*) FROM activities
        WHERE primes_mentioned LIKE '%SAIC%' OR note_text LIKE '%SAIC%' OR about LIKE '%SAIC%'""")
    total_saic = c.fetchone()[0]
    print(f"\nTotal SAIC-related notes: {total_saic}")
    print(f"  - primes_mentioned contains SAIC: {primes_count}")
    print(f"  - note_text mentions SAIC: {text_count}")
    print(f"  - about (contact) contains SAIC: {about_count}")

    # Recruiter engagement with SAIC
    print("\n--- RECRUITERS ENGAGING SAIC ---")
    c.execute("""
        SELECT actor, COUNT(*) as notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive,
               COUNT(DISTINCT about) as contacts,
               MAX(activity_date) as last_date
        FROM activities
        WHERE primes_mentioned LIKE '%SAIC%' OR note_text LIKE '%SAIC%'
        GROUP BY actor
        ORDER BY notes DESC
    """)
    rows = c.fetchall()
    print(f"  Recruiters with SAIC activity: {len(rows)}")
    for r in rows:
        actor = (r["actor"] or "Unknown")[:20]
        last = (r["last_date"] or "")[:10]
        print(f"  {actor:20s} | {r['notes']:4d} notes | hiring={r['hiring']:2d} traction={r['traction']:2d} positive={r['positive']:2d} | {r['contacts']:3d} contacts | last={last}")

    # Notes with signals
    print("\n--- SAIC NOTES WITH HIRING SIGNALS / TRACTION ---")
    c.execute("""
        SELECT activity_date, actor, about, note_text, hiring_signal, traction, positive_response
        FROM activities
        WHERE (primes_mentioned LIKE '%SAIC%' OR note_text LIKE '%SAIC%')
        AND (hiring_signal = 1 OR traction = 1 OR positive_response = 1)
        ORDER BY activity_date DESC
        LIMIT 30
    """)
    rows = c.fetchall()
    print(f"  Notes with signals: {len(rows)}")
    for r in rows:
        date = (r["activity_date"] or "")[:10]
        actor = (r["actor"] or "")[:15]
        about = (r["about"] or "")[:25]
        note = (r["note_text"] or "")[:200]
        signals = []
        if r["hiring_signal"]: signals.append("HIRING")
        if r["traction"]: signals.append("TRACTION")
        if r["positive_response"]: signals.append("POSITIVE")
        print(f"\n  [{date}] {actor:15s} -> {about:25s} | {'/'.join(signals)}")
        print(f"    {note}")

    # ALL SAIC notes (most recent)
    print("\n--- ALL SAIC NOTES (most recent 40) ---")
    c.execute("""
        SELECT activity_date, actor, about, note_text, action,
               hiring_signal, traction, positive_response
        FROM activities
        WHERE primes_mentioned LIKE '%SAIC%' OR note_text LIKE '%SAIC%'
        ORDER BY activity_date DESC
        LIMIT 40
    """)
    for r in c.fetchall():
        date = (r["activity_date"] or "")[:10]
        actor = (r["actor"] or "")[:15]
        about = (r["about"] or "")[:25]
        action = (r["action"] or "")[:15]
        note = (r["note_text"] or "")[:150]
        flags = []
        if r["hiring_signal"]: flags.append("H")
        if r["traction"]: flags.append("T")
        if r["positive_response"]: flags.append("P")
        flag_str = f" [{'/'.join(flags)}]" if flags else ""
        print(f"  [{date}] {actor:15s} | {action:15s} | {about:25s}{flag_str}")
        if note:
            print(f"    {note}")

    # 6. SUBAWARDS TO/FROM SAIC
    print("\n" + "=" * 100)
    print("SAIC SUBAWARD NETWORK")
    print("=" * 100)

    c.execute("""
        SELECT prime_name, sub_recipient_name, SUM(subaward_amount) as total,
               COUNT(*) as count, awarding_agency
        FROM task_orders
        WHERE (prime_name LIKE '%SAIC%' OR sub_recipient_name LIKE '%SAIC%')
        GROUP BY prime_name, sub_recipient_name
        ORDER BY total DESC
        LIMIT 20
    """)
    for r in c.fetchall():
        prime = (r["prime_name"] or "")[:30]
        sub = (r["sub_recipient_name"] or "")[:30]
        total = r["total"] or 0
        count = r["count"]
        print(f"  {prime:30s} -> {sub:30s} | {format_value(total):>12s} ({count} awards)")

    # 7. SCORING DATA
    print("\n" + "=" * 100)
    print("SAIC BD SCORES")
    print("=" * 100)

    c.execute("""
        SELECT s.entity_name, s.bd_score, s.priority_tier, s.composite_score,
               s.contact_access_score, s.recompete_proximity_score
        FROM scoring s
        WHERE s.entity_name LIKE '%SAIC%'
        ORDER BY COALESCE(s.composite_score, s.bd_score, 0) DESC
        LIMIT 15
    """)
    for r in c.fetchall():
        name = (r["entity_name"] or "")[:50]
        bd = r["bd_score"] or 0
        comp = r["composite_score"] or 0
        pri = r["priority_tier"] or ""
        contact = r["contact_access_score"] or 0
        recomp = r["recompete_proximity_score"] or 0
        print(f"  {name:50s} | BD={bd:.0f} | composite={comp:.0f} | {pri:8s} | contacts={contact:.0f} | recompete={recomp:.0f}")

    conn.close()

if __name__ == "__main__":
    run()
