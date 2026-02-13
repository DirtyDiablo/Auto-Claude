#!/usr/bin/env python3
"""
PTS BD Dashboard — Phase Validator
Run after each phase to verify deliverables before moving to the next phase.

Usage: python scripts/validate_phase.py [1|2|3]
"""

import sys
import os

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def check(name, condition, detail=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if condition else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))
    return condition

def http_get(url, timeout=5):
    try:
        import httpx
        r = httpx.get(url, timeout=timeout)
        return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except Exception as e:
        return None, str(e)

def http_post(url, body, timeout=10):
    try:
        import httpx
        r = httpx.post(url, json=body, timeout=timeout)
        return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except Exception as e:
        return None, str(e)

def file_exists(path):
    return os.path.exists(path)

def npm_package_installed(package_name):
    """Check if npm package is in node_modules."""
    # Find package.json directories
    for root, dirs, files in os.walk("."):
        if "node_modules" in root:
            continue
        if "package.json" in files:
            node_modules = os.path.join(root, "node_modules", package_name)
            if os.path.exists(node_modules):
                return True
    return False

def validate_phase_1():
    """Phase 1: Foundation + AI Search"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ VALIDATING PHASE 1: Foundation + AI Search ═══{Colors.RESET}\n")
    
    results = []
    
    # Infrastructure
    print(f"{Colors.BOLD}Infrastructure:{Colors.RESET}")
    code, data = http_get("http://localhost:8100/health")
    results.append(check("Hub API responding", code == 200, f"status={code}"))
    
    code, data = http_get("http://localhost:5173")
    results.append(check("Vite dev server running", code is not None, f"status={code}"))
    
    code, data = http_get("http://localhost:6333/collections")
    results.append(check("Qdrant accessible", code == 200))
    
    # npm packages
    print(f"\n{Colors.BOLD}npm Packages:{Colors.RESET}")
    packages = ["@tremor/react", "@tanstack/react-table", "cmdk", "framer-motion", "zod", 
                "react-hook-form", "@dnd-kit/core", "date-fns"]
    for pkg in packages:
        results.append(check(f"Package: {pkg}", npm_package_installed(pkg)))
    
    # API Client
    print(f"\n{Colors.BOLD}API Integration:{Colors.RESET}")
    
    # Test vector search
    code, data = http_post("http://localhost:8100/search", {"query": "DCGS", "limit": 3})
    results.append(check("POST /search working", code == 200, f"returned {len(data.get('results', [])) if isinstance(data, dict) else '?'} results"))
    
    # Test smart search
    code, data = http_post("http://localhost:8100/ask/smart", {"query": "What programs does GDIT run?"})
    results.append(check("POST /ask/smart working", code == 200))
    
    # Test stats
    code, data = http_get("http://localhost:8100/stats")
    results.append(check("GET /stats working", code == 200))
    
    # Test agents endpoint
    code, data = http_get("http://localhost:8100/agents/tasks")
    results.append(check("GET /agents/tasks working", code == 200))
    
    # Vite proxy
    print(f"\n{Colors.BOLD}Vite Proxy:{Colors.RESET}")
    code, data = http_get("http://localhost:5173/api/health")
    results.append(check("Vite proxy /api/* → :8100", code == 200, "proxy working" if code == 200 else "check vite.config.ts"))
    
    # Key files
    print(f"\n{Colors.BOLD}Key Files:{Colors.RESET}")
    api_client_paths = [
        "src/lib/api.ts", "src/lib/api.tsx",
        "frontend/src/lib/api.ts", "frontend/src/lib/api.tsx",
        "dashboard/src/lib/api.ts"
    ]
    found_api = any(file_exists(p) for p in api_client_paths)
    results.append(check("API client file exists", found_api, "src/lib/api.ts or equivalent"))
    
    hooks_paths = [
        "src/lib/hooks.ts", "src/lib/hooks.tsx",
        "frontend/src/lib/hooks.ts", "frontend/src/lib/hooks.tsx",
        "src/hooks/useApi.ts", "src/hooks/use-api.ts"
    ]
    found_hooks = any(file_exists(p) for p in hooks_paths)
    results.append(check("TanStack Query hooks file exists", found_hooks))
    
    return results

def validate_phase_2():
    """Phase 2: Entity Pages + Org Chart"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ VALIDATING PHASE 2: Entity Pages + Org Chart ═══{Colors.RESET}\n")
    
    results = []
    
    # Check Phase 1 is still working
    print(f"{Colors.BOLD}Phase 1 Still Working:{Colors.RESET}")
    code, _ = http_get("http://localhost:8100/health")
    results.append(check("Hub API still responding", code == 200))
    code, _ = http_get("http://localhost:5173")
    results.append(check("Vite still running", code is not None))
    
    # G6 package
    print(f"\n{Colors.BOLD}Graph Packages:{Colors.RESET}")
    results.append(check("Package: @antv/g6", npm_package_installed("@antv/g6")))
    
    # Page routes (check if pages respond)
    print(f"\n{Colors.BOLD}Page Routes (via Vite):{Colors.RESET}")
    routes = ["/", "/search", "/contacts", "/programs", "/agents"]
    for route in routes:
        code, _ = http_get(f"http://localhost:5173{route}")
        # SPA returns 200 for all routes (React Router handles it)
        results.append(check(f"Route {route} accessible", code == 200))
    
    # Contact filter endpoint
    print(f"\n{Colors.BOLD}API Endpoints:{Colors.RESET}")
    code, data = http_post("http://localhost:8100/search", {
        "query": "program manager", 
        "collection_name": "contacts", 
        "limit": 5
    })
    has_results = isinstance(data, dict) and len(data.get("results", [])) > 0
    results.append(check("Contact search returns results", has_results, 
                        f"{len(data.get('results', [])) if isinstance(data, dict) else 0} contacts"))
    
    code, data = http_post("http://localhost:8100/search", {
        "query": "DCGS", 
        "collection_name": "programs", 
        "limit": 5
    })
    has_results = isinstance(data, dict) and len(data.get("results", [])) > 0
    results.append(check("Program search returns results", has_results,
                        f"{len(data.get('results', [])) if isinstance(data, dict) else 0} programs"))
    
    return results

def validate_phase_3():
    """Phase 3: Pipeline + Outreach + Analytics"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ VALIDATING PHASE 3: Pipeline + Outreach + Analytics ═══{Colors.RESET}\n")
    
    results = []
    
    # Phase 1+2 still working
    print(f"{Colors.BOLD}Previous Phases:{Colors.RESET}")
    code, _ = http_get("http://localhost:8100/health")
    results.append(check("Hub API responding", code == 200))
    code, _ = http_get("http://localhost:5173")
    results.append(check("Vite running", code is not None))
    
    # Outreach engine
    print(f"\n{Colors.BOLD}Outreach Engine:{Colors.RESET}")
    code, _ = http_get("http://localhost:8300/health")
    results.append(check("Outreach API (:8300) responding", code == 200, 
                        "running" if code == 200 else "start with: uvicorn src.outreach.api:app --port 8300"))
    
    code, data = http_get("http://localhost:8300/sequences")
    if code == 200:
        count = len(data.get("sequences", []))
        results.append(check("Outreach sequences endpoint", True, f"{count} sequences"))
    else:
        results.append(check("Outreach sequences endpoint", False))
    
    # Agent trigger test
    print(f"\n{Colors.BOLD}Agent Integration:{Colors.RESET}")
    code, data = http_get("http://localhost:8100/agents/tasks")
    if code == 200 and isinstance(data, list):
        results.append(check("Agent task history accessible", True, f"{len(data)} tasks"))
    else:
        results.append(check("Agent task history accessible", code == 200))
    
    # Jobs collection for pipeline
    print(f"\n{Colors.BOLD}Pipeline Data:{Colors.RESET}")
    code, data = http_post("http://localhost:8100/search", {
        "query": "network engineer TS/SCI",
        "collection_name": "jobs",
        "limit": 5
    })
    has_jobs = isinstance(data, dict) and len(data.get("results", [])) > 0
    results.append(check("Jobs collection searchable", has_jobs,
                        f"{len(data.get('results', [])) if isinstance(data, dict) else 0} jobs"))
    
    return results

def main():
    phase = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    validators = {1: validate_phase_1, 2: validate_phase_2, 3: validate_phase_3}
    
    if phase not in validators:
        print(f"Usage: python scripts/validate_phase.py [1|2|3]")
        sys.exit(1)
    
    results = validators[phase]()
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\n{Colors.BOLD}{'='*50}{Colors.RESET}")
    color = Colors.GREEN if passed == total else Colors.YELLOW if passed > total * 0.7 else Colors.RED
    print(f"{color}Phase {phase}: {passed}/{total} checks passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ Phase {phase} VALIDATED — ready for Phase {phase+1}{Colors.RESET}")
    elif passed > total * 0.7:
        print(f"{Colors.YELLOW}⚠️ Phase {phase} MOSTLY COMPLETE — review failures above{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Phase {phase} INCOMPLETE — fix failures before proceeding{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}COPY-PASTE FOR ORCHESTRATOR:{Colors.RESET}")
    print(f"Phase {phase} validation: {passed}/{total} passed. " + 
          ("Ready for next phase." if passed == total else 
           f"Failing: {', '.join(r for r, ok in zip([str(i) for i in range(len(results))], results) if not ok)}"))

if __name__ == "__main__":
    main()
