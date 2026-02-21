"""
Tests for Docker production deployment configuration files.
Feature 14: Docker Production Deployment

Run: python -m pytest tests/test_docker_config.py -v --tb=short
"""

import os
import re
from pathlib import Path

import pytest
import yaml

# Project root is one level up from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ────────────────────────────────────────────────

def load_yaml(filename: str) -> dict:
    """Load and parse a YAML file from the project root."""
    filepath = PROJECT_ROOT / filename
    assert filepath.exists(), f"{filename} does not exist"
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_file(filename: str) -> str:
    """Read a file from the project root as text."""
    filepath = PROJECT_ROOT / filename
    assert filepath.exists(), f"{filename} does not exist"
    return filepath.read_text(encoding="utf-8")


# ── Dockerfile Tests ───────────────────────────────────────

class TestDockerfile:
    """Validate the multi-stage Dockerfile."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file("Dockerfile")

    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_has_builder_stage(self):
        assert "AS builder" in self.content, "Dockerfile must have a builder stage"

    def test_has_runtime_stage(self):
        assert "AS runtime" in self.content, "Dockerfile must have a runtime stage"

    def test_uses_python_312_slim(self):
        assert "python:3.12-slim" in self.content

    def test_non_root_user_created(self):
        assert "bduser" in self.content, "Dockerfile must create a non-root bduser"

    def test_user_directive_present(self):
        assert re.search(r"^USER\s+bduser", self.content, re.MULTILINE), \
            "Dockerfile must switch to bduser before CMD"

    def test_exposes_port_8100(self):
        assert re.search(r"^EXPOSE\s+8100", self.content, re.MULTILINE)

    def test_healthcheck_defined(self):
        assert "HEALTHCHECK" in self.content
        assert "localhost:8100/health" in self.content

    def test_entrypoint_uses_script(self):
        assert "docker-entrypoint.sh" in self.content

    def test_copies_requirements(self):
        assert "COPY requirements.txt" in self.content

    def test_copies_migrations(self):
        assert "COPY migrations/" in self.content

    def test_copies_workflows(self):
        assert "COPY workflows/" in self.content

    def test_python_unbuffered(self):
        assert "PYTHONUNBUFFERED=1" in self.content

    def test_no_root_cmd(self):
        """CMD should come after USER bduser, not before."""
        user_pos = self.content.rfind("USER bduser")
        cmd_pos = self.content.rfind("CMD")
        assert user_pos < cmd_pos, "CMD must appear after USER directive"


# ── docker-compose.yml Tests ──────────────────────────────

class TestDockerCompose:
    """Validate the production docker-compose.yml."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.compose = load_yaml("docker-compose.yml")

    def test_compose_parses_as_valid_yaml(self):
        assert self.compose is not None
        assert isinstance(self.compose, dict)

    def test_has_services_key(self):
        assert "services" in self.compose

    def test_required_services_present(self):
        services = set(self.compose["services"].keys())
        required = {"api", "qdrant", "postgres", "worker", "redis"}
        missing = required - services
        assert not missing, f"Missing required services: {missing}"

    def test_api_service_port_mapping(self):
        api = self.compose["services"]["api"]
        ports = api.get("ports", [])
        port_strs = [str(p) for p in ports]
        assert any("8100" in p for p in port_strs), "API must expose port 8100"

    def test_qdrant_service_port_mapping(self):
        qdrant = self.compose["services"]["qdrant"]
        ports = [str(p) for p in qdrant.get("ports", [])]
        assert any("6333" in p for p in ports), "Qdrant must expose port 6333"

    def test_postgres_service_port_mapping(self):
        pg = self.compose["services"]["postgres"]
        ports = [str(p) for p in pg.get("ports", [])]
        assert any("5432" in p for p in ports), "Postgres must expose port 5432"

    def test_redis_service_port_mapping(self):
        redis_svc = self.compose["services"]["redis"]
        ports = [str(p) for p in redis_svc.get("ports", [])]
        assert any("6379" in p for p in ports), "Redis must expose port 6379"

    def test_all_services_have_healthchecks(self):
        for name, svc in self.compose["services"].items():
            # Worker doesn't need its own healthcheck (depends on api)
            if name == "worker":
                continue
            assert "healthcheck" in svc, f"Service '{name}' must have a healthcheck"

    def test_qdrant_healthcheck_correct(self):
        hc = self.compose["services"]["qdrant"]["healthcheck"]
        test_cmd = " ".join(hc["test"]) if isinstance(hc["test"], list) else hc["test"]
        assert "healthz" in test_cmd or "health" in test_cmd

    def test_postgres_healthcheck_correct(self):
        hc = self.compose["services"]["postgres"]["healthcheck"]
        test_cmd = " ".join(hc["test"]) if isinstance(hc["test"], list) else hc["test"]
        assert "pg_isready" in test_cmd

    def test_redis_healthcheck_correct(self):
        hc = self.compose["services"]["redis"]["healthcheck"]
        test_cmd = " ".join(hc["test"]) if isinstance(hc["test"], list) else hc["test"]
        assert "redis-cli" in test_cmd and "ping" in test_cmd

    def test_volumes_defined(self):
        volumes = self.compose.get("volumes", {})
        required_volumes = {"qdrant-data", "postgres-data", "redis-data", "api-data"}
        defined = set(volumes.keys())
        missing = required_volumes - defined
        assert not missing, f"Missing volume definitions: {missing}"

    def test_network_defined(self):
        networks = self.compose.get("networks", {})
        assert "bd-network" in networks, "Must define bd-network"
        assert networks["bd-network"]["driver"] == "bridge"

    def test_all_services_on_network(self):
        for name, svc in self.compose["services"].items():
            networks = svc.get("networks", [])
            assert "bd-network" in networks, \
                f"Service '{name}' must be on bd-network"

    def test_api_depends_on_infrastructure(self):
        api = self.compose["services"]["api"]
        deps = api.get("depends_on", {})
        assert "qdrant" in deps, "API must depend on qdrant"
        assert "postgres" in deps, "API must depend on postgres"
        assert "redis" in deps, "API must depend on redis"

    def test_worker_depends_on_api(self):
        worker = self.compose["services"]["worker"]
        deps = worker.get("depends_on", {})
        assert "api" in deps, "Worker must depend on api"

    def test_api_depends_on_healthy(self):
        """API should wait for healthy infrastructure, not just started."""
        api = self.compose["services"]["api"]
        deps = api.get("depends_on", {})
        for dep_name, dep_config in deps.items():
            if isinstance(dep_config, dict):
                assert dep_config.get("condition") == "service_healthy", \
                    f"API depends_on {dep_name} should use condition: service_healthy"

    def test_services_restart_policy(self):
        for name, svc in self.compose["services"].items():
            assert svc.get("restart") == "unless-stopped", \
                f"Service '{name}' must have restart: unless-stopped"

    def test_resource_limits_present(self):
        """Production compose should have resource limits."""
        for name, svc in self.compose["services"].items():
            deploy = svc.get("deploy", {})
            resources = deploy.get("resources", {})
            limits = resources.get("limits", {})
            assert "memory" in limits, \
                f"Service '{name}' must have memory limits in deploy.resources.limits"

    def test_api_uses_env_file(self):
        api = self.compose["services"]["api"]
        env_file = api.get("env_file", [])
        if isinstance(env_file, str):
            env_file = [env_file]
        assert ".env" in env_file, "API service must use env_file: .env"

    def test_api_has_data_volumes(self):
        api = self.compose["services"]["api"]
        volumes = api.get("volumes", [])
        volume_strs = [str(v) for v in volumes]
        has_knowledge_data = any("Engine8_Knowledge/data" in v for v in volume_strs)
        has_bullhorn_data = any("Engine7_BullhornETL/data" in v for v in volume_strs)
        assert has_knowledge_data, "API must mount Engine8_Knowledge/data"
        assert has_bullhorn_data, "API must mount Engine7_BullhornETL/data"

    def test_worker_uses_same_image_as_api(self):
        """Worker should build from the same Dockerfile as api."""
        api_build = self.compose["services"]["api"].get("build", {})
        worker_build = self.compose["services"]["worker"].get("build", {})
        assert api_build.get("dockerfile") == worker_build.get("dockerfile"), \
            "Worker must use the same Dockerfile as API"

    def test_postgres_has_persistent_volume(self):
        pg = self.compose["services"]["postgres"]
        volumes = pg.get("volumes", [])
        volume_strs = [str(v) for v in volumes]
        assert any("postgres-data" in v for v in volume_strs), \
            "Postgres must use a named volume for data persistence"


# ── .dockerignore Tests ───────────────────────────────────

class TestDockerignore:
    """Validate .dockerignore excludes sensitive and unnecessary files."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file(".dockerignore")

    def test_dockerignore_exists(self):
        assert (PROJECT_ROOT / ".dockerignore").exists()

    def test_excludes_git(self):
        assert ".git" in self.content

    def test_excludes_env_files(self):
        assert ".env" in self.content

    def test_excludes_pycache(self):
        assert "__pycache__" in self.content

    def test_excludes_pyc_files(self):
        assert "*.pyc" in self.content

    def test_excludes_pytest_cache(self):
        assert ".pytest_cache" in self.content

    def test_excludes_node_modules(self):
        assert "node_modules" in self.content

    def test_excludes_outputs(self):
        assert "outputs/" in self.content

    def test_excludes_large_sqlite(self):
        assert "bullhorn.db" in self.content

    def test_excludes_vscode(self):
        assert ".vscode" in self.content

    def test_excludes_idea(self):
        assert ".idea" in self.content

    def test_excludes_venv(self):
        assert "venv" in self.content or ".venv" in self.content


# ── Entrypoint Script Tests ───────────────────────────────

class TestEntrypointScript:
    """Validate the docker-entrypoint.sh script."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file("scripts/docker-entrypoint.sh")

    def test_entrypoint_exists(self):
        assert (PROJECT_ROOT / "scripts" / "docker-entrypoint.sh").exists()

    def test_has_shebang(self):
        assert self.content.startswith("#!/")

    def test_uses_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content, \
            "Entrypoint must use strict bash error handling"

    def test_validates_openai_api_key(self):
        assert "OPENAI_API_KEY" in self.content

    def test_handles_serve_command(self):
        assert "serve)" in self.content or "serve" in self.content

    def test_handles_worker_command(self):
        assert "worker)" in self.content or "worker" in self.content

    def test_handles_migrate_command(self):
        assert "migrate)" in self.content

    def test_runs_alembic_migrations(self):
        assert "alembic" in self.content

    def test_checks_database_url_before_migration(self):
        assert "DATABASE_URL" in self.content

    def test_configurable_workers(self):
        assert "WORKERS" in self.content

    def test_uses_exec_for_main_process(self):
        """Main process should use exec to replace shell (proper signal handling)."""
        assert "exec python" in self.content or "exec uvicorn" in self.content


# ── Environment Example Tests ─────────────────────────────

class TestEnvExample:
    """Validate .env.example has Docker-specific settings."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file(".env.example")

    def test_env_example_exists(self):
        assert (PROJECT_ROOT / ".env.example").exists()

    def test_has_qdrant_url(self):
        assert "QDRANT_URL" in self.content

    def test_has_database_url(self):
        assert "DATABASE_URL" in self.content

    def test_has_redis_url(self):
        assert "REDIS_URL" in self.content

    def test_has_workers_setting(self):
        assert "WORKERS" in self.content

    def test_no_real_secrets(self):
        """Ensure no actual API keys are in the example file."""
        lines = self.content.splitlines()
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                value = value.strip()
                # Skip empty values, placeholders, and numeric/boolean settings
                if not value or value.startswith("your-") or value.startswith("secret_your"):
                    continue
                if value.startswith("http") or value.startswith("redis://"):
                    continue
                if value.startswith("bolt://"):
                    continue
                if value.startswith("{"):  # JSON values
                    continue
                if value.replace(".", "").isdigit():  # Numeric
                    continue
                if value.lower() in ("true", "false", "info", "debug"):
                    continue
                if value.startswith("smtp") or "@" in value:
                    continue
                if value.startswith("xoxb-") or value.startswith("https://hooks"):
                    continue
                # UUIDs (Notion DB IDs) are fine
                if re.match(r"^[0-9a-f-]{20,}$", value):
                    continue
                # Anything else that looks like a real key is suspicious
                if len(value) > 40 and not value.startswith("your"):
                    pytest.fail(f"Possible real secret in .env.example: {key}")


# ── Dev Compose Override Tests ────────────────────────────

class TestDevCompose:
    """Validate docker-compose.dev.yml development overrides."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.compose = load_yaml("docker-compose.dev.yml")

    def test_dev_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.dev.yml").exists()

    def test_dev_compose_parses(self):
        assert self.compose is not None

    def test_api_has_reload_flag(self):
        api = self.compose["services"]["api"]
        command = api.get("command", "")
        assert "--reload" in command, "Dev API must use --reload for hot-reload"

    def test_api_mounts_source_code(self):
        api = self.compose["services"]["api"]
        volumes = api.get("volumes", [])
        volume_strs = [str(v) for v in volumes]
        assert any("Engine8_Knowledge" in v for v in volume_strs), \
            "Dev API must mount Engine8_Knowledge source code"

    def test_dev_log_level_debug(self):
        api = self.compose["services"]["api"]
        env = api.get("environment", [])
        env_str = str(env)
        assert "debug" in env_str.lower(), "Dev API should use debug log level"
