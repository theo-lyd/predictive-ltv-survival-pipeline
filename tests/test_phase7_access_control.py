from __future__ import annotations

from streamlit_app.core.auth import build_access_denied_message, get_visible_views, role_can_access


def test_executive_can_access_sensitive_views():
    assert role_can_access("Executive", "executive_dashboard") is True
    assert role_can_access("Executive", "narrative_review") is True
    assert role_can_access("Executive", "sla_operations") is True


def test_sales_leadership_is_restricted_from_ops_views():
    assert role_can_access("Sales Leadership", "executive_dashboard") is False
    assert role_can_access("Sales Leadership", "narrative_review") is False
    assert role_can_access("Sales Leadership", "sla_operations") is False


def test_visible_views_match_role_permissions():
    visible_labels = {view.label for view in get_visible_views("Finance")}
    assert "AI Daily Narrative" in visible_labels
    assert "SLA Compliance" not in visible_labels


def test_denial_message_is_actionable():
    message = build_access_denied_message("Sales Leadership", "SLA Compliance", "sla_operations")
    assert "Access denied" in message
    assert "SLA Compliance" in message
    assert "sla_operations" in message
    assert "Executive" in message
