"""Phase 43A — Schema Registry

Versioned schemas for all data types. Schema validation on write,
evolution with backward compatibility checks, and auto-generation
from existing data.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# ENUMS
# =========================================

class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


class CompatibilityMode(str, Enum):
    NONE = "none"               # No compatibility check
    BACKWARD = "backward"       # New schema can read old data
    FORWARD = "forward"         # Old schema can read new data
    FULL = "full"               # Both directions


class EvolutionType(str, Enum):
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    FIELD_MADE_REQUIRED = "field_made_required"
    FIELD_MADE_OPTIONAL = "field_made_optional"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class SchemaField:
    """A field definition within a schema."""
    name: str = ""
    field_type: str = FieldType.STRING.value
    required: bool = False
    description: str = ""
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)  # min, max, pattern, enum


@dataclass
class DataSchema:
    """A versioned schema for a data type."""
    id: str = ""
    name: str = ""
    version: int = 1
    domain: str = ""
    description: str = ""
    fields: List[SchemaField] = field(default_factory=list)
    compatibility: str = CompatibilityMode.BACKWARD.value
    status: str = "active"  # active, deprecated, draft
    created_at: str = ""
    created_by: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validating data against a schema."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fields_checked: int = 0
    fields_valid: int = 0


@dataclass
class EvolutionChange:
    """A single change in schema evolution."""
    change_type: str = ""
    field_name: str = ""
    old_value: Any = None
    new_value: Any = None
    breaking: bool = False


@dataclass
class CompatibilityReport:
    """Report from a compatibility check between two schema versions."""
    compatible: bool = True
    mode: str = CompatibilityMode.BACKWARD.value
    changes: List[EvolutionChange] = field(default_factory=list)
    breaking_changes: int = 0


# =========================================
# TYPE VALIDATORS
# =========================================

_TYPE_VALIDATORS = {
    FieldType.STRING.value: lambda v: isinstance(v, str),
    FieldType.INTEGER.value: lambda v: isinstance(v, int) and not isinstance(v, bool),
    FieldType.FLOAT.value: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    FieldType.BOOLEAN.value: lambda v: isinstance(v, bool),
    FieldType.DATE.value: lambda v: isinstance(v, str) and bool(re.match(r'\d{4}-\d{2}-\d{2}$', v)),
    FieldType.DATETIME.value: lambda v: isinstance(v, str) and len(v) >= 19,
    FieldType.LIST.value: lambda v: isinstance(v, list),
    FieldType.DICT.value: lambda v: isinstance(v, dict),
    FieldType.ANY.value: lambda v: True,
}


def _infer_type(value: Any) -> str:
    """Infer field type from a Python value."""
    if isinstance(value, bool):
        return FieldType.BOOLEAN.value
    if isinstance(value, int):
        return FieldType.INTEGER.value
    if isinstance(value, float):
        return FieldType.FLOAT.value
    if isinstance(value, list):
        return FieldType.LIST.value
    if isinstance(value, dict):
        return FieldType.DICT.value
    if isinstance(value, str):
        if re.match(r'\d{4}-\d{2}-\d{2}T', value):
            return FieldType.DATETIME.value
        if re.match(r'\d{4}-\d{2}-\d{2}$', value):
            return FieldType.DATE.value
        return FieldType.STRING.value
    return FieldType.ANY.value


# =========================================
# SCHEMA REGISTRY
# =========================================

class SchemaRegistry:
    """Versioned schema registry with validation and evolution."""

    def __init__(self):
        # schema_name → list of versions (ordered by version number)
        self._schemas: Dict[str, List[DataSchema]] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Seed registry with known platform schemas."""
        self.register(DataSchema(
            name="contact", domain="contacts", version=1,
            description="CRM contact record",
            fields=[
                SchemaField(name="name", field_type="string", required=True, description="Full name"),
                SchemaField(name="email", field_type="string", required=False, description="Email address"),
                SchemaField(name="phone", field_type="string", required=False),
                SchemaField(name="title", field_type="string", required=False, description="Job title"),
                SchemaField(name="company", field_type="string", required=False),
                SchemaField(name="tier", field_type="integer", required=False, description="1-6 tier classification",
                            constraints={"min": 1, "max": 6}),
                SchemaField(name="location", field_type="string", required=False),
                SchemaField(name="source", field_type="string", required=False),
            ],
            compatibility="backward",
        ))
        self.register(DataSchema(
            name="job_posting", domain="jobs", version=1,
            description="Scraped job posting record",
            fields=[
                SchemaField(name="title", field_type="string", required=True),
                SchemaField(name="company", field_type="string", required=True),
                SchemaField(name="location", field_type="string", required=False),
                SchemaField(name="description", field_type="string", required=False),
                SchemaField(name="clearance_required", field_type="string", required=False),
                SchemaField(name="mapped_program", field_type="string", required=False),
                SchemaField(name="bd_priority_score", field_type="float", required=False,
                            constraints={"min": 0, "max": 100}),
                SchemaField(name="date_posted", field_type="string", required=False),
                SchemaField(name="source_url", field_type="string", required=False),
            ],
            compatibility="backward",
        ))
        self.register(DataSchema(
            name="program", domain="programs", version=1,
            description="Federal program record",
            fields=[
                SchemaField(name="name", field_type="string", required=True),
                SchemaField(name="agency", field_type="string", required=False),
                SchemaField(name="prime_contractor", field_type="string", required=False),
                SchemaField(name="value", field_type="string", required=False),
                SchemaField(name="status", field_type="string", required=False),
                SchemaField(name="description", field_type="string", required=False),
            ],
            compatibility="backward",
        ))

    # -----------------------------------------
    # REGISTER & RETRIEVE
    # -----------------------------------------

    def register(self, schema: DataSchema) -> str:
        """Register a new schema or version."""
        if not schema.id:
            schema.id = f"{schema.name}_v{schema.version}"
        if not schema.created_at:
            schema.created_at = datetime.now(timezone.utc).isoformat()

        if schema.name not in self._schemas:
            self._schemas[schema.name] = []

        # Check if version already exists
        existing_versions = {s.version for s in self._schemas[schema.name]}
        if schema.version in existing_versions:
            # Update existing version
            self._schemas[schema.name] = [
                schema if s.version == schema.version else s
                for s in self._schemas[schema.name]
            ]
        else:
            self._schemas[schema.name].append(schema)
            self._schemas[schema.name].sort(key=lambda s: s.version)

        logger.debug("Registered schema: %s v%d", schema.name, schema.version)
        return schema.id

    def get(self, name: str, version: Optional[int] = None) -> Optional[DataSchema]:
        """Get a schema by name (latest version if version not specified)."""
        versions = self._schemas.get(name, [])
        if not versions:
            return None
        if version is not None:
            for s in versions:
                if s.version == version:
                    return s
            return None
        return versions[-1]  # latest

    def get_versions(self, name: str) -> List[DataSchema]:
        """Get all versions of a schema."""
        return list(self._schemas.get(name, []))

    def list_schemas(self) -> List[DataSchema]:
        """List latest version of all schemas."""
        return [versions[-1] for versions in self._schemas.values() if versions]

    # -----------------------------------------
    # VALIDATION
    # -----------------------------------------

    def validate(self, name: str, data: Dict[str, Any], version: Optional[int] = None) -> ValidationResult:
        """Validate a data record against a schema."""
        schema = self.get(name, version)
        if not schema:
            return ValidationResult(
                valid=False,
                errors=[f"Schema '{name}' not found"],
            )

        result = ValidationResult()
        field_map = {f.name: f for f in schema.fields}

        # Check required fields
        for sf in schema.fields:
            result.fields_checked += 1
            if sf.required and sf.name not in data:
                result.errors.append(f"Missing required field: {sf.name}")
                result.valid = False
            elif sf.name in data:
                value = data[sf.name]
                # Type check
                if value is not None:
                    validator = _TYPE_VALIDATORS.get(sf.field_type, lambda v: True)
                    if not validator(value):
                        result.errors.append(
                            f"Field '{sf.name}': expected {sf.field_type}, got {type(value).__name__}"
                        )
                        result.valid = False
                    else:
                        # Constraint checks
                        self._check_constraints(sf, value, result)
                        result.fields_valid += 1
                else:
                    result.fields_valid += 1  # None is valid for optional

        # Warn about extra fields not in schema
        schema_fields = {f.name for f in schema.fields}
        for key in data:
            if key not in schema_fields:
                result.warnings.append(f"Extra field not in schema: {key}")

        return result

    def _check_constraints(self, sf: SchemaField, value: Any, result: ValidationResult) -> None:
        """Check field constraints (min, max, pattern, enum)."""
        constraints = sf.constraints
        if not constraints:
            return

        if "min" in constraints and isinstance(value, (int, float)):
            if value < constraints["min"]:
                result.errors.append(
                    f"Field '{sf.name}': value {value} below minimum {constraints['min']}"
                )
                result.valid = False

        if "max" in constraints and isinstance(value, (int, float)):
            if value > constraints["max"]:
                result.errors.append(
                    f"Field '{sf.name}': value {value} above maximum {constraints['max']}"
                )
                result.valid = False

        if "pattern" in constraints and isinstance(value, str):
            if not re.match(constraints["pattern"], value):
                result.warnings.append(
                    f"Field '{sf.name}': value doesn't match pattern {constraints['pattern']}"
                )

        if "enum" in constraints:
            if value not in constraints["enum"]:
                result.errors.append(
                    f"Field '{sf.name}': value '{value}' not in allowed values"
                )
                result.valid = False

    # -----------------------------------------
    # EVOLUTION & COMPATIBILITY
    # -----------------------------------------

    def evolve(self, name: str, new_schema: DataSchema) -> CompatibilityReport:
        """Check compatibility and register new version."""
        current = self.get(name)
        if not current:
            new_schema.version = 1
            self.register(new_schema)
            return CompatibilityReport(compatible=True, mode=new_schema.compatibility)

        report = self.check_compatibility(current, new_schema)

        if report.compatible or new_schema.compatibility == CompatibilityMode.NONE.value:
            new_schema.version = current.version + 1
            new_schema.id = f"{name}_v{new_schema.version}"
            self.register(new_schema)

        return report

    def check_compatibility(self, old: DataSchema, new: DataSchema) -> CompatibilityReport:
        """Check backward compatibility between two schema versions."""
        changes: List[EvolutionChange] = []
        old_fields = {f.name: f for f in old.fields}
        new_fields = {f.name: f for f in new.fields}

        # Fields removed in new version
        for name, of in old_fields.items():
            if name not in new_fields:
                breaking = of.required  # removing required field is breaking
                changes.append(EvolutionChange(
                    change_type=EvolutionType.FIELD_REMOVED.value,
                    field_name=name,
                    old_value=of.field_type,
                    breaking=breaking,
                ))

        # Fields added in new version
        for name, nf in new_fields.items():
            if name not in old_fields:
                breaking = nf.required and nf.default is None  # required without default
                changes.append(EvolutionChange(
                    change_type=EvolutionType.FIELD_ADDED.value,
                    field_name=name,
                    new_value=nf.field_type,
                    breaking=breaking,
                ))

        # Fields modified
        for name in old_fields:
            if name in new_fields:
                of = old_fields[name]
                nf = new_fields[name]

                if of.field_type != nf.field_type:
                    changes.append(EvolutionChange(
                        change_type=EvolutionType.FIELD_TYPE_CHANGED.value,
                        field_name=name,
                        old_value=of.field_type,
                        new_value=nf.field_type,
                        breaking=True,
                    ))

                if not of.required and nf.required:
                    changes.append(EvolutionChange(
                        change_type=EvolutionType.FIELD_MADE_REQUIRED.value,
                        field_name=name,
                        breaking=True,
                    ))

                if of.required and not nf.required:
                    changes.append(EvolutionChange(
                        change_type=EvolutionType.FIELD_MADE_OPTIONAL.value,
                        field_name=name,
                        breaking=False,
                    ))

        breaking_count = sum(1 for c in changes if c.breaking)
        mode = old.compatibility

        compatible = True
        if mode == CompatibilityMode.BACKWARD.value and breaking_count > 0:
            compatible = False
        elif mode == CompatibilityMode.FULL.value and breaking_count > 0:
            compatible = False

        return CompatibilityReport(
            compatible=compatible,
            mode=mode,
            changes=changes,
            breaking_changes=breaking_count,
        )

    # -----------------------------------------
    # AUTO-GENERATE
    # -----------------------------------------

    def generate_from_data(self, name: str, records: List[Dict[str, Any]], domain: str = "") -> DataSchema:
        """Auto-generate a schema from sample data records."""
        if not records:
            return DataSchema(name=name, domain=domain)

        # Collect all field info across records
        field_info: Dict[str, Dict[str, Any]] = {}
        total = len(records)

        for record in records:
            for key, value in record.items():
                if key not in field_info:
                    field_info[key] = {"types": {}, "count": 0, "non_null": 0}
                field_info[key]["count"] += 1
                if value is not None:
                    field_info[key]["non_null"] += 1
                    inferred = _infer_type(value)
                    field_info[key]["types"][inferred] = field_info[key]["types"].get(inferred, 0) + 1

        # Build schema fields
        fields: List[SchemaField] = []
        for fname, info in field_info.items():
            # Pick most common type
            if info["types"]:
                ftype = max(info["types"], key=info["types"].get)
            else:
                ftype = FieldType.ANY.value

            # Required if present in >90% of records
            required = (info["count"] / total) > 0.9 and (info["non_null"] / max(info["count"], 1)) > 0.8

            fields.append(SchemaField(
                name=fname,
                field_type=ftype,
                required=required,
            ))

        return DataSchema(
            name=name,
            domain=domain,
            description=f"Auto-generated from {total} records",
            fields=fields,
            status="draft",
        )

    # -----------------------------------------
    # STATS
    # -----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_schemas = len(self._schemas)
        total_versions = sum(len(vs) for vs in self._schemas.values())
        return {
            "total_schemas": total_schemas,
            "total_versions": total_versions,
            "schemas": [
                {"name": name, "versions": len(vs), "latest": vs[-1].version}
                for name, vs in self._schemas.items()
            ],
        }


# =========================================
# SINGLETON
# =========================================

_registry: Optional[SchemaRegistry] = None


def get_schema_registry() -> SchemaRegistry:
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry
