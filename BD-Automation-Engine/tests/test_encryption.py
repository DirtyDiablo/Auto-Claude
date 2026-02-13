"""Tests for Phase 52A — Encryption at Rest."""

import pytest

from src.security.encryption import (
    EncryptionManager,
    EncryptedField,
    KeyStatus,
    FieldSensitivity,
    KeyRotationResult,
    EncryptionStatus,
    get_encryption_manager,
)


@pytest.fixture
def mgr():
    return EncryptionManager()


# =========================================
# BOOTSTRAP
# =========================================

def test_bootstrap_creates_kek(mgr):
    assert len(mgr._keks) == 1


def test_bootstrap_creates_dek(mgr):
    assert len(mgr._deks) == 1


def test_dek_wrapped_by_kek(mgr):
    dek = list(mgr._deks.values())[0]
    assert dek.encrypted_by_kek in mgr._keks


def test_dek_is_active(mgr):
    dek = list(mgr._deks.values())[0]
    assert dek.status == KeyStatus.ACTIVE


# =========================================
# FIELD ENCRYPTION
# =========================================

def test_encrypt_field(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    assert isinstance(ef, EncryptedField)
    assert ef.field_id.startswith("ef_")
    assert ef.ciphertext != ""
    assert ef.nonce != ""


def test_decrypt_field(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == "test@example.com"


def test_encrypt_preserves_unicode(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "日本語テスト")
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == "日本語テスト"


def test_encrypt_empty_string(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "")
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == ""


def test_encrypt_long_text(mgr):
    long_text = "A" * 10000
    ef = mgr.encrypt_field("humint_note", "hn1", "note_body", long_text)
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == long_text


def test_decrypt_not_found(mgr):
    assert mgr.decrypt_field("ef_nonexistent") is None


def test_sensitivity_auto_detected(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    assert ef.sensitivity == FieldSensitivity.CONFIDENTIAL


def test_sensitivity_restricted(mgr):
    ef = mgr.encrypt_field("humint_note", "hn1", "note_body", "secret info")
    assert ef.sensitivity == FieldSensitivity.RESTRICTED


def test_sensitivity_default(mgr):
    ef = mgr.encrypt_field("report", "r1", "summary", "data")
    assert ef.sensitivity == FieldSensitivity.INTERNAL


def test_dek_usage_count(mgr):
    dek = mgr._get_active_dek()
    before = dek.usage_count
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    assert dek.usage_count == before + 1


# =========================================
# RESOURCE ENCRYPTION
# =========================================

def test_encrypt_resource(mgr):
    fields = mgr.encrypt_resource(
        "contact", "c1",
        {"email": "test@example.com", "phone": "555-1234"},
    )
    assert len(fields) == 2


def test_decrypt_resource(mgr):
    mgr.encrypt_resource(
        "contact", "c1",
        {"email": "test@example.com", "phone": "555-1234"},
    )
    result = mgr.decrypt_resource("contact", "c1")
    assert result["email"] == "test@example.com"
    assert result["phone"] == "555-1234"


def test_encrypt_resource_with_searchable(mgr):
    fields = mgr.encrypt_resource(
        "contact", "c1",
        {"email": "test@example.com", "phone": "555-1234"},
        searchable_fields={"email"},
    )
    email_field = next(f for f in fields if f.field_name == "email")
    phone_field = next(f for f in fields if f.field_name == "phone")
    assert email_field.search_token != ""
    assert phone_field.search_token == ""


# =========================================
# SEARCHABLE ENCRYPTION
# =========================================

def test_searchable_encrypt(mgr):
    ef = mgr.encrypt_field(
        "contact", "c1", "email", "test@example.com", searchable=True,
    )
    assert ef.search_token != ""


def test_search_encrypted(mgr):
    mgr.encrypt_field(
        "contact", "c1", "email", "test@example.com", searchable=True,
    )
    results = mgr.search_encrypted("test@example.com")
    assert len(results) == 1
    assert results[0].field_name == "email"


def test_search_case_insensitive(mgr):
    mgr.encrypt_field(
        "contact", "c1", "email", "Test@Example.com", searchable=True,
    )
    results = mgr.search_encrypted("test@example.com")
    assert len(results) == 1


def test_search_no_match(mgr):
    mgr.encrypt_field(
        "contact", "c1", "email", "test@example.com", searchable=True,
    )
    results = mgr.search_encrypted("other@example.com")
    assert len(results) == 0


def test_search_multiple_matches(mgr):
    mgr.encrypt_field(
        "contact", "c1", "email", "shared@example.com", searchable=True,
    )
    mgr.encrypt_field(
        "contact", "c2", "email", "shared@example.com", searchable=True,
    )
    results = mgr.search_encrypted("shared@example.com")
    assert len(results) == 2


# =========================================
# KEY ROTATION
# =========================================

def test_rotate_keys(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    result = mgr.rotate_keys()
    assert isinstance(result, KeyRotationResult)
    assert result.success is True
    assert result.fields_re_encrypted == 1


def test_rotation_creates_new_dek(mgr):
    before_count = len(mgr._deks)
    mgr.rotate_keys()
    assert len(mgr._deks) == before_count + 1


def test_rotation_retires_old_dek(mgr):
    old_dek = mgr._get_active_dek()
    old_id = old_dek.key_id
    mgr.rotate_keys()
    assert mgr._deks[old_id].status == KeyStatus.ROTATED


def test_data_readable_after_rotation(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    mgr.rotate_keys()
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == "test@example.com"


def test_multiple_rotations(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    mgr.rotate_keys()
    mgr.rotate_keys()
    mgr.rotate_keys()
    plaintext = mgr.decrypt_field(ef.field_id)
    assert plaintext == "test@example.com"


def test_rotation_history(mgr):
    mgr.rotate_keys()
    mgr.rotate_keys()
    history = mgr.get_rotation_history()
    assert len(history) == 2
    # Most recent first
    assert history[0].rotation_id != history[1].rotation_id


def test_rotation_re_encrypts_all(mgr):
    for i in range(5):
        mgr.encrypt_field("contact", f"c{i}", "email", f"u{i}@test.com")
    result = mgr.rotate_keys()
    assert result.fields_re_encrypted == 5


# =========================================
# QUERIES
# =========================================

def test_get_encrypted_field(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    fetched = mgr.get_encrypted_field(ef.field_id)
    assert fetched is not None
    assert fetched.field_id == ef.field_id


def test_list_encrypted_fields(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    mgr.encrypt_field("contact", "c2", "phone", "555-1234")
    mgr.encrypt_field("humint_note", "hn1", "note_body", "secret")
    fields = mgr.list_encrypted_fields()
    assert len(fields) == 3


def test_list_by_resource_type(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    mgr.encrypt_field("humint_note", "hn1", "note_body", "secret")
    fields = mgr.list_encrypted_fields(resource_type="contact")
    assert len(fields) == 1


def test_get_key_info_dek(mgr):
    dek = list(mgr._deks.values())[0]
    info = mgr.get_key_info(dek.key_id)
    assert info is not None
    assert "key_id" in info
    assert "key_material" not in info  # Never expose key material


def test_get_key_info_kek(mgr):
    kek = list(mgr._keks.values())[0]
    info = mgr.get_key_info(kek.kek_id)
    assert info is not None


def test_list_keys_all(mgr):
    keys = mgr.list_keys("all")
    assert len(keys) == 2  # 1 KEK + 1 DEK


def test_list_keys_dek_only(mgr):
    keys = mgr.list_keys("dek")
    assert len(keys) == 1


# =========================================
# STATUS & STATS
# =========================================

def test_status(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    status = mgr.get_status()
    assert isinstance(status, EncryptionStatus)
    assert status.total_encrypted_fields == 1
    assert status.active_deks == 1


def test_status_to_dict(mgr):
    status = mgr.get_status()
    d = status.to_dict()
    assert "total_encrypted_fields" in d
    assert "total_deks" in d


def test_stats(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    stats = mgr.get_stats()
    assert stats["total_encrypted_fields"] == 1
    assert stats["active_deks"] == 1


def test_sensitive_field_registry(mgr):
    reg = mgr.get_sensitive_field_registry()
    assert "contact" in reg
    assert "email" in reg["contact"]
    assert reg["humint_note"]["note_body"] == "restricted"


# =========================================
# FIELD TO_DICT
# =========================================

def test_encrypted_field_to_dict(mgr):
    ef = mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    d = ef.to_dict()
    assert "field_id" in d
    assert "ciphertext" not in d  # to_dict doesn't expose ciphertext
    assert "sensitivity" in d


def test_key_to_dict(mgr):
    dek = list(mgr._deks.values())[0]
    d = dek.to_dict()
    assert "key_id" in d
    assert "key_material" not in d  # Never expose


def test_rotation_result_to_dict(mgr):
    mgr.encrypt_field("contact", "c1", "email", "test@example.com")
    result = mgr.rotate_keys()
    d = result.to_dict()
    assert "rotation_id" in d
    assert "success" in d


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.security.encryption as mod
    mod._instance = None
    m1 = get_encryption_manager()
    m2 = get_encryption_manager()
    assert m1 is m2
    mod._instance = None
