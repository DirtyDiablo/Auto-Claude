"""Tests for Phase 43A — Schema Registry."""

import pytest

from src.governance.schema_registry import (
    SchemaRegistry,
    DataSchema,
    SchemaField,
    FieldType,
    CompatibilityMode,
    EvolutionType,
    ValidationResult,
    CompatibilityReport,
    get_schema_registry,
    _infer_type,
)


@pytest.fixture
def registry():
    return SchemaRegistry()


# =========================================
# SEEDED SCHEMAS
# =========================================

def test_seeded_schemas(registry):
    schemas = registry.list_schemas()
    assert len(schemas) >= 3
    names = {s.name for s in schemas}
    assert "contact" in names
    assert "job_posting" in names
    assert "program" in names


def test_get_contact_schema(registry):
    schema = registry.get("contact")
    assert schema is not None
    assert schema.version == 1
    field_names = {f.name for f in schema.fields}
    assert "name" in field_names
    assert "email" in field_names


# =========================================
# REGISTER & RETRIEVE
# =========================================

def test_register_new(registry):
    schema_id = registry.register(DataSchema(
        name="test_schema", domain="test", version=1,
        fields=[SchemaField(name="id", field_type="string", required=True)],
    ))
    assert schema_id != ""
    assert registry.get("test_schema") is not None


def test_get_versions(registry):
    versions = registry.get_versions("contact")
    assert len(versions) >= 1


def test_get_nonexistent(registry):
    assert registry.get("nonexistent") is None


# =========================================
# VALIDATION
# =========================================

def test_validate_valid_contact(registry):
    result = registry.validate("contact", {
        "name": "John Smith",
        "email": "john@example.com",
        "tier": 3,
    })
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_missing_required(registry):
    result = registry.validate("contact", {
        "email": "john@example.com",
    })
    assert result.valid is False
    assert any("name" in e for e in result.errors)


def test_validate_wrong_type(registry):
    result = registry.validate("contact", {
        "name": "John Smith",
        "tier": "not_a_number",
    })
    assert result.valid is False
    assert any("tier" in e for e in result.errors)


def test_validate_constraint_min(registry):
    result = registry.validate("contact", {
        "name": "John Smith",
        "tier": 0,
    })
    assert result.valid is False
    assert any("minimum" in e for e in result.errors)


def test_validate_constraint_max(registry):
    result = registry.validate("contact", {
        "name": "John Smith",
        "tier": 10,
    })
    assert result.valid is False
    assert any("maximum" in e for e in result.errors)


def test_validate_extra_fields(registry):
    result = registry.validate("contact", {
        "name": "John Smith",
        "unknown_field": "value",
    })
    assert result.valid is True
    assert any("Extra field" in w for w in result.warnings)


def test_validate_nonexistent_schema(registry):
    result = registry.validate("nonexistent", {"a": 1})
    assert result.valid is False


def test_validate_job_posting(registry):
    result = registry.validate("job_posting", {
        "title": "Software Engineer",
        "company": "GDIT",
        "bd_priority_score": 85.5,
    })
    assert result.valid is True


# =========================================
# EVOLUTION & COMPATIBILITY
# =========================================

def test_evolve_add_optional_field(registry):
    new_schema = DataSchema(
        name="contact", domain="contacts",
        fields=[
            SchemaField(name="name", field_type="string", required=True),
            SchemaField(name="email", field_type="string"),
            SchemaField(name="phone", field_type="string"),
            SchemaField(name="title", field_type="string"),
            SchemaField(name="company", field_type="string"),
            SchemaField(name="tier", field_type="integer", constraints={"min": 1, "max": 6}),
            SchemaField(name="location", field_type="string"),
            SchemaField(name="source", field_type="string"),
            SchemaField(name="linkedin_url", field_type="string"),  # new optional
        ],
        compatibility="backward",
    )
    report = registry.evolve("contact", new_schema)
    assert report.compatible is True
    assert registry.get("contact").version == 2


def test_evolve_breaking_change(registry):
    new_schema = DataSchema(
        name="contact", domain="contacts",
        fields=[
            SchemaField(name="full_name", field_type="string", required=True),  # renamed
        ],
        compatibility="backward",
    )
    report = registry.evolve("contact", new_schema)
    assert report.compatible is False
    assert report.breaking_changes > 0


def test_compatibility_check(registry):
    old = registry.get("contact")
    new = DataSchema(
        name="contact",
        fields=list(old.fields) + [SchemaField(name="notes", field_type="string")],
        compatibility="backward",
    )
    report = registry.check_compatibility(old, new)
    assert report.compatible is True
    assert any(c.change_type == EvolutionType.FIELD_ADDED.value for c in report.changes)


# =========================================
# AUTO-GENERATE
# =========================================

def test_generate_from_data(registry):
    records = [
        {"name": "John", "age": 30, "active": True, "score": 0.95},
        {"name": "Jane", "age": 25, "active": False, "score": 0.88},
    ]
    schema = registry.generate_from_data("auto_test", records, domain="test")
    assert schema.name == "auto_test"
    assert len(schema.fields) == 4
    field_map = {f.name: f for f in schema.fields}
    assert field_map["name"].field_type == "string"
    assert field_map["age"].field_type == "integer"
    assert field_map["active"].field_type == "boolean"
    assert field_map["score"].field_type == "float"


def test_generate_empty(registry):
    schema = registry.generate_from_data("empty", [])
    assert len(schema.fields) == 0


# =========================================
# TYPE INFERENCE
# =========================================

def test_infer_string():
    assert _infer_type("hello") == "string"


def test_infer_int():
    assert _infer_type(42) == "integer"


def test_infer_float():
    assert _infer_type(3.14) == "float"


def test_infer_bool():
    assert _infer_type(True) == "boolean"


def test_infer_datetime():
    assert _infer_type("2025-01-15T10:30:00") == "datetime"


def test_infer_date():
    assert _infer_type("2025-01-15") == "date"


def test_infer_list():
    assert _infer_type([1, 2, 3]) == "list"


def test_infer_dict():
    assert _infer_type({"a": 1}) == "dict"


# =========================================
# STATS
# =========================================

def test_stats(registry):
    stats = registry.get_stats()
    assert stats["total_schemas"] >= 3
    assert stats["total_versions"] >= 3


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    r1 = get_schema_registry()
    r2 = get_schema_registry()
    assert r1 is r2
