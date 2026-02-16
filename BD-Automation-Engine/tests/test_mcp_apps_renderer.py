"""Tests for Phase 45A — MCP Apps Renderer."""

import pytest

from src.mcp.apps_renderer import (
    MCPAppsRenderer,
    MCPAppResponse,
    MCPAppAction,
    MCPAppEvent,
    RenderStatus,
    ActionStatus,
    get_apps_renderer,
)


@pytest.fixture
def renderer():
    return MCPAppsRenderer(seed_templates=True)


@pytest.fixture
def empty_renderer():
    return MCPAppsRenderer(seed_templates=False)


# =========================================
# SEEDED TEMPLATES
# =========================================


def test_seeded_templates(renderer):
    templates = renderer.list_templates()
    assert len(templates) >= 6
    ids = {t.template_id for t in templates}
    assert "contact_card" in ids
    assert "program_overview" in ids
    assert "pipeline_kanban" in ids
    assert "geographic_map" in ids
    assert "org_chart_mini" in ids
    assert "call_briefing" in ids


def test_get_template(renderer):
    t = renderer.get_template("contact_card")
    assert t is not None
    assert t.name == "Contact Card"
    assert "display" in t.permissions


# =========================================
# TEMPLATE REGISTRATION
# =========================================


def test_register_template(empty_renderer):
    t = empty_renderer.register_template(
        template_id="custom",
        name="Custom Template",
        html="<div>{{content}}</div>",
        permissions=["display"],
        description="A custom template",
    )
    assert t.template_id == "custom"
    assert empty_renderer.get_template("custom") is not None


def test_register_overwrites(renderer):
    renderer.register_template("contact_card", "Updated", "<div>New</div>")
    t = renderer.get_template("contact_card")
    assert t.name == "Updated"


# =========================================
# RENDERING
# =========================================


def test_render_contact_card(renderer):
    resp = MCPAppResponse(
        template_id="contact_card",
        data={"name": "Craig Lindahl", "title": "VP", "company": "GDIT", "tier": "1"},
    )
    rendered = renderer.render_app(resp)
    assert rendered.status == RenderStatus.RENDERED.value
    assert "Craig Lindahl" in rendered.html
    assert "VP" in rendered.html
    assert "GDIT" in rendered.html


def test_render_program_overview(renderer):
    resp = MCPAppResponse(
        template_id="program_overview",
        data={
            "program_name": "DCGS-A",
            "prime": "Leidos",
            "value": "950",
            "metrics": "[0.9,0.8]",
        },
    )
    rendered = renderer.render_app(resp)
    assert rendered.status == RenderStatus.RENDERED.value
    assert "DCGS-A" in rendered.html


def test_render_template_not_found(renderer):
    resp = MCPAppResponse(template_id="nonexistent", data={})
    rendered = renderer.render_app(resp)
    assert rendered.status == RenderStatus.TEMPLATE_NOT_FOUND.value


def test_render_stores_result(renderer):
    resp = MCPAppResponse(template_id="contact_card", data={"name": "Test"})
    rendered = renderer.render_app(resp)
    assert renderer.get_rendered(rendered.id) is not None


def test_render_logs_event(renderer):
    resp = MCPAppResponse(template_id="contact_card", data={"name": "Test"})
    renderer.render_app(resp)
    events = renderer.get_events(template_id="contact_card")
    assert len(events) >= 1
    assert events[-1].event_type == "render"


# =========================================
# SANDBOX CONFIG
# =========================================


def test_sandbox_basic(renderer):
    resp = MCPAppResponse(template_id="call_briefing", data={})
    rendered = renderer.render_app(resp)
    assert rendered.sandbox_config["allow_scripts"] is False


def test_sandbox_with_actions(renderer):
    resp = MCPAppResponse(template_id="contact_card", data={})
    rendered = renderer.render_app(resp)
    # contact_card has action:email permission
    assert rendered.sandbox_config["allow_scripts"] is True


def test_sandbox_with_chart(renderer):
    resp = MCPAppResponse(template_id="program_overview", data={})
    rendered = renderer.render_app(resp)
    assert rendered.sandbox_config["allow_scripts"] is True
    assert "script-src" in rendered.sandbox_config["csp"]


# =========================================
# ACTIONS
# =========================================


def test_render_with_actions(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card",
        data={"name": "Test"},
        actions=[action],
    )
    rendered = renderer.render_app(resp)
    assert len(rendered.actions) == 1
    assert rendered.actions[0].status == ActionStatus.PENDING.value


def test_approve_action(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    assert renderer.approve_action(rendered.id, "a1") is True


def test_deny_action(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    assert renderer.deny_action(rendered.id, "a1") is True


def test_execute_approved_action(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    renderer.approve_action(rendered.id, "a1")
    result = renderer.execute_action(rendered.id, "a1")
    assert result is not None
    assert result["status"] == "executed"


def test_execute_unapproved_action(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    result = renderer.execute_action(rendered.id, "a1")
    assert result is None


def test_execute_auto_approved(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="read_only", requires_approval=False
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    result = renderer.execute_action(rendered.id, "a1")
    assert result is not None


def test_action_nonexistent_app(renderer):
    assert renderer.approve_action("nonexistent", "a1") is False
    assert renderer.deny_action("nonexistent", "a1") is False
    assert renderer.execute_action("nonexistent", "a1") is None


# =========================================
# EVENTS
# =========================================


def test_events_audit_trail(renderer):
    action = MCPAppAction(
        action_id="a1", tool_call="send_email", requires_approval=True
    )
    resp = MCPAppResponse(
        template_id="contact_card", data={"name": "Test"}, actions=[action]
    )
    rendered = renderer.render_app(resp)
    renderer.approve_action(rendered.id, "a1")
    renderer.execute_action(rendered.id, "a1")

    events = renderer.get_events()
    event_types = {e.event_type for e in events}
    assert "render" in event_types
    assert "action_approved" in event_types
    assert "action_executed" in event_types


def test_event_auto_id():
    e = MCPAppEvent(event_type="test", template_id="t1")
    assert e.event_id.startswith("evt_")
    assert e.timestamp != ""


# =========================================
# STATS
# =========================================


def test_stats(renderer):
    resp = MCPAppResponse(template_id="contact_card", data={"name": "Test"})
    renderer.render_app(resp)
    stats = renderer.get_stats()
    assert stats["total_templates"] >= 6
    assert stats["total_rendered"] == 1
    assert stats["total_events"] >= 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    r1 = get_apps_renderer()
    r2 = get_apps_renderer()
    assert r1 is r2
