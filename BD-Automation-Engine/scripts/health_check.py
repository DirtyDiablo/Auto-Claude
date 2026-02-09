#!/usr/bin/env python3
"""
PTS BD Platform — Health Check Script
Run this from Terminal A (BD-Automation-Engine) to get a condensed state report.
Paste the output into the Claude orchestrator chat to update context.

Usage: python scripts/health_check.py
"""

import json
import sys
import os
from datetime import datetime

def check_qdrant():
    """Check Qdrant collections and vector counts."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections().collections
        results = {}
        total = 0
        for col in collections:
            info = client.get_collection(col.name)
            count = info.points_count
            results[col.name] = count
            total += count
        return {"status": "✅", "collections": len(results), "total_vectors": total, "detail": results}
    except Exception as e:
        return {"status": "❌", "error": str(e)}

def check_api():
    """Check Hub API health."""
    try:
        import httpx
        r = httpx.get("http://localhost:8100/health", timeout=5)
        data = r.json()
        return {"status": "✅", "response": data}
    except Exception as e:
        return {"status": "❌", "error": str(e)}

def check_neo4j():
    """Check Neo4j connectivity."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
        driver.close()
        return {"status": "✅", "nodes": nodes, "relationships": rels}
    except Exception as e:
        return {"status": "❌", "error": str(e)}

def check_vite():
    """Check if Vite dev server is running."""
    try:
        import httpx
        r = httpx.get("http://localhost:5173", timeout=3)
        return {"status": "✅", "code": r.status_code}
    except:
        return {"status": "⏸️", "note": "Not running (start with: npm run dev)"}

def check_mem0():
    """Check Mem0 memories in Qdrant."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        info = client.get_collection("bd_memories")
        return {"status": "✅", "memories": info.points_count}
    except:
        return {"status": "⚠️", "memories": 0}

def check_git():
    """Check git status."""
    try:
        import subprocess
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%h %s (%ar)"], text=True
        ).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        return {
            "branch": branch,
            "last_commit": last_commit,
            "dirty_files": len(dirty.split("\n")) if dirty else 0
        }
    except:
        return {"branch": "unknown", "last_commit": "unknown", "dirty_files": "?"}

def format_report(qdrant, api, neo4j, vite, mem0, git):
    """Format a condensed report for pasting into Claude."""
    
    # Build Qdrant summary
    if qdrant["status"] == "✅":
        q_detail = ", ".join(f"{k}:{v:,}" for k, v in sorted(qdrant["detail"].items(), key=lambda x: -x[1]))
        q_summary = f"Qdrant {qdrant['status']} {qdrant['total_vectors']:,} vectors across {qdrant['collections']} collections ({q_detail})"
    else:
        q_summary = f"Qdrant {qdrant['status']} {qdrant.get('error', 'unreachable')}"
    
    api_summary = f"Hub API {api['status']}" + (f" healthy" if api["status"] == "✅" else f" {api.get('error', '')}")
    neo4j_summary = f"Neo4j {neo4j['status']}" + (f" {neo4j.get('nodes',0)} nodes, {neo4j.get('relationships',0)} rels" if neo4j["status"] == "✅" else f" {neo4j.get('error','')}")
    vite_summary = f"Vite {vite['status']}" + (f" on :5173" if vite["status"] == "✅" else f" {vite.get('note','')}")
    mem0_summary = f"Mem0 {mem0['status']} {mem0.get('memories',0)} memories"
    
    report = f"""
═══ HEALTH CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ═══
Git: {git['branch']} | {git['last_commit']} | {git['dirty_files']} uncommitted files

{q_summary}
{api_summary}
{neo4j_summary}
{vite_summary}
{mem0_summary}

COPY-PASTE FOR ORCHESTRATOR:
Health check {datetime.now().strftime('%b %d %H:%M')}: {qdrant.get('status','?')} Qdrant ({qdrant.get('total_vectors','?'):,} vectors, {qdrant.get('collections','?')} collections), {api.get('status','?')} Hub API (:8100), {neo4j.get('status','?')} Neo4j ({neo4j.get('nodes','?')} nodes), {vite.get('status','?')} Vite (:5173), {mem0.get('status','?')} Mem0 ({mem0.get('memories','?')} memories). Branch: {git['branch']}, last commit: {git['last_commit']}.
═══ END ═══
"""
    return report.strip()

if __name__ == "__main__":
    print("Running PTS BD Platform health check...\n")
    
    qdrant = check_qdrant()
    api = check_api()
    neo4j = check_neo4j()
    vite = check_vite()
    mem0 = check_mem0()
    git = check_git()
    
    report = format_report(qdrant, api, neo4j, vite, mem0, git)
    print(report)
    
    # Also save to file
    os.makedirs("docs", exist_ok=True)
    with open("docs/HEALTH_CHECK_LATEST.txt", "w") as f:
        f.write(report)
    print(f"\nSaved to docs/HEALTH_CHECK_LATEST.txt")
