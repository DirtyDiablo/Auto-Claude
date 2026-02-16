"""
Phase 21A — Cypher Query Library

Pre-built Cypher queries for BD intelligence operations.
All queries return structured dicts, not raw Neo4j records.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GraphQueries:
    """Pre-built Cypher queries for BD Intelligence."""

    def __init__(self, manager: "Neo4jManager") -> None:
        self._mgr = manager

    # ── 1. Contacts by program ───────────────────────────

    def find_contacts_by_program(self, program_name: str) -> list[dict]:
        """All people on a given program with their tier and priority."""
        results = self._mgr.run_query(
            """
            MATCH (p:Person)-[r:MANAGES|WORKS_AT*1..2]-(pr:Program)
            WHERE pr.name =~ $pattern OR pr.acronym =~ $pattern
            RETURN DISTINCT p.name AS name, p.title AS title, p.tier AS tier,
                   p.bd_priority AS bd_priority, p.company AS company,
                   p.email AS email, p.phone AS phone
            ORDER BY p.tier ASC, p.name ASC
            LIMIT 100
            """,
            {"pattern": f"(?i).*{program_name}.*"},
        )
        return results

    # ── 2. Shortest path ────────────────────────────────

    def find_shortest_path(self, person_a: str, person_b: str) -> dict:
        """Shortest relationship path between two people."""
        result = self._mgr.run_single(
            """
            MATCH (a:Person), (b:Person),
                  path = shortestPath((a)-[*..8]-(b))
            WHERE a.name =~ $pattern_a AND b.name =~ $pattern_b
            RETURN [n IN nodes(path) | {
                name: CASE WHEN n:Person THEN n.name
                           WHEN n:Company THEN n.name
                           WHEN n:Program THEN n.name
                           ELSE labels(n)[0] END,
                type: labels(n)[0]
            }] AS path_nodes,
            [r IN relationships(path) | type(r)] AS path_rels,
            length(path) AS hops
            """,
            {"pattern_a": f"(?i).*{person_a}.*", "pattern_b": f"(?i).*{person_b}.*"},
        )
        if not result:
            return {
                "from": person_a,
                "to": person_b,
                "path": [],
                "hops": 0,
                "found": False,
            }
        return {
            "from": person_a,
            "to": person_b,
            "path": result.get("path_nodes", []),
            "relationships": result.get("path_rels", []),
            "hops": result.get("hops", 0),
            "found": True,
        }

    # ── 3. Introduction path ────────────────────────────

    def find_introduction_path(self, target_person: str) -> list[dict]:
        """Best warm introduction paths from any PTS contact to target."""
        results = self._mgr.run_query(
            """
            MATCH (target:Person)
            WHERE target.name =~ $pattern
            WITH target
            MATCH (pts:Person)
            WHERE pts.company =~ '(?i).*pts.*' OR pts.source_db = 'internal'
            WITH pts, target
            MATCH path = shortestPath((pts)-[*..6]-(target))
            RETURN pts.name AS from_person,
                   target.name AS to_person,
                   length(path) AS hops,
                   [n IN nodes(path) | coalesce(n.name, labels(n)[0])] AS path_names
            ORDER BY hops ASC
            LIMIT 5
            """,
            {"pattern": f"(?i).*{target_person}.*"},
        )
        return results

    # ── 4. Program org chart ────────────────────────────

    def get_program_org_chart(self, program_name: str) -> dict:
        """Hierarchical view of all people on a program."""
        results = self._mgr.run_query(
            """
            MATCH (pr:Program)
            WHERE pr.name =~ $pattern OR pr.acronym =~ $pattern
            WITH pr
            OPTIONAL MATCH (p:Person)-[:MANAGES]->(pr)
            WITH pr, collect({name: p.name, title: p.title, tier: p.tier, role: 'manager'}) AS managers
            OPTIONAL MATCH (p2:Person)-[:WORKS_AT]->(c:Company)-[:PRIMES_ON]->(pr)
            WITH pr, managers, collect(DISTINCT {name: p2.name, title: p2.title, tier: p2.tier, company: c.name, role: 'team'}) AS team
            RETURN pr.name AS program, pr.acronym AS acronym,
                   pr.prime_contractor AS prime, pr.agency_owner AS agency,
                   managers, team
            """,
            {"pattern": f"(?i).*{program_name}.*"},
        )
        if not results:
            return {"program": program_name, "managers": [], "team": []}
        r = results[0]
        return {
            "program": r.get("program"),
            "acronym": r.get("acronym"),
            "prime": r.get("prime"),
            "agency": r.get("agency"),
            "managers": r.get("managers", []),
            "team": r.get("team", []),
        }

    # ── 5. Company network ──────────────────────────────

    def get_company_network(self, company_name: str) -> dict:
        """All programs, people, and subs for a company."""
        results = self._mgr.run_query(
            """
            MATCH (c:Company)
            WHERE c.name =~ $pattern
            WITH c
            OPTIONAL MATCH (c)-[:PRIMES_ON]->(pr:Program)
            WITH c, collect(DISTINCT {name: pr.name, acronym: pr.acronym, value: pr.value}) AS programs
            OPTIONAL MATCH (p:Person)-[:WORKS_AT]->(c)
            WITH c, programs, collect(DISTINCT {name: p.name, title: p.title, tier: p.tier}) AS people
            OPTIONAL MATCH (sub:Company)-[:SUBS_TO]->(c)
            WITH c, programs, people, collect(DISTINCT sub.name) AS subs
            RETURN c.name AS company, c.type AS type,
                   c.is_defense_prime AS defense_prime,
                   programs, people, subs,
                   size(programs) AS program_count,
                   size(people) AS people_count
            """,
            {"pattern": f"(?i).*{company_name}.*"},
        )
        if not results:
            return {"company": company_name, "programs": [], "people": [], "subs": []}
        return results[0]

    # ── 6. Hiring signals ───────────────────────────────

    def find_hiring_signals(self, days: int = 30) -> list[dict]:
        """Programs with recent job postings (hiring activity)."""
        results = self._mgr.run_query(
            """
            MATCH (j:Job)-[:MAPPED_TO]->(pr:Program)
            WITH pr, count(j) AS job_count, collect(j.title)[0..3] AS sample_titles
            WHERE job_count >= 2
            OPTIONAL MATCH (c:Company)-[:PRIMES_ON]->(pr)
            RETURN pr.name AS program, pr.acronym AS acronym,
                   job_count, sample_titles,
                   c.name AS prime_contractor
            ORDER BY job_count DESC
            LIMIT 20
            """,
        )
        return results

    # ── 7. Influence leaders ────────────────────────────

    def find_influence_leaders(self, program_name: str) -> list[dict]:
        """People with most relationships/interactions on a program."""
        results = self._mgr.run_query(
            """
            MATCH (p:Person)-[r]-(pr:Program)
            WHERE pr.name =~ $pattern OR pr.acronym =~ $pattern
            WITH p, count(r) AS rel_count
            OPTIONAL MATCH (p)-[:CONTACTED_BY]->(i:Interaction)
            WITH p, rel_count, count(i) AS interaction_count
            RETURN p.name AS name, p.title AS title, p.tier AS tier,
                   p.company AS company,
                   rel_count + interaction_count AS influence_score,
                   rel_count AS relationships,
                   interaction_count AS interactions
            ORDER BY influence_score DESC
            LIMIT 10
            """,
            {"pattern": f"(?i).*{program_name}.*"},
        )
        return results

    # ── 8. Contact 360 ──────────────────────────────────

    def get_contact_360(self, person_name: str) -> dict:
        """Full profile: company, programs, interactions, connections."""
        result = self._mgr.run_single(
            """
            MATCH (p:Person)
            WHERE p.name =~ $pattern
            WITH p
            OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
            OPTIONAL MATCH (p)-[:MANAGES]->(pr:Program)
            WITH p, c, collect(DISTINCT pr.name) AS programs
            OPTIONAL MATCH (p)-[:CONTACTED_BY]->(i:Interaction)
            WITH p, c, programs, count(i) AS interaction_count,
                 collect(DISTINCT {date: i.date, type: i.type, summary: left(i.summary, 100)})[0..5] AS recent_interactions
            OPTIONAL MATCH (p)-[r]-(other:Person)
            WITH p, c, programs, interaction_count, recent_interactions,
                 collect(DISTINCT {name: other.name, relationship: type(r)})[0..10] AS connections
            RETURN p.name AS name, p.title AS title, p.tier AS tier,
                   p.bd_priority AS bd_priority, p.email AS email,
                   p.phone AS phone, p.linkedin AS linkedin,
                   c.name AS company,
                   programs, interaction_count, recent_interactions, connections
            """,
            {"pattern": f"(?i).*{person_name}.*"},
        )
        if not result:
            return {"name": person_name, "found": False}
        result["found"] = True
        return result

    # ── 9. Competitive overlap ──────────────────────────

    def find_competitive_overlap(self, company_a: str, company_b: str) -> dict:
        """Programs where two companies compete."""
        results = self._mgr.run_query(
            """
            MATCH (a:Company)-[:PRIMES_ON|SUBS_TO]->(pr:Program)<-[:PRIMES_ON|SUBS_TO]-(b:Company)
            WHERE a.name =~ $pattern_a AND b.name =~ $pattern_b
            RETURN pr.name AS program, pr.acronym AS acronym,
                   pr.value AS value, pr.agency_owner AS agency
            ORDER BY pr.name
            """,
            {"pattern_a": f"(?i).*{company_a}.*", "pattern_b": f"(?i).*{company_b}.*"},
        )
        return {
            "company_a": company_a,
            "company_b": company_b,
            "overlap_programs": results,
            "overlap_count": len(results),
        }

    # ── 10. Location intelligence ───────────────────────

    def get_location_intel(self, city: str) -> dict:
        """All programs, people, and jobs at a location."""
        results = self._mgr.run_query(
            """
            MATCH (l:Location)
            WHERE l.city =~ $pattern OR l.hub_name =~ $pattern
            WITH l
            OPTIONAL MATCH (pr:Program)-[:LOCATED_AT]->(l)
            WITH l, collect(DISTINCT {name: pr.name, acronym: pr.acronym}) AS programs
            OPTIONAL MATCH (p:Person)-[:LOCATED_IN]->(l)
            WITH l, programs, collect(DISTINCT {name: p.name, title: p.title, company: p.company}) AS people
            OPTIONAL MATCH (j:Job)-[:JOB_AT]->(l)
            WITH l, programs, people, collect(DISTINCT {title: j.title, company: j.clearance}) AS jobs
            RETURN l.hub_name AS location, l.city AS city, l.state AS state,
                   l.coordinates_lat AS lat, l.coordinates_lon AS lon,
                   programs, people, jobs,
                   size(programs) AS program_count,
                   size(people) AS people_count,
                   size(jobs) AS job_count
            """,
            {"pattern": f"(?i).*{city}.*"},
        )
        if not results:
            return {"location": city, "programs": [], "people": [], "jobs": []}
        return results[0]

    # ── 11. Orphan contacts ─────────────────────────────

    def find_orphan_contacts(self) -> list[dict]:
        """People not connected to any program."""
        results = self._mgr.run_query(
            """
            MATCH (p:Person)
            WHERE NOT (p)-[:MANAGES]->(:Program)
                  AND NOT (p)-[:WORKS_AT]->(:Company)-[:PRIMES_ON]->(:Program)
            RETURN p.name AS name, p.title AS title, p.company AS company,
                   p.tier AS tier, p.email AS email
            ORDER BY p.name
            LIMIT 100
            """,
        )
        return results

    # ── 12. Graph stats ─────────────────────────────────

    def get_graph_stats(self) -> dict:
        """Node counts, relationship counts, density metrics."""
        node_labels = [
            "Person",
            "Company",
            "Program",
            "Job",
            "Contract",
            "Location",
            "Interaction",
        ]
        node_counts = {}
        for label in node_labels:
            node_counts[label] = self._mgr.get_node_count(label)

        rel_counts = {}
        rel_types = [
            "WORKS_AT",
            "MANAGES",
            "PRIMES_ON",
            "SUBS_TO",
            "POSTED_BY",
            "MAPPED_TO",
            "BETWEEN",
            "ABOUT",
            "BY_USER",
            "LOCATED_IN",
            "LOCATED_AT",
            "JOB_AT",
            "AWARDED_TO",
        ]
        for rt in rel_types:
            count = self._mgr.get_relationship_count(rt)
            if count > 0:
                rel_counts[rt] = count

        total_nodes = sum(node_counts.values())
        total_rels = sum(rel_counts.values())

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
            "density": round(total_rels / max(total_nodes, 1), 2),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[GraphQueries] = None


def get_graph_queries() -> GraphQueries:
    """Get singleton GraphQueries instance."""
    global _instance
    if _instance is None:
        from Engine8_Knowledge.graph.neo4j_manager import get_neo4j_manager

        _instance = GraphQueries(get_neo4j_manager())
    return _instance
