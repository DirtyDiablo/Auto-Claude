"""
Coworker Takeover Export Script
Generates comprehensive output files for BD takeover analysis.
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =========================================
# CONFIGURATION
# =========================================

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "coworker_takeover"
PLAYBOOK_JSON = OUTPUT_DIR / "bd_playbook.json"
PARSED_DATA = OUTPUT_DIR / "parsed_data.json"


def load_data():
    """Load parsed data and playbook."""
    with open(PLAYBOOK_JSON, "r", encoding="utf-8") as f:
        playbook = json.load(f)
    with open(PARSED_DATA, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    return playbook, parsed


def generate_instructions_md(playbook: Dict, output_dir: Path):
    """Generate instructions markdown file."""
    lines = [
        "# BD Takeover Instructions",
        "",
        f"**Salesperson:** {playbook.get('salesperson', 'Unknown')}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Activity Period:** {playbook['summary'].get('activity_period', 'Unknown')}",
        "",
        "---",
        "",
        "## Overview",
        "",
        "This package contains all the data needed to take over Colton Scurry's book of business.",
        "",
        "## Files Included",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `INSTRUCTIONS.md` | This file - how to use the data |",
        "| `master_data.csv` | All activity data in one file |",
        "| `programs_jobs.csv` | All jobs/programs with status and metrics |",
        "| `contacts.csv` | All contacts with classification |",
        "| `contact_org_chart.csv` | Contacts organized by program/client |",
        "| `programs/` | Individual playbook for each major program |",
        "",
        "---",
        "",
        "## Quick Stats",
        "",
        f"- **{playbook['summary']['total_contacts']}** Contacts to manage",
        f"- **{playbook['summary']['total_clients']}** Client relationships",
        f"- **{playbook['summary']['total_jobs']}** Active/recent jobs",
        f"- **{playbook['summary']['total_candidates']}** Candidates in pipeline",
        f"- **{playbook['summary']['total_submissions']}** Total submissions made",
        f"- **{playbook['summary']['total_placements']}** Successful placements",
        f"- **{playbook['summary']['total_interviews']}** Active interviews",
        "",
        "---",
        "",
        "## Priority Actions (In Order)",
        "",
        "### 1. URGENT: Active Interviews",
        "",
        f"There are **{playbook['summary']['total_interviews']} candidates in interview stage**.",
        "These are closest to placement and need immediate follow-up.",
        "",
        "**Action:** Review `master_data.csv` filtered by Status='Interview Scheduled'",
        "",
        "### 2. HIGH: Client Introductions",
        "",
        "Introduce yourself to key client contacts at:",
        "",
    ]

    for client in playbook["analysis"].get("top_clients", [])[:5]:
        lines.append(
            f"- **{client['name']}** ({client['submissions']} submissions, {client['placements']} placements)"
        )

    lines.extend(
        [
            "",
            "### 3. MEDIUM: Pending Submissions",
            "",
            f"There are **{len(playbook['pipeline'].get('submissions', []))} pending submissions** that need status checks.",
            "",
            "**Action:** Review `master_data.csv` filtered by Status='Client Submission'",
            "",
            "### 4. MEDIUM: Recruiter Coordination",
            "",
            "Connect with these recruiting partners who worked with Colton:",
            "",
        ]
    )

    for recruiter in playbook.get("recruiters", [])[:10]:
        lines.append(f"- {recruiter}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## How to Use Each File",
            "",
            "### master_data.csv",
            "The master file contains ALL activity. Use filters to slice by:",
            "- **Client** - Focus on one client at a time",
            "- **Status** - Prioritize interviews, then submissions",
            "- **Date** - See recent vs older activity",
            "- **Job ID** - Track specific positions",
            "",
            "### programs_jobs.csv",
            "Lists all job requisitions with:",
            "- Current status (Open/Placed/Closed)",
            "- Client name",
            "- Number of submissions and placements",
            "- Key candidates",
            "",
            "### contacts.csv",
            "All contacts Colton was managing:",
            "- Contact name and status",
            "- Date added",
            "- Relationship type (Client Visit vs New Lead)",
            "",
            "### contact_org_chart.csv",
            "Contacts organized by client/program:",
            "- Shows who to contact for each client",
            "- Helps identify key decision makers",
            "",
            "### programs/ folder",
            "Individual markdown files for each major program with:",
            "- All candidates submitted",
            "- Interview status",
            "- Placements made",
            "- Notes and activity history",
            "",
            "---",
            "",
            "## Recommended Workflow",
            "",
            "1. **Day 1:** Review interviews in progress, reach out to candidates",
            "2. **Day 2:** Introduce yourself to top 3 client contacts",
            "3. **Day 3:** Connect with recruiter partners",
            "4. **Week 1:** Check status of all pending submissions",
            "5. **Week 2:** Review open jobs and candidate pipelines",
            "",
            "---",
            "",
            "## Questions?",
            "",
            "All data was extracted from Bullhorn on the activity period noted above.",
            "Source files are preserved in `Engine7_BullhornETL/data/raw/coworker_takeover/`",
            "",
        ]
    )

    output_path = output_dir / "INSTRUCTIONS.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Created: {output_path.name}")


def generate_master_csv(playbook: Dict, parsed: Dict, output_dir: Path):
    """Generate master data CSV with all activity."""
    rows = []

    # Add submissions
    for sub in parsed.get("submissions", []):
        rows.append(
            {
                "Record_Type": "Submission",
                "Date": sub.get("date", ""),
                "Client": sub.get("client", ""),
                "Job_ID": sub.get("job_id", ""),
                "Job_Title": sub.get("title", ""),
                "Candidate": sub.get("candidate", ""),
                "Status": sub.get("status", ""),
                "Recruiter": sub.get("recruiter", ""),
                "Salesperson": sub.get("salesperson", ""),
                "Department": sub.get("department", ""),
                "Contact_Name": "",
                "Notes": "",
            }
        )

    # Add contacts
    for contact in parsed.get("contacts", []) + parsed.get("new_contacts", []):
        rows.append(
            {
                "Record_Type": "Contact",
                "Date": contact.get("date_added", ""),
                "Client": "",
                "Job_ID": "",
                "Job_Title": "",
                "Candidate": "",
                "Status": contact.get("status", ""),
                "Recruiter": "",
                "Salesperson": contact.get("salesperson", ""),
                "Department": contact.get("department", ""),
                "Contact_Name": contact.get("name", ""),
                "Notes": "",
            }
        )

    # Add jobs
    for job in parsed.get("jobs", []):
        rows.append(
            {
                "Record_Type": "Job",
                "Date": job.get("date", ""),
                "Client": job.get("client", ""),
                "Job_ID": job.get("job_id", ""),
                "Job_Title": job.get("title", ""),
                "Candidate": "",
                "Status": job.get("status", ""),
                "Recruiter": "",
                "Salesperson": "",
                "Department": "",
                "Contact_Name": "",
                "Notes": "",
            }
        )

    output_path = output_dir / "master_data.csv"
    if rows:
        fieldnames = [
            "Record_Type",
            "Date",
            "Client",
            "Job_ID",
            "Job_Title",
            "Candidate",
            "Status",
            "Recruiter",
            "Salesperson",
            "Department",
            "Contact_Name",
            "Notes",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"  Created: {output_path.name} ({len(rows)} rows)")


def generate_programs_csv(playbook: Dict, parsed: Dict, output_dir: Path):
    """Generate programs/jobs CSV."""
    # Aggregate job data
    job_stats = defaultdict(
        lambda: {
            "job_id": "",
            "title": "",
            "client": "",
            "status": "",
            "type": "",
            "location": "",
            "date": "",
            "submissions": 0,
            "interviews": 0,
            "placements": 0,
            "candidates": [],
        }
    )

    # From jobs
    for job in parsed.get("jobs", []):
        job_id = job.get("job_id", "")
        if job_id:
            job_stats[job_id]["job_id"] = job_id
            job_stats[job_id]["title"] = (
                job.get("title", "") or job_stats[job_id]["title"]
            )
            job_stats[job_id]["client"] = (
                job.get("client", "") or job_stats[job_id]["client"]
            )
            job_stats[job_id]["status"] = (
                job.get("status", "") or job_stats[job_id]["status"]
            )
            job_stats[job_id]["type"] = job.get("type", "") or job_stats[job_id]["type"]
            job_stats[job_id]["location"] = (
                job.get("location", "") or job_stats[job_id]["location"]
            )
            job_stats[job_id]["date"] = job.get("date", "") or job_stats[job_id]["date"]

    # From submissions
    for sub in parsed.get("submissions", []):
        job_id = sub.get("job_id", "")
        if job_id:
            job_stats[job_id]["job_id"] = job_id
            job_stats[job_id]["title"] = (
                sub.get("title", "") or job_stats[job_id]["title"]
            )
            job_stats[job_id]["client"] = (
                sub.get("client", "") or job_stats[job_id]["client"]
            )
            job_stats[job_id]["submissions"] += 1

            status = sub.get("status", "")
            if status == "Placed":
                job_stats[job_id]["placements"] += 1
            elif "Interview" in status:
                job_stats[job_id]["interviews"] += 1

            candidate = sub.get("candidate", "")
            if candidate and candidate not in job_stats[job_id]["candidates"]:
                job_stats[job_id]["candidates"].append(candidate)

    rows = []
    for job_id, stats in sorted(job_stats.items()):
        rows.append(
            {
                "Job_ID": stats["job_id"],
                "Title": stats["title"],
                "Client": stats["client"],
                "Status": stats["status"],
                "Type": stats["type"],
                "Location": stats["location"],
                "Date_Opened": stats["date"],
                "Total_Submissions": stats["submissions"],
                "Interviews": stats["interviews"],
                "Placements": stats["placements"],
                "Top_Candidates": "; ".join(stats["candidates"][:5]),
            }
        )

    output_path = output_dir / "programs_jobs.csv"
    if rows:
        fieldnames = [
            "Job_ID",
            "Title",
            "Client",
            "Status",
            "Type",
            "Location",
            "Date_Opened",
            "Total_Submissions",
            "Interviews",
            "Placements",
            "Top_Candidates",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"  Created: {output_path.name} ({len(rows)} programs/jobs)")

    return job_stats


def generate_contacts_csv(playbook: Dict, parsed: Dict, output_dir: Path):
    """Generate contacts CSV."""
    rows = []

    all_contacts = parsed.get("contacts", []) + parsed.get("new_contacts", [])

    # Deduplicate
    seen = set()
    for contact in all_contacts:
        name = contact.get("name", "").lower()
        if name and name not in seen:
            seen.add(name)
            rows.append(
                {
                    "Name": contact.get("name", ""),
                    "First_Name": contact.get("first_name", ""),
                    "Last_Name": contact.get("last_name", ""),
                    "Status": contact.get("status", ""),
                    "Type": contact.get("type", ""),
                    "Department": contact.get("department", ""),
                    "Date_Added": contact.get("date_added", ""),
                    "Salesperson": contact.get("salesperson", ""),
                }
            )

    output_path = output_dir / "contacts.csv"
    if rows:
        fieldnames = [
            "Name",
            "First_Name",
            "Last_Name",
            "Status",
            "Type",
            "Department",
            "Date_Added",
            "Salesperson",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"  Created: {output_path.name} ({len(rows)} contacts)")


def generate_org_chart_csv(playbook: Dict, parsed: Dict, output_dir: Path):
    """Generate contact org chart by client/program."""
    # Group candidates by client
    client_contacts = defaultdict(list)

    for sub in parsed.get("submissions", []):
        client = sub.get("client", "Unknown")
        candidate = sub.get("candidate", "")
        job_id = sub.get("job_id", "")
        job_title = sub.get("title", "")
        status = sub.get("status", "")
        recruiter = sub.get("recruiter", "")

        if candidate:
            client_contacts[client].append(
                {
                    "Client": client,
                    "Contact_Name": candidate,
                    "Role": "Candidate",
                    "Job_ID": job_id,
                    "Job_Title": job_title,
                    "Status": status,
                    "Associated_Recruiter": recruiter,
                }
            )

    # Add direct contacts (might be client contacts, not candidates)
    for contact in parsed.get("contacts", []) + parsed.get("new_contacts", []):
        client_contacts["Direct Contacts"].append(
            {
                "Client": "Direct Contact",
                "Contact_Name": contact.get("name", ""),
                "Role": contact.get("status", "Contact"),
                "Job_ID": "",
                "Job_Title": "",
                "Status": contact.get("status", ""),
                "Associated_Recruiter": "",
            }
        )

    # Flatten and deduplicate
    rows = []
    seen = set()
    for client, contacts in client_contacts.items():
        for contact in contacts:
            key = f"{contact['Client']}|{contact['Contact_Name']}|{contact['Job_ID']}"
            if key not in seen:
                seen.add(key)
                rows.append(contact)

    output_path = output_dir / "contact_org_chart.csv"
    if rows:
        fieldnames = [
            "Client",
            "Contact_Name",
            "Role",
            "Job_ID",
            "Job_Title",
            "Status",
            "Associated_Recruiter",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"  Created: {output_path.name} ({len(rows)} entries)")


def generate_program_md_files(
    playbook: Dict, parsed: Dict, job_stats: Dict, output_dir: Path
):
    """Generate individual MD files for each major program."""
    programs_dir = output_dir / "programs"
    programs_dir.mkdir(exist_ok=True)

    # Get top programs by activity
    sorted_jobs = sorted(
        job_stats.items(), key=lambda x: x[1]["submissions"], reverse=True
    )

    for job_id, stats in sorted_jobs[:30]:  # Top 30 programs
        if stats["submissions"] < 5:  # Skip low-activity jobs
            continue

        # Sanitize filename
        safe_name = f"{job_id}_{stats['title'][:30]}".replace(" ", "_").replace(
            "/", "-"
        )
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")

        lines = [
            f"# {job_id} - {stats['title']}",
            "",
            f"**Client:** {stats['client']}",
            f"**Status:** {stats['status']}",
            f"**Type:** {stats['type']}",
            f"**Location:** {stats['location']}",
            f"**Date Opened:** {stats['date']}",
            "",
            "---",
            "",
            "## Metrics",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total Submissions | {stats['submissions']} |",
            f"| Interviews | {stats['interviews']} |",
            f"| Placements | {stats['placements']} |",
            "",
            "---",
            "",
            "## Candidates",
            "",
        ]

        # Get all submissions for this job
        job_submissions = [
            s for s in parsed.get("submissions", []) if s.get("job_id") == job_id
        ]

        # Group by status
        by_status = defaultdict(list)
        for sub in job_submissions:
            status = sub.get("status", "Unknown")
            by_status[status].append(sub)

        # Placements first
        if "Placed" in by_status:
            lines.append("### Placements")
            lines.append("")
            for sub in by_status["Placed"]:
                lines.append(
                    f"- **{sub.get('candidate', 'Unknown')}** - Placed {sub.get('date', '')}"
                )
            lines.append("")

        # Interviews
        interview_keys = [k for k in by_status.keys() if "Interview" in k]
        if interview_keys:
            lines.append("### Interviews")
            lines.append("")
            for key in interview_keys:
                for sub in by_status[key]:
                    lines.append(
                        f"- **{sub.get('candidate', 'Unknown')}** - {key} ({sub.get('date', '')})"
                    )
            lines.append("")

        # Submissions
        if "Client Submission" in by_status:
            lines.append("### Pending Submissions")
            lines.append("")
            for sub in by_status["Client Submission"][:20]:
                lines.append(
                    f"- {sub.get('candidate', 'Unknown')} - Submitted {sub.get('date', '')}"
                )
            if len(by_status["Client Submission"]) > 20:
                lines.append(
                    f"- ... and {len(by_status['Client Submission']) - 20} more"
                )
            lines.append("")

        # Recruiters involved
        recruiters = set(
            s.get("recruiter", "") for s in job_submissions if s.get("recruiter")
        )
        if recruiters:
            lines.append("---")
            lines.append("")
            lines.append("## Recruiters")
            lines.append("")
            for r in recruiters:
                lines.append(f"- {r}")
            lines.append("")

        output_path = programs_dir / f"{safe_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    print(
        f"  Created: programs/ folder ({len(list(programs_dir.glob('*.md')))} program files)"
    )


def main():
    """Main export function."""
    print("=" * 60)
    print("COWORKER TAKEOVER EXPORT")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    playbook, parsed = load_data()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nGenerating files...")

    # 1. Instructions MD
    generate_instructions_md(playbook, OUTPUT_DIR)

    # 2. Master data CSV
    generate_master_csv(playbook, parsed, OUTPUT_DIR)

    # 3. Programs/Jobs CSV (returns job_stats for program MDs)
    job_stats = generate_programs_csv(playbook, parsed, OUTPUT_DIR)

    # 4. Contacts CSV
    generate_contacts_csv(playbook, parsed, OUTPUT_DIR)

    # 5. Contact Org Chart CSV
    generate_org_chart_csv(playbook, parsed, OUTPUT_DIR)

    # 6. Individual program MD files
    generate_program_md_files(playbook, parsed, job_stats, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"\nAll files saved to: {OUTPUT_DIR}")
    print("\nFiles created:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  - {f.name}")
    programs_dir = OUTPUT_DIR / "programs"
    if programs_dir.exists():
        print(f"  - programs/ ({len(list(programs_dir.glob('*.md')))} files)")


if __name__ == "__main__":
    main()
