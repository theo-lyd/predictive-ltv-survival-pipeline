# Release Policy & Versioning Strategy

## Overview

This document defines the release process, versioning scheme, and approval workflows for the predictive-ltv-survival-pipeline project.

**Key Principles**:
- **Semantic Versioning**: Version format `MAJOR.MINOR.PATCH` clearly signals breaking changes
- **Frequent Releases**: Aim for weekly or bi-weekly releases with meaningful features
- **Automated Changelogs**: Generated from commit messages (conventional commits)
- **Approval Gates**: Data pipeline changes require consensus before release

---

## Semantic Versioning

### Version Format

```
v{MAJOR}.{MINOR}.{PATCH}[-{PRERELEASE}][+{BUILD}]
```

**Components**:
- **MAJOR**: Breaking changes (e.g., metric rename, schema redesign)
- **MINOR**: New features, non-breaking (e.g., new KPI added)
- **PATCH**: Bug fixes, performance improvements (e.g., query optimization)
- **PRERELEASE**: Alpha/beta versions (e.g., `v2.0.0-alpha.1`, `v1.5.0-rc.1`)
- **BUILD**: Build metadata, rarely used (e.g., `v1.0.0+build.123`)

### Examples

| Version | Type | Reason |
|---------|------|--------|
| v0.1.0 | Initial | First deployable version |
| v0.1.1 | Patch | Bug fix in Phase 1 |
| v0.2.0 | Minor | Phase 2 complete (new features) |
| v1.0.0 | Major | Phase 5 complete (production ready) |
| v1.1.0 | Minor | Add discount efficiency metric |
| v1.1.1 | Patch | Fix NRR calculation edge case |
| v2.0.0 | Major | Redesign LTV computation (breaking) |
| v2.0.0-alpha.1 | Prerelease | Early draft of v2.0.0 |
| v2.0.0-rc.1 | Release Candidate | Near-final v2.0.0, awaiting approval |

### Incrementing Rules

**When to increment MAJOR** (breaking changes):
- ❌ Metric removed or renamed
- ❌ Model schema changed (columns dropped/type changed)
- ❌ API contract broken (if external consumers)
- ❌ Deployment steps changed (new database credentials needed)

**When to increment MINOR** (new features):
- ✅ New metric/KPI added
- ✅ New data source integrated
- ✅ New visualization created
- ✅ Performance improvement (backward compatible)

**When to increment PATCH** (bug fixes):
- ✅ Query result corrected
- ✅ Edge case handled
- ✅ Documentation fix
- ✅ Performance optimization

---

## Release Cadence & Process

### Recommended Schedule

**Standard Cadence**: Weekly releases (Tuesday morning)

```
Monday:    Code review cutoff (no new PRs after 5pm)
Tuesday:   Release trigger + testing (8am-12pm)
Wednesday: Stakeholder validation
Thursday:  Hold for urgent fixes
Friday:    Post-release stability monitoring
```

### Release Decision Committee

| Role | Approval Power | Triggers Release | Resolves Conflicts |
|------|----------------|------------------|-------------------|
| Data Engineer | ✅ Can approve | ✅ Can trigger | ❌ No |
| Analytics Lead | ✅ Can approve | ✅ Can trigger | ✅ Yes |
| Platform Owner | ✅ Can approve | ✅ Can trigger | ✅ Yes |

**Minimum requirement**: 2 of 3 approval for release to production

**Urgent hotfixes** (e.g., broken metric): 1 approval sufficient

---

## Release Workflow Steps

### Phase 1: Prepare Release Branch (Day Before Release)

```bash
# 1. Ensure master is latest
git checkout master
git pull origin master

# 2. Create release branch
git checkout -b release/v1.1.0

# 3. Update version in code
# Edit dbt_project.yml: version: 1.1.0
# Edit setup.py (if exists): version="1.1.0"

# 4. Create/review CHANGELOG entry
# Add to CHANGELOG.md:
# ## Version 1.1.0 - 2024-04-07
# ### Features
# - Add discount curve visualization (PR #123)
# - Integrate Unity Catalog lineage (PR #124)
# ### Fixes
# - Fix NRR rounding edge case (PR #122)

# 5. Commit release changes
git add dbt_project.yml setup.py CHANGELOG.md
git commit -m "release: prepare v1.1.0"

# 6. Push release branch to GitHub
git push origin release/v1.1.0

# 7. Create PR for review
# Title: "Release v1.1.0"
# Body: Link to CHANGELOG entry, highlight breaking changes (if any)
```

### Phase 2: Code Review (Release PR)

**Required Reviews** (2 of 3):
1. Data Engineer: "Does the CHANGELOG accurately reflect changes?"
2. Analytics Lead: "Are breaking changes clearly documented?"
3. Platform Owner: "Are deployment steps documented?"

**Comments to Address**:
- ✅ "Changelog entry is clear and complete"
- ✅ "No breaking changes identified"
- ✅ "Ready to release"

**Blocking Issues**:
- ❌ "CHANGELOG incomplete"
- ❌ "Breaking changes not mentioned"
- ❌ "Test failures in master"

### Phase 3: Merge & Tag (Release Day Morning)

```bash
# 1. Ensure release PR approved
# (review comments resolved)

# 2. Merge PR to master (squash commit)
# GitHub UI: "Squash and merge" button
# Commit message: "release: v1.1.0 - Add visualizations and fix NRR edge case"

# 3. Create annotated tag locally
git checkout master
git pull origin master
git tag -a v1.1.0 -m "Release v1.1.0: Add discount curve visualization, integrate Unity Catalog lineage"

# 4. Push tag (triggers release workflow automatically)
git push origin v1.1.0

# 5. GitHub Actions runs:
#    - build-artifacts: Creates wheel, sdist, SBOM
#    - create-release: Creates GitHub Release with changelog
#    - update-docs: Updates CHANGELOG with release link
#    - validate-release: Runs full test suite on tag
```

### Phase 4: Post-Release Monitoring (Day After Release)

**Tasks**:
1. ✅ Monitor Slack #data-pipeline for errors
2. ✅ Verify SLA metrics (data freshness, latency)
3. ✅ Check downstream consumers (dashboards loading correctly)
4. ✅ Review post-release test results (GitHub Actions artifacts)
5. ✅ Document any issues encountered

**If issues found**:
```bash
option A (Quick Fix - same version):
  - Fix bug in hotfix branch
  - Create PR against v1.1.0 tag
  - Merge, re-tag as v1.1.1 (patch bump)
  
option B (Full Rollback - new version):
  - Revert v1.1.0 to v1.0.0 (last known good)
  - Create PR documenting revert reason
  - Merge, tag as v1.0.1
  - Schedule root cause analysis
```

---

## Special Release Scenarios

### Scenario 1: Hotfix for Production Bug

**Urgency**: High (breaking metrics, data corruption)

**Process** (bypass standard cadence):
```
1. Assess severity: "Does this break SLAs or user queries?"
   - Yes = hotfix immediately
   - No = include in next weekly release

2. Create hotfix branch from master
   git checkout -b hotfix/metric-name

3. Fix issue, test locally
   make ci-local  # Verify all checks pass

4. Create PR: Title "HOTFIX: [issue description]"

5. Single-approval merge (skip waiting for 2nd reviewer)

6. Tag as v1.1.1 (patch bump from v1.1.0)

7. Notify stakeholders: Slack #data-alerts channel
```

### Scenario 2: Release Candidate (Pre-release)

**Urgency**: Medium (major feature, needs stakeholder review)

**Process**:
```
1. Create release candidate branch
   git checkout -b release/v2.0.0-rc.1

2. Bump version in code to v2.0.0-rc.1

3. Commit & tag
   git tag -a v2.0.0-rc.1 -m "Release Candidate: v2.0.0 redesign"
   git push origin v2.0.0-rc.1

4. GitHub creates draft release (not published)

5. Stakeholders test RC in staging environment

6. Once approved, create final release from RC
   git tag -a v2.0.0 -m "Release v2.0.0: LTV redesign"
   git push origin v2.0.0
```

### Scenario 3: Emergency Rollback

**Urgency**: Critical (data corrupted, dashboards broken)

**Process**:
```
1. Identify last known good version
   git describe --tags --abbrev=0 HEAD~1

2. Create rollback tag
   git tag -a v1.1.0-rollback -m "Rollback from v1.2.0 due to data issue"

3. Redeploy v1.1.0 infrastructure/code

4. Post-mortem meeting: why did qa miss this?

5. Update release policy if process Gap found
```

---

## Changelog Management

### Format (Conventional Commits style)

```markdown
## Version 1.1.0 - 2024-04-07

### ✨ Features
- Add discount curve visualization (PR #123) [@author]
- Integrate Unity Catalog lineage tracking (PR #124) [@author]

### 🐛 Fixes
- Fix NRR rounding edge case in churn calculation (PR #122) [@author]
- Handle null MRR values gracefully (PR #125) [@author]

### 📊 Performance
- Optimize survival curve query (10x faster) (PR #126) [@author]

### 🔒 Security
- Update vulnerable dependency lodash (PR #127) [@author]

### ⚠️ Breaking Changes
None

### 📝 Internal
- Refactor narrative generation for readability (PR #128)
- Add code complexity metrics to CI (PR #129)

### 🙏 Contributors
- @data-engineer-1 (3 PRs)
- @analytics-lead (2 PRs)
```

### Automated Generation

The release workflow automatically creates changelog from commit messages:
- Scans commits since last tag
- Groups by type (feat, fix, perf, security)
- Links to PRs and authors
- Detects breaking changes (commit body contains "BREAKING CHANGE:")

---

## Approval Checklist

**Release Decision Template**:

```
Release: v1.1.0

Dates:
- Code freeze: April 6 5pm
- Release date: April 7 9am
- Target deployment: April 7 2pm

Key Changes:
- [ ] Feature 1 (link to PR)
- [ ] Feature 2
- [ ] Bug fix 1

Breaking Changes?
- [ ] No breaking changes
- [ ] Has breaking changes (documented in CHANGELOG)

Tests:
- [ ] All CI checks passed
- [ ] Manual QA testing completed
- [ ] Downstream dashboards validated

Approvals:
- [ ] Data Engineer approved
- [ ] Analytics Lead approved
- [ ] Platform Owner approved (if deployment needed)

Readiness:
- [ ] CHANGELOG updated
- [ ] Version bumped in code
- [ ] Post-release runbook prepared

Sign-off: (@reviewer-name) Approved for release
```

---

## Version Constraint Policy

### Service Dependencies

| Package | Version | Reason |
|---------|---------|--------|
| dbt-core | >=1.7.0, <2.0.0 | Stability, mature feature set |
| Python | 3.10+ | Security, modern async support |
| Streamlit | >=1.20 | Production ready |
| Great Expectations | >=0.15 | Mature validation framework |
| Apache Airflow | >=2.6.0 | DAG serialization improvements |

### Update Policy

**Critical Security Updates**: Release same day
```
Example: dbt-core 1.7.5 → 1.7.6 (CVE patch)
Process: Patch bump (1.1.0 → 1.1.1)
```

**Minor/Feature Updates**: Include in next weekly
```
Example: Streamlit 1.20 → 1.21 (new feature)
Process: Test in staging, include in MINOR bump
```

**Major Version Updates**: Quarterly review
```
Example: dbt-core 1.8 → 2.0 (breaking)
Process: Dedicated PR, milestone planning, separate major release
```

---

## Release Metrics & Reporting

### Track These Post-Release

| Metric | Target | Action if Missed |
|--------|--------|------------------|
| Time to 1st bug report | <24h | OK (fast detection) |
| Time to rollback ready | <1h | Automate more steps |
| Test coverage maintained | ≥80% | Improve test coverage |
| SLA compliance | 100% | Investigate root cause |
| Documentation completeness | 100% | Add/improve docs |

### Monthly Release Report

Template:
```
April 2024 Release Summary:

Releases: 4 (v1.0.0, v1.0.1, v1.1.0, v1.1.1)
Time between releases: 7 days average
Total PRs merged: 18
Total commits: 52
Test coverage: 82% (up from 79%)
Incidents: 1 (hotfix for NRR rounding)
Rollbacks: 0

Highlights:
- Integrated Unity Catalog lineage
- 10x performance improvement on survival curves
- Zero SLA breaches

Next quarter goals:
- Reduce release cycle to 5 days (from 7)
- Improve test coverage to 85%
- Automate more approval workflows
```

---

## Timeline for Implementation

| Phase | Actions | Status |
|-------|---------|--------|
| **Phase 6 B2** | Document release policy (this file) | ✅ Now |
| **Phase 6 B2** | Configure branch protection (BRANCH_PROTECTION_RULES.md) | ✅ Now |
| **Phase 6 B3** | Define data ownership (DATA_OWNERSHIP.md) | ⏳ Next |
| **Phase 7** | Automate approval workflow via GitHub Actions | 📋 Future |
| **Phase 8** | Auto-increment version via conventional commits | 📋 Future |

---

## References

- [Semantic Versioning](https://semver.org/) - Version numbering spec
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) - GitHub release features
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format standard
