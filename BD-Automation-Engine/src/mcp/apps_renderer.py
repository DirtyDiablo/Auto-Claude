"""Phase 45A — MCP Apps Renderer.

Renders interactive UI elements returned by MCP servers, based on the
MCP Apps Extension (SEP-1865) specification. Templates are pre-declared
and verified before rendering; actions require host approval.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================
# ENUMS & DATA CLASSES
# =========================================

class RenderStatus(str, Enum):
    RENDERED = "rendered"
    TEMPLATE_NOT_FOUND = "template_not_found"
    PERMISSION_DENIED = "permission_denied"
    ERROR = "error"


class ActionStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    DENIED = "denied"
    EXECUTED = "executed"


@dataclass
class MCPAppTemplate:
    template_id: str = ""
    name: str = ""
    html: str = ""
    permissions: List[str] = field(default_factory=list)
    description: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class MCPAppAction:
    action_id: str = ""
    tool_call: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = True
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


@dataclass
class MCPAppEvent:
    event_id: str = ""
    event_type: str = ""  # render | action | error | interaction
    template_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.event_id:
            raw = f"{self.event_type}:{self.template_id}:{datetime.utcnow().isoformat()}"
            self.event_id = f"evt_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class MCPAppResponse:
    template_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    actions: List[MCPAppAction] = field(default_factory=list)
    title: str = ""
    server_id: str = ""


@dataclass
class RenderedApp:
    id: str = ""
    template_id: str = ""
    status: str = "rendered"
    html: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    actions: List[MCPAppAction] = field(default_factory=list)
    sandbox_config: Dict[str, Any] = field(default_factory=dict)
    events: List[MCPAppEvent] = field(default_factory=list)
    rendered_at: str = ""

    def __post_init__(self):
        if not self.id:
            raw = f"{self.template_id}:{datetime.utcnow().isoformat()}"
            self.id = f"app_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
        if not self.rendered_at:
            self.rendered_at = datetime.utcnow().isoformat()


# =========================================
# BUILT-IN TEMPLATES
# =========================================

_BUILTIN_TEMPLATES: List[MCPAppTemplate] = [
    MCPAppTemplate(
        template_id="contact_card",
        name="Contact Card",
        html='<div class="contact-card"><h2>{{name}}</h2><p>{{title}} at {{company}}</p><p>Tier: {{tier}}</p><div class="actions"><button data-action="email">Email</button><button data-action="call">Call</button></div></div>',
        permissions=["display", "action:email", "action:call"],
        description="Interactive contact profile with call/email actions",
    ),
    MCPAppTemplate(
        template_id="program_overview",
        name="Program Overview",
        html='<div class="program-overview"><h2>{{program_name}}</h2><p>Prime: {{prime}}</p><p>Value: ${{value}}M</p><div class="chart" data-type="bar" data-values="{{metrics}}"></div></div>',
        permissions=["display", "chart"],
        description="Program intelligence summary with charts",
    ),
    MCPAppTemplate(
        template_id="pipeline_kanban",
        name="Pipeline Kanban",
        html='<div class="kanban"><div class="col" data-stage="prospect">{{prospects}}</div><div class="col" data-stage="qualified">{{qualified}}</div><div class="col" data-stage="proposal">{{proposals}}</div><div class="col" data-stage="won">{{won}}</div></div>',
        permissions=["display", "drag_drop", "action:move_card"],
        description="Drag-and-drop opportunity pipeline",
    ),
    MCPAppTemplate(
        template_id="geographic_map",
        name="Geographic Map",
        html='<div class="map-widget"><div id="kepler-map" data-center="{{center}}" data-zoom="{{zoom}}" data-markers="{{markers}}"></div></div>',
        permissions=["display", "geolocation"],
        description="Embedded map widget for geographic intelligence",
    ),
    MCPAppTemplate(
        template_id="org_chart_mini",
        name="Mini Org Chart",
        html='<div class="org-chart"><div class="node root">{{root}}</div><div class="children">{{children}}</div></div>',
        permissions=["display", "expand_collapse"],
        description="Collapsible org chart for a program",
    ),
    MCPAppTemplate(
        template_id="call_briefing",
        name="Call Briefing",
        html='<div class="call-brief"><h2>Pre-Call Brief: {{contact_name}}</h2><section class="intel">{{intelligence}}</section><section class="talking-points"><ul>{{talking_points}}</ul></section><section class="questions"><ul>{{questions}}</ul></section></div>',
        permissions=["display"],
        description="Pre-call intelligence briefing with key talking points",
    ),
]


# =========================================
# MCP APPS RENDERER
# =========================================

class MCPAppsRenderer:
    """Renders interactive UI elements from MCP servers."""

    def __init__(self, seed_templates: bool = True) -> None:
        self._templates: Dict[str, MCPAppTemplate] = {}
        self._rendered: List[RenderedApp] = []
        self._events: List[MCPAppEvent] = []
        self._action_log: List[Dict[str, Any]] = []

        if seed_templates:
            for t in _BUILTIN_TEMPLATES:
                self._templates[t.template_id] = t

    # --------------------------------------------------
    # TEMPLATES
    # --------------------------------------------------

    def register_template(self, template_id: str, name: str, html: str,
                          permissions: Optional[List[str]] = None,
                          description: str = "") -> MCPAppTemplate:
        """Pre-declare an HTML template for MCP Apps."""
        template = MCPAppTemplate(
            template_id=template_id,
            name=name,
            html=html,
            permissions=permissions or ["display"],
            description=description,
        )
        self._templates[template_id] = template
        return template

    def get_template(self, template_id: str) -> Optional[MCPAppTemplate]:
        return self._templates.get(template_id)

    def list_templates(self) -> List[MCPAppTemplate]:
        return list(self._templates.values())

    # --------------------------------------------------
    # RENDERING
    # --------------------------------------------------

    def render_app(self, app_response: MCPAppResponse) -> RenderedApp:
        """Render an MCP App response into a sandboxed UI element."""
        template = self._templates.get(app_response.template_id)

        if not template:
            event = MCPAppEvent(
                event_type="error",
                template_id=app_response.template_id,
                details={"error": "Template not found"},
            )
            self._events.append(event)
            return RenderedApp(
                template_id=app_response.template_id,
                status=RenderStatus.TEMPLATE_NOT_FOUND.value,
                events=[event],
            )

        # Apply data to template (simple {{key}} replacement)
        rendered_html = template.html
        for key, value in app_response.data.items():
            placeholder = "{{" + key + "}}"
            rendered_html = rendered_html.replace(placeholder, str(value))

        # Build sandbox config
        sandbox_config = self._build_sandbox(template)

        # Process actions — mark those needing approval
        processed_actions: List[MCPAppAction] = []
        for action in app_response.actions:
            if action.requires_approval:
                action.status = ActionStatus.PENDING.value
            else:
                action.status = ActionStatus.APPROVED.value
            processed_actions.append(action)

        # Log render event
        render_event = MCPAppEvent(
            event_type="render",
            template_id=app_response.template_id,
            details={
                "data_keys": list(app_response.data.keys()),
                "action_count": len(processed_actions),
                "server_id": app_response.server_id,
            },
        )
        self._events.append(render_event)

        rendered = RenderedApp(
            template_id=app_response.template_id,
            status=RenderStatus.RENDERED.value,
            html=rendered_html,
            data=app_response.data,
            actions=processed_actions,
            sandbox_config=sandbox_config,
            events=[render_event],
        )
        self._rendered.append(rendered)
        return rendered

    def _build_sandbox(self, template: MCPAppTemplate) -> Dict[str, Any]:
        """Build iframe sandbox configuration from template permissions."""
        # Default: very restrictive
        sandbox = {
            "allow_scripts": False,
            "allow_forms": False,
            "allow_popups": False,
            "allow_modals": False,
            "allow_same_origin": False,
            "csp": "default-src 'none'; style-src 'unsafe-inline'; img-src data:",
            "permissions": template.permissions,
        }

        # Relax based on permissions
        if "action:email" in template.permissions or "action:call" in template.permissions:
            sandbox["allow_scripts"] = True
        if "drag_drop" in template.permissions:
            sandbox["allow_scripts"] = True
        if "chart" in template.permissions:
            sandbox["allow_scripts"] = True
            sandbox["csp"] = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:"
        if "geolocation" in template.permissions:
            sandbox["allow_scripts"] = True

        return sandbox

    # --------------------------------------------------
    # ACTIONS
    # --------------------------------------------------

    def approve_action(self, app_id: str, action_id: str) -> bool:
        """Approve a pending action in a rendered app."""
        for rendered in self._rendered:
            if rendered.id == app_id:
                for action in rendered.actions:
                    if action.action_id == action_id:
                        action.status = ActionStatus.APPROVED.value
                        self._log_action_event(rendered.template_id, action, "approved")
                        return True
        return False

    def deny_action(self, app_id: str, action_id: str) -> bool:
        """Deny a pending action in a rendered app."""
        for rendered in self._rendered:
            if rendered.id == app_id:
                for action in rendered.actions:
                    if action.action_id == action_id:
                        action.status = ActionStatus.DENIED.value
                        self._log_action_event(rendered.template_id, action, "denied")
                        return True
        return False

    def execute_action(self, app_id: str, action_id: str) -> Optional[Dict[str, Any]]:
        """Execute an approved action. Returns result or None if not approved."""
        for rendered in self._rendered:
            if rendered.id == app_id:
                for action in rendered.actions:
                    if action.action_id == action_id:
                        if action.status != ActionStatus.APPROVED.value:
                            return None
                        # Simulate execution
                        result = {
                            "tool_call": action.tool_call,
                            "parameters": action.parameters,
                            "status": "executed",
                            "executed_at": datetime.utcnow().isoformat(),
                        }
                        action.status = ActionStatus.EXECUTED.value
                        action.result = result
                        self._log_action_event(rendered.template_id, action, "executed")
                        return result
        return None

    def _log_action_event(self, template_id: str, action: MCPAppAction, event_type: str) -> None:
        event = MCPAppEvent(
            event_type=f"action_{event_type}",
            template_id=template_id,
            details={"action_id": action.action_id, "tool_call": action.tool_call},
        )
        self._events.append(event)
        self._action_log.append({
            "action_id": action.action_id,
            "event": event_type,
            "timestamp": event.timestamp,
        })

    # --------------------------------------------------
    # QUERIES
    # --------------------------------------------------

    def get_rendered(self, app_id: str) -> Optional[RenderedApp]:
        for r in self._rendered:
            if r.id == app_id:
                return r
        return None

    def get_events(self, template_id: str = "") -> List[MCPAppEvent]:
        if template_id:
            return [e for e in self._events if e.template_id == template_id]
        return list(self._events)

    def get_stats(self) -> Dict[str, Any]:
        status_counts: Dict[str, int] = {}
        for r in self._rendered:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

        return {
            "total_templates": len(self._templates),
            "total_rendered": len(self._rendered),
            "total_events": len(self._events),
            "total_actions": len(self._action_log),
            "by_status": status_counts,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[MCPAppsRenderer] = None


def get_apps_renderer() -> MCPAppsRenderer:
    global _instance
    if _instance is None:
        _instance = MCPAppsRenderer()
    return _instance
