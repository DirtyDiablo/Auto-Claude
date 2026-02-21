"""
Insight Global Jobs - Data Mapped & Enriched Pipeline
=====================================================
Takes raw Apify scraper output, parses each job into structured fields,
maps to federal programs, matches PTS contacts & past performance.

Usage: python enrich_insight_global_jobs.py <path_to_scraper_json>
"""

import ast
import sys
import os
import re
import json
import csv
import logging

logger = logging.getLogger(__name__)
from datetime import datetime
from collections import defaultdict

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DASHBOARD_DATA = os.path.join(PROJECT_DIR, "dashboard", "dist", "data")
ENGINE2_DATA = os.path.join(BASE_DIR, "data")
ENGINE7_DIR = os.path.join(PROJECT_DIR, "Engine7_BullhornETL")
BULLHORN_ANALYSIS = os.path.join(ENGINE7_DIR, "colton_scurry_analysis")
OUTPUT_DIR = os.path.join(ENGINE2_DATA)

# === PROGRAM MAPPING SIGNALS ===
# Location -> likely programs/primes mapping
LOCATION_PROGRAM_MAP = {
    "colorado springs": [
        "MDA",
        "Space Force",
        "NORAD",
        "NORTHCOM",
        "Schriever",
        "Peterson",
        "SBIRS",
        "GPS",
        "AEHF",
        "SDA",
    ],
    "huntsville": [
        "MDA",
        "PEO Missiles",
        "AMCOM",
        "SLS",
        "NASA",
        "THAAD",
        "Patriot",
        "IBCS",
        "Sentinel",
        "AUSA",
    ],
    "san diego": ["Navy", "SPAWAR", "NAVWAR", "PMS", "Aegis", "DDG", "LCS"],
    "el segundo": ["Space Force", "SMC", "GPS", "SBIRS", "AEHF", "NRO", "MILSATCOM"],
    "redondo beach": ["Northrop Grumman", "Space Force", "B-21", "GBSD", "Sentinel"],
    "fort worth": ["F-35", "F-16", "Lockheed Martin"],
    "dallas": ["Raytheon", "Lockheed Martin"],
    "st. louis": ["Boeing", "F-15", "F-18", "T7", "MQ-25"],
    "chantilly": ["NRO", "IC", "NGA"],
    "mclean": ["IC", "CIA", "Booz Allen", "SAIC", "Leidos"],
    "reston": ["IC", "Leidos", "SAIC", "General Dynamics"],
    "arlington": ["DoD", "DARPA", "Pentagon"],
    "springfield": ["NGA", "IC", "Leidos", "GDIT"],
    "fort meade": ["NSA", "USCYBERCOM", "Cyber"],
    "annapolis junction": ["NSA", "Cyber"],
    "linthicum": ["DISA", "Leidos", "GDIT"],
    "aberdeen": ["Army", "APG", "C5ISR", "CERDEC"],
    "dahlgren": ["Navy", "NSWC"],
    "norfolk": ["Navy", "NAVSEA"],
    "hampton roads": ["Navy", "NAVSEA", "Langley"],
    "lexington park": ["Navy", "NAVAIR", "PMA"],
    "wright-patterson": ["Air Force", "AFRL", "AFLCMC"],
    "eglin": ["Air Force", "AFRL", "53rd Wing"],
    "hill afb": ["Air Force", "ICBM", "Minuteman", "Sentinel"],
    "tinker": ["Air Force", "AWACS", "KC-135"],
    "lackland": ["Air Force", "Cyber", "16AF", "24AF"],
    "offutt": ["STRATCOM", "Air Force"],
    "omaha": ["STRATCOM"],
    "warren afb": ["Air Force", "ICBM", "Minuteman", "Sentinel", "GBSD"],
    "malmstrom": ["Air Force", "ICBM", "Minuteman"],
    "cape canaveral": ["Space Force", "NASA", "SLS"],
    "kennedy space center": ["NASA", "Space Force", "SLS"],
    "patrick": ["Space Force", "45th Space Wing"],
    "montgomery": ["Air Force", "Maxwell AFB", "Gunter"],
    "warner robins": ["Air Force", "Robins AFB", "AFLCMC"],
    "panama city": ["Navy", "NSWC"],
    "san antonio": ["Air Force", "Lackland", "JBSA"],
    "tampa": ["CENTCOM", "SOCOM", "MacDill"],
    "fort liberty": ["Army", "JSOC", "USASOC"],
    "fort bragg": ["Army", "JSOC", "USASOC"],
    "fort belvoir": ["Army", "INSCOM", "PEO IEW&S"],
    "fort huachuca": ["Army", "NETCOM"],
    "sierra vista": ["Army", "Fort Huachuca", "NETCOM"],
    "white sands": ["Army", "WSMR", "MDA"],
    "yuma": ["Army", "YPG"],
    "tucson": ["Raytheon", "MDA", "Missiles"],
    "phoenix": ["Luke AFB"],
    "clearfield": ["Hill AFB", "Air Force"],
    "ogden": ["Hill AFB", "Air Force"],
    "cheyenne": ["Warren AFB", "ICBM", "Minuteman", "Sentinel"],
}

# Keywords -> program mapping
KEYWORD_PROGRAM_MAP = {
    "missile defense": ["MDA", "THAAD", "Patriot", "Aegis BMD"],
    "ballistic missile": ["MDA", "ICBM", "Minuteman", "Sentinel", "GBSD"],
    "icbm": ["ICBM", "Minuteman", "Sentinel", "GBSD"],
    "sentinel": ["Sentinel", "GBSD"],
    "minuteman": ["Minuteman", "ICBM", "Sentinel"],
    "ground based strategic deterrent": ["GBSD", "Sentinel"],
    "aegis": ["Aegis", "Aegis BMD", "DDG"],
    "thaad": ["THAAD", "MDA"],
    "patriot": ["Patriot", "IBCS"],
    "ibcs": ["IBCS", "PEO Missiles"],
    "f-35": ["F-35", "JSF"],
    "f-22": ["F-22"],
    "f-15": ["F-15"],
    "f-16": ["F-16"],
    "f-47": ["F-47", "NGAD"],
    "b-21": ["B-21", "Raider"],
    "b-52": ["B-52"],
    "space launch": ["SLS", "NASA"],
    "dcgs": ["DCGS"],
    "c2bmc": ["C2BMC", "MDA"],
    "abms": ["ABMS", "JADC2"],
    "jadc2": ["JADC2", "ABMS"],
    "cyber": ["Cyber", "USCYBERCOM"],
    "intelligence": ["IC", "Intel"],
    "sigint": ["NSA", "SIGINT"],
    "geoint": ["NGA", "GEOINT"],
    "humint": ["DIA", "HUMINT"],
    "satellite": ["Space Force", "MILSATCOM"],
    "gps": ["GPS", "Space Force"],
    "radar": ["Radar", "AESA"],
    "electronic warfare": ["EW", "EA-18G"],
    "sonar": ["Navy", "ASW"],
    "submarine": ["Navy", "SSBN", "SSN"],
    "surface combatant": ["Navy", "DDG", "CG"],
    "carrier": ["Navy", "CVN"],
    "unmanned": ["UAS", "UAV", "MQ-25"],
    "logistics": ["Logistics", "DLA"],
    "cloud": ["Cloud", "Cloud One", "C2E"],
    "devsecops": ["DevSecOps", "Platform One"],
    "artificial intelligence": ["AI/ML"],
    "machine learning": ["AI/ML"],
    "data analytics": ["Data Analytics"],
    "network": ["Network", "DISA"],
    "nsa": ["NSA"],
    "disa": ["DISA"],
    "nga": ["NGA"],
    "nro": ["NRO"],
    "stratcom": ["STRATCOM"],
    "centcom": ["CENTCOM"],
    "socom": ["SOCOM"],
    "special operations": ["SOCOM", "JSOC"],
}

# Clearance -> program relevance
CLEARANCE_PROGRAM_WEIGHT = {
    "TS/SCI with Polygraph": ["IC", "NSA", "NRO", "CIA"],
    "TS/SCI": ["IC", "Space Force", "MDA", "DCGS", "Cyber"],
    "Top Secret": ["DoD", "Space Force", "MDA"],
    "Secret": ["DoD", "General Defense"],
}

# Prime contractor indicators in descriptions
PRIME_INDICATORS = {
    "Lockheed Martin": ["lockheed", "lm ", "lmt", "lm,"],
    "Northrop Grumman": ["northrop", "ngc", "grumman"],
    "Boeing": ["boeing"],
    "Raytheon": ["raytheon", "rtx", "rtn"],
    "General Dynamics": ["general dynamics", "gdit", "gd-it", "gd "],
    "Leidos": ["leidos"],
    "SAIC": ["saic"],
    "BAE Systems": ["bae systems", "bae "],
    "L3Harris": ["l3harris", "l3 harris", "harris corporation"],
    "CACI": ["caci"],
    "Booz Allen": ["booz allen", "booz"],
    "Peraton": ["peraton"],
    "ManTech": ["mantech"],
    "Parsons": ["parsons"],
    "KBR": [" kbr"],
    "Amentum": ["amentum"],
    "Jacobs": ["jacobs engineering", "jacobs "],
    "Maximus": ["maximus"],
    "Serco": ["serco"],
    "DXC": ["dxc technology", "dxc "],
    "Accenture Federal": ["accenture federal", "accenture"],
    "ICF": ["icf international", "icf "],
    "CGI": ["cgi federal", "cgi "],
}


def load_json(filepath):
    """Load JSON file with error handling."""
    if not os.path.exists(filepath):
        print(f"  WARNING: File not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_csv_data(filepath):
    """Load CSV file into list of dicts."""
    if not os.path.exists(filepath):
        print(f"  WARNING: File not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def load_reference_data():
    """Load all reference data for enrichment."""
    print("Loading reference data...")

    # Contacts from dashboard
    contacts = load_json(os.path.join(DASHBOARD_DATA, "contacts.json"))
    print(f"  Contacts: {len(contacts)}")

    # Past performance
    past_perf = load_json(os.path.join(DASHBOARD_DATA, "past_performance.json"))
    print(f"  Past Performance: {len(past_perf)}")

    # Placements
    placements = load_json(os.path.join(DASHBOARD_DATA, "placements.json"))
    print(f"  Placements: {len(placements)}")

    # Federal programs
    fed_programs = load_csv_data(
        os.path.join(ENGINE2_DATA, "Federal Programs MASTER ENRICHED.csv")
    )
    print(f"  Federal Programs: {len(fed_programs)}")

    # Bullhorn contacts with notes
    bullhorn_contacts = load_csv_data(os.path.join(BULLHORN_ANALYSIS, "contacts.csv"))
    print(f"  Bullhorn Contacts: {len(bullhorn_contacts)}")

    # Bullhorn companies
    bullhorn_companies = load_csv_data(os.path.join(BULLHORN_ANALYSIS, "companies.csv"))
    print(f"  Bullhorn Companies: {len(bullhorn_companies)}")

    # Bullhorn timeline for note summaries
    bullhorn_timeline = load_csv_data(os.path.join(BULLHORN_ANALYSIS, "timeline.csv"))
    print(f"  Bullhorn Timeline: {len(bullhorn_timeline)}")

    return {
        "contacts": contacts,
        "past_performance": past_perf,
        "placements": placements,
        "federal_programs": fed_programs,
        "bullhorn_contacts": bullhorn_contacts,
        "bullhorn_companies": bullhorn_companies,
        "bullhorn_timeline": bullhorn_timeline,
    }


# === DESCRIPTION PARSING ===


def parse_description(desc):
    """Parse job description into structured sections."""
    if not desc:
        return {
            "overview": "",
            "responsibilities": [],
            "qualifications_required": [],
            "qualifications_preferred": [],
            "skills": [],
            "technologies": [],
            "certifications": [],
            "education": [],
            "experience_years": "",
            "clearance_details": "",
            "work_schedule": "",
            "compensation_details": "",
        }

    # Clean up
    text = desc.strip()

    # Extract sections by common headers
    sections = {
        "overview": "",
        "responsibilities": [],
        "qualifications_required": [],
        "qualifications_preferred": [],
        "skills": [],
        "technologies": [],
        "certifications": [],
        "education": [],
        "experience_years": "",
        "clearance_details": "",
        "work_schedule": "",
        "compensation_details": "",
    }

    # Split into sections by common headers
    section_patterns = [
        (
            r"(?:responsibilities|duties|what you.?ll do|key responsibilities|day to day)[:\s]*",
            "responsibilities",
        ),
        (
            r"(?:required\s*(?:skills|qualifications|experience)|must.?have|minimum qualifications|qualifications)[:\s]*",
            "qualifications_required",
        ),
        (
            r"(?:preferred|nice.?to.?have|desired|plus|bonus)[:\s]*",
            "qualifications_preferred",
        ),
        (r"(?:skills|technical skills|core competencies)[:\s]*", "skills"),
        (r"(?:education|degree)[:\s]*", "education"),
        (r"(?:certifications?|certs?)[:\s]*", "certifications"),
        (
            r"(?:compensation|salary|pay|benefits|exact compensation)[:\s]*",
            "compensation_details",
        ),
    ]

    # Find section boundaries
    boundaries = []
    text_lower = text.lower()
    for pattern, section_name in section_patterns:
        for m in re.finditer(pattern, text_lower):
            boundaries.append((m.start(), m.end(), section_name))

    boundaries.sort(key=lambda x: x[0])

    if boundaries:
        # Overview is everything before first section header
        sections["overview"] = text[: boundaries[0][0]].strip()

        # Extract each section
        for i, (start, content_start, section_name) in enumerate(boundaries):
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
            content = text[content_start:end].strip()
            # Split into bullet points
            items = re.split(r"\n\s*[-•*]\s*|\n\s*\d+[.)]\s*|\n\s*", content)
            items = [
                item.strip() for item in items if item.strip() and len(item.strip()) > 5
            ]
            if section_name in (
                "responsibilities",
                "qualifications_required",
                "qualifications_preferred",
                "skills",
                "education",
                "certifications",
            ):
                sections[section_name] = items
            else:
                sections[section_name] = content
    else:
        # No clear sections found - use the whole text as overview
        sections["overview"] = text[:500]
        # Try to extract bullet points as responsibilities
        bullets = re.findall(r"[-•*]\s*(.+?)(?:\n|$)", text)
        if bullets:
            sections["responsibilities"] = [
                b.strip() for b in bullets if len(b.strip()) > 10
            ]

    # Extract technologies from full text
    tech_keywords = [
        "Python",
        "Java",
        "C++",
        "C#",
        ".NET",
        "JavaScript",
        "TypeScript",
        "React",
        "Angular",
        "Node.js",
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Ansible",
        "Jenkins",
        "GitLab",
        "Jira",
        "Confluence",
        "Splunk",
        "Elasticsearch",
        "Kafka",
        "Redis",
        "PostgreSQL",
        "MongoDB",
        "Oracle",
        "SQL Server",
        "Linux",
        "Red Hat",
        "RHEL",
        "Windows Server",
        "VMware",
        "Cisco",
        "Palo Alto",
        "Fortinet",
        "SIEM",
        "SOAR",
        "MATLAB",
        "Simulink",
        "Cameo",
        "DOORS",
        "Teamcenter",
        "Creo",
        "SolidWorks",
        "CATIA",
        "NX",
        "AutoCAD",
        "LabVIEW",
        "Verilog",
        "VHDL",
        "FPGA",
        "Embedded",
        "RTOS",
        "VxWorks",
        "STK",
        "AFSIM",
        "Wireshark",
        "Nessus",
        "Tenable",
        "ServiceNow",
        "Remedy",
        "BMC",
        "Tableau",
        "Power BI",
        "Snowflake",
        "Databricks",
        "Hadoop",
        "Spring Boot",
        "Microservices",
        "REST API",
        "GraphQL",
        "CI/CD",
        "SAP",
        "Deltek",
        "Costpoint",
        "Cobra",
        "Crystal Reports",
        "SharePoint",
        "Active Directory",
        "LDAP",
        "PKI",
        "STIG",
        "Agile",
        "Scrum",
        "SAFe",
        "DevSecOps",
        "RMF",
        "NIST",
    ]
    found_tech = []
    for tech in tech_keywords:
        if re.search(r"\b" + re.escape(tech) + r"\b", text, re.IGNORECASE):
            found_tech.append(tech)
    sections["technologies"] = found_tech

    # Extract certifications from full text
    cert_patterns = [
        r"(?:Security\+|Sec\+)",
        r"CISSP",
        r"CISM",
        r"CEH",
        r"CompTIA",
        r"CCNA",
        r"CCNP",
        r"CCIE",
        r"AWS\s+(?:Solutions?\s+Architect|Developer|SysOps)",
        r"PMP",
        r"ITIL",
        r"Six Sigma",
        r"CAPM",
        r"Agile\s+Certified",
        r"MCSE",
        r"MCSA",
        r"A\+",
        r"Network\+",
        r"Linux\+",
        r"CySA\+",
        r"GIAC",
        r"GSEC",
        r"GCIH",
        r"OSCP",
        r"CISA",
        r"TS/SCI",
        r"Secret\s+Clearance",
        r"Top\s+Secret",
        r"8570",
        r"8140",
        r"DoD\s+8570",
        r"IAT\s+Level",
        r"PE\b",
        r"EIT\b",
        r"FE\b",
    ]
    found_certs = []
    for pat in cert_patterns:
        if re.search(pat, text, re.IGNORECASE):
            match = re.search(pat, text, re.IGNORECASE)
            found_certs.append(match.group())
    if found_certs:
        sections["certifications"] = list(set(found_certs))

    # Extract experience years
    exp_match = re.search(
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        text,
        re.IGNORECASE,
    )
    if exp_match:
        sections["experience_years"] = exp_match.group()

    # Extract clearance details
    clearance_match = re.search(
        r"(?:clearance|security)[:\s]*((?:TS/SCI|Top\s*Secret|Secret|Public\s*Trust|"
        r"Confidential|CI\s*Poly|Full\s*Scope\s*Poly|Polygraph)[^.]*)",
        text,
        re.IGNORECASE,
    )
    if clearance_match:
        sections["clearance_details"] = clearance_match.group(1).strip()

    # Extract work schedule
    schedule_match = re.search(
        r"(?:schedule|shift|hours)[:\s]*([^.]*(?:AM|PM|shift|remote|hybrid|onsite|on-site)[^.]*)",
        text,
        re.IGNORECASE,
    )
    if schedule_match:
        sections["work_schedule"] = schedule_match.group(1).strip()

    return sections


# === PROGRAM MAPPING ===


def extract_state_from_location(location):
    """Extract state from location string."""
    if not location:
        return ""
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 2:
        return parts[-1].strip()
    return ""


def identify_prime_contractor(job, desc_lower):
    """Try to identify the prime contractor from job details."""
    primes_found = []
    for prime, indicators in PRIME_INDICATORS.items():
        for ind in indicators:
            if ind in desc_lower:
                primes_found.append(prime)
                break
    return primes_found


def map_job_to_programs(job, parsed_desc, federal_programs):
    """Map a job to federal programs using multiple signals."""
    desc = job.get("description", "")
    desc_lower = desc.lower() if desc else ""
    title_lower = job.get("jobTitle", "").lower()
    location = job.get("location", "").lower()
    clearance = job.get("securityClearance", "")
    category = job.get("category", "")

    scores = defaultdict(float)
    evidence = defaultdict(list)

    # Signal 1: Location matching
    for loc_key, programs in LOCATION_PROGRAM_MAP.items():
        if loc_key in location:
            for prog in programs:
                scores[prog] += 3.0
                evidence[prog].append(f"Location: {loc_key}")

    # Signal 2: Keyword matching in description and title
    combined_text = f"{title_lower} {desc_lower}"
    for keyword, programs in KEYWORD_PROGRAM_MAP.items():
        if keyword in combined_text:
            for prog in programs:
                scores[prog] += 4.0
                evidence[prog].append(f"Keyword: {keyword}")

    # Signal 3: Clearance-based relevance
    if clearance:
        for cl_level, programs in CLEARANCE_PROGRAM_WEIGHT.items():
            if cl_level.lower() in clearance.lower():
                for prog in programs:
                    scores[prog] += 1.5
                    evidence[prog].append(f"Clearance: {cl_level}")

    # Signal 4: Technology stack matching against federal programs
    for fp in federal_programs:
        fp_name = (fp.get("Program Name", "") or "").lower()
        fp_acronym = (fp.get("Acronym", "") or "").lower()
        fp_keywords = (fp.get("Keywords/Signals", "") or "").lower()
        fp_roles = (fp.get("Typical Roles", "") or "").lower()
        fp_locations = (fp.get("Key Locations", "") or "").lower()
        fp_prime = (fp.get("Prime Contractor (Consolidated)", "") or "").lower()
        fp_functional = (fp.get("Functional Areas", "") or "").lower()

        # Check if acronym appears in job text
        if fp_acronym and len(fp_acronym) > 2 and fp_acronym in combined_text:
            prog_label = fp.get("Acronym") or fp.get("Program Name", "")
            scores[prog_label] += 5.0
            evidence[prog_label].append(f"Direct program match: {fp_acronym}")

        # Check location overlap
        if fp_locations:
            for loc_part in location.split(","):
                loc_part = loc_part.strip()
                if loc_part and len(loc_part) > 3 and loc_part in fp_locations:
                    prog_label = fp.get("Acronym") or fp.get("Program Name", "")
                    scores[prog_label] += 2.0
                    evidence[prog_label].append(f"Program location match: {loc_part}")

        # Check functional area overlap
        if fp_functional:
            if category and category.lower() in fp_functional:
                prog_label = fp.get("Acronym") or fp.get("Program Name", "")
                scores[prog_label] += 1.5
                evidence[prog_label].append(f"Functional area: {category}")

    # Signal 5: Prime contractor identification
    primes = identify_prime_contractor(job, desc_lower)

    # Sort and return top matches
    sorted_programs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_programs = [
        (prog, score, evidence[prog]) for prog, score in sorted_programs if score >= 3.0
    ][:5]

    return {
        "primary_program": top_programs[0][0] if top_programs else "Unknown",
        "primary_score": top_programs[0][1] if top_programs else 0,
        "primary_evidence": top_programs[0][2] if top_programs else [],
        "all_program_matches": top_programs,
        "identified_primes": primes,
        "confidence": "High"
        if (top_programs and top_programs[0][1] >= 8)
        else "Moderate"
        if (top_programs and top_programs[0][1] >= 5)
        else "Low"
        if top_programs
        else "Unknown",
    }


# === CONTACT MATCHING ===


def build_contact_index(contacts, bullhorn_contacts, bullhorn_timeline):
    """Build searchable indexes for contacts."""
    # Index by company
    company_contacts = defaultdict(list)
    for c in contacts:
        company = (c.get("company") or "").strip()
        if company:
            company_contacts[company.lower()].append(c)

    # Name -> dashboard contact lookup (for enriching Bullhorn contacts)
    name_to_dashboard = {}
    for c in contacts:
        name = (c.get("name") or "").strip().lower()
        if name:
            name_to_dashboard[name] = c
        # Also index by firstName + lastName
        first = (c.get("firstName") or "").strip()
        last = (c.get("lastName") or "").strip()
        if first and last:
            name_to_dashboard[f"{first} {last}".lower()] = c
            # Also index last, first
            name_to_dashboard[f"{last}, {first}".lower()] = c

    # Also map GDIT -> General Dynamics since dashboard contacts are GDIT-labeled
    if "gdit" in company_contacts:
        company_contacts["general dynamics"] = (
            company_contacts.get("general dynamics", []) + company_contacts["gdit"]
        )
    elif "general dynamics" not in company_contacts:
        # Check if all contacts are GDIT-labeled
        for c in contacts:
            comp = (c.get("company") or "").lower()
            if "gd" in comp or "general" in comp:
                company_contacts["general dynamics"].append(c)

    # Build note summaries from timeline
    contact_notes = defaultdict(list)
    for entry in bullhorn_timeline:
        contact_name = (entry.get("contact") or "").strip()
        if contact_name:
            contact_notes[contact_name.lower()].append(
                {
                    "date": entry.get("date", ""),
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", "")[:200],
                    "companies": entry.get("companies", ""),
                    "programs": entry.get("programs", ""),
                }
            )

    # Index bullhorn contacts by company
    bh_company_contacts = defaultdict(list)
    for bc in bullhorn_contacts:
        companies_str = bc.get("companies", "[]")
        try:
            companies = (
                ast.literal_eval(companies_str) if companies_str and companies_str != "[]" else []
            )
        except (ValueError, SyntaxError):
            companies = []
        for company in companies:
            bh_company_contacts[company.lower()].append(bc)

    # Extract emails and phones mentioned in notes per contact
    contact_details_from_notes = defaultdict(lambda: {"emails": set(), "phones": set()})
    for entry in bullhorn_timeline:
        contact_name = (entry.get("contact") or "").strip().lower()
        summary = entry.get("summary", "")
        if contact_name and summary:
            import re as re_mod

            emails = re_mod.findall(r"[\w.+-]+@[\w.-]+\.\w+", summary)
            phones = re_mod.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", summary)
            contact_details_from_notes[contact_name]["emails"].update(emails)
            contact_details_from_notes[contact_name]["phones"].update(phones)

    return (
        company_contacts,
        contact_notes,
        bh_company_contacts,
        name_to_dashboard,
        contact_details_from_notes,
    )


def find_matching_contacts(program_mapping, ref_data, contact_index):
    """Find contacts relevant to the job's program and prime."""
    (
        company_contacts,
        contact_notes,
        bh_company_contacts,
        name_to_dashboard,
        contact_details_from_notes,
    ) = contact_index
    primes = program_mapping.get("identified_primes", [])
    programs = [m[0] for m in program_mapping.get("all_program_matches", [])]

    matched = []

    # Search by prime contractor
    for prime in primes:
        prime_lower = prime.lower()
        # Dashboard contacts (have email, phone, title)
        for c in company_contacts.get(prime_lower, []):
            c_name_lower = (c.get("name") or "").lower()
            notes_for_contact = contact_notes.get(c_name_lower, [])
            note_summary = "; ".join(
                [n["summary"][:100] for n in notes_for_contact[-3:]]
            )
            # Also check notes for email/phone if dashboard doesn't have them
            email = c.get("email", "") or ""
            phone = c.get("phone", "") or ""
            if (
                not email or email == "None"
            ) and c_name_lower in contact_details_from_notes:
                emails = contact_details_from_notes[c_name_lower]["emails"]
                email = next(iter(emails), "")
            if (
                not phone or phone == "None"
            ) and c_name_lower in contact_details_from_notes:
                phones = contact_details_from_notes[c_name_lower]["phones"]
                phone = next(iter(phones), "")
            matched.append(
                {
                    "name": c.get("name", ""),
                    "job_title": c.get("jobTitle", ""),
                    "company": c.get("company", ""),
                    "email": email if email != "None" else "",
                    "phone": phone if phone != "None" else "",
                    "city": c.get("city", ""),
                    "state": c.get("state", ""),
                    "tier": c.get("tier", ""),
                    "source": "Dashboard",
                    "recent_notes": note_summary,
                }
            )
        # Bullhorn contacts - cross-reference with dashboard for details
        for bc in bh_company_contacts.get(prime_lower, []):
            bc_name = bc.get("name", "")
            bc_name_lower = bc_name.lower().strip()
            notes_for_contact = contact_notes.get(bc_name_lower, [])
            note_summary = "; ".join(
                [n["summary"][:100] for n in notes_for_contact[-3:]]
            )
            # Try to find this contact in dashboard data for email/phone/title
            dashboard_match = name_to_dashboard.get(bc_name_lower, {})
            # Also check notes for extracted emails/phones
            email = dashboard_match.get("email", "") or ""
            phone = dashboard_match.get("phone", "") or ""
            if (
                not email or email == "None"
            ) and bc_name_lower in contact_details_from_notes:
                emails = contact_details_from_notes[bc_name_lower]["emails"]
                email = next(iter(emails), "")
            if (
                not phone or phone == "None"
            ) and bc_name_lower in contact_details_from_notes:
                phones = contact_details_from_notes[bc_name_lower]["phones"]
                phone = next(iter(phones), "")
            matched.append(
                {
                    "name": bc_name,
                    "job_title": dashboard_match.get("jobTitle", ""),
                    "company": prime,
                    "email": email if email != "None" else "",
                    "phone": phone if phone != "None" else "",
                    "city": dashboard_match.get("city", ""),
                    "state": dashboard_match.get("state", ""),
                    "tier": dashboard_match.get("tier", ""),
                    "source": "Bullhorn+Dashboard" if dashboard_match else "Bullhorn",
                    "recent_notes": note_summary,
                }
            )

    # Deduplicate by name
    seen = set()
    unique = []
    for m in matched:
        name = m["name"].lower().strip()
        if name and name not in seen:
            seen.add(name)
            unique.append(m)

    # Sort by tier (lower = higher priority), limit to top 20
    unique.sort(key=lambda x: int(x.get("tier") or 99))
    return unique[:20]


# === PAST PERFORMANCE ===


def find_past_performance(program_mapping, ref_data):
    """Find PTS past performance data for the job's prime/program/location."""
    primes = program_mapping.get("identified_primes", [])
    past_perf = ref_data["past_performance"]
    placements = ref_data["placements"]

    results = {
        "prime_performance": [],
        "relevant_placements": [],
        "total_placements_at_prime": 0,
        "active_placements_at_prime": 0,
        "avg_bill_rate": 0,
        "avg_margin": 0,
        "relationship_strength": "None",
    }

    for prime in primes:
        prime_lower = prime.lower()
        # Find past performance record
        for pp in past_perf:
            pp_prime = (pp.get("prime_contractor") or "").lower()
            if prime_lower in pp_prime or pp_prime in prime_lower:
                results["prime_performance"].append(
                    {
                        "prime": pp.get("prime_contractor", ""),
                        "total_jobs": pp.get("total_jobs", 0),
                        "filled_jobs": pp.get("filled_jobs", 0),
                        "total_placements": pp.get("total_placements", 0),
                        "avg_bill_rate": pp.get("avg_bill_rate", 0),
                        "avg_pay_rate": pp.get("avg_pay_rate", 0),
                        "avg_margin": pp.get("avg_margin", 0),
                        "fill_rate": pp.get("fill_rate", 0),
                        "relationship_strength": pp.get("relationship_strength", ""),
                        "is_defense_prime": pp.get("is_defense_prime", ""),
                        "estimated_annual_revenue": pp.get(
                            "estimated_annual_revenue", 0
                        ),
                    }
                )
                results["relationship_strength"] = pp.get("relationship_strength", "")
                try:
                    results["avg_bill_rate"] = float(pp.get("avg_bill_rate", 0) or 0)
                    results["avg_margin"] = float(pp.get("avg_margin", 0) or 0)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse financial data for {prime_lower}: {e}")

        # Find relevant placements
        for pl in placements:
            pl_prime = (pl.get("prime_contractor") or "").lower()
            if prime_lower in pl_prime or pl_prime in prime_lower:
                results["total_placements_at_prime"] += 1
                if pl.get("status") in ("Active", "Submitted"):
                    results["active_placements_at_prime"] += 1
                results["relevant_placements"].append(
                    {
                        "candidate": pl.get("candidate", ""),
                        "job_title": pl.get("job_title", ""),
                        "status": pl.get("status", ""),
                        "start_date": pl.get("start_date", ""),
                        "bill_rate": pl.get("bill_rate", ""),
                        "margin_percent": pl.get("margin_percent", ""),
                    }
                )

    # Limit placements shown
    results["relevant_placements"] = results["relevant_placements"][:15]
    return results


# === BD SCORING ===


def calculate_bd_score(job, program_mapping, past_perf):
    """Calculate a BD priority score for the job."""
    score = 0
    reasons = []

    clearance = (job.get("securityClearance") or "").lower()

    # Clearance value (cleared jobs = higher BD value)
    if "ts/sci" in clearance and "poly" in clearance:
        score += 25
        reasons.append("TS/SCI w/ Poly (+25)")
    elif "ts/sci" in clearance:
        score += 20
        reasons.append("TS/SCI (+20)")
    elif "top secret" in clearance:
        score += 18
        reasons.append("Top Secret (+18)")
    elif "secret" in clearance:
        score += 15
        reasons.append("Secret (+15)")

    # Program match quality
    confidence = program_mapping.get("confidence", "Unknown")
    if confidence == "High":
        score += 20
        reasons.append("Strong program match (+20)")
    elif confidence == "Moderate":
        score += 12
        reasons.append("Moderate program match (+12)")
    elif confidence == "Low":
        score += 5
        reasons.append("Weak program match (+5)")

    # Existing prime relationship
    rel = past_perf.get("relationship_strength", "")
    if rel == "Strategic":
        score += 25
        reasons.append(f"Strategic relationship (+25)")
    elif rel == "Strong":
        score += 20
        reasons.append(f"Strong relationship (+20)")
    elif rel == "Growing":
        score += 15
        reasons.append(f"Growing relationship (+15)")
    elif rel == "Established":
        score += 12
        reasons.append(f"Established relationship (+12)")
    elif rel == "Emerging":
        score += 5
        reasons.append(f"Emerging relationship (+5)")

    # Active placements at prime
    active = past_perf.get("active_placements_at_prime", 0)
    if active > 5:
        score += 15
        reasons.append(f"{active} active placements (+15)")
    elif active > 0:
        score += 10
        reasons.append(f"{active} active placements (+10)")

    # Employment type (contract = faster revenue)
    emp_type = (job.get("employmentType") or "").lower()
    if "contract" in emp_type:
        score += 5
        reasons.append("Contract role (+5)")

    # Cap at 100
    score = min(score, 100)

    # Priority label
    if score >= 80:
        priority = "Critical"
    elif score >= 60:
        priority = "High"
    elif score >= 40:
        priority = "Medium"
    elif score >= 20:
        priority = "Low"
    else:
        priority = "Research"

    return score, priority, reasons


# === MAIN PIPELINE ===


def enrich_jobs(jobs, ref_data):
    """Main enrichment pipeline for all jobs."""
    print(f"\nEnriching {len(jobs)} jobs...")

    # Build contact index
    contact_index = build_contact_index(
        ref_data["contacts"],
        ref_data["bullhorn_contacts"],
        ref_data["bullhorn_timeline"],
    )

    enriched = []
    for i, job in enumerate(jobs):
        if (i + 1) % 25 == 0:
            print(f"  Processing job {i + 1}/{len(jobs)}...")

        # Parse description
        parsed_desc = parse_description(job.get("description", ""))

        # Map to programs
        program_mapping = map_job_to_programs(
            job, parsed_desc, ref_data["federal_programs"]
        )

        # Find matching contacts
        matched_contacts = find_matching_contacts(
            program_mapping, ref_data, contact_index
        )

        # Find past performance
        past_perf = find_past_performance(program_mapping, ref_data)

        # Calculate BD score
        bd_score, bd_priority, bd_reasons = calculate_bd_score(
            job, program_mapping, past_perf
        )

        # Build enriched record
        record = {
            # === CORE JOB FIELDS ===
            "job_number": job.get("jobNumber", ""),
            "job_title": job.get("jobTitle", ""),
            "job_url": job.get("url", ""),
            "location": job.get("location", ""),
            "state": extract_state_from_location(job.get("location", "")),
            "employment_type": job.get("employmentType", ""),
            "date_posted": job.get("datePosted", ""),
            "security_clearance": job.get("securityClearance", ""),
            "pay_rate": job.get("payRate", ""),
            "duration": job.get("duration", ""),
            "category": job.get("category", ""),
            "req_number": job.get("reqNumber", ""),
            "scraped_at": job.get("scrapedAt", ""),
            # === PARSED DESCRIPTION ===
            "job_overview": parsed_desc["overview"][:500],
            "responsibilities": " | ".join(parsed_desc["responsibilities"][:10]),
            "qualifications_required": " | ".join(
                parsed_desc["qualifications_required"][:10]
            ),
            "qualifications_preferred": " | ".join(
                parsed_desc["qualifications_preferred"][:10]
            ),
            "skills_extracted": " | ".join(parsed_desc["skills"][:10]),
            "technologies": " | ".join(parsed_desc["technologies"]),
            "certifications": " | ".join(parsed_desc["certifications"]),
            "education_requirements": " | ".join(parsed_desc["education"][:5]),
            "experience_years": parsed_desc["experience_years"],
            "clearance_details": parsed_desc["clearance_details"],
            "work_schedule": parsed_desc["work_schedule"],
            "compensation_details": str(parsed_desc["compensation_details"])[:200]
            if parsed_desc["compensation_details"]
            else "",
            # === PROGRAM MAPPING ===
            "mapped_program": program_mapping["primary_program"],
            "program_confidence": program_mapping["confidence"],
            "program_match_score": program_mapping["primary_score"],
            "program_evidence": " | ".join(program_mapping["primary_evidence"][:5]),
            "all_program_matches": " | ".join(
                [f"{p[0]} ({p[1]:.0f})" for p in program_mapping["all_program_matches"]]
            ),
            "identified_prime_contractor": " | ".join(
                program_mapping["identified_primes"]
            )
            if program_mapping["identified_primes"]
            else "Unknown - Requires Research",
            # === BD SCORING ===
            "bd_score": bd_score,
            "bd_priority": bd_priority,
            "bd_score_reasons": " | ".join(bd_reasons),
            # === MATCHING CONTACTS ===
            "contacts_count": len(matched_contacts),
            "contacts_summary": "",
            "contact_1_name": "",
            "contact_1_title": "",
            "contact_1_company": "",
            "contact_1_email": "",
            "contact_1_phone": "",
            "contact_1_location": "",
            "contact_1_notes": "",
            "contact_2_name": "",
            "contact_2_title": "",
            "contact_2_company": "",
            "contact_2_email": "",
            "contact_2_phone": "",
            "contact_2_location": "",
            "contact_2_notes": "",
            "contact_3_name": "",
            "contact_3_title": "",
            "contact_3_company": "",
            "contact_3_email": "",
            "contact_3_phone": "",
            "contact_3_location": "",
            "contact_3_notes": "",
            "contact_4_name": "",
            "contact_4_title": "",
            "contact_4_company": "",
            "contact_4_email": "",
            "contact_4_phone": "",
            "contact_4_location": "",
            "contact_4_notes": "",
            "contact_5_name": "",
            "contact_5_title": "",
            "contact_5_company": "",
            "contact_5_email": "",
            "contact_5_phone": "",
            "contact_5_location": "",
            "contact_5_notes": "",
            "all_contacts_detail": "",
            # === PAST PERFORMANCE ===
            "pts_relationship_strength": past_perf["relationship_strength"],
            "pts_total_placements_at_prime": past_perf["total_placements_at_prime"],
            "pts_active_placements_at_prime": past_perf["active_placements_at_prime"],
            "pts_avg_bill_rate": past_perf["avg_bill_rate"],
            "pts_avg_margin": past_perf["avg_margin"],
            "pts_past_performance_summary": "",
            "pts_relevant_placements": "",
        }

        # Fill contact details
        contacts_summary_parts = []
        for j, contact in enumerate(matched_contacts[:5]):
            prefix = f"contact_{j + 1}"
            record[f"{prefix}_name"] = contact["name"]
            record[f"{prefix}_title"] = contact["job_title"]
            record[f"{prefix}_company"] = contact["company"]
            record[f"{prefix}_email"] = contact["email"]
            record[f"{prefix}_phone"] = contact["phone"]
            record[f"{prefix}_location"] = (
                f"{contact['city']}, {contact['state']}"
                if contact["city"]
                else contact["state"]
            )
            record[f"{prefix}_notes"] = contact["recent_notes"][:300]
            contacts_summary_parts.append(
                f"{contact['name']} ({contact['job_title']}) at {contact['company']} "
                f"[{contact['email']}] [{contact['phone']}]"
            )

        record["contacts_summary"] = " || ".join(contacts_summary_parts)

        # All contacts detail (for the full list beyond top 5)
        all_contacts_lines = []
        for contact in matched_contacts:
            loc = (
                f"{contact['city']}, {contact['state']}"
                if contact["city"]
                else contact["state"]
            )
            all_contacts_lines.append(
                f"{contact['name']} | {contact['job_title']} | {contact['company']} | "
                f"{loc} | {contact['phone']} | {contact['email']} | Notes: {contact['recent_notes'][:150]}"
            )
        record["all_contacts_detail"] = " ||| ".join(all_contacts_lines)

        # Past performance summary
        pp_summaries = []
        for pp in past_perf["prime_performance"]:
            pp_summaries.append(
                f"{pp['prime']}: {pp['total_placements']} placements, "
                f"{pp['filled_jobs']} filled jobs, "
                f"${pp['avg_bill_rate']}/hr avg bill, "
                f"{pp['avg_margin']}% avg margin, "
                f"Relationship: {pp['relationship_strength']}, "
                f"Est Revenue: ${pp['estimated_annual_revenue']}"
            )
        record["pts_past_performance_summary"] = " || ".join(pp_summaries)

        # Relevant placements detail
        placement_lines = []
        for pl in past_perf["relevant_placements"][:10]:
            placement_lines.append(
                f"{pl['candidate']} - {pl['job_title']} ({pl['status']}) "
                f"Started: {pl['start_date']} Bill: ${pl['bill_rate']}/hr Margin: {pl['margin_percent']}%"
            )
        record["pts_relevant_placements"] = " || ".join(placement_lines)

        enriched.append(record)

    return enriched


def write_output(enriched, output_dir):
    """Write enriched data to CSV and JSON."""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # CSV output
    csv_path = os.path.join(
        output_dir, f"Insight_Global_Jobs_DataMapped_Enriched_{timestamp}.csv"
    )
    if enriched:
        fieldnames = list(enriched[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)
    print(f"\nCSV output: {csv_path}")

    # JSON output
    json_path = os.path.join(
        output_dir, f"Insight_Global_Jobs_DataMapped_Enriched_{timestamp}.json"
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, default=str)
    print(f"JSON output: {json_path}")

    # Summary report
    summary_path = os.path.join(
        output_dir, f"Insight_Global_Jobs_Enrichment_Summary_{timestamp}.md"
    )
    write_summary_report(enriched, summary_path)
    print(f"Summary: {summary_path}")

    return csv_path, json_path, summary_path


def write_summary_report(enriched, filepath):
    """Write a markdown summary report of the enrichment results."""
    from collections import Counter

    total = len(enriched)
    priorities = Counter(r["bd_priority"] for r in enriched)
    programs = Counter(r["mapped_program"] for r in enriched)
    primes = Counter()
    for r in enriched:
        for p in (r.get("identified_prime_contractor") or "").split(" | "):
            if p and p != "Unknown - Requires Research":
                primes[p] += 1
    confidences = Counter(r["program_confidence"] for r in enriched)
    clearances = Counter(r["security_clearance"] for r in enriched)
    categories = Counter(r["category"] for r in enriched)
    states = Counter(r["state"] for r in enriched)
    emp_types = Counter(r["employment_type"] for r in enriched)

    with_contacts = sum(1 for r in enriched if r["contacts_count"] > 0)
    with_past_perf = sum(1 for r in enriched if r["pts_total_placements_at_prime"] > 0)

    lines = [
        "# Insight Global Jobs - Enrichment Summary Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Jobs Processed:** {total}",
        f"**Jobs with Matching Contacts:** {with_contacts} ({with_contacts * 100 // total}%)",
        f"**Jobs with PTS Past Performance:** {with_past_perf} ({with_past_perf * 100 // total}%)",
        "",
        "---",
        "",
        "## BD Priority Distribution",
        "",
        "| Priority | Count | % |",
        "|----------|-------|---|",
    ]
    for p in ["Critical", "High", "Medium", "Low", "Research"]:
        count = priorities.get(p, 0)
        lines.append(f"| {p} | {count} | {count * 100 // total}% |")

    lines.extend(
        [
            "",
            "## Program Mapping Confidence",
            "",
            "| Confidence | Count | % |",
            "|-----------|-------|---|",
        ]
    )
    for c in ["High", "Moderate", "Low", "Unknown"]:
        count = confidences.get(c, 0)
        lines.append(f"| {c} | {count} | {count * 100 // total}% |")

    lines.extend(
        [
            "",
            "## Top Mapped Programs",
            "",
            "| Program | Jobs |",
            "|---------|------|",
        ]
    )
    for prog, count in programs.most_common(20):
        lines.append(f"| {prog} | {count} |")

    lines.extend(
        [
            "",
            "## Identified Prime Contractors",
            "",
            "| Prime | Jobs |",
            "|-------|------|",
        ]
    )
    for prime, count in primes.most_common():
        lines.append(f"| {prime} | {count} |")

    lines.extend(
        [
            "",
            "## Clearance Distribution",
            "",
            "| Clearance | Jobs |",
            "|-----------|------|",
        ]
    )
    for cl, count in clearances.most_common():
        lines.append(f"| {cl or 'None'} | {count} |")

    lines.extend(
        [
            "",
            "## Employment Type",
            "",
            "| Type | Jobs |",
            "|------|------|",
        ]
    )
    for et, count in emp_types.most_common():
        lines.append(f"| {et} | {count} |")

    lines.extend(
        [
            "",
            "## Top States",
            "",
            "| State | Jobs |",
            "|-------|------|",
        ]
    )
    for state, count in states.most_common(15):
        lines.append(f"| {state or 'Unknown'} | {count} |")

    lines.extend(
        [
            "",
            "## Top Categories",
            "",
            "| Category | Jobs |",
            "|----------|------|",
        ]
    )
    for cat, count in categories.most_common(15):
        lines.append(f"| {cat} | {count} |")

    # Top BD-scored jobs
    top_jobs = sorted(enriched, key=lambda x: x["bd_score"], reverse=True)[:20]
    lines.extend(
        [
            "",
            "---",
            "",
            "## Top 20 BD Priority Jobs",
            "",
            "| Rank | Score | Priority | Job Title | Location | Clearance | Prime | Program |",
            "|------|-------|----------|-----------|----------|-----------|-------|---------|",
        ]
    )
    for i, job in enumerate(top_jobs, 1):
        lines.append(
            f"| {i} | {job['bd_score']} | {job['bd_priority']} | "
            f"{job['job_title'][:40]} | {job['location'][:25]} | "
            f"{job['security_clearance']} | {job['identified_prime_contractor'][:20]} | "
            f"{job['mapped_program'][:20]} |"
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if len(sys.argv) < 2:
        # Try to find the file in the project root
        import glob

        pattern = os.path.join(PROJECT_DIR, "dataset_puppeteer-scraper_*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if files:
            input_path = files[0]
        else:
            print("ERROR: No scraper JSON file found. Provide path as argument.")
            sys.exit(1)
    else:
        input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    print(f"=== Insight Global Jobs - Data Mapping & Enrichment ===")
    print(f"Source: {input_path}")
    print()

    # Load raw jobs
    print("Loading scraper data...")
    with open(input_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    print(f"  Raw jobs: {len(jobs)}")

    # Load reference data
    ref_data = load_reference_data()

    # Enrich all jobs
    enriched = enrich_jobs(jobs, ref_data)

    # Write output
    csv_path, json_path, summary_path = write_output(enriched, OUTPUT_DIR)

    # Move source file to proper location
    scraper_data_dir = os.path.join(PROJECT_DIR, "Engine1_Scraper", "data")
    os.makedirs(scraper_data_dir, exist_ok=True)
    dest_path = os.path.join(scraper_data_dir, os.path.basename(input_path))
    if not os.path.exists(dest_path):
        import shutil

        shutil.move(input_path, dest_path)
        print(f"\nMoved source file to: {dest_path}")
    else:
        print(f"\nSource file already exists at: {dest_path}")

    # Print summary stats
    from collections import Counter

    priorities = Counter(r["bd_priority"] for r in enriched)
    print(f"\n=== ENRICHMENT COMPLETE ===")
    print(f"Total jobs enriched: {len(enriched)}")
    print(f"BD Priority breakdown:")
    for p in ["Critical", "High", "Medium", "Low", "Research"]:
        print(f"  {p}: {priorities.get(p, 0)}")
    print(f"\nOutput files:")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    main()
