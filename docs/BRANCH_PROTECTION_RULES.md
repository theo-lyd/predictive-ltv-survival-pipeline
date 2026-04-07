# Branch Protection Rules & Approval Gates

## Overview

This document specifies the GitHub branch protection rules that enforce code quality and governance on the `master` branch. These rules ensure all production code changes go through automated quality gates and human review.

---

## Master Branch Protection Configuration

### 1. Require a Pull Request Before Merging

**Setting**: ✅ Enabled

**Configuration**:
```
Require pull request reviews before merging:
  - Number of required approvals: 1
  - Dismiss stale pull request approvals when new commits are pushed: ✅
  - Require review from code owners: (future: add CODEOWNERS file)
  - Allow specified actors to bypass required pull requests: (none)
```

**Rationale**: Every code change must:
- Go through PR review process (transparency)
- Trigger full CI validation (quality gate)
- Allow discussion and feedback (collaboration)

**Impact on Developers**:
- No direct pushes to master (use feature branches → PR → merge)
- All PRs require 1 approval before merging
- Approvals dismissed if new commits pushed (ensures latest code reviewed)

---

### 2. Require Status Checks to Pass Before Merging

**Setting**: ✅ Enabled

**Required Status Checks**:

| Check Name | Type | Purpose | Blocking |
|-----------|------|---------|----------|
| quality | CI | Code linting, tests, coverage | ✅ Yes |
| dbt-lint | CI | dbt syntax validation | ✅ Yes |
| dbt-tests | CI | dbt model assertions | ✅ Yes |
| data-quality | CI | Great Expectations validation | ⚠️ Informational |
| code-metrics | CI | Complexity tracking | ⚠️ Informational |
| ci-status | CI | Summary gate | ✅ Yes |

**Configuration**:
```
Require status checks to pass before merging: ✅
Require branches to be up to date before merging: ✅
Require code reviews before merging: ✅
Restrict who can push to matching branches: (future)
```

**Rationale**:
- **Blocking checks**: Catch breaking changes, test failures, security issues before merge
- **Informational checks**: Tracked but don't block (reduce friction while maintaining observability)
- **Up-to-date requirement**: Ensures status checks ran against current master

**Example PR Flow**:
```
1. Create PR from feature branch
   ↓
2. CI pipeline runs (quality → dbt-lint → dbt-tests parallel)
   ↓
3. All checks pass (6 jobs green) or PR blocked with error details
   ↓
4. If passing: Request review, wait for approval
   ↓
5. With approval + checks passing: "Squash and merge" button enabled
   ↓
6. Merge to master (triggering potential release workflow if tagged)
```

---

### 3. Require Code Reviews Before Merging

**Setting**: ✅ Enabled

**Configuration**:
```
Require pull request reviews before merging:
  - Number of required approvals: 1
  - Dismiss stale pull request approvals when new commits are pushed: ✅
  - Require review from code owners: (optional, future with CODEOWNERS)
```

**Who Can Approve**:
- For now: Any maintainer with write access
- Future: Specific code owners per file/area (via `.github/CODEOWNERS`)

**Review Guidelines**:
- ✅ Approve if: All CI checks pass, code quality acceptable, no breaking changes
- ❌ Request changes if: Failing tests, security issues, unclear logic
- ❓ Comment if: Questions, suggestions, or minor style notes

---

### 4. Require Branches to Be Up to Date Before Merging

**Setting**: ✅ Enabled

**Behavior**:
- PR requires latest master code
- If master updated after PR creation → PR mark "out of date"
- Developer must rebase/merge before merge allowed

**Rationale**: 
- Ensures all checks ran against current master
- Prevents subtle conflicts going unnoticed
- Guarantees latest code quality baseline

---

### 5. Require Code Owners Review (Future)

**Current Status**: ⏸ Not enabled (no CODEOWNERS file yet)

**When to Enable**: Post-Phase 6 once team structure is formalized

**Example `.github/CODEOWNERS`**:
```
# Data layer
models/**/* @data-team
dbt_project.yml @data-team
great_expectations/** @data-team

# Streamlit app
streamlit_app/** @frontend-team

# Airflow orchestration  
airflow/** @platform-team

# GitHub config
.github/workflows/** @devops-team
```

---

## Settings Applied via GitHub UI

### Step 1: Navigate to Repository Settings
```
https://github.com/theo-lyd/predictive-ltv-survival-pipeline/settings/branches
```

### Step 2: Create/Edit Rule for `master`

1. Click **"Add rule"** button
2. Branch name pattern: `master`
3. Configure checkboxes:

```
✅ Require a pull request before merging
   └─ Require approvals: [1]
   └─ ✅ Dismiss stale pull request approvals
   └─ ☐ Require review from code owners (future)

✅ Require status checks to pass before merging
   └─ ✅ Require branches to be up to date before merging
   └─ Select required status checks:
      - quality (✅)
      - dbt-lint (✅)
      - dbt-tests (✅)
      - ci-status (✅)

✅ Include administrators
   └─ Enforcement level: (check if admins bypass rules)

✅ Restrict who can push to matching branches
   └─ (leave empty to restrict to PR merges only)

✅ Allow force pushes
   └─ ☐ (keep disabled for protection)

✅ Allow deletions
   └─ ☐ (keep disabled for protection)
```

### Step 3: Save

Click **"Create"** button at bottom

---

## Suggested Merge Strategy

### Recommended: Squash and Merge
```
Always "Squash and merge" PRs to master:
  - Keeps master commit history clean
  - Each PR = one logical commit
  - Easy to revert individual features
  - Conventional commits preserved in squashed message
```

### Alternative: Create a Merge Commit
```
Use "Create a merge commit" for large features:
  - Preserves PR author's commit history
  - Shows feature development progression
  - Trade-off: More commits in master history
```

### Never: Fast-Forward Merge
```
Disable "Allow rebase and fast-forward" on master
  - Loses PR context (who, when, why merged?)
  - No automatic deploy tracking point
```

---

## Workflow Rules by Branch

| Branch | Protection | Status Checks | Reviews | Auto-delete |
|--------|-----------|---------------|---------|-------------|
| `master` | ✅ Full | ✅ All | 1 req. | ✅ Yes |
| `develop` | ⏸ Future | ⏸ Future | ⏸ Future | ⏸ Future |
| `feature/*` | ❌ None | ❌ None | ❌ None | ✅ auto-delete after 30 days |
| `hotfix/*` | ❌ None | ❌ None | ❌ None | ✅ auto-delete after 30 days |

---

## Common Scenarios

### Scenario 1: PR Blocked on Failing Test

**Problem**: "Tests cannot pass. Tests must pass before merging." error appears

**Solution**:
```bash
# 1. Check which test failed
# View GitHub Actions logs in PR

# 2. Fix locally
git checkout feature/my-feature
pytest tests/ -v  # or specific test

# 3. Fix the issue
vim src/problematic_file.py

# 4. Run tests again locally to verify
make ci-local

# 5. Push fix
git add .
git commit -m "fix: address test failure"
git push origin feature/my-feature

# 6. CI re-runs automatically; once passing, PR unblocked
```

### Scenario 2: PR Becomes Out of Date

**Problem**: "This branch is out of date with the base branch" + yellow warning

**Solution (Option A - Rebase)**:
```bash
git fetch origin
git rebase origin/master feature/my-feature
git push origin feature/my-feature -f
```

**Solution (Option B - Merge)**:
```bash
git fetch origin
git merge origin/master
git push origin feature/my-feature
```

GitHub will show "Update branch" button in PR UI as alternative.

### Scenario 3: Need to Bypass Branch Protection (Emergency)

**Process**:
1. Contact repository admin
2. Admin temporarily allows force push
3. Push fix directly to master
4. Admin re-enables protection
5. Document in PR/issue why bypass was needed

**Example**: Production data pipeline crashed, rollback needed immediately

---

## Enforcement & Monitoring

### Monitoring PR Status

**On PR page, check**:
- ✅ All status checks passed (green checkmark)
- ✅ Approved by at least 1 reviewer
- ✅ Branch up to date with master
- 🟢 Merge button is green ("Squash and merge" enabled)

### Viewing Denied Merges

**GitHub logs all merge attempts**:
```
Settings → General → Merge button → Push settings
```

Shows: Timestamp, user, reason why merge blocked

---

## Escalation Policy

### If a Check Consistently Fails

1. **First occurrence**: Debug and fix in PR
2. **Second occurrence**: File issue to improve check
3. **Recurring false positives**: 
   - Document the pattern
   - Request check configuration adjustment
   - Consider downgrading to informational until fixed

### If a Check is Too Strict

**Example**: Coverage requirement blocking good PRs

**Process**:
1. Propose adjustment with data
2. Discuss in team meeting
3. Update configuration if consensus reached
4. Document rationale in this file

---

## Timeline Implementation

| Phase | Actions | Status |
|-------|---------|--------|
| **Now** | Enable master protection rules as config'd above | ✅ Ready |
| **Phase 6 B3** | Add CODEOWNERS for data ownership | ⏳ Planned |
| **Phase 6 B3** | Configure data-quality check as required (not informational) | ⏳ Planned |
| **Phase 7** | Add pre-merge deployment dry-run | 📋 Future |
| **Phase 8** | Add auto-close stale PRs policy | 📋 Future |

---

## References

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories/about-status-checks)
