#!/usr/bin/env python3
"""
BD Automation Engine — Service Startup & Health Monitor

Cross-platform startup script that validates environment, starts services,
and monitors health with auto-restart capability.

Usage:
    python start.py                     # Start all services
    python start.py --api-only          # Start only the Knowledge API
    python start.py --health            # Run health check only
    python start.py --validate          # Validate .env configuration only
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

SERVICES = {
    "knowledge_api": {
        "command": [sys.executable, str(PROJECT_ROOT / "Engine8_Knowledge" / "api.py")],
        "port": 8100,
        "health_url": "http://localhost:8100/health",
        "log_file": LOG_DIR / "knowledge_api.log",
        "description": "Knowledge API (FastAPI)",
    },
}

# Required env vars — service won't start without these
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
]

# Optional but recommended env vars
RECOMMENDED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "QDRANT_URL",
    "NOTION_TOKEN",
]

MAX_RESTART_ATTEMPTS = 3
HEALTH_CHECK_INTERVAL = 30  # seconds
STARTUP_WAIT = 5  # seconds to wait after starting a service


# ---------------------------------------------------------------------------
# Environment Validation
# ---------------------------------------------------------------------------


def validate_env() -> tuple[list[str], list[str]]:
    """Validate .env configuration. Returns (errors, warnings)."""
    from dotenv import load_dotenv

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return [".env file not found — copy .env.example to .env and configure"], []

    load_dotenv(env_file)

    errors = []
    warnings = []

    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var, "").strip()
        if not val or val.startswith("your_") or val.startswith("sk-xxx"):
            errors.append(f"Missing or placeholder: {var}")

    for var in RECOMMENDED_ENV_VARS:
        val = os.getenv(var, "").strip()
        if not val or val.startswith("your_") or val.startswith("sk-xxx"):
            warnings.append(f"Not configured (optional): {var}")

    return errors, warnings


# ---------------------------------------------------------------------------
# Port & Process Utilities
# ---------------------------------------------------------------------------


def is_port_in_use(port: int) -> bool:
    """Check if a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def check_health(url: str, timeout: float = 5.0) -> dict | None:
    """Hit a health endpoint. Returns parsed JSON or None on failure."""
    try:
        import httpx

        resp = httpx.get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Service Management
# ---------------------------------------------------------------------------


class ServiceManager:
    """Manages service lifecycle with health monitoring and auto-restart."""

    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self.restart_counts: dict[str, int] = {}
        self._shutdown = False

    def start_service(self, name: str) -> bool:
        """Start a single service. Returns True if started successfully."""
        svc = SERVICES[name]

        if is_port_in_use(svc["port"]):
            print(f"  [{name}] Port {svc['port']} already in use — service may be running")
            result = check_health(svc["health_url"])
            if result:
                print(f"  [{name}] Health check passed — already healthy")
                return True
            print(f"  [{name}] Port occupied but health check failed")
            return False

        log_file = open(svc["log_file"], "a")
        try:
            proc = subprocess.Popen(
                svc["command"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(PROJECT_ROOT),
            )
            self.processes[name] = proc
            self.restart_counts.setdefault(name, 0)
            print(f"  [{name}] Started (PID {proc.pid}) — logging to {svc['log_file']}")
        except Exception as e:
            print(f"  [{name}] Failed to start: {e}")
            log_file.close()
            return False

        # Wait for health
        print(f"  [{name}] Waiting for health check...", end="", flush=True)
        for _ in range(STARTUP_WAIT * 2):
            time.sleep(0.5)
            if proc.poll() is not None:
                print(f" CRASHED (exit code {proc.returncode})")
                return False
            result = check_health(svc["health_url"], timeout=2.0)
            if result:
                print(f" healthy")
                return True
        print(f" timeout (may still be starting)")
        return True  # Optimistic — might just be slow

    def stop_all(self):
        """Gracefully stop all managed services."""
        self._shutdown = True
        for name, proc in self.processes.items():
            if proc.poll() is None:
                print(f"  [{name}] Stopping (PID {proc.pid})...")
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                print(f"  [{name}] Stopped")

    def health_loop(self):
        """Monitor health and auto-restart crashed services."""
        print(f"\nHealth monitor running (check every {HEALTH_CHECK_INTERVAL}s, Ctrl+C to stop)\n")

        while not self._shutdown:
            time.sleep(HEALTH_CHECK_INTERVAL)
            if self._shutdown:
                break

            for name, proc in list(self.processes.items()):
                svc = SERVICES[name]

                if proc.poll() is not None:
                    # Process died
                    if self.restart_counts[name] >= MAX_RESTART_ATTEMPTS:
                        print(f"  [{name}] Crashed and exceeded {MAX_RESTART_ATTEMPTS} restart attempts — giving up")
                        continue

                    self.restart_counts[name] += 1
                    attempt = self.restart_counts[name]
                    print(f"  [{name}] Crashed — restarting (attempt {attempt}/{MAX_RESTART_ATTEMPTS})")
                    self.start_service(name)
                else:
                    # Process alive — verify health
                    result = check_health(svc["health_url"], timeout=3.0)
                    if not result:
                        print(f"  [{name}] Running but health check failed — monitoring")


# ---------------------------------------------------------------------------
# Health Check (standalone mode)
# ---------------------------------------------------------------------------


def run_health_check():
    """Run a comprehensive health check and print results."""
    print("=" * 60)
    print("BD Automation Engine — Health Check")
    print("=" * 60)
    print()

    all_healthy = True

    for name, svc in SERVICES.items():
        port_up = is_port_in_use(svc["port"])
        health = check_health(svc["health_url"]) if port_up else None

        if health:
            status = "HEALTHY"
        elif port_up:
            status = "DEGRADED (port open, health failed)"
            all_healthy = False
        else:
            status = "DOWN"
            all_healthy = False

        print(f"  {svc['description']:40s} [{status}]")
        if health:
            for k, v in health.items():
                if k != "status":
                    print(f"    {k}: {v}")

    # Check external services
    print()
    print("External Services:")
    externals = {
        "Qdrant": ("http://localhost:6333/collections", 6333),
        "Redis": (None, 6379),
        "Neo4j": (None, 7687),
    }
    for name, (url, port) in externals.items():
        port_up = is_port_in_use(port)
        health = check_health(url) if url and port_up else None
        status = "UP" if port_up else "DOWN"
        print(f"  {name:40s} [{status}] (:{port})")

    print()
    print(f"Overall: {'ALL HEALTHY' if all_healthy else 'ISSUES DETECTED'}")
    return 0 if all_healthy else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="BD Automation Engine — Service Startup & Health Monitor"
    )
    parser.add_argument("--api-only", action="store_true", help="Start only the Knowledge API")
    parser.add_argument("--health", action="store_true", help="Run health check only (no startup)")
    parser.add_argument("--validate", action="store_true", help="Validate .env configuration only")
    parser.add_argument("--no-monitor", action="store_true", help="Start services but don't monitor")
    args = parser.parse_args()

    # Health check mode
    if args.health:
        sys.exit(run_health_check())

    # Validate mode
    print("=" * 60)
    print("BD Automation Engine — Service Startup")
    print("=" * 60)
    print()

    print("[1/3] Validating environment...")
    errors, warnings = validate_env()
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN:  {w}")

    if args.validate:
        sys.exit(1 if errors else 0)

    if errors:
        print("\nFix required environment variables before starting. Use --validate to check.")
        sys.exit(1)

    print()

    # Start services
    print("[2/3] Starting services...")
    manager = ServiceManager()

    services_to_start = ["knowledge_api"] if args.api_only else list(SERVICES.keys())

    for name in services_to_start:
        manager.start_service(name)

    print()
    print("[3/3] All services launched")

    if args.no_monitor:
        print("Monitoring disabled. Services running in background.")
        return

    # Set up graceful shutdown
    def handle_signal(signum, frame):
        print("\nShutting down...")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Monitor loop
    try:
        manager.health_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
        manager.stop_all()


if __name__ == "__main__":
    main()
