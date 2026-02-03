# BD Takeover Instructions

**Salesperson:** Colton Scurry
**Generated:** 2026-01-30 08:50
**Activity Period:** Period 01/01/2025 to 01/30/2026

---

## Overview

This package contains all the data needed to take over Colton Scurry's book of business.

## Files Included

| File | Description |
|------|-------------|
| `INSTRUCTIONS.md` | This file - how to use the data |
| `master_data.csv` | All activity data in one file |
| `programs_jobs.csv` | All jobs/programs with status and metrics |
| `contacts.csv` | All contacts with classification |
| `contact_org_chart.csv` | Contacts organized by program/client |
| `programs/` | Individual playbook for each major program |

---

## Quick Stats

- **36** Contacts to manage
- **4** Client relationships
- **3026** Active/recent jobs
- **193** Candidates in pipeline
- **1840** Total submissions made
- **264** Successful placements
- **528** Active interviews

---

## Priority Actions (In Order)

### 1. URGENT: Active Interviews

There are **528 candidates in interview stage**.
These are closest to placement and need immediate follow-up.

**Action:** Review `master_data.csv` filtered by Status='Interview Scheduled'

### 2. HIGH: Client Introductions

Introduce yourself to key client contacts at:

- **Northrop Grumman** (1124 submissions, 124 placements)
- **SAIC** (472 submissions, 72 placements)
- **Unknown** (196 submissions, 48 placements)
- **GDIT** (48 submissions, 20 placements)

### 3. MEDIUM: Pending Submissions

There are **1048 pending submissions** that need status checks.

**Action:** Review `master_data.csv` filtered by Status='Client Submission'

### 4. MEDIUM: Recruiter Coordination

Connect with these recruiting partners who worked with Colton:

- Jackson Denson
- Ryan Whitmire
- James Heltzer
- Garrison Pirkle
- Modern Technology Solutions
- Josh Tipton
- Garrett Seckler
- Colton Scurry
- Ben Moser
- Lockheed Martin

---

## How to Use Each File

### master_data.csv
The master file contains ALL activity. Use filters to slice by:
- **Client** - Focus on one client at a time
- **Status** - Prioritize interviews, then submissions
- **Date** - See recent vs older activity
- **Job ID** - Track specific positions

### programs_jobs.csv
Lists all job requisitions with:
- Current status (Open/Placed/Closed)
- Client name
- Number of submissions and placements
- Key candidates

### contacts.csv
All contacts Colton was managing:
- Contact name and status
- Date added
- Relationship type (Client Visit vs New Lead)

### contact_org_chart.csv
Contacts organized by client/program:
- Shows who to contact for each client
- Helps identify key decision makers

### programs/ folder
Individual markdown files for each major program with:
- All candidates submitted
- Interview status
- Placements made
- Notes and activity history

---

## Recommended Workflow

1. **Day 1:** Review interviews in progress, reach out to candidates
2. **Day 2:** Introduce yourself to top 3 client contacts
3. **Day 3:** Connect with recruiter partners
4. **Week 1:** Check status of all pending submissions
5. **Week 2:** Review open jobs and candidate pipelines

---

## Questions?

All data was extracted from Bullhorn on the activity period noted above.
Source files are preserved in `Engine7_BullhornETL/data/raw/coworker_takeover/`
