"""Centralized role and page authorization helpers for Streamlit pages."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_ROLE = "Executive"

ROLE_CAPABILITIES: dict[str, set[str]] = {
    "Executive": {"executive_dashboard", "narrative_review", "sla_operations", "public_views"},
    "RevOps": {"executive_dashboard", "narrative_review", "sla_operations", "public_views"},
    "Finance": {"narrative_review", "public_views"},
    "Sales Leadership": {"public_views"},
}


@dataclass(frozen=True)
class ProtectedView:
    """Metadata describing a page or action that requires authorization."""

    label: str
    capability: str | None
    description: str


PROTECTED_VIEWS: tuple[ProtectedView, ...] = (
    ProtectedView(
        label="Executive Flight Deck",
        capability="executive_dashboard",
        description="Primary executive KPI dashboard and what-if simulation surface",
    ),
    ProtectedView(
        label="AI Daily Narrative",
        capability="narrative_review",
        description="Narrative review and governance surface for daily AI-generated summaries",
    ),
    ProtectedView(
        label="SLA Compliance",
        capability="sla_operations",
        description="Operational SLA monitoring, alerts, and compliance review",
    ),
    ProtectedView(
        label="Operations Status",
        capability="sla_operations",
        description="Run health, history freshness, and recent operational snapshot",
    ),
    ProtectedView(
        label="KPI Glossary",
        capability="public_views",
        description="Reference help for KPI definitions and formulas",
    ),
)


def normalize_role(role: str | None) -> str:
    """Return a known role, defaulting to the executive baseline."""

    if role in ROLE_CAPABILITIES:
        return role
    return DEFAULT_ROLE


def get_allowed_capabilities(role: str | None) -> set[str]:
    """Return the capability set for a role."""

    return set(ROLE_CAPABILITIES.get(normalize_role(role), ROLE_CAPABILITIES[DEFAULT_ROLE]))


def role_can_access(role: str | None, capability: str | None) -> bool:
    """Check whether a role can access the requested capability."""

    if capability is None:
        return True
    return capability in get_allowed_capabilities(role)


def get_visible_views(role: str | None) -> list[ProtectedView]:
    """Return the views a role is allowed to access."""

    return [view for view in PROTECTED_VIEWS if role_can_access(role, view.capability)]


def get_locked_views(role: str | None) -> list[ProtectedView]:
    """Return the views a role cannot access."""

    return [view for view in PROTECTED_VIEWS if not role_can_access(role, view.capability)]


def build_access_denied_message(role: str | None, view_label: str, capability: str | None) -> str:
    """Build the denial message shown to unauthorized users."""

    normalized_role = normalize_role(role)
    if capability is None:
        return f"{view_label} is available to all roles."

    allowed_roles = [
        name for name, capabilities in ROLE_CAPABILITIES.items() if capability in capabilities
    ]
    allowed_text = ", ".join(allowed_roles)
    return (
        f"Access denied for role '{normalized_role}'. "
        f"{view_label} requires capability '{capability}'. "
        f"Allowed roles: {allowed_text}. Contact the repository owner if this seems incorrect."
    )
