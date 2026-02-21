"""Portfolio configuration dataclass and default portfolio definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PortfolioConfig:
    """Configuration for a single defense portfolio."""

    id: str
    name: str
    description: str
    estimated_value: str
    keywords: List[str]
    secondary_keywords: List[str]
    programs: List[str]
    agencies: List[str]
    clearance_boost: Dict[str, int]
    keyword_boost: int
    location_keywords: List[str]
    location_boost: int
    competitors: List[str]
    scoring_weights: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Default portfolio definitions
# ---------------------------------------------------------------------------

DCGS_PORTFOLIO = PortfolioConfig(
    id="dcgs",
    name="DCGS (Distributed Common Ground System)",
    description=(
        "Multi-service intelligence processing, exploitation, and dissemination "
        "system family including DCGS-A, DCGS-N, and AF DCGS."
    ),
    estimated_value="$950M",
    keywords=[
        "DCGS",
        "DCGS-A",
        "DCGS-N",
        "AF DCGS",
        "Distributed Common Ground System",
    ],
    secondary_keywords=[
        "ISR",
        "intelligence surveillance reconnaissance",
        "SIGINT",
        "GEOINT",
        "IMINT",
        "ELINT",
        "sensor fusion",
        "intelligence processing",
        "PED",
        "processing exploitation dissemination",
    ],
    programs=[
        "AF DCGS - PACAF",
        "AF DCGS - Langley",
        "AF DCGS - Wright-Patt",
        "Navy DCGS-N",
        "Army DCGS-A",
    ],
    agencies=["US Air Force", "US Army", "US Navy", "DIA", "NGA", "NSA"],
    clearance_boost={
        "TS/SCI w/ Poly": 35,
        "TS/SCI w/ Full Scope Poly": 35,
        "TS/SCI w/ CI Poly": 30,
        "TS/SCI": 25,
        "Top Secret": 15,
        "Secret": 5,
    },
    keyword_boost=20,
    location_keywords=["San Diego", "Hampton", "Dayton", "Langley", "Wright-Patterson"],
    location_boost=10,
    competitors=[
        "Raytheon",
        "Northrop Grumman",
        "BAE Systems",
        "Leidos",
        "L3Harris",
        "Palantir",
    ],
    scoring_weights={
        "clearance": 1.0,
        "keyword": 1.0,
        "location": 1.0,
        "program": 1.0,
    },
)

GBSD_PORTFOLIO = PortfolioConfig(
    id="gbsd",
    name="GBSD (Ground-Based Strategic Deterrent)",
    description=(
        "Next-generation ICBM modernization program replacing Minuteman III. "
        "Full lifecycle nuclear deterrent sustainment and modernization."
    ),
    estimated_value="$264B",
    keywords=[
        "GBSD",
        "Ground Based Strategic Deterrent",
        "Sentinel",
        "LGM-35A",
        "ICBM modernization",
    ],
    secondary_keywords=[
        "nuclear deterrent",
        "strategic deterrent",
        "Minuteman",
        "ICBM",
        "missile defense",
        "nuclear triad",
        "nuclear command control",
        "NC3",
        "strategic forces",
        "global strike",
    ],
    programs=[
        "LGM-35A Sentinel",
        "Minuteman III Sustainment",
        "NC3 Modernization",
        "Nuclear Command Control Communications",
    ],
    agencies=[
        "US Air Force",
        "AFGSC",
        "Air Force Global Strike Command",
        "NNSA",
        "STRATCOM",
    ],
    clearance_boost={
        "TS/SCI w/ Poly": 35,
        "TS/SCI w/ Full Scope Poly": 35,
        "TS/SCI w/ CI Poly": 30,
        "TS/SCI": 25,
        "Top Secret": 15,
        "Secret": 10,
        "Q Clearance": 30,
        "L Clearance": 15,
    },
    keyword_boost=25,
    location_keywords=[
        "Hill AFB",
        "F.E. Warren",
        "Malmstrom",
        "Minot",
        "Roy",
        "Utah",
    ],
    location_boost=10,
    competitors=[
        "Northrop Grumman",
        "Lockheed Martin",
        "Boeing",
        "General Dynamics",
        "Bechtel",
        "RTX",
    ],
    scoring_weights={
        "clearance": 1.2,
        "keyword": 1.0,
        "location": 0.8,
        "program": 1.0,
    },
)

JADC2_PORTFOLIO = PortfolioConfig(
    id="jadc2",
    name="JADC2 (Joint All-Domain Command and Control)",
    description=(
        "DoD initiative to connect sensors across all domains (air, land, sea, "
        "space, cyber) into a unified command and control network."
    ),
    estimated_value="$15B+",
    keywords=[
        "JADC2",
        "Joint All-Domain Command and Control",
        "Joint All Domain",
        "CJADC2",
        "Combined JADC2",
    ],
    secondary_keywords=[
        "multi-domain operations",
        "MDO",
        "data fusion",
        "kill chain",
        "sensor to shooter",
        "mission partner environment",
        "cross-domain",
        "all-domain",
        "command and control",
        "C2",
        "C4ISR",
        "joint fires",
    ],
    programs=[
        "ABMS",
        "Project Convergence",
        "Project Overmatch",
        "CJADC2",
        "Joint Fires Network",
    ],
    agencies=[
        "Joint Staff",
        "US Air Force",
        "US Army",
        "US Navy",
        "OUSD(R&E)",
        "CDAO",
        "DISA",
    ],
    clearance_boost={
        "TS/SCI w/ Poly": 35,
        "TS/SCI w/ Full Scope Poly": 35,
        "TS/SCI w/ CI Poly": 30,
        "TS/SCI": 25,
        "Top Secret": 15,
        "Secret": 5,
    },
    keyword_boost=20,
    location_keywords=[
        "Pentagon",
        "Arlington",
        "Fort Belvoir",
        "Scott AFB",
        "Fort Liberty",
        "Fort Meade",
    ],
    location_boost=8,
    competitors=[
        "Lockheed Martin",
        "Northrop Grumman",
        "Raytheon",
        "L3Harris",
        "Palantir",
        "Anduril",
        "Microsoft",
    ],
    scoring_weights={
        "clearance": 1.0,
        "keyword": 1.1,
        "location": 0.7,
        "program": 1.0,
    },
)

ABMS_PORTFOLIO = PortfolioConfig(
    id="abms",
    name="ABMS (Advanced Battle Management System)",
    description=(
        "USAF digital infrastructure for connecting joint force sensors and "
        "shooters. Air and space C2 modernization with edge computing and AI."
    ),
    estimated_value="$4B+",
    keywords=[
        "ABMS",
        "Advanced Battle Management System",
        "battle management",
        "battle network",
    ],
    secondary_keywords=[
        "air operations center",
        "AOC",
        "edge computing",
        "tactical edge",
        "air C2",
        "space C2",
        "digital infrastructure",
        "cloud to edge",
        "DevSecOps",
        "data mesh",
        "digital engineering",
    ],
    programs=[
        "ABMS Digital Infrastructure",
        "AOC Modernization",
        "ABMS On-Ramp",
        "Kessel Run",
        "Platform One",
    ],
    agencies=[
        "US Air Force",
        "Air Combat Command",
        "Air Force Life Cycle Management Center",
        "Space Force",
        "AFLCMC",
    ],
    clearance_boost={
        "TS/SCI w/ Poly": 30,
        "TS/SCI w/ Full Scope Poly": 30,
        "TS/SCI w/ CI Poly": 25,
        "TS/SCI": 20,
        "Top Secret": 15,
        "Secret": 5,
    },
    keyword_boost=20,
    location_keywords=[
        "Hanscom AFB",
        "Langley AFB",
        "Tyndall AFB",
        "San Antonio",
        "Colorado Springs",
    ],
    location_boost=8,
    competitors=[
        "Lockheed Martin",
        "Northrop Grumman",
        "Boeing",
        "L3Harris",
        "Palantir",
        "Anduril",
    ],
    scoring_weights={
        "clearance": 0.9,
        "keyword": 1.2,
        "location": 0.8,
        "program": 1.0,
    },
)

MQ25_PORTFOLIO = PortfolioConfig(
    id="mq25",
    name="MQ-25 Stingray",
    description=(
        "US Navy carrier-based unmanned aerial refueling drone. First operational "
        "carrier-based UAV for fleet logistics and ISR missions."
    ),
    estimated_value="$13B",
    keywords=[
        "MQ-25",
        "MQ-25A",
        "Stingray",
        "MQ25",
        "T1 Stingray",
    ],
    secondary_keywords=[
        "carrier UAV",
        "unmanned aerial refueling",
        "carrier-based drone",
        "CBARS",
        "autonomous aerial refueling",
        "naval aviation",
        "carrier air wing",
        "unmanned carrier",
        "autonomous systems",
        "aerial refueling",
    ],
    programs=[
        "MQ-25A Stingray",
        "CBARS",
        "Carrier-Based Aerial Refueling System",
        "Unmanned Carrier Aviation",
    ],
    agencies=[
        "US Navy",
        "NAVAIR",
        "Naval Air Systems Command",
        "PMA-268",
    ],
    clearance_boost={
        "TS/SCI w/ Poly": 30,
        "TS/SCI w/ Full Scope Poly": 30,
        "TS/SCI w/ CI Poly": 25,
        "TS/SCI": 20,
        "Top Secret": 15,
        "Secret": 10,
    },
    keyword_boost=25,
    location_keywords=[
        "Patuxent River",
        "Pax River",
        "St. Louis",
        "Norfolk",
        "San Diego",
        "Jacksonville",
    ],
    location_boost=10,
    competitors=[
        "Boeing",
        "Lockheed Martin",
        "General Atomics",
        "Northrop Grumman",
    ],
    scoring_weights={
        "clearance": 1.0,
        "keyword": 1.0,
        "location": 1.0,
        "program": 1.1,
    },
)

# All default portfolios in registration order
DEFAULT_PORTFOLIOS: List[PortfolioConfig] = [
    DCGS_PORTFOLIO,
    GBSD_PORTFOLIO,
    JADC2_PORTFOLIO,
    ABMS_PORTFOLIO,
    MQ25_PORTFOLIO,
]
