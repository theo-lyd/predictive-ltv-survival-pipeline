# Access Control Policy

## Overview

Phase 7 Batch 1 converts the documented RBAC model into enforced UI behavior for the Streamlit application.

The goal is not to replace enterprise identity providers. The goal is to make access behavior explicit, centralized, and testable so the app does not expose sensitive operational views to the wrong role.

---

## Role-to-Capability Matrix

| Role | executive_dashboard | narrative_review | sla_operations | public_views |
|------|---------------------|------------------|----------------|--------------|
| Executive | ✅ | ✅ | ✅ | ✅ |
| RevOps | ✅ | ✅ | ✅ | ✅ |
| Finance | ❌ | ✅ | ❌ | ✅ |
| Sales Leadership | ❌ | ❌ | ❌ | ✅ |

### Interpretation

- `executive_dashboard` protects the main executive flight deck.
- `narrative_review` protects daily AI narrative review and governance content.
- `sla_operations` protects operational SLA monitoring and alert-related workflows.
- `public_views` represents read-only reference content that is safe for all roles.

---

## Enforcement Rules

1. Page access is checked at render time using a shared authorization helper.
2. Unauthorized users see a clear denial message instead of a broken page.
3. Allowed and denied views are centralized so the app does not drift over time.
4. Page gating is applied consistently to the executive dashboard, narrative surface, and SLA operations page.
5. The role selector in the sidebar is the single source of truth for the current view role in local development.

---

## Protected Surfaces

### Executive Flight Deck

- Capability: `executive_dashboard`
- Intended audience: Executive, RevOps
- Behavior: full dashboard view and strategic questions panel

### AI Daily Narrative

- Capability: `narrative_review`
- Intended audience: Executive, RevOps, Finance
- Behavior: narrative review surface with provenance and contract validation

### SLA Compliance

- Capability: `sla_operations`
- Intended audience: Executive, RevOps
- Behavior: operational monitoring, alert payloads, and historical SLA charts

### Public Reference Views

- Capability: `public_views`
- Intended audience: all roles
- Behavior: glossary and other reference-only content

---

## Fallback Behavior

If the role cannot be determined, the app defaults to the Executive role for local development so the UI remains usable.

If a role is present but does not satisfy a page capability:

- the page stops rendering,
- the user sees a denial message explaining the required capability,
- the message includes the roles that are allowed,
- no stack trace is shown to the user.

---

## Testing Expectations

The Batch 1 test suite should prove that:

- allowed roles pass authorization for their pages,
- restricted roles are denied for protected pages,
- denial messages name the page and capability,
- the allowed role list is stable and easy to review.

---

## Operational Notes

- This policy is deliberately UI-level and does not claim backend SSO enforcement.
- External authentication can be layered on later without changing the capability names.
- The authorization helper should remain the only place where role-to-capability mapping is defined.
