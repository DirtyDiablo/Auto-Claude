"""Tests for Phase 28A - Defense NER (Custom Named Entity Recognition)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.ml.defense_ner import (
    DefenseNER,
    Entity,
    TrainingExample,
    NERMetrics,
    get_defense_ner,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def ner():
    """Create a DefenseNER instance with spaCy mocked out."""
    with patch("Engine8_Knowledge.ml.defense_ner.DefenseNER._load_model"):
        instance = DefenseNER()
        instance.nlp = None
        instance._trained = False
    return instance


@pytest.fixture
def sample_defense_text():
    """Sample text containing multiple defense-domain entities."""
    return (
        "GDIT was awarded a $50M contract by DISA for the DCGS modernization. "
        "Requires TS/SCI clearance. NAICS code 541512 applies."
    )


# =============================================================================
# Initialization tests
# =============================================================================


class TestDefenseNERInit:
    """Tests for DefenseNER initialization."""

    def test_init_without_spacy(self):
        """DefenseNER should initialize gracefully when spaCy is not available."""
        with patch.dict("sys.modules", {"spacy": None}):
            with patch(
                "Engine8_Knowledge.ml.defense_ner.DefenseNER._load_model"
            ) as mock_load:
                DefenseNER()
                mock_load.assert_called_once()

    def test_init_default_model_path_is_none(self):
        """Default model_path should be None."""
        with patch("Engine8_Knowledge.ml.defense_ner.DefenseNER._load_model"):
            instance = DefenseNER()
        assert instance.model_path is None

    def test_init_with_model_path(self):
        """Specifying model_path should store it on the instance."""
        with patch("Engine8_Knowledge.ml.defense_ner.DefenseNER._load_model"):
            instance = DefenseNER(model_path="/tmp/test_model")
        assert instance.model_path == "/tmp/test_model"

    def test_entity_types_defined(self, ner):
        """ENTITY_TYPES should contain all expected defense entity categories."""
        expected = {
            "PROGRAM",
            "CONTRACT",
            "COMPANY",
            "INSTALLATION",
            "CLEARANCE",
            "NAICS",
            "ROLE_TITLE",
            "SET_ASIDE",
            "AGENCY",
            "VALUE",
        }
        assert set(ner.ENTITY_TYPES) == expected


# =============================================================================
# Entity dataclass tests
# =============================================================================


class TestEntityDataclass:
    """Tests for the Entity dataclass."""

    def test_entity_fields(self):
        """Entity should have text, label, start, end, confidence fields."""
        entity = Entity(text="GDIT", label="COMPANY", start=0, end=4, confidence=0.9)
        assert entity.text == "GDIT"
        assert entity.label == "COMPANY"
        assert entity.start == 0
        assert entity.end == 4
        assert entity.confidence == 0.9

    def test_entity_default_confidence(self):
        """Entity confidence should default to 0.0."""
        entity = Entity(text="test", label="PROGRAM", start=0, end=4)
        assert entity.confidence == 0.0


# =============================================================================
# Pattern-based extraction tests (fallback)
# =============================================================================


class TestPatternExtraction:
    """Tests for the pattern-based fallback NER extraction."""

    def test_predict_extracts_company_entities(self, ner):
        """predict() should extract known defense companies from text."""
        text = "GDIT and Leidos are competing for the contract."
        entities = ner.predict(text)
        company_texts = [e.text for e in entities if e.label == "COMPANY"]
        assert "GDIT" in company_texts
        assert "Leidos" in company_texts

    def test_predict_extracts_clearance_entities(self, ner):
        """predict() should extract clearance levels from text."""
        text = "This position requires TS/SCI clearance."
        entities = ner.predict(text)
        clearance_texts = [e.text for e in entities if e.label == "CLEARANCE"]
        assert "TS/SCI" in clearance_texts

    def test_predict_extracts_agency_entities(self, ner):
        """predict() should extract government agency names from text."""
        text = "Contract awarded by DISA for the DoD network."
        entities = ner.predict(text)
        agency_texts = [e.text for e in entities if e.label == "AGENCY"]
        assert "DISA" in agency_texts
        assert "DoD" in agency_texts

    def test_predict_extracts_value_entities(self, ner, sample_defense_text):
        """predict() should extract dollar value mentions."""
        entities = ner.predict(sample_defense_text)
        value_texts = [e.text for e in entities if e.label == "VALUE"]
        assert any("50M" in v for v in value_texts)

    def test_predict_extracts_set_aside_entities(self, ner):
        """predict() should extract set-aside designations."""
        text = "This is an SDVOSB set-aside opportunity in HUBZone."
        entities = ner.predict(text)
        set_aside_texts = [e.text for e in entities if e.label == "SET_ASIDE"]
        assert "SDVOSB" in set_aside_texts
        assert "HUBZone" in set_aside_texts

    def test_predict_empty_text(self, ner):
        """predict() on empty text should return no entities."""
        entities = ner.predict("")
        assert entities == []

    def test_predict_no_defense_content(self, ner):
        """predict() on text with no defense content should return no entities."""
        text = "The weather today is sunny and warm."
        entities = ner.predict(text)
        assert len(entities) == 0

    def test_pattern_confidence_is_set(self, ner):
        """Pattern-matched entities should have confidence >= 0.7."""
        text = "GDIT has a TS/SCI requirement."
        entities = ner.predict(text)
        for e in entities:
            assert e.confidence >= 0.7


# =============================================================================
# Deduplication tests
# =============================================================================


class TestDeduplication:
    """Tests for entity deduplication logic."""

    def test_deduplicate_keeps_highest_confidence(self, ner):
        """Deduplication should keep the entity with the highest confidence."""
        entities = [
            Entity(text="GDIT", label="COMPANY", start=0, end=4, confidence=0.7),
            Entity(text="GDIT", label="COMPANY", start=0, end=4, confidence=0.9),
        ]
        result = ner._deduplicate(entities)
        assert len(result) == 1
        assert result[0].confidence == 0.9


# =============================================================================
# Training data generation tests
# =============================================================================


class TestTrainingDataGeneration:
    """Tests for auto-generated training data."""

    def test_generate_training_data_returns_list(self, ner):
        """generate_training_data() should return a list of TrainingExample."""
        data = ner.generate_training_data()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all(isinstance(d, TrainingExample) for d in data)

    def test_generate_training_data_has_company_examples(self, ner):
        """Generated data should include examples for each known company."""
        data = ner.generate_training_data()
        company_examples = [
            d for d in data if any(e["label"] == "COMPANY" for e in d.entities)
        ]
        assert len(company_examples) == len(ner.PATTERNS["COMPANY"])

    def test_generate_training_data_has_clearance_examples(self, ner):
        """Generated data should include examples for clearance entities."""
        data = ner.generate_training_data()
        clearance_examples = [
            d for d in data if any(e["label"] == "CLEARANCE" for e in d.entities)
        ]
        assert len(clearance_examples) == len(ner.PATTERNS["CLEARANCE"])

    def test_generate_training_data_entity_spans_are_valid(self, ner):
        """Entity spans in generated data should match the text content."""
        data = ner.generate_training_data()
        for example in data:
            for ent in example.entities:
                extracted = example.text[ent["start"] : ent["end"]]
                assert len(extracted) > 0


# =============================================================================
# Train and evaluate tests
# =============================================================================


class TestTrainAndEvaluate:
    """Tests for NER training and evaluation methods."""

    def test_train_without_nlp_returns_empty_metrics(self, ner):
        """train() should return empty NERMetrics when nlp is None."""
        ner.nlp = None
        data = [TrainingExample(text="test", entities=[])]
        metrics = ner.train(data)
        assert isinstance(metrics, NERMetrics)
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1 == 0.0

    def test_train_with_nlp_marks_trained(self, ner):
        """train() with an nlp model should mark the instance as trained."""
        ner.nlp = MagicMock()
        data = ner.generate_training_data()
        metrics = ner.train(data, epochs=5)
        assert ner._trained is True
        assert isinstance(metrics, NERMetrics)
        assert metrics.total_examples == len(data)

    def test_evaluate_untrained_returns_empty_metrics(self, ner):
        """evaluate() on an untrained model should return empty NERMetrics."""
        ner._trained = False
        data = [TrainingExample(text="test", entities=[])]
        metrics = ner.evaluate(data)
        assert isinstance(metrics, NERMetrics)
        assert metrics.f1 == 0.0

    def test_evaluate_with_no_data_returns_empty(self, ner):
        """evaluate() with empty test data should return empty NERMetrics."""
        ner._trained = True
        metrics = ner.evaluate([])
        assert isinstance(metrics, NERMetrics)
        assert metrics.total_examples == 0

    def test_evaluate_returns_metrics_fields(self, ner):
        """evaluate() should return NERMetrics with all expected fields."""
        ner._trained = True
        data = ner.generate_training_data()
        metrics = ner.evaluate(data)
        assert isinstance(metrics, NERMetrics)
        assert hasattr(metrics, "precision")
        assert hasattr(metrics, "recall")
        assert hasattr(metrics, "f1")
        assert hasattr(metrics, "per_entity")
        assert hasattr(metrics, "total_examples")
        assert metrics.total_examples == len(data)


# =============================================================================
# Singleton tests
# =============================================================================


class TestSingleton:
    """Tests for the module-level singleton accessor."""

    def test_get_defense_ner_returns_instance(self):
        """get_defense_ner() should return a DefenseNER instance."""
        # Reset the module-level singleton
        import Engine8_Knowledge.ml.defense_ner as mod

        mod._ner = None
        instance = get_defense_ner()
        assert isinstance(instance, DefenseNER)

    def test_get_defense_ner_is_singleton(self):
        """Calling get_defense_ner() twice should return the same instance."""
        import Engine8_Knowledge.ml.defense_ner as mod

        mod._ner = None
        a = get_defense_ner()
        b = get_defense_ner()
        assert a is b


# =============================================================================
# Batch enrichment tests
# =============================================================================


class TestBatchEnrichment:
    """Tests for batch NER enrichment."""

    def test_enrich_batch_adds_entities(self, ner):
        """enrich_batch() should add 'entities' key to each record."""
        records = [
            {"description": "GDIT awarded $50M by DISA for DCGS"},
            {"description": "Leidos TS/SCI cleared engineers needed"},
        ]
        enriched = ner.enrich_batch(records)
        for r in enriched:
            assert "entities" in r

    def test_enrich_batch_extracts_correct_types(self, ner):
        """enrich_batch() should extract entities grouped by label."""
        records = [{"description": "GDIT was awarded by DISA for DCGS-A modernization"}]
        enriched = ner.enrich_batch(records)
        entities = enriched[0]["entities"]
        assert "COMPANY" in entities
        assert "GDIT" in entities["COMPANY"]
        assert "AGENCY" in entities
        assert "DISA" in entities["AGENCY"]
        assert "PROGRAM" in entities
        assert "DCGS-A" in entities["PROGRAM"]

    def test_enrich_batch_empty_records(self, ner):
        """enrich_batch() on empty records should return empty list."""
        result = ner.enrich_batch([])
        assert result == []

    def test_enrich_batch_no_text_fields(self, ner):
        """enrich_batch() with records lacking text fields gives empty entities."""
        records = [{"id": 1, "score": 50}]
        enriched = ner.enrich_batch(records)
        assert enriched[0]["entities"] == {}

    def test_enrich_batch_custom_text_fields(self, ner):
        """enrich_batch() should use custom text fields when specified."""
        records = [{"notes": "Leidos is the prime contractor"}]
        enriched = ner.enrich_batch(records, text_fields=["notes"])
        assert "COMPANY" in enriched[0]["entities"]

    def test_enrich_batch_deduplicates_within_record(self, ner):
        """enrich_batch() should not duplicate entity values within a record."""
        records = [{"title": "GDIT DCGS", "description": "GDIT DCGS-A contract"}]
        enriched = ner.enrich_batch(records, text_fields=["title", "description"])
        # GDIT should appear only once in the COMPANY list
        companies = enriched[0]["entities"].get("COMPANY", [])
        assert companies.count("GDIT") == 1


class TestGetStats:
    """Tests for NER stats reporting."""

    def test_get_stats_returns_dict(self, ner):
        """get_stats() should return a dict with expected keys."""
        stats = ner.get_stats()
        assert "entity_types" in stats
        assert "pattern_types" in stats
        assert "total_patterns" in stats
        assert "spacy_available" in stats
        assert "trained" in stats
        assert stats["entity_types"] == 10

    def test_get_stats_pattern_counts(self, ner):
        """get_stats() should report pattern counts per type."""
        stats = ner.get_stats()
        assert "PROGRAM" in stats["patterns_by_type"]
        assert "COMPANY" in stats["patterns_by_type"]
        assert stats["patterns_by_type"]["PROGRAM"] > 0


class TestPipelineStage:
    """Tests for the pipeline stage wrapper."""

    def test_run_ner_pipeline_stage(self):
        """run_ner_pipeline_stage() should enrich records."""
        from Engine8_Knowledge.ml.defense_ner import run_ner_pipeline_stage

        records = [
            {"description": "GDIT TS/SCI DCGS-A at Fort Belvoir"},
        ]
        result = run_ner_pipeline_stage(records)
        assert len(result) == 1
        assert "entities" in result[0]
        assert "COMPANY" in result[0]["entities"]
        assert "PROGRAM" in result[0]["entities"]
        assert "INSTALLATION" in result[0]["entities"]
