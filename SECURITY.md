# Security Policy

## Supported Versions

This repository currently supports the `master` branch for security fixes.

## Reporting a Vulnerability

1. Do not open public issues for suspected vulnerabilities.
2. Report privately to the repository owner with:
- affected component,
- impact summary,
- minimal reproduction steps,
- suggested remediation if available.
3. Expect acknowledgment within 3 business days.

## Response Goals

- Triage start: within 3 business days.
- Initial mitigation plan: within 7 business days.
- Target patch window for high severity issues: 14 business days.

## Security Controls in Repository

- CI pipeline includes static analysis and dependency vulnerability checks.
- Scheduled monitoring produces integrity metadata for generated SLA artifacts.
- Access to privileged Streamlit views is claim-based and deny-by-default.
