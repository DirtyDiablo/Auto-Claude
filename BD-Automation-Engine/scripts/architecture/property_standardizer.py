"""Property type standardization.

Normalizes 80+ raw type strings from 3 architecture JSONs into 12 canonical
types, preserving raw_type for lossless round-tripping.
"""

import re

# Canonical types: string, text, integer, float, date, datetime, boolean,
#                  json, list[string], list[json], vector(N), enum

_EXACT_MAP = {
    # String variants
    'string': 'string', 'String': 'string', 'str': 'string',
    'varchar': 'string', 'char': 'string',
    # Text variants
    'text': 'text', 'Text': 'text', 'longtext': 'text', 'clob': 'text',
    # Integer variants
    'int': 'integer', 'integer': 'integer', 'Integer': 'integer',
    'bigint': 'integer', 'smallint': 'integer', 'tinyint': 'integer',
    'int (PK auto)': 'integer',
    # Float variants
    'float': 'float', 'Float': 'float', 'double': 'float',
    'decimal': 'float', 'real': 'float', 'numeric': 'float',
    'number': 'float',
    # Date/time variants
    'date': 'date', 'Date': 'date',
    'datetime': 'datetime', 'DateTime': 'datetime',
    'timestamp': 'datetime', 'Timestamp': 'datetime',
    # Boolean variants
    'bool': 'boolean', 'boolean': 'boolean', 'Boolean': 'boolean',
    # JSON/complex variants
    'json': 'json', 'JSON': 'json', 'jsonb': 'json',
    'dict': 'json', 'Dict': 'json', 'object': 'json', 'Object': 'json',
    'map': 'json',
    # List variants
    'list': 'list[string]', 'List': 'list[string]', 'array': 'list[string]',
    'list[str]': 'list[string]', 'list[string]': 'list[string]',
    'List[str]': 'list[string]', 'String[]': 'list[string]',
    'list[int]': 'list[integer]', 'list[dict]': 'list[json]',
    'list[float]': 'list[float]',
    'JSON[]': 'list[json]',
}

# Patterns matched via regex (order matters -- first match wins)
_REGEX_PATTERNS = [
    # String(N) -> string
    (re.compile(r'^[Ss]tring\(\d+\)$'), 'string'),
    # Integer(N-M) -> integer
    (re.compile(r'^[Ii]nteger\(\d+(?:-\d+)?\)$'), 'integer'),
    # string PK / string FK -> string
    (re.compile(r'^string\s+(?:PK|FK)$', re.I), 'string'),
    # int PK / int FK -> integer
    (re.compile(r'^int\s+(?:PK|FK|auto)$', re.I), 'integer'),
    # nullable variants -> base type with nullable flag
    (re.compile(r'^(\w+)\s*\(nullable\)$', re.I), None),  # handled specially
    # unique variants -> base type
    (re.compile(r'^(\w+)\s*\(unique\)$', re.I), None),
    # FK->table.column -> fk:table.column
    (re.compile(r'^FK\s*->\s*(.+)$'), None),
    # FK:entity -> fk:entity
    (re.compile(r'^FK:(.+)$'), None),
    # Enum(...) / enum:Name -> enum
    (re.compile(r'^[Ee]num\((.+)\)$'), 'enum'),
    (re.compile(r'^enum:(.+)$'), 'enum'),
    # Vector(N) -> vector(N)
    (re.compile(r'^[Vv]ector\((\d+)\)$'), None),
    # Text/JSON -> json
    (re.compile(r'^[Tt]ext/[Jj][Ss][Oo][Nn]$'), 'json'),
]


def normalize_type(raw_type: str) -> dict:
    """Normalize a raw property type string to canonical form.

    Returns:
        {
            'type': 'string',       # canonical type
            'raw_type': 'String(255)',  # original
            'nullable': False,
            'fk_target': None,      # e.g. 'contractors.id'
            'enum_values': None,    # e.g. ['FFP', 'T&M', 'Cost-Plus']
            'vector_dim': None,     # e.g. 1536
        }
    """
    if not raw_type:
        return {
            'type': 'string', 'raw_type': '', 'nullable': False,
            'fk_target': None, 'enum_values': None, 'vector_dim': None,
        }

    result = {
        'type': 'string',
        'raw_type': raw_type,
        'nullable': False,
        'fk_target': None,
        'enum_values': None,
        'vector_dim': None,
    }

    stripped = raw_type.strip()

    # Check exact match first
    if stripped in _EXACT_MAP:
        result['type'] = _EXACT_MAP[stripped]
        return result

    # Try regex patterns
    for pattern, canonical in _REGEX_PATTERNS:
        m = pattern.match(stripped)
        if not m:
            continue

        # Nullable: "(nullable)" suffix
        if '(nullable)' in stripped.lower():
            base = m.group(1).strip().lower()
            base_norm = _EXACT_MAP.get(base, base)
            result['type'] = base_norm
            result['nullable'] = True
            return result

        # Unique: "(unique)" suffix
        if '(unique)' in stripped.lower():
            base = m.group(1).strip().lower()
            result['type'] = _EXACT_MAP.get(base, base)
            return result

        # FK reference
        if stripped.startswith('FK') and ('->' in stripped or ':' in stripped):
            target = m.group(1).strip()
            result['type'] = 'fk'
            result['fk_target'] = target
            return result

        # Enum
        if canonical == 'enum':
            values_str = m.group(1).strip()
            if '/' in values_str:
                result['enum_values'] = [v.strip() for v in values_str.split('/')]
            elif ',' in values_str:
                result['enum_values'] = [v.strip() for v in values_str.split(',')]
            else:
                result['enum_values'] = [values_str]
            result['type'] = 'enum'
            return result

        # Vector
        if 'ector' in stripped:
            dim = m.group(1)
            result['type'] = f'vector({dim})'
            result['vector_dim'] = int(dim)
            return result

        # Default pattern match
        if canonical:
            result['type'] = canonical
            return result

    # Fallback: keep as-is lowercased
    result['type'] = stripped.lower()
    return result


def standardize_property(prop: dict, project_id: str = '') -> dict:
    """Standardize a single property dict.

    Input:  {'name': 'id', 'type': 'String(50)', 'source': 'Tango', 'note': '...'}
    Output: {'name': 'id', 'type': 'string', 'raw_type': 'String(50)',
             'nullable': False, 'source': 'Tango', 'note': '...',
             'contributed_by': ['BD_ENGINE']}
    """
    type_info = normalize_type(prop.get('type', 'string'))

    result = {
        'name': prop.get('name', ''),
        'type': type_info['type'],
        'raw_type': type_info['raw_type'],
        'nullable': type_info['nullable'],
        'source': prop.get('source', ''),
        'note': prop.get('note', '') or prop.get('description', '') or '',
        'contributed_by': [project_id] if project_id else [],
    }

    if type_info['fk_target']:
        result['fk_target'] = type_info['fk_target']
    if type_info['enum_values']:
        result['enum_values'] = type_info['enum_values']
    if type_info['vector_dim']:
        result['vector_dim'] = type_info['vector_dim']

    return result


def merge_properties(existing: list[dict], new_props: list[dict]) -> list[dict]:
    """Merge two property lists, deduplicating by name.

    For duplicate names: combines contributed_by, picks richest note,
    keeps standardized type from first occurrence.
    """
    by_name = {}
    for p in existing:
        by_name[p['name']] = p

    for p in new_props:
        name = p['name']
        if name in by_name:
            ex = by_name[name]
            # Merge contributed_by
            for c in p.get('contributed_by', []):
                if c not in ex.get('contributed_by', []):
                    ex.setdefault('contributed_by', []).append(c)
            # Take longer note
            if len(p.get('note', '')) > len(ex.get('note', '')):
                ex['note'] = p['note']
        else:
            by_name[name] = p

    return list(by_name.values())
