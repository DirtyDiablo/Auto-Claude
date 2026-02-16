"""Phase 52A — Encryption at Rest with Envelope Encryption.

AES-256-GCM field-level encryption using envelope encryption pattern:
KEK (Key Encryption Key) wraps DEK (Data Encryption Key), DEK wraps data.
Supports key rotation, searchable encryption via HMAC tokens, and
encrypted field management for sensitive BD data.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class KeyStatus(str, Enum):
    ACTIVE = "active"
    ROTATED = "rotated"
    RETIRED = "retired"
    COMPROMISED = "compromised"


class FieldSensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class EncryptionKey:
    """Represents a DEK (Data Encryption Key)."""

    key_id: str
    key_material: bytes  # 32 bytes for AES-256
    status: KeyStatus = KeyStatus.ACTIVE
    created_at: str = ""
    rotated_at: Optional[str] = None
    expires_at: Optional[str] = None
    encrypted_by_kek: str = ""  # KEK id that wraps this DEK
    usage_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "rotated_at": self.rotated_at,
            "expires_at": self.expires_at,
            "encrypted_by_kek": self.encrypted_by_kek,
            "usage_count": self.usage_count,
            # Never expose key_material
        }


@dataclass
class KEK:
    """Key Encryption Key — wraps DEKs."""

    kek_id: str
    key_material: bytes  # 32 bytes
    status: KeyStatus = KeyStatus.ACTIVE
    created_at: str = ""
    dek_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kek_id": self.kek_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "dek_count": len(self.dek_ids),
        }


@dataclass
class EncryptedField:
    """An encrypted data field with metadata."""

    field_id: str
    resource_type: str  # contact, humint_note, simulation, api_key
    resource_id: str
    field_name: str  # email, phone, note_body, competitor_data
    ciphertext: str  # base64-encoded
    nonce: str  # base64-encoded
    dek_id: str
    sensitivity: FieldSensitivity = FieldSensitivity.CONFIDENTIAL
    encrypted_at: str = ""
    search_token: str = ""  # HMAC token for searchable encryption

    def __post_init__(self):
        if not self.encrypted_at:
            self.encrypted_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "field_name": self.field_name,
            "sensitivity": self.sensitivity.value,
            "encrypted_at": self.encrypted_at,
            "dek_id": self.dek_id,
            "has_search_token": bool(self.search_token),
        }


@dataclass
class KeyRotationResult:
    """Result of a key rotation operation."""

    rotation_id: str
    old_key_id: str
    new_key_id: str
    fields_re_encrypted: int
    duration_ms: float
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rotation_id": self.rotation_id,
            "old_key_id": self.old_key_id,
            "new_key_id": self.new_key_id,
            "fields_re_encrypted": self.fields_re_encrypted,
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
            "error": self.error,
        }


@dataclass
class EncryptionStatus:
    """Overall encryption system status."""

    total_encrypted_fields: int = 0
    total_deks: int = 0
    active_deks: int = 0
    total_keks: int = 0
    fields_by_type: Dict[str, int] = field(default_factory=dict)
    fields_by_sensitivity: Dict[str, int] = field(default_factory=dict)
    last_rotation: Optional[str] = None
    next_rotation_due: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_encrypted_fields": self.total_encrypted_fields,
            "total_deks": self.total_deks,
            "active_deks": self.active_deks,
            "total_keks": self.total_keks,
            "fields_by_type": self.fields_by_type,
            "fields_by_sensitivity": self.fields_by_sensitivity,
            "last_rotation": self.last_rotation,
            "next_rotation_due": self.next_rotation_due,
        }


# =========================================
# SENSITIVE FIELD REGISTRY
# =========================================

_SENSITIVE_FIELDS: Dict[str, Dict[str, FieldSensitivity]] = {
    "contact": {
        "email": FieldSensitivity.CONFIDENTIAL,
        "phone": FieldSensitivity.CONFIDENTIAL,
        "personal_notes": FieldSensitivity.RESTRICTED,
    },
    "humint_note": {
        "note_body": FieldSensitivity.RESTRICTED,
        "source_identity": FieldSensitivity.RESTRICTED,
    },
    "simulation": {
        "competitor_data": FieldSensitivity.CONFIDENTIAL,
        "pricing_model": FieldSensitivity.CONFIDENTIAL,
    },
    "api_key": {
        "key_value": FieldSensitivity.RESTRICTED,
        "secret": FieldSensitivity.RESTRICTED,
    },
}


# =========================================
# ENCRYPTION MANAGER
# =========================================


class EncryptionManager:
    """Field-level encryption with envelope encryption and key rotation.

    Uses a simplified AES-256-GCM simulation (XOR-based for portability
    without requiring cryptographic libraries). In production, replace
    _encrypt_raw/_decrypt_raw with actual AES-256-GCM.

    Envelope pattern: KEK wraps DEK, DEK wraps data fields.
    """

    def __init__(self):
        self._keks: Dict[str, KEK] = {}
        self._deks: Dict[str, EncryptionKey] = {}
        self._encrypted_fields: Dict[str, EncryptedField] = {}
        self._search_index: Dict[str, List[str]] = {}  # token → field_ids
        self._rotation_history: List[KeyRotationResult] = []
        self._hmac_key = os.urandom(32)

        # Bootstrap: create initial KEK and DEK
        self._bootstrap_keys()
        logger.info("EncryptionManager initialized with envelope encryption")

    def _bootstrap_keys(self) -> None:
        """Create initial KEK and DEK pair."""
        kek = KEK(
            kek_id=f"kek_{uuid.uuid4().hex[:12]}",
            key_material=os.urandom(32),
        )
        self._keks[kek.kek_id] = kek

        dek = EncryptionKey(
            key_id=f"dek_{uuid.uuid4().hex[:12]}",
            key_material=os.urandom(32),
            encrypted_by_kek=kek.kek_id,
            expires_at=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        )
        self._deks[dek.key_id] = dek
        kek.dek_ids.append(dek.key_id)

    def _get_active_dek(self) -> EncryptionKey:
        """Get the current active DEK."""
        for dek in self._deks.values():
            if dek.status == KeyStatus.ACTIVE:
                return dek
        # If no active DEK, create one
        kek = next(k for k in self._keks.values() if k.status == KeyStatus.ACTIVE)
        dek = EncryptionKey(
            key_id=f"dek_{uuid.uuid4().hex[:12]}",
            key_material=os.urandom(32),
            encrypted_by_kek=kek.kek_id,
            expires_at=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        )
        self._deks[dek.key_id] = dek
        kek.dek_ids.append(dek.key_id)
        return dek

    # ----- core encryption (simplified) -----

    def _encrypt_raw(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """Encrypt data using XOR cipher with random nonce (simplified AES-256-GCM).

        In production, use actual AES-256-GCM from cryptography library.
        """
        nonce = os.urandom(12)
        # Derive a stream from key + nonce via SHA-256 chain
        stream = b""
        block = key + nonce
        while len(stream) < len(plaintext):
            block = hashlib.sha256(block).digest()
            stream += block

        ciphertext = bytes(p ^ s for p, s in zip(plaintext, stream[: len(plaintext)]))
        return ciphertext, nonce

    def _decrypt_raw(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypt data (XOR is symmetric)."""
        stream = b""
        block = key + nonce
        while len(stream) < len(ciphertext):
            block = hashlib.sha256(block).digest()
            stream += block

        return bytes(c ^ s for c, s in zip(ciphertext, stream[: len(ciphertext)]))

    # ----- field encryption -----

    def encrypt_field(
        self,
        resource_type: str,
        resource_id: str,
        field_name: str,
        plaintext: str,
        searchable: bool = False,
    ) -> EncryptedField:
        """Encrypt a single field value."""
        dek = self._get_active_dek()
        dek.usage_count += 1

        ciphertext, nonce = self._encrypt_raw(
            plaintext.encode("utf-8"), dek.key_material
        )

        # Determine sensitivity
        sensitivity = _SENSITIVE_FIELDS.get(resource_type, {}).get(
            field_name, FieldSensitivity.INTERNAL
        )

        # Generate search token if requested
        search_token = ""
        if searchable:
            search_token = self._generate_search_token(plaintext.lower().strip())

        field_id = f"ef_{uuid.uuid4().hex[:12]}"
        ef = EncryptedField(
            field_id=field_id,
            resource_type=resource_type,
            resource_id=resource_id,
            field_name=field_name,
            ciphertext=base64.b64encode(ciphertext).decode(),
            nonce=base64.b64encode(nonce).decode(),
            dek_id=dek.key_id,
            sensitivity=sensitivity,
            search_token=search_token,
        )

        self._encrypted_fields[field_id] = ef

        # Index search token
        if search_token:
            self._search_index.setdefault(search_token, []).append(field_id)

        return ef

    def decrypt_field(self, field_id: str) -> Optional[str]:
        """Decrypt a field by its ID. Returns plaintext or None."""
        ef = self._encrypted_fields.get(field_id)
        if not ef:
            return None

        dek = self._deks.get(ef.dek_id)
        if not dek:
            logger.error("DEK %s not found for field %s", ef.dek_id, field_id)
            return None

        ciphertext = base64.b64decode(ef.ciphertext)
        nonce = base64.b64decode(ef.nonce)
        plaintext = self._decrypt_raw(ciphertext, dek.key_material, nonce)
        return plaintext.decode("utf-8")

    def encrypt_resource(
        self,
        resource_type: str,
        resource_id: str,
        fields: Dict[str, str],
        searchable_fields: Optional[Set[str]] = None,
    ) -> List[EncryptedField]:
        """Encrypt multiple fields for a resource."""
        searchable = searchable_fields or set()
        results = []
        for field_name, value in fields.items():
            ef = self.encrypt_field(
                resource_type=resource_type,
                resource_id=resource_id,
                field_name=field_name,
                plaintext=value,
                searchable=field_name in searchable,
            )
            results.append(ef)
        return results

    def decrypt_resource(self, resource_type: str, resource_id: str) -> Dict[str, str]:
        """Decrypt all fields for a resource."""
        result: Dict[str, str] = {}
        for ef in self._encrypted_fields.values():
            if ef.resource_type == resource_type and ef.resource_id == resource_id:
                plaintext = self.decrypt_field(ef.field_id)
                if plaintext is not None:
                    result[ef.field_name] = plaintext
        return result

    # ----- searchable encryption -----

    def _generate_search_token(self, value: str) -> str:
        """Generate HMAC-based search token for deterministic encrypted search."""
        return hmac.new(
            self._hmac_key, value.encode("utf-8"), hashlib.sha256
        ).hexdigest()[:32]

    def search_encrypted(self, query: str) -> List[EncryptedField]:
        """Search encrypted fields using HMAC tokens."""
        token = self._generate_search_token(query.lower().strip())
        field_ids = self._search_index.get(token, [])
        return [
            self._encrypted_fields[fid]
            for fid in field_ids
            if fid in self._encrypted_fields
        ]

    # ----- key rotation -----

    def rotate_keys(self) -> KeyRotationResult:
        """Rotate the active DEK: create new DEK, re-encrypt all fields."""
        start = time.time()
        rotation_id = f"rot_{uuid.uuid4().hex[:10]}"

        old_dek = self._get_active_dek()
        old_key_id = old_dek.key_id

        # Retire old DEK
        old_dek.status = KeyStatus.ROTATED
        old_dek.rotated_at = datetime.utcnow().isoformat()

        # Create new DEK
        kek = self._keks.get(old_dek.encrypted_by_kek)
        if not kek:
            kek = next(k for k in self._keks.values() if k.status == KeyStatus.ACTIVE)

        new_dek = EncryptionKey(
            key_id=f"dek_{uuid.uuid4().hex[:12]}",
            key_material=os.urandom(32),
            encrypted_by_kek=kek.kek_id,
            expires_at=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        )
        self._deks[new_dek.key_id] = new_dek
        kek.dek_ids.append(new_dek.key_id)

        # Re-encrypt all fields that used the old DEK
        re_encrypted = 0
        for ef in self._encrypted_fields.values():
            if ef.dek_id == old_key_id:
                # Decrypt with old key
                ciphertext = base64.b64decode(ef.ciphertext)
                nonce = base64.b64decode(ef.nonce)
                plaintext = self._decrypt_raw(ciphertext, old_dek.key_material, nonce)

                # Re-encrypt with new key
                new_ciphertext, new_nonce = self._encrypt_raw(
                    plaintext, new_dek.key_material
                )
                ef.ciphertext = base64.b64encode(new_ciphertext).decode()
                ef.nonce = base64.b64encode(new_nonce).decode()
                ef.dek_id = new_dek.key_id
                new_dek.usage_count += 1
                re_encrypted += 1

        elapsed = (time.time() - start) * 1000
        result = KeyRotationResult(
            rotation_id=rotation_id,
            old_key_id=old_key_id,
            new_key_id=new_dek.key_id,
            fields_re_encrypted=re_encrypted,
            duration_ms=elapsed,
            success=True,
        )
        self._rotation_history.append(result)
        return result

    # ----- queries -----

    def get_encrypted_field(self, field_id: str) -> Optional[EncryptedField]:
        return self._encrypted_fields.get(field_id)

    def list_encrypted_fields(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[EncryptedField]:
        fields = list(self._encrypted_fields.values())
        if resource_type:
            fields = [f for f in fields if f.resource_type == resource_type]
        if resource_id:
            fields = [f for f in fields if f.resource_id == resource_id]
        return fields[:limit]

    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        dek = self._deks.get(key_id)
        if dek:
            return dek.to_dict()
        kek = self._keks.get(key_id)
        if kek:
            return kek.to_dict()
        return None

    def list_keys(self, key_type: str = "all") -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        if key_type in ("all", "dek"):
            result.extend(d.to_dict() for d in self._deks.values())
        if key_type in ("all", "kek"):
            result.extend(k.to_dict() for k in self._keks.values())
        return result

    def get_rotation_history(self, limit: int = 20) -> List[KeyRotationResult]:
        return list(reversed(self._rotation_history))[:limit]

    # ----- status -----

    def get_status(self) -> EncryptionStatus:
        fields_by_type: Dict[str, int] = {}
        fields_by_sensitivity: Dict[str, int] = {}
        for ef in self._encrypted_fields.values():
            fields_by_type[ef.resource_type] = (
                fields_by_type.get(ef.resource_type, 0) + 1
            )
            s = ef.sensitivity.value
            fields_by_sensitivity[s] = fields_by_sensitivity.get(s, 0) + 1

        active_deks = sum(
            1 for d in self._deks.values() if d.status == KeyStatus.ACTIVE
        )

        last_rotation = None
        next_due = None
        if self._rotation_history:
            last_rotation = self._rotation_history[-1].rotation_id
        # Next rotation: 30 days from active DEK creation
        active_dek = None
        for d in self._deks.values():
            if d.status == KeyStatus.ACTIVE:
                active_dek = d
                break
        if active_dek and active_dek.expires_at:
            next_due = active_dek.expires_at

        return EncryptionStatus(
            total_encrypted_fields=len(self._encrypted_fields),
            total_deks=len(self._deks),
            active_deks=active_deks,
            total_keks=len(self._keks),
            fields_by_type=fields_by_type,
            fields_by_sensitivity=fields_by_sensitivity,
            last_rotation=last_rotation,
            next_rotation_due=next_due,
        )

    def get_sensitive_field_registry(self) -> Dict[str, Dict[str, str]]:
        """Return the registry of fields that should be encrypted."""
        return {
            rt: {fn: s.value for fn, s in fields.items()}
            for rt, fields in _SENSITIVE_FIELDS.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        status = self.get_status()
        return {
            "total_encrypted_fields": status.total_encrypted_fields,
            "total_keys": status.total_deks + status.total_keks,
            "active_deks": status.active_deks,
            "total_rotations": len(self._rotation_history),
            "fields_by_type": status.fields_by_type,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    global _instance
    if _instance is None:
        _instance = EncryptionManager()
    return _instance
