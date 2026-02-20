"""Update all analysis documents with latest Bullhorn notes data (Feb 16-20 ingestion).

Regenerates key reports from the master_federal_contracts.db which now contains
51,524 activities including 833 new notes from Feb 16-20, 2026.
"""
import sqlite3
import csv
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "data" / "master_federal_contracts.db"
REPORTS = BASE / "data" / "deliverables" / "reports"
FINAL_OUTPUTS = BASE / "data" / "bullhorn_analysis" / "FINAL_OUTPUTS"
INTELLIGENCE = BASE / "data" / "enriched" / "intelligence"
MASTER_NOTES = BASE / "data" / "bullhorn_analysis" / "source_csvs" / "master_notes.csv"

NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def fmt_val(val):
    if not val: return "N/A"
    if val > 1e9: return f"${val/1e9:.2f}B"
    if val > 1e6: return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Update AM_TERRITORY_PLAYBOOK.md
# ─────────────────────────────────────────────────────────────────────────────
def update_territory_playbook(conn):
    print("\n[1/8] Updating AM_TERRITORY_PLAYBOOK.md...")
    c = conn.cursor()

    # Total notes
    c.execute("SELECT COUNT(*) FROM activities")
    total_notes = c.fetchone()[0]

    # Get recruiter stats
    c.execute("""
        SELECT actor, COUNT(*) as notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive,
               COUNT(DISTINCT about) as unique_contacts,
               MAX(activity_date) as last_activity
        FROM activities
        WHERE actor IS NOT NULL AND actor != ''
        GROUP BY actor
        ORDER BY notes DESC
    """)
    recruiters = c.fetchall()

    # Hiring managers with attempts but no conversions
    c.execute("""
        SELECT about, COUNT(*) as attempts,
               GROUP_CONCAT(DISTINCT actor) as worked_by,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes
        FROM activities
        WHERE hiring_signal = 0 AND traction = 0
        AND about IS NOT NULL AND about != ''
        GROUP BY about
        HAVING attempts >= 3
        ORDER BY attempts DESC
        LIMIT 25
    """)
    unclaimed = c.fetchall()

    # Programs being worked but not won (no placements)
    c.execute("""
        SELECT programs_mentioned, COUNT(*) as mentions,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               GROUP_CONCAT(DISTINCT actor) as actors
        FROM activities
        WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''
        GROUP BY programs_mentioned
        ORDER BY mentions DESC
        LIMIT 30
    """)
    program_activity = c.fetchall()

    # Prime contractor breakdown
    c.execute("""
        SELECT primes_mentioned, COUNT(*) as mentions,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               GROUP_CONCAT(DISTINCT actor) as actors
        FROM activities
        WHERE primes_mentioned IS NOT NULL AND primes_mentioned != ''
        GROUP BY primes_mentioned
        ORDER BY mentions DESC
        LIMIT 20
    """)
    prime_activity = c.fetchall()

    # New data: Feb 16-20 activity
    c.execute("""
        SELECT actor, COUNT(*) as notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction
        FROM activities
        WHERE activity_date >= '2026-02-16'
        AND actor IS NOT NULL AND actor != ''
        GROUP BY actor
        ORDER BY notes DESC
    """)
    recent_recruiters = c.fetchall()

    doc = f"""# ACCOUNT MANAGER TERRITORY PLAYBOOK
## Claim Programs Before Your Competition
### Your Competitive Edge Guide

**Last Updated:** {NOW}
**Data through:** 2026-02-20 (includes Feb 16-20 Bullhorn import)

---

# THE RULES OF THE GAME

1. **First meeting wins** - Once you have a meaningful meeting, that program/contact is YOURS
2. **Calls without meetings = Fair game** - If someone is just leaving voicemails, you can swoop in
3. **No jobs coming in = Open territory** - Programs with no placements are available
4. **More programs = More revenue** - Lock down as many as possible

---

# YOUR CURRENT OPPORTUNITY

Based on analysis of **{total_notes:,}** notes (updated {NOW}):

## UNCLAIMED TERRITORY SUMMARY

| Category | Count | Status |
|----------|-------|--------|
| **Hiring Managers with 0 conversions** | {len(unclaimed)}+ | FAIR GAME |
| **Active Recruiters** | {len(recruiters)} | TRACKED |
| **Primes with activity** | {len(prime_activity)} | IN PLAY |
| **Programs being worked** | {len(program_activity)} | AVAILABLE |

---

# PLAYBOOK 1: GRAB UNCLAIMED CONTACTS

## The Opportunity
{len(unclaimed)}+ contacts have been called **3+ times** by other recruiters but **NO ONE has converted**.

## Your Targets (Top 25)

| Contact | Prime | Attempts by Others | Worked By |
|---------|-------|-------------------|-----------|
"""
    for r in unclaimed[:25]:
        name = (r['about'] or '')[:30]
        primes = (r['primes'] or '')[:20]
        worked = (r['worked_by'] or '')[:25]
        doc += f"| {name} | {primes} | {r['attempts']} | {worked} |\n"

    doc += """
## Your Approach

**Why they're not answering others:**
- Same pitch every time ("do you have any openings?")
- Calling at the same time
- Leaving generic voicemails
- No value proposition

**What you do differently:**
1. **Lead with VALUE** - "I have a TS/SCI Java dev who worked on [similar program]"
2. **Different channel** - Email or LinkedIn instead of phone
3. **Different time** - Early morning (7am) or late afternoon (5pm)
4. **Specific ask** - "5 minutes to see if there's a fit"

## Script

> "Hi [Name], I'm not going to waste your time with the generic 'do you have openings' call - you've probably gotten enough of those. I actually have a [specific skill/clearance] professional who just came off [similar program] and is looking for their next role. Worth a quick 5-minute call to see if there's a fit on your team?"

---

# PLAYBOOK 2: CLAIM BY PRIME

## Primes with Most Activity

| Prime | Total Notes | Hiring Signals | Traction | Worked By |
|-------|------------|---------------|----------|-----------|
"""
    for r in prime_activity[:15]:
        prime = (r['primes_mentioned'] or '')[:25]
        actors = (r['actors'] or '')[:40]
        doc += f"| **{prime}** | {r['mentions']} | {r['hiring']} | {r['traction']} | {actors} |\n"

    doc += """
---

# PLAYBOOK 3: RECRUITER LEADERBOARD

## Who is Working What (Full Roster)

| Recruiter | Total Notes | Hiring Signals | Traction | Positive | Unique Contacts | Last Activity |
|-----------|------------|---------------|----------|----------|----------------|---------------|
"""
    for r in recruiters[:30]:
        actor = (r['actor'] or '')[:20]
        last = (r['last_activity'] or '')[:10]
        doc += f"| {actor} | {r['notes']} | {r['hiring']} | {r['traction']} | {r['positive']} | {r['unique_contacts']} | {last} |\n"

    doc += f"""
---

# PLAYBOOK 4: PROGRAM TERRITORY MAP

## Programs Being Worked

| Program | Mentions | Hiring Signals | Traction | Worked By |
|---------|----------|---------------|----------|-----------|
"""
    for r in program_activity[:25]:
        prog = (r['programs_mentioned'] or '')[:25]
        actors = (r['actors'] or '')[:40]
        doc += f"| **{prog}** | {r['mentions']} | {r['hiring']} | {r['traction']} | {actors} |\n"

    doc += f"""
---

# NEW INTELLIGENCE: FEB 16-20, 2026

## This Week's Activity (833 new notes ingested)

| Recruiter | Notes This Week | Hiring Signals | Traction |
|-----------|----------------|---------------|----------|
"""
    for r in recent_recruiters[:20]:
        actor = (r['actor'] or '')[:25]
        doc += f"| {actor} | {r['notes']} | {r['hiring']} | {r['traction']} |\n"

    doc += f"""
---

*Updated: {NOW} | Source: master_federal_contracts.db ({total_notes:,} total activities)*
"""
    out = REPORTS / "AM_TERRITORY_PLAYBOOK.md"
    out.write_text(doc, encoding='utf-8')
    print(f"  Written: {out} ({len(doc):,} chars)")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Update ACTIONABLE_INSIGHTS_REPORT.md
# ─────────────────────────────────────────────────────────────────────────────
def update_actionable_insights(conn):
    print("\n[2/8] Updating ACTIONABLE_INSIGHTS_REPORT.md...")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM activities")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT about) FROM activities WHERE about IS NOT NULL")
    contacts = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT programs_mentioned) FROM activities WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''")
    programs = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT primes_mentioned) FROM activities WHERE primes_mentioned IS NOT NULL AND primes_mentioned != ''")
    primes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activities WHERE hiring_signal = 1")
    hiring = c.fetchone()[0]

    # Top hiring opportunities - from all notes with hiring signals
    c.execute("""
        SELECT about, activity_date, note_text, primes_mentioned, programs_mentioned, actor
        FROM activities
        WHERE hiring_signal = 1
        ORDER BY activity_date DESC
        LIMIT 50
    """)
    hiring_notes = c.fetchall()

    # New hiring signals from Feb 16-20
    c.execute("""
        SELECT about, activity_date, note_text, primes_mentioned, programs_mentioned, actor
        FROM activities
        WHERE hiring_signal = 1 AND activity_date >= '2026-02-16'
        ORDER BY activity_date DESC
    """)
    new_hiring = c.fetchall()

    # Traction notes
    c.execute("""
        SELECT about, activity_date, note_text, primes_mentioned, programs_mentioned, actor
        FROM activities
        WHERE traction = 1
        ORDER BY activity_date DESC
        LIMIT 30
    """)
    traction_notes = c.fetchall()

    doc = f"""# Actionable Insights Report

**Updated:** {NOW}
**Data through:** 2026-02-20 (includes Feb 16-20 Bullhorn import)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Notes Analyzed** | {total:,} |
| **Unique Contacts** | {contacts:,} |
| **Programs Identified** | {programs} |
| **Companies/Primes** | {primes} |
| **Hiring Signals** | {hiring:,} |

---

## NEW THIS WEEK: Feb 16-20, 2026 Hiring Signals

**{len(new_hiring)} new hiring signals detected:**

"""
    for r in new_hiring:
        name = (r['about'] or 'Unknown')[:30]
        date = (r['activity_date'] or '')[:10]
        prime = (r['primes_mentioned'] or 'TBD')[:20]
        prog = (r['programs_mentioned'] or 'General')[:25]
        note = (r['note_text'] or '')[:200]
        actor = (r['actor'] or '')[:15]
        doc += f"### {name} at {prime}\n"
        doc += f"- **Date:** {date}\n"
        doc += f"- **Programs:** {prog}\n"
        doc += f"- **Recruiter:** {actor}\n"
        doc += f"- **Details:** {note}\n\n"

    doc += """---

## Hot Opportunities - Active Hiring (All Time)

"""
    for r in hiring_notes[:30]:
        name = (r['about'] or 'Unknown')[:30]
        date = (r['activity_date'] or '')[:10]
        prime = (r['primes_mentioned'] or 'TBD')[:20]
        prog = (r['programs_mentioned'] or 'General')[:25]
        note = (r['note_text'] or '')[:300]
        doc += f"### {name} at {prime}\n"
        doc += f"- **Date:** {date}\n"
        doc += f"- **Programs:** {prog}\n"
        doc += f"- **Details:** {note}\n\n"

    doc += f"""---

## Traction Notes - Meetings Set / Positive Progress

"""
    for r in traction_notes[:20]:
        name = (r['about'] or 'Unknown')[:30]
        date = (r['activity_date'] or '')[:10]
        prime = (r['primes_mentioned'] or 'TBD')[:20]
        note = (r['note_text'] or '')[:200]
        doc += f"### {name} at {prime}\n"
        doc += f"- **Date:** {date}\n"
        doc += f"- **Details:** {note}\n\n"

    doc += f"\n---\n\n*Updated: {NOW} | Source: master_federal_contracts.db ({total:,} activities)*\n"

    out = REPORTS / "ACTIONABLE_INSIGHTS_REPORT.md"
    out.write_text(doc, encoding='utf-8')
    print(f"  Written: {out} ({len(doc):,} chars)")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Update NOTES_INTELLIGENCE_EXTRACT.md
# ─────────────────────────────────────────────────────────────────────────────
def update_notes_intelligence(conn):
    print("\n[3/8] Updating NOTES_INTELLIGENCE_EXTRACT.md...")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM activities WHERE hiring_signal = 1")
    total_hiring = c.fetchone()[0]

    c.execute("""
        SELECT about, activity_date, note_text, primes_mentioned, programs_mentioned, actor
        FROM activities
        WHERE hiring_signal = 1
        ORDER BY activity_date DESC
        LIMIT 80
    """)
    rows = c.fetchall()

    doc = f"""# Business Intelligence Extraction

**Updated:** {NOW}
**Data through:** 2026-02-20

---

## Hiring Plans & Recruiting Intelligence

**Total Hiring-Related Notes:** {total_hiring:,}

"""
    for r in rows:
        name = (r['about'] or 'Unknown')[:35]
        prime = (r['primes_mentioned'] or 'TBD')[:25]
        date = (r['activity_date'] or '')[:10]
        prog = (r['programs_mentioned'] or 'N/A')[:30]
        note = (r['note_text'] or '')[:500]
        actor = (r['actor'] or '')[:15]
        doc += f"### {name} - {prime}\n"
        doc += f"**Date:** {date}\n"
        doc += f"**Programs:** {prog}\n"
        doc += f"**Recruiter:** {actor}\n"
        doc += f"**Details:**\n{note}\n\n"

    doc += f"\n---\n*Updated: {NOW}*\n"
    out = REPORTS / "NOTES_INTELLIGENCE_EXTRACT.md"
    out.write_text(doc, encoding='utf-8')
    print(f"  Written: {out} ({len(doc):,} chars)")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Update AGGREGATED_NOTES_BY_CONTACT.md (deliverables/reports)
# ─────────────────────────────────────────────────────────────────────────────
def update_aggregated_notes(conn):
    print("\n[4/8] Updating AGGREGATED_NOTES_BY_CONTACT.md...")
    c = conn.cursor()

    c.execute("SELECT COUNT(DISTINCT about) FROM activities WHERE about IS NOT NULL AND about != ''")
    total_contacts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activities")
    total_notes = c.fetchone()[0]

    # Top contacts by note count
    c.execute("""
        SELECT about, COUNT(*) as notes,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               GROUP_CONCAT(DISTINCT programs_mentioned) as programs,
               MAX(activity_date) as last_activity,
               GROUP_CONCAT(DISTINCT actor) as worked_by
        FROM activities
        WHERE about IS NOT NULL AND about != ''
        GROUP BY about
        ORDER BY notes DESC
        LIMIT 100
    """)
    contacts = c.fetchall()

    doc = f"""# MASTER CONTACT NOTES REPORT
**Updated:** {NOW}
**Data through:** 2026-02-20 (includes Feb 16-20 import)
**Total Contacts:** {total_contacts:,}
**Total Notes Processed:** {total_notes:,}

---

# TABLE OF CONTENTS

"""
    for i, r in enumerate(contacts, 1):
        name = (r['about'] or 'Unknown')[:35]
        primes = (r['primes'] or '')[:30]
        doc += f"{i}. **{name}** ({r['notes']} notes) - {primes}\n"

    doc += "\n---\n\n"

    for r in contacts[:60]:
        name = r['about'] or 'Unknown'
        primes = r['primes'] or ''
        programs = r['programs'] or ''
        last = (r['last_activity'] or '')[:10]
        worked = r['worked_by'] or ''

        doc += f"## {name}\n\n"
        doc += f"**Total Notes:** {r['notes']}\n\n"
        doc += f"**Companies:** {primes}\n\n"
        doc += f"**Programs:** {programs}\n\n"
        doc += f"**Last Activity:** {last}\n\n"
        doc += f"**Worked By:** {worked}\n\n"

        # Get recent notes for this contact
        c2 = conn.cursor()
        c2.execute("""
            SELECT activity_date, note_text, actor
            FROM activities
            WHERE about = ?
            ORDER BY activity_date DESC
            LIMIT 5
        """, (r['about'],))
        recent = c2.fetchall()

        doc += "### Recent Notes\n\n"
        for n in recent:
            date = (n['activity_date'] or '')[:10]
            note = (n['note_text'] or '')[:300]
            doc += f"**[{date}]** ({n['actor'] or 'Unknown'})\n{note}\n\n"

        remaining = r['notes'] - len(recent)
        if remaining > 0:
            doc += f"_... and {remaining} more notes_\n\n"
        doc += "---\n\n"

    doc += f"\n*Updated: {NOW} | {total_notes:,} total notes across {total_contacts:,} contacts*\n"
    out = REPORTS / "AGGREGATED_NOTES_BY_CONTACT.md"
    out.write_text(doc, encoding='utf-8')
    print(f"  Written: {out} ({len(doc):,} chars)")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Update CONTACT_PROGRAM_MATRIX.md
# ─────────────────────────────────────────────────────────────────────────────
def update_contact_program_matrix(conn):
    print("\n[5/8] Updating CONTACT_PROGRAM_MATRIX.md...")
    c = conn.cursor()

    c.execute("SELECT COUNT(DISTINCT about) FROM activities WHERE about IS NOT NULL AND about != ''")
    total_contacts = c.fetchone()[0]

    c.execute("""
        SELECT about, COUNT(*) as notes,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               GROUP_CONCAT(DISTINCT programs_mentioned) as programs,
               MAX(activity_date) as last_date,
               GROUP_CONCAT(DISTINCT actor) as actors
        FROM activities
        WHERE about IS NOT NULL AND about != ''
        GROUP BY about
        ORDER BY notes DESC
        LIMIT 80
    """)
    contacts = c.fetchall()

    doc = f"""# Contact Program Matrix

**Updated:** {NOW}
**Data through:** 2026-02-20

**Total Unique Contacts:** {total_contacts:,}

---

"""
    for r in contacts[:60]:
        name = r['about'] or 'Unknown'
        primes = r['primes'] or 'TBD'
        programs = r['programs'] or 'General'
        last = (r['last_date'] or '')[:10]
        actors = r['actors'] or ''

        doc += f"## {name}\n\n"
        doc += f"**Total Notes:** {r['notes']}\n\n"
        doc += f"**Companies:** {primes}\n\n"
        doc += f"**Programs:** {programs}\n\n"
        doc += f"**Worked By:** {actors}\n\n"
        doc += f"**Last Activity:** {last}\n\n"

        # Recent notes
        c2 = conn.cursor()
        c2.execute("""
            SELECT activity_date, note_text, hiring_signal, traction
            FROM activities WHERE about = ?
            ORDER BY activity_date DESC LIMIT 5
        """, (r['about'],))
        for n in c2.fetchall():
            date = (n['activity_date'] or '')[:10]
            note = (n['note_text'] or '')[:300]
            flags = []
            if n['hiring_signal']: flags.append("Hiring")
            if n['traction']: flags.append("Traction")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            doc += f"**[{date}]**{flag_str}\n{note}\n\n"

        remaining = r['notes'] - 5
        if remaining > 0:
            doc += f"_... and {remaining} more notes_\n\n"
        doc += "---\n\n"

    doc += f"\n*Updated: {NOW}*\n"
    out = REPORTS / "CONTACT_PROGRAM_MATRIX.md"
    out.write_text(doc, encoding='utf-8')
    print(f"  Written: {out} ({len(doc):,} chars)")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Update SAIC Report with new notes
# ─────────────────────────────────────────────────────────────────────────────
def update_saic_report(conn):
    print("\n[6/8] Updating SAIC_NAVY_AF_ARMY_OPPORTUNITY_REPORT.md with new SAIC notes...")
    c = conn.cursor()

    # Get all SAIC-related activity notes
    c.execute("""
        SELECT activity_date, actor, about, note_text, hiring_signal, traction, positive_response
        FROM activities
        WHERE note_text LIKE '%SAIC%' OR primes_mentioned LIKE '%SAIC%' OR about LIKE '%SAIC%'
        ORDER BY activity_date DESC
    """)
    saic_notes = c.fetchall()

    # Read existing report
    saic_report = REPORTS / "SAIC_NAVY_AF_ARMY_OPPORTUNITY_REPORT.md"
    if saic_report.exists():
        content = saic_report.read_text(encoding='utf-8')

        # Add a new section with the latest SAIC intelligence
        new_section = f"""

---

## UPDATED: SAIC INTELLIGENCE FROM FEB 16-20, 2026

**{len(saic_notes)} total SAIC-related notes found in database**

### Latest SAIC Activity Notes

"""
        for r in saic_notes[:20]:
            date = (r['activity_date'] or '')[:10]
            actor = (r['actor'] or 'Unknown')[:20]
            about = (r['about'] or '')[:30]
            note = (r['note_text'] or '')[:400]
            signals = []
            if r['hiring_signal']: signals.append("HIRING")
            if r['traction']: signals.append("TRACTION")
            if r['positive_response']: signals.append("POSITIVE")
            sig = f" **[{'/'.join(signals)}]**" if signals else ""

            new_section += f"#### [{date}] {actor} -> {about}{sig}\n"
            new_section += f"{note}\n\n"

        new_section += f"\n*Section updated: {NOW}*\n"

        # Check if we already appended this section before
        if "UPDATED: SAIC INTELLIGENCE FROM FEB" in content:
            # Replace existing section
            idx = content.index("## UPDATED: SAIC INTELLIGENCE FROM FEB")
            # Find the preceding ---
            dash_idx = content.rfind("---", 0, idx)
            if dash_idx > 0:
                content = content[:dash_idx] + new_section
            else:
                content = content[:idx-1] + new_section
        else:
            content += new_section

        saic_report.write_text(content, encoding='utf-8')
        print(f"  Updated: {saic_report}")
    else:
        print("  SAIC report not found, skipping")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Update FINAL_OUTPUTS executive docs
# ─────────────────────────────────────────────────────────────────────────────
def update_final_outputs(conn):
    print("\n[7/8] Updating FINAL_OUTPUTS/...")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM activities")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT about) FROM activities WHERE about IS NOT NULL")
    contacts = c.fetchone()[0]

    # Update 00_EXECUTIVE_TAKEOVER_SUMMARY
    c.execute("""
        SELECT actor, COUNT(*) as notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(DISTINCT about) as contacts
        FROM activities
        WHERE actor IS NOT NULL AND actor != ''
        GROUP BY actor
        ORDER BY notes DESC
    """)
    recruiters = c.fetchall()

    doc = f"""# EXECUTIVE TAKEOVER SUMMARY
**Updated:** {NOW}
**Data through:** 2026-02-20 (includes Feb 16-20 import of 833 notes)

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Total Notes** | {total:,} |
| **Unique Contacts** | {contacts:,} |
| **Active Recruiters** | {len(recruiters)} |

## Recruiter Activity Summary

| Recruiter | Notes | Hiring Signals | Traction | Unique Contacts |
|-----------|-------|---------------|----------|----------------|
"""
    for r in recruiters[:25]:
        actor = (r['actor'] or '')[:25]
        doc += f"| {actor} | {r['notes']} | {r['hiring']} | {r['traction']} | {r['contacts']} |\n"

    # Top contacts
    c.execute("""
        SELECT about, COUNT(*) as notes,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring
        FROM activities
        WHERE about IS NOT NULL AND about != ''
        GROUP BY about
        ORDER BY notes DESC
        LIMIT 30
    """)
    top_contacts = c.fetchall()

    doc += f"""
## Top Contacts by Engagement

| Contact | Notes | Primes | Hiring Signals |
|---------|-------|--------|---------------|
"""
    for r in top_contacts:
        name = (r['about'] or '')[:30]
        primes = (r['primes'] or '')[:30]
        doc += f"| {name} | {r['notes']} | {primes} | {r['hiring']} |\n"

    doc += f"\n---\n*Updated: {NOW}*\n"
    (FINAL_OUTPUTS / "00_EXECUTIVE_TAKEOVER_SUMMARY.md").write_text(doc, encoding='utf-8')
    print(f"  Written: 00_EXECUTIVE_TAKEOVER_SUMMARY.md")

    # Update 02_FAIR_GAME_CONTACTS_LIST
    c.execute("""
        SELECT about, COUNT(*) as attempts,
               GROUP_CONCAT(DISTINCT actor) as worked_by,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               MAX(activity_date) as last_activity
        FROM activities
        WHERE hiring_signal = 0 AND traction = 0 AND positive_response = 0
        AND about IS NOT NULL AND about != ''
        GROUP BY about
        HAVING attempts >= 3
        ORDER BY attempts DESC
        LIMIT 100
    """)
    fair_game = c.fetchall()

    doc2 = f"""# FAIR GAME CONTACTS LIST
**Updated:** {NOW}
**Contacts with 3+ attempts but ZERO conversions**

---

| # | Contact | Attempts | Primes | Worked By | Last Activity |
|---|---------|----------|--------|-----------|---------------|
"""
    for i, r in enumerate(fair_game[:80], 1):
        name = (r['about'] or '')[:30]
        primes = (r['primes'] or '')[:25]
        worked = (r['worked_by'] or '')[:25]
        last = (r['last_activity'] or '')[:10]
        doc2 += f"| {i} | {name} | {r['attempts']} | {primes} | {worked} | {last} |\n"

    doc2 += f"\n---\n*Total fair game contacts: {len(fair_game)} | Updated: {NOW}*\n"
    (FINAL_OUTPUTS / "02_FAIR_GAME_CONTACTS_LIST.md").write_text(doc2, encoding='utf-8')
    print(f"  Written: 02_FAIR_GAME_CONTACTS_LIST.md")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Update Intelligence CSVs
# ─────────────────────────────────────────────────────────────────────────────
def update_intelligence_csvs(conn):
    print("\n[8/8] Updating intelligence CSVs...")
    c = conn.cursor()

    # AUTHOR_PERFORMANCE.csv
    c.execute("""
        SELECT actor as author, COUNT(*) as total_notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring_signals,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction_notes,
               COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive_responses,
               COUNT(DISTINCT about) as unique_contacts,
               COUNT(DISTINCT programs_mentioned) as programs_touched,
               COUNT(DISTINCT primes_mentioned) as primes_touched,
               MIN(activity_date) as first_activity,
               MAX(activity_date) as last_activity
        FROM activities
        WHERE actor IS NOT NULL AND actor != ''
        GROUP BY actor
        ORDER BY total_notes DESC
    """)
    rows = c.fetchall()

    out = INTELLIGENCE / "AUTHOR_PERFORMANCE.csv"
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Author', 'Total Notes', 'Hiring Signals', 'Traction', 'Positive',
                         'Unique Contacts', 'Programs', 'Primes', 'First Activity', 'Last Activity'])
        for r in rows:
            writer.writerow([r['author'], r['total_notes'], r['hiring_signals'],
                             r['traction_notes'], r['positive_responses'],
                             r['unique_contacts'], r['programs_touched'],
                             r['primes_touched'], r['first_activity'], r['last_activity']])
    print(f"  Written: AUTHOR_PERFORMANCE.csv ({len(rows)} rows)")

    # CONTACTS_INTELLIGENCE.csv
    c.execute("""
        SELECT about as contact, COUNT(*) as notes,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               GROUP_CONCAT(DISTINCT programs_mentioned) as programs,
               GROUP_CONCAT(DISTINCT actor) as worked_by,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring_signals,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive,
               MIN(activity_date) as first_activity,
               MAX(activity_date) as last_activity
        FROM activities
        WHERE about IS NOT NULL AND about != ''
        GROUP BY about
        ORDER BY notes DESC
    """)
    rows = c.fetchall()

    out = INTELLIGENCE / "CONTACTS_INTELLIGENCE.csv"
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Contact', 'Total Notes', 'Primes', 'Programs', 'Worked By',
                         'Hiring Signals', 'Traction', 'Positive', 'First Activity', 'Last Activity'])
        for r in rows:
            writer.writerow([r['contact'], r['notes'], r['primes'], r['programs'],
                             r['worked_by'], r['hiring_signals'], r['traction'],
                             r['positive'], r['first_activity'], r['last_activity']])
    print(f"  Written: CONTACTS_INTELLIGENCE.csv ({len(rows)} rows)")

    # PROGRAM_INTELLIGENCE.csv
    c.execute("""
        SELECT programs_mentioned as program, COUNT(*) as mentions,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(CASE WHEN positive_response = 1 THEN 1 END) as positive,
               GROUP_CONCAT(DISTINCT primes_mentioned) as primes,
               GROUP_CONCAT(DISTINCT actor) as recruiters,
               COUNT(DISTINCT about) as contacts,
               MAX(activity_date) as last_activity
        FROM activities
        WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''
        GROUP BY programs_mentioned
        ORDER BY mentions DESC
    """)
    rows = c.fetchall()

    out = INTELLIGENCE / "PROGRAM_INTELLIGENCE.csv"
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Program', 'Mentions', 'Hiring Signals', 'Traction', 'Positive',
                         'Primes', 'Recruiters', 'Contacts', 'Last Activity'])
        for r in rows:
            writer.writerow([r['program'], r['mentions'], r['hiring'], r['traction'],
                             r['positive'], r['primes'], r['recruiters'],
                             r['contacts'], r['last_activity']])
    print(f"  Written: PROGRAM_INTELLIGENCE.csv ({len(rows)} rows)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print(f"UPDATING ANALYSIS DOCUMENTS — {NOW}")
    print(f"Database: {DB_PATH}")
    print("=" * 80)

    conn = get_conn()

    # Verify data
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM activities")
    total = c.fetchone()[0]
    c.execute("SELECT MIN(activity_date), MAX(activity_date) FROM activities WHERE activity_date IS NOT NULL")
    dates = c.fetchone()
    print(f"\nDatabase: {total:,} activities | Date range: {dates[0]} to {dates[1]}")

    update_territory_playbook(conn)
    update_actionable_insights(conn)
    update_notes_intelligence(conn)
    update_aggregated_notes(conn)
    update_contact_program_matrix(conn)
    update_saic_report(conn)
    update_final_outputs(conn)
    update_intelligence_csvs(conn)

    conn.close()

    print("\n" + "=" * 80)
    print("ALL DOCUMENTS UPDATED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nFiles updated:")
    print(f"  Reports:      AM_TERRITORY_PLAYBOOK.md")
    print(f"                ACTIONABLE_INSIGHTS_REPORT.md")
    print(f"                NOTES_INTELLIGENCE_EXTRACT.md")
    print(f"                AGGREGATED_NOTES_BY_CONTACT.md")
    print(f"                CONTACT_PROGRAM_MATRIX.md")
    print(f"                SAIC_NAVY_AF_ARMY_OPPORTUNITY_REPORT.md")
    print(f"  Final:        00_EXECUTIVE_TAKEOVER_SUMMARY.md")
    print(f"                02_FAIR_GAME_CONTACTS_LIST.md")
    print(f"  Intelligence: AUTHOR_PERFORMANCE.csv")
    print(f"                CONTACTS_INTELLIGENCE.csv")
    print(f"                PROGRAM_INTELLIGENCE.csv")


if __name__ == "__main__":
    main()
