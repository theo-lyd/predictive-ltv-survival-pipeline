# Branch Protection Required Checks

This document defines the required GitHub branch protection checks for production-grade governance.

## Protected Branch

- `master`

## Required Status Checks

Enable "Require status checks to pass before merging" and require these checks:

1. `CI Status` from [ci-enhanced workflow](../.github/workflows/ci-enhanced.yml)
2. Optionally require `SLA Compliance Monitor` for release windows with strict operational readiness policies

`CI Status` already aggregates required jobs, including:
- `Code Quality & Testing`
- `Dependency Lock Check`
- `dbt Lint & Parse`
- `dbt Tests (Slim CI)`
- `Great Expectations Quality Checks`
- `Phase 7 Latency SLOs`

## Required Reviewers

Enable:
- `Require a pull request before merging`
- `Require approvals`
- `Require review from Code Owners`

Code ownership source:
- [CODEOWNERS](../.github/CODEOWNERS)

## Recommended Additional Settings

1. Require branches to be up to date before merging.
2. Dismiss stale approvals when new commits are pushed.
3. Restrict who can push directly to `master`.
4. Enforce linear history.
5. Do not allow bypass for administrators unless incident policy explicitly requires it.

## Notes

Branch protection is configured in GitHub repository settings and cannot be fully enforced from source files alone. This document is the required policy baseline for repository administrators.
