"""Tests for Phase 55A — Feature Flag Engine."""

import pytest

from src.experimentation.feature_flags import (
    FeatureFlagEngine,
    FlagType,
    FlagStatus,
    get_flag_engine,
)


@pytest.fixture
def engine():
    return FeatureFlagEngine()


# =========================================
# DEFAULT FLAGS
# =========================================

def test_default_flags(engine):
    flags = engine.list_flags()
    assert len(flags) == 8


def test_dark_mode_flag(engine):
    flags = engine.list_flags()
    dark_mode = [f for f in flags if f.name == "dark_mode"]
    assert len(dark_mode) == 1


# =========================================
# CREATE FLAGS
# =========================================

def test_create_flag(engine):
    flag = engine.create_flag("test_flag", FlagType.BOOLEAN, "A test flag")
    assert flag.flag_id.startswith("flag_")
    assert flag.name == "test_flag"


def test_create_percentage_flag(engine):
    flag = engine.create_flag("pct_flag", FlagType.PERCENTAGE)
    assert flag.flag_type == FlagType.PERCENTAGE


# =========================================
# IS_ENABLED
# =========================================

def test_boolean_enabled(engine):
    flag = engine.create_flag("test_bool", FlagType.BOOLEAN)
    engine.update_flag(flag.flag_id, enabled=True)
    assert engine.is_enabled(flag.flag_id) is True


def test_boolean_disabled(engine):
    flag = engine.create_flag("test_bool", FlagType.BOOLEAN)
    assert engine.is_enabled(flag.flag_id) is False


def test_percentage_flag(engine):
    flag = engine.create_flag("pct_test", FlagType.PERCENTAGE)
    engine.update_flag(flag.flag_id, enabled=True, percentage=100.0)
    assert engine.is_enabled(flag.flag_id, user_id="user1") is True


def test_percentage_zero(engine):
    flag = engine.create_flag("pct_zero", FlagType.PERCENTAGE)
    engine.update_flag(flag.flag_id, enabled=True, percentage=0.0)
    assert engine.is_enabled(flag.flag_id, user_id="user1") is False


def test_user_list_flag(engine):
    flag = engine.create_flag("ul_flag", FlagType.USER_LIST)
    engine.update_flag(flag.flag_id, enabled=True, allowed_users=["u1", "u2"])
    assert engine.is_enabled(flag.flag_id, user_id="u1") is True
    assert engine.is_enabled(flag.flag_id, user_id="u3") is False


def test_is_enabled_not_found(engine):
    assert engine.is_enabled("flag_nonexistent") is False


# =========================================
# UPDATE / DELETE
# =========================================

def test_update_flag(engine):
    flag = engine.create_flag("upd", FlagType.BOOLEAN)
    result = engine.update_flag(flag.flag_id, description="Updated")
    assert result.description == "Updated"


def test_update_not_found(engine):
    assert engine.update_flag("flag_fake") is None


def test_delete_flag(engine):
    flag = engine.create_flag("del_me", FlagType.BOOLEAN)
    engine.delete_flag(flag.flag_id)
    f = engine.get_flag(flag.flag_id)
    assert f.status == FlagStatus.ARCHIVED


# =========================================
# ROLLOUT STAGES
# =========================================

def test_set_rollout_stages(engine):
    flag = engine.create_flag("rollout_test", FlagType.GRADUAL_ROLLOUT)
    engine.set_rollout_stages(flag.flag_id, [
        {"percentage": 10, "duration_hours": 24},
        {"percentage": 50, "duration_hours": 48},
        {"percentage": 100, "duration_hours": 72},
    ])
    f = engine.get_flag(flag.flag_id)
    assert len(f.rollout_stages) == 3


def test_advance_rollout(engine):
    flag = engine.create_flag("adv_test", FlagType.GRADUAL_ROLLOUT)
    engine.set_rollout_stages(flag.flag_id, [
        {"percentage": 10, "duration_hours": 24},
        {"percentage": 100, "duration_hours": 48},
    ])
    engine.advance_rollout(flag.flag_id)
    f = engine.get_flag(flag.flag_id)
    assert f.rollout_stages[0].completed is True


# =========================================
# QUERY
# =========================================

def test_list_by_status(engine):
    active = engine.list_flags(status=FlagStatus.ACTIVE)
    assert len(active) >= 8


def test_list_by_tag(engine):
    flag = engine.create_flag("tagged", FlagType.BOOLEAN, tags=["beta"])
    flags = engine.list_flags(tag="beta")
    assert len(flags) >= 1


def test_get_flag(engine):
    flag = engine.create_flag("get_test", FlagType.BOOLEAN)
    fetched = engine.get_flag(flag.flag_id)
    assert fetched is not None
    assert fetched.name == "get_test"


# =========================================
# TO_DICT & STATS
# =========================================

def test_flag_to_dict(engine):
    flag = engine.create_flag("dict_test", FlagType.BOOLEAN)
    d = flag.to_dict()
    assert "flag_id" in d
    assert "flag_type" in d
    assert "status" in d


def test_stats(engine):
    stats = engine.get_stats()
    assert stats["total_flags"] == 8
    assert stats["active_flags"] == 8


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.experimentation.feature_flags as mod
    mod._instance = None
    e1 = get_flag_engine()
    e2 = get_flag_engine()
    assert e1 is e2
    mod._instance = None
