"""Tests for Phase 30A - Kubernetes manifests (namespace, deployments, statefulsets, etc.)."""

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

# Base paths
K8S_DIR = Path(__file__).parent.parent / "k8s"


def _load_yaml(filepath: Path):
    """Load and return the first YAML document from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_all_yaml(filepath: Path):
    """Load all YAML documents from a file (handles multi-doc files)."""
    with open(filepath, "r", encoding="utf-8") as f:
        return list(yaml.safe_load_all(f))


class TestNamespace:
    """Tests for k8s/namespace.yaml."""

    def test_namespace_file_exists(self):
        """namespace.yaml should exist in k8s directory."""
        assert (K8S_DIR / "namespace.yaml").exists()

    def test_namespace_has_correct_name(self):
        """Namespace should be named 'pts-bd'."""
        doc = _load_yaml(K8S_DIR / "namespace.yaml")
        assert doc["kind"] == "Namespace"
        assert doc["metadata"]["name"] == "pts-bd"

    def test_namespace_has_labels(self):
        """Namespace should have kubernetes labels."""
        doc = _load_yaml(K8S_DIR / "namespace.yaml")
        labels = doc["metadata"]["labels"]
        assert "app.kubernetes.io/name" in labels
        assert labels["app.kubernetes.io/name"] == "pts-bd"


class TestHubApiDeployment:
    """Tests for k8s/hub-api/deployment.yaml."""

    def test_hub_api_deployment_exists(self):
        """hub-api deployment.yaml should exist."""
        assert (K8S_DIR / "hub-api" / "deployment.yaml").exists()

    def test_hub_api_deployment_kind(self):
        """Should be a Deployment resource."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        assert doc["kind"] == "Deployment"

    def test_hub_api_correct_image(self):
        """Container image should be pts-bd/hub-api:latest."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        containers = doc["spec"]["template"]["spec"]["containers"]
        assert containers[0]["image"] == "pts-bd/hub-api:latest"

    def test_hub_api_replicas(self):
        """Deployment should have 2 replicas."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        assert doc["spec"]["replicas"] == 2

    def test_hub_api_has_probes(self):
        """Deployment should configure liveness and readiness probes."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        container = doc["spec"]["template"]["spec"]["containers"][0]
        assert "livenessProbe" in container
        assert container["livenessProbe"]["httpGet"]["path"] == "/monitoring/live"
        assert "readinessProbe" in container
        assert container["readinessProbe"]["httpGet"]["path"] == "/monitoring/ready"

    def test_hub_api_prometheus_annotations(self):
        """Pod template should have Prometheus scrape annotations."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        annotations = doc["spec"]["template"]["metadata"]["annotations"]
        assert annotations["prometheus.io/scrape"] == "true"
        assert annotations["prometheus.io/port"] == "8100"
        assert annotations["prometheus.io/path"] == "/metrics"

    def test_hub_api_namespace(self):
        """Deployment should be in the pts-bd namespace."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "deployment.yaml")
        assert doc["metadata"]["namespace"] == "pts-bd"


class TestQdrantStatefulSet:
    """Tests for k8s/qdrant/statefulset.yaml."""

    def test_qdrant_statefulset_exists(self):
        """qdrant statefulset.yaml should exist."""
        assert (K8S_DIR / "qdrant" / "statefulset.yaml").exists()

    def test_qdrant_is_statefulset(self):
        """Should be a StatefulSet resource."""
        doc = _load_yaml(K8S_DIR / "qdrant" / "statefulset.yaml")
        assert doc["kind"] == "StatefulSet"

    def test_qdrant_image_version(self):
        """Qdrant should use the expected image version."""
        doc = _load_yaml(K8S_DIR / "qdrant" / "statefulset.yaml")
        container = doc["spec"]["template"]["spec"]["containers"][0]
        assert "qdrant/qdrant:" in container["image"]

    def test_qdrant_has_volume_claim(self):
        """Qdrant should have a persistent volume claim template."""
        doc = _load_yaml(K8S_DIR / "qdrant" / "statefulset.yaml")
        assert "volumeClaimTemplates" in doc["spec"]
        assert len(doc["spec"]["volumeClaimTemplates"]) > 0


class TestNeo4jStatefulSet:
    """Tests for k8s/neo4j/statefulset.yaml."""

    def test_neo4j_statefulset_exists(self):
        """neo4j statefulset.yaml should exist."""
        assert (K8S_DIR / "neo4j" / "statefulset.yaml").exists()

    def test_neo4j_is_statefulset(self):
        """Should be a StatefulSet resource."""
        doc = _load_yaml(K8S_DIR / "neo4j" / "statefulset.yaml")
        assert doc["kind"] == "StatefulSet"

    def test_neo4j_has_volume_claim(self):
        """Neo4j should have a persistent volume claim template."""
        doc = _load_yaml(K8S_DIR / "neo4j" / "statefulset.yaml")
        assert "volumeClaimTemplates" in doc["spec"]


class TestRedisDeployment:
    """Tests for k8s/redis/deployment.yaml."""

    def test_redis_deployment_exists(self):
        """redis deployment.yaml should exist."""
        assert (K8S_DIR / "redis" / "deployment.yaml").exists()

    def test_redis_has_deployment_and_service(self):
        """Redis file should contain both a Deployment and a Service."""
        docs = _load_all_yaml(K8S_DIR / "redis" / "deployment.yaml")
        kinds = [d["kind"] for d in docs if d is not None]
        assert "Deployment" in kinds
        assert "Service" in kinds

    def test_redis_uses_alpine_image(self):
        """Redis should use the redis alpine image."""
        docs = _load_all_yaml(K8S_DIR / "redis" / "deployment.yaml")
        deployment = [d for d in docs if d and d["kind"] == "Deployment"][0]
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        assert "redis" in container["image"]
        assert "alpine" in container["image"]


class TestIngress:
    """Tests for k8s/ingress.yaml."""

    def test_ingress_exists(self):
        """ingress.yaml should exist."""
        assert (K8S_DIR / "ingress.yaml").exists()

    def test_ingress_kind(self):
        """Should be an Ingress resource."""
        doc = _load_yaml(K8S_DIR / "ingress.yaml")
        assert doc["kind"] == "Ingress"

    def test_ingress_has_tls(self):
        """Ingress should have TLS configuration."""
        doc = _load_yaml(K8S_DIR / "ingress.yaml")
        assert "tls" in doc["spec"]

    def test_ingress_has_rules(self):
        """Ingress should have routing rules."""
        doc = _load_yaml(K8S_DIR / "ingress.yaml")
        assert "rules" in doc["spec"]
        assert len(doc["spec"]["rules"]) > 0


class TestSecretsTemplate:
    """Tests for k8s/secrets/secrets-template.yaml."""

    def test_secrets_template_exists(self):
        """secrets-template.yaml should exist."""
        assert (K8S_DIR / "secrets" / "secrets-template.yaml").exists()

    def test_secrets_kind(self):
        """Should be a Secret resource."""
        doc = _load_yaml(K8S_DIR / "secrets" / "secrets-template.yaml")
        assert doc["kind"] == "Secret"

    def test_secrets_has_placeholder_keys(self):
        """Secret should have placeholder API key entries."""
        doc = _load_yaml(K8S_DIR / "secrets" / "secrets-template.yaml")
        string_data = doc["stringData"]
        assert "anthropic-api-key" in string_data
        assert "openai-api-key" in string_data


class TestHPA:
    """Tests for k8s/hub-api/hpa.yaml (HorizontalPodAutoscaler)."""

    def test_hpa_exists(self):
        """hpa.yaml should exist."""
        assert (K8S_DIR / "hub-api" / "hpa.yaml").exists()

    def test_hpa_kind(self):
        """Should be a HorizontalPodAutoscaler resource."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "hpa.yaml")
        assert doc["kind"] == "HorizontalPodAutoscaler"

    def test_hpa_targets_hub_api(self):
        """HPA should target the hub-api Deployment."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "hpa.yaml")
        ref = doc["spec"]["scaleTargetRef"]
        assert ref["name"] == "hub-api"
        assert ref["kind"] == "Deployment"

    def test_hpa_min_max_replicas(self):
        """HPA should define min and max replica counts."""
        doc = _load_yaml(K8S_DIR / "hub-api" / "hpa.yaml")
        assert doc["spec"]["minReplicas"] >= 1
        assert doc["spec"]["maxReplicas"] >= doc["spec"]["minReplicas"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
