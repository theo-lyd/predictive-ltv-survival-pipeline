# GitHub Actions CI/CD Workflow Documentation

## Overview

This document describes the GitHub Actions workflows that enforce quality gates, run automated tests, and manage releases for the predictive-ltv-survival-pipeline project.

**Workflows:**
1. **ci-enhanced.yml** - Continuous Integration (PR validation, testing, quality gates)
2. **release.yml** - Release management (versioning, publishing, documentation)

---

## CI Enhanced Workflow (`ci-enhanced.yml`)

### Purpose
Automatically validate code quality, test coverage, and data quality on every pull request and push to protected branches.

### Triggers
- Pull requests to `master` or `develop` branches
- Pushes to `master` or `develop` branches
- Git tags matching `v*` (e.g., `v1.0.0`)

### Jobs & Quality Gates

#### 1. **Code Quality & Testing** (`quality`)
Runs Python linting, formatting checks, security scanning, and comprehensive test suite.

**Steps:**
- Checkout code with full git history (needed for caching/diff analysis)
- Set up Python 3.10
- Cache pip dependencies and dbt artifacts
- Install dependencies including dev/security tools
- **pylint**: Static analysis, catches code smells (warnings allowed)
- **flake8**: PEP 8 compliance (warnings allowed)
- **black**: Code formatting check (blocking)
- **yamllint**: YAML configuration validation (warnings allowed)
- **bandit**: Security vulnerability scanning (warnings allowed)
- **pip-audit**: Check for known vulnerable dependencies (warnings allowed)
- **pytest**: Run full test suite with coverage
  - Minimum coverage per-file: 80%
  - Report uploaded to Codecov
  - Coverage HTML report saved as artifact
- Upload test results and coverage reports

**Status**: ✅ Blocking (must pass to merge)

**Why each tool:**
- **pylint** (vs. Ruff): Catches semantic issues beyond style; industry standard for Python
- **flake8**: Enforces PEP 8 standard; complements pylint for style consistency
- **black**: Opinionated formatter eliminates formatting debates; consistent code style
- **bandit**: Security-focused; catches common vulnerabilities (SQL injection, hardcoded secrets)
- **Coverage**: 80% threshold reflects industry best practice for data pipelines

---

#### 2. **dbt Lint & Parse** (`dbt-lint`)
Validates dbt model syntax and schema without running transformations.

**Steps:**
- Checkout code
- Set up Python and cache dependencies
- **dbt parse**: Validates YAML syntax, schema references, macro definitions
  - Uses `state:modified` to check only changed models (slim CI)
  - Compares against previous state stored in `target/` directory
- **dbt compile**: Generates SQL for all models (validation only, no execution)

**Status**: ✅ Blocking (must pass before tests run)

**Why dbt state:modified:**
- **Slim CI** reduces CI time from ~5min to <1min for typical model changes
- Only validates models that changed + their descendants
- Available in dbt Cloud/Core v1.5+

---

#### 3. **dbt Tests (Slim CI)** (`dbt-tests`)
Runs dbt assertions (uniqueness, not_null, referential integrity) using slim CI on PRs.

**Logic:**
```bash
if on master:
  dbt test --select * (full suite)
else:
  dbt test --select state:modified (slim mode - only changed models)
```

**Status**: ✅ Blocking (must pass to merge)

**Why full suite on master:**
- Catches breaking changes to non-modified models
- Monthly/quarterly full runs ensure data pipeline integrity
- On PRs: slim tests catch problems instantly while keeping fast feedback

---

#### 4. **Great Expectations Quality Checks** (`data-quality`)
Validates data assumptions before models reach downstream consumers.

**Steps:**
- Run `silver_integrity_checkpoint` (validates column nullability, type consistency, value ranges)
- Generate HTML validation report
- Upload report as artifact for review

**Status**: ⚠️ Informational (warnings logged, doesn't block merge)

**Why non-blocking:**
- Requires live data connection (may be unavailable in CI)
- Failures usually indicate data issues, not code issues
- Manual review needed to decide if data schema changed intentionally

---

#### 5. **Code Complexity Metrics** (`code-metrics`)
Tracks code maintainability trends over time.

**Tools:**
- **radon**: Cyclomatic complexity (how many code paths?)
- **radon**: Maintainability index (0-100, higher = more maintainable)

**Reports:**
- `complexity-report.json`: Functions with CC > 10 flagged
- `maintainability-report.json`: Module-level MI trends

**Status**: ⓘ Informational (tracked, not enforced)

---

#### 6. **CI Status Check** (`ci-status`)
Summary job that gates merge based on critical checks.

**Blocks merge if:** quality, dbt-lint, or dbt-tests failed

**Allows merge if:** only data-quality or code-metrics warnings

---

### Environment Variables
```yaml
PYTHON_VERSION: "3.10"
PIP_CACHE_DIR: ~/.cache/pip
DBT_PROFILES_DIR: ${{ github.workspace }}
```

### Artifact Retention
- Test results: 30 days (default)
- Coverage reports: 30 days
- GE reports: 30 days
- Code metrics: 30 days

### Caching Strategy

**Cache Keys:**
- **pip**: Hash of `requirements*.txt` (invalidates when dependencies change)
- **dbt**: Git SHA (unique per commit)
- **Fallback**: Previous branch cache used if exact match not found

**Benefit:** ~40-50% faster CI runs after first execution

---

## Release Workflow (`release.yml`)

### Purpose
Automatically create releases, publish artifacts, and update documentation when a version tag is pushed.

### Triggers
- Push of git tag matching `v*` (e.g., `v1.2.3`)
- Pushes to `master` branch

### Jobs & Release Pipeline

#### 1. **Parse Version** (`parse-version`)
Extracts semantic version components from git tag.

**Output:**
- `version`: Full version (e.g., "1.2.3")
- `major`, `minor`, `patch`: Components (1, 2, 3)

**Example:** Tag `v1.2.3` → `version=1.2.3`, `major=1`, `minor=2`, `patch=3`

---

#### 2. **Create GitHub Release** (`create-release`)
Creates GitHub release with auto-generated changelog.

**Steps:**
- Generate changelog from commits since last tag
- Create GitHub release with:
  - Release name: "Release 1.2.3"
  - Release notes from commit messages
  - Draft toggle: `false` (immediate public release)
  - Prerelease toggle: `false` (marks as stable)

**Release Notes Format:**
```markdown
## Changes in 1.2.3

- abc1234: Add provenance badge to executive pages
- def5678: Implement SLA monitoring
- ...
```

---

#### 3. **Build Artifacts** (`build-artifacts`)
Creates distributable packages and bill of materials.

**Steps:**
- Build Python wheel and sdist packages
- Generate SBOM (Software Bill of Materials) in CycloneDX format
- Upload to GitHub artifacts

**SBOM Purpose:**
- Tracks all dependencies and versions shipped with release
- Required for compliance (SOC 2, FedRAMP, etc.)
- Enables security audit trail

---

#### 4. **Update Documentation** (`update-docs`)
Updates CHANGELOG and version references.

**Steps:**
- Add new entry to CHANGELOG.md
  - Format: "## Version 1.2.3 - 2024-04-07"
  - Links to GitHub release
- Update version in `dbt_project.yml`
- Commit and push changes back to master

---

#### 5. **Validate Release** (`validate-release`)
Runs validation tests on the released version to ensure production readiness.

**Steps:**
- Checkout the exact version tag
- Install dependencies
- Run full test suite
- Verify dbt parse/compile

**Purpose:** Catch any tag-specific issues before release goes live

---

## Local CI Execution

Run complete CI pipeline locally before pushing:

```bash
# Run all checks
make ci-local

# Or run individual checks
make lint                  # Code formatting
make test                  # Unit tests + coverage
make dbt-parse            # dbt syntax validation
make dbt-test             # dbt model tests
make ge-validate          # Great Expectations
make sec-audit           # Security scanning
```

---

## Common Failure Scenarios & Recovery

### Scenario 1: Black Formatting Fails
```bash
# Fix: Auto-format code
make format
git add .
git commit -m "style: auto-format with black"
git push
```

### Scenario 2: Coverage Below 80%
```bash
# Review coverage report
open htmlcov/index.html

# Write tests
vim tests/test_new_function.py

# Push & retry
git push
```

### Scenario 3: dbt Test Fails
```bash
# Review failing test
dbt test --select failing_test_name --debug

# Fix model SQL
vim models/marts/my_model.sql

# Re-run
git push
```

### Scenario 4: GE Validation Fails
```bash
# This is informational; indicates data schema change
# Review artifact: ge-validation-report in GitHub Actions

# If expected, no action needed
# If unexpected, investigate data source
```

---

## Status Badges

Add to README.md to display CI status:

```markdown
[![CI/CD Pipeline](https://github.com/theo-lyd/predictive-ltv-survival-pipeline/actions/workflows/ci-enhanced.yml/badge.svg)](https://github.com/theo-lyd/predictive-ltv-survival-pipeline/actions)
```

---

## Troubleshooting

### Pipeline times out (>10 minutes)
- Check dbt-tests job for infinite loops in SQL tests
- Verify no slow data queries in GE checkpoint
- Review GitHub Actions runner logs for resources

### Artifacts not uploading
- Check write permissions on GitHub repo
- Verify artifact path exists (no trailing slashes)
- Ensure artifact size < 100MB (GitHub limit)

### Cache not working
- Cache keys are immutable once set; different key needed for new cache
- Check if `fetch-depth: 0` is set (needed for full git history)

---

## Performance Tips

| Task | Typical Time | Bottleneck |
|------|------|----------|
| Python linting | 10-15s | Number of files |
| dbt parse (full) | 20-30s | Model count |
| dbt parse (slim) | 5-10s | Changed models |
| dbt tests (full) | 2-5min | Test query complexity |
| dbt tests (slim) | 30-60s | Changed model tests |
| pytest unit tests | 1-2min | Test count |
| Coverage report | 30s | File count |
| **Total (PR)** | **3-5min** | Slim CI enabled |
| **Total (master)** | **8-12min** | Full validation |

---

## Roadmap

- [ ] Container image building & pushing to ECR
- [ ] dbt Cloud integration for job orchestration
- [ ] Slack notifications for build status
- [ ] Performance regression detection
- [ ] Automated rollback on production failures
