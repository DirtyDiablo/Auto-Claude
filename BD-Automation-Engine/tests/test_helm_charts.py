"""Tests for Phase 30A - Helm chart manifests (Chart.yaml, values files)."""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import yaml
except ImportError:
    yaml = None

pytestmark = pytest.mark.skipif(yaml is None, reason="PyYAML not installed")

# Base path for Helm chart
HELM_DIR = Path(__file__).parent.parent / "helm" / "pts-bd"


def _load_yaml(filepath: Path):
    """Load and return the first YAML document from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestChartYaml:
    """Tests for Chart.yaml."""

    def test_chart_yaml_exists(self):
        """Chart.yaml should exist in the helm chart directory."""
        assert (HELM_DIR / "Chart.yaml").exists()

    def test_chart_has_name(self):
        """Chart.yaml should have a name field set to 'pts-bd'."""
        doc = _load_yaml(HELM_DIR / "Chart.yaml")
        assert "name" in doc
        assert doc["name"] == "pts-bd"

    def test_chart_has_version(self):
        """Chart.yaml should have a version field."""
        doc = _load_yaml(HELM_DIR / "Chart.yaml")
        assert "version" in doc
        assert isinstance(doc["version"], str)

    def test_chart_has_app_version(self):
        """Chart.yaml should have an appVersion field."""
        doc = _load_yaml(HELM_DIR / "Chart.yaml")
        assert "appVersion" in doc

    def test_chart_has_description(self):
        """Chart.yaml should have a description field."""
        doc = _load_yaml(HELM_DIR / "Chart.yaml")
        assert "description" in doc
        assert len(doc["description"]) > 0

    def test_chart_api_version(self):
        """Chart.yaml should use apiVersion v2."""
        doc = _load_yaml(HELM_DIR / "Chart.yaml")
        assert doc["apiVersion"] == "v2"


class TestValuesYaml:
    """Tests for values.yaml (default values)."""

    def test_values_yaml_exists(self):
        """values.yaml should exist in the helm chart directory."""
        assert (HELM_DIR / "values.yaml").exists()

    def test_values_has_hub_api_key(self):
        """values.yaml should have a hubApi configuration section."""
        doc = _load_yaml(HELM_DIR / "values.yaml")
        assert "hubApi" in doc

    def test_values_has_expected_service_keys(self):
        """values.yaml should have configuration for all core services."""
        doc = _load_yaml(HELM_DIR / "values.yaml")
        expected_keys = ["hubApi", "qdrant", "neo4j", "redis", "dashboard", "ingress", "monitoring"]
        for key in expected_keys:
            assert key in doc, f"Missing service key: {key}"

    def test_values_hub_api_has_replicas(self):
        """hubApi section should define replicas."""
        doc = _load_yaml(HELM_DIR / "values.yaml")
        assert "replicas" in doc["hubApi"]
        assert isinstance(doc["hubApi"]["replicas"], int)

    def test_values_hub_api_has_resources(self):
        """hubApi section should define resource requests and limits."""
        doc = _load_yaml(HELM_DIR / "values.yaml")
        resources = doc["hubApi"]["resources"]
        assert "requests" in resources
        assert "limits" in resources

    def test_values_monitoring_section(self):
        """values.yaml should have a monitoring section with prometheus and grafana."""
        doc = _load_yaml(HELM_DIR / "values.yaml")
        monitoring = doc["monitoring"]
        assert "prometheus" in monitoring
        assert monitoring["prometheus"]["enabled"] is True
        assert "grafana" in monitoring


class TestValuesDevYaml:
    """Tests for values-dev.yaml (dev overrides)."""

    def test_values_dev_exists(self):
        """values-dev.yaml should exist."""
        assert (HELM_DIR / "values-dev.yaml").exists()

    def test_values_dev_has_hub_api(self):
        """values-dev.yaml should override hubApi settings."""
        doc = _load_yaml(HELM_DIR / "values-dev.yaml")
        assert "hubApi" in doc

    def test_values_dev_smaller_replicas(self):
        """Dev environment should use fewer replicas than default."""
        default = _load_yaml(HELM_DIR / "values.yaml")
        dev = _load_yaml(HELM_DIR / "values-dev.yaml")
        assert dev["hubApi"]["replicas"] <= default["hubApi"]["replicas"]

    def test_values_dev_autoscaling_disabled(self):
        """Dev environment should have autoscaling disabled."""
        doc = _load_yaml(HELM_DIR / "values-dev.yaml")
        assert doc["hubApi"]["autoscaling"]["enabled"] is False


class TestValuesProdYaml:
    """Tests for values-prod.yaml (production overrides)."""

    def test_values_prod_exists(self):
        """values-prod.yaml should exist."""
        assert (HELM_DIR / "values-prod.yaml").exists()

    def test_values_prod_has_hub_api(self):
        """values-prod.yaml should override hubApi settings."""
        doc = _load_yaml(HELM_DIR / "values-prod.yaml")
        assert "hubApi" in doc

    def test_values_prod_higher_replicas(self):
        """Production should use more replicas than default."""
        default = _load_yaml(HELM_DIR / "values.yaml")
        prod = _load_yaml(HELM_DIR / "values-prod.yaml")
        assert prod["hubApi"]["replicas"] >= default["hubApi"]["replicas"]

    def test_values_prod_autoscaling_enabled(self):
        """Production should have autoscaling enabled."""
        doc = _load_yaml(HELM_DIR / "values-prod.yaml")
        assert doc["hubApi"]["autoscaling"]["enabled"] is True

    def test_values_prod_larger_storage(self):
        """Production should allocate more storage for Qdrant."""
        default = _load_yaml(HELM_DIR / "values.yaml")
        prod = _load_yaml(HELM_DIR / "values-prod.yaml")
        # Compare storage strings (e.g., "50Gi" vs "200Gi")
        def parse_gi(s):
            return int(str(s).replace("Gi", ""))
        assert parse_gi(prod["qdrant"]["storage"]) >= parse_gi(default["qdrant"]["storage"])


class TestAllValuesHubApiKey:
    """Cross-file test: all values files should have hubApi key."""

    @pytest.mark.parametrize("filename", ["values.yaml", "values-dev.yaml", "values-prod.yaml"])
    def test_all_values_files_have_hub_api(self, filename):
        """Each values file should contain a hubApi configuration section."""
        filepath = HELM_DIR / filename
        assert filepath.exists(), f"{filename} does not exist"
        doc = _load_yaml(filepath)
        assert "hubApi" in doc, f"{filename} is missing hubApi key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
