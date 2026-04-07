# Branch Protection Configuration Test Plan

**Date**: April 7, 2026  
**Status**: Ready for Implementation  
**Test Coverage**: UI Configuration + Workflow Validation  

---

## Part 1: GitHub UI Configuration Checklist

### Prerequisites
- ✅ Admin access to repository
- ✅ All CI workflows deployed (ci-enhanced.yml, release.yml)
- ✅ Current branch: master, all commits pushed

### Step 1: Enable Branch Protection Rule

**Navigate to**: `https://github.com/theo-lyd/predictive-ltv-survival-pipeline/settings/branches`

**Action**: Click **"Add rule"** button

| Setting | Status | Expected Value |
|---------|--------|-----------------|
| Branch name pattern | ☐ Set | `master` |
| Require a pull request before merging | ☐ ✅ Checked | Required |
| Require approvals | ☐ Set | `1` |
| Dismiss stale approvals | ☐ ✅ Checked | When new commits pushed |
| Require CODEOWNERS review | ☐ ☐ Unchecked | Future/Not enabled |
| Require status checks to pass | ☐ ✅ Checked | — |
| Require branches to be up to date | ☐ ✅ Checked | — |

**Test Action**: Take screenshot showing all settings enabled, then click **"Create"**

### Step 2: Select Required Status Checks

After creating the rule, edit it again and scroll to **"Required status checks"**

**Required Checks** (select these):
```
☐ quality               (Code Quality & Testing)
☐ dbt-lint             (dbt Lint & Parse)
☐ dbt-tests            (dbt Tests - Slim CI)
☐ ci-status            (Summary gate)
```

**Informational Checks** (do NOT select):
```
☐ data-quality         (Will track but not block)
☐ code-metrics         (Will track but not block)
```

**Test Action**: Click each checkbox for blocking checks, leave informational unchecked, save

### Step 3: Enable Actions Permissions

**Navigate to**: `https://github.com/theo-lyd/predictive-ltv-survival-pipeline/settings/actions`

| Setting | Expected | Status |
|---------|----------|--------|
| Actions permissions | Enabled | ☐ Check |
| Allow all actions | Enabled | ☐ Check |
| Default permissions | Read repository contents | ☐ Check |

**Test Action**: Save settings

### Step 4: Enable Dependabot Alerts

**Navigate to**: `https://github.com/theo-lyd/predictive-ltv-survival-pipeline/settings/security_analysis`

| Setting | Status |
|---------|--------|
| Dependabot alerts | ☐ ✅ Enable |
| Dependabot security updates | ☐ ✅ Enable |

**Test Action**: Save and verify alerts enabled

---

## Part 2: Functional Workflow Test

### Test Scenario: Create a Test PR

**Objective**: Verify branch protection blocks non-compliant PRs and allows compliant ones

#### Step 1: Create Feature Branch
```bash
cd /workspaces/predictive-ltv-survival-pipeline
git checkout -b test/branch-protection-validation
```

#### Step 2: Make a Trivial Change
```bash
# Add a comment to a test file
echo "# Branch protection test" >> tests/test_phase5_storytelling.py
git add tests/test_phase5_storytelling.py
git commit -m "test: branch protection validation"
git push origin test/branch-protection-validation
```

#### Step 3: Create PR on GitHub

**Navigate to**: `https://github.com/theo-lyd/predictive-ltv-survival-pipeline/compare/master...test/branch-protection-validation`

**Action**: Click **"Create pull request"**

**Expected Behavior**:
- ✅ PR created successfully
- ✅ CI pipeline triggers automatically (status checks running)
- ⏳ Workflow shows 6 jobs: quality, dbt-lint, dbt-tests, data-quality, code-metrics, ci-status

#### Step 4: Monitor CI Execution

**Verify with**:
```bash
cd /workspaces/predictive-ltv-survival-pipeline
git log --all --oneline -5
```

**Expected CI Flow**:
```
1. quality job starts:
   - pylint runs
   - flake8 runs
   - black runs
   - Security checks (bandit, pip-audit)
   - pytest runs

2. dbt-lint job starts (parallel):
   - dbt parse (schema validation)
   - dbt compile (SQL generation)

3. dbt-tests job (depends on dbt-lint):
   - dbt test (slim CI: only modified models)
   - Tests pass or fail

4. data-quality job (parallel):
   - Great Expectations validation runs

5. code-metrics job (parallel):
   - Radon complexity analysis

6. ci-status job:
   - Aggregates results
   - Final pass/fail signal
```

#### Step 5: Verify PR Blocking Rules

**Expected UI Behavior** (on PR page):
- ❌ Merge button is **DISABLED** (gray) if:
  - Any blocking check failing
  - No approvals yet
  - Branch is out of date with master

- ✅ Merge button is **ENABLED** (green) if:
  - All blocking checks passing (quality, dbt-lint, dbt-tests, ci-status)
  - 1+ approvals received
  - Branch is up to date with master

**Test Action**: Screenshot PR page showing disabled merge button during CI

#### Step 6: Verify Status Check Details

**On PR page** → Scroll to **"Checks"** section

**Expected Results**:
```
✅ quality ........................... PASSED
✅ dbt-lint .......................... PASSED
✅ dbt-tests ......................... PASSED
⚠️  data-quality ..................... PASSED (informational)
⚠️  code-metrics ..................... PASSED (informational)
✅ ci-status ......................... PASSED
```

**Test Action**: Click each check to view logs, verify no errors

### Test Scenario 2: Verify Out-of-Date Branch Protection

#### Step 1: Make Change to Master

```bash
git checkout master
git pull origin master
echo "# Unrelated change" >> README.md
git add README.md
git commit -m "docs: test update"
git push origin master
```

#### Step 2: Return to PR

**Navigate to** your test PR page

**Expected Behavior**:
- ⚠️ PR shows "This branch is out of date with the base branch"
- ❌ "Update branch" button appears
- ❌ Merge button remains disabled until branch updated

**Test Action**: Screenshot showing out-of-date warning

#### Step 3: Update Branch

```bash
git checkout test/branch-protection-validation
git merge origin/master
git push origin test/branch-protection-validation
```

**Expected Behavior**:
- ✅ PR updates automatically
- ✅ Out-of-date warning clears
- ⏳ CI re-runs automatically
- ✅ Once CI passes + approval: Merge button re-enabled

**Test Action**: Screenshot showing "Branch up to date" message

### Test Scenario 3: Verify Approval Requirement

#### Step 1: Check Merge Button Status (No Approval)

**On PR page**, merge button shows *one of*:
- ❌ "Waiting for status checks"
- ❌ "Waiting for review approval"
- ❌ "Waiting for branch to be up to date"

**Test Action**: Screenshot showing blocking reason

#### Step 2: Add Approval

**On PR page** → Click **"Review changes"** → Select **"Approve"** → Click **"Submit review"**

**Or** (if testing with another account - ask in code review):

**Expected Result**: PR now requires approval from another user

#### Step 3: Verify Merge Button Enables

**After approval + all checks passing**:
- ✅ Merge button turns green
- ✅ Dropdown shows "Squash and merge" option
- ✅ Click to merge

**Test Action**: Screenshot showing enabled merge button

### Test Scenario 4: Verify Informational Checks Don't Block

#### Create PR with Data Quality Failure

```bash
# This scenario verifies data-quality check is informational (doesn't block merge)
```

**Expected Behavior**:
- ⚠️ data-quality check shows as failed
- ⚠️ But marked as "Informational" 
- ✅ Merge button still ENABLED (not blocked by this check)
- ✅ Merge allowed even though data-quality failed

**Rationale**: Informational checks allow development to continue while tracking issues

---

## Part 3: CI Pipeline Validation

### Verify All Workflow Jobs Exist

```bash
cd /workspaces/predictive-ltv-survival-pipeline

# Check workflow syntax
python -c "import yaml; print(yaml.safe_load(open('.github/workflows/ci-enhanced.yml'))['jobs'].keys())"
```

**Expected Output**:
```
dict_keys(['quality', 'dbt-lint', 'dbt-tests', 'data-quality', 'code-metrics', 'ci-status'])
```

### Verify Status Check Names Match

The status check names in the workflow **must match exactly** the branch protection rule selection.

**Verify in workflow**:
```bash
grep "name:" .github/workflows/ci-enhanced.yml | head -10
```

**Expected Match** (order doesn't matter):
- Workflow job name: "Code Quality & Testing" → Status check: "quality"
- Workflow job name: "dbt Lint & Parse" → Status check: "dbt-lint"
- Workflow job name: "dbt Tests (Slim CI)" → Status check: "dbt-tests"
- Workflow job name: "Great Expectations Quality Checks" → Status check: "data-quality"
- Workflow job name: "Code Metrics & Complexity" → Status check: "code-metrics"
- Workflow job name: "CI Status Check" → Status check: "ci-status"

**Test Action**: Verify each job has correct `name:` field

### Verify Dependabot Workflow

```bash
# Verify dependabot config exists and is valid YAML
python -c "import yaml; d=yaml.safe_load(open('.github/dependabot.yml')); print('Targets:', [v['package-ecosystem'] for v in d['updates']])"
```

**Expected Output**:
```
Targets: ['pip', 'github-actions']
```

---

## Part 4: Makefile Local CI Validation

### Run Local CI Pipeline

```bash
cd /workspaces/predictive-ltv-survival-pipeline
make ci-local
```

**Expected Output**:
```
Running clean...
Running install-dev...
Running lint... (pylint, flake8, black checks)
Running test... (pytest with coverage)
Running dbt-parse...
Running dbt-test...
Running ge-validate...
All checks passed!
```

**Success Criteria**:
- ✅ No compilation errors
- ✅ All tests pass
- ✅ Coverage meets threshold
- ✅ dbt models parse without errors
- ✅ Great Expectations checkpoint passes

---

## Part 5: Release Workflow Validation

### Verify Release Workflow Can Be Triggered

```bash
# Create a test tag (without pushing)
git tag v0.99.0-test -m "Test release"

# Verify workflow trigger
python -c "import yaml; w=yaml.safe_load(open('.github/workflows/release.yml')); print('Release triggers:', w['on'])"
```

**Expected Output**:
```
Release triggers: Tags matching v*
```

**Test Action**: Verify release.yml has correct tag pattern

### Verify Release Jobs

```bash
python -c "import yaml; w=yaml.safe_load(open('.github/workflows/release.yml')); print('Jobs:', list(w['jobs'].keys()))"
```

**Expected Output**:
```
Jobs: ['parse-version', 'create-release', 'build-artifacts', 'update-docs', 'validate-release']
```

---

## Part 6: Checklist for Sign-Off

### Configuration Verified
- [ ] Branch protection rule created for `master`
- [ ] 1 approval required
- [ ] All 4 blocking status checks selected (quality, dbt-lint, dbt-tests, ci-status)
- [ ] Informational checks not blocking (data-quality, code-metrics)
- [ ] "Require branches to be up to date" enabled
- [ ] "Dismiss stale approvals" enabled
- [ ] Force pushes disabled
- [ ] Deletions disabled

### Workflows Validated
- [ ] ci-enhanced.yml syntax valid
- [ ] release.yml syntax valid
- [ ] dependabot.yml syntax valid
- [ ] All 6 CI jobs present and correctly named
- [ ] All job dependencies correct (dbt-tests depends on dbt-lint)

### Functional Tests Passed
- [ ] Created test PR, CI triggered
- [ ] All 6 status checks executed
- [ ] Merge button disabled without approval
- [ ] Merge button disabled with out-of-date branch
- [ ] Merge button enabled after approval + checks passing
- [ ] Merge successful when all requirements met
- [ ] Cleanup: Deleted test branch after merging

### Local CI Passed
- [ ] `make ci-local` runs without errors
- [ ] All linting checks pass
- [ ] All tests pass with coverage
- [ ] dbt models parse and compile
- [ ] Great Expectations checkpoint passes

### Documentation Complete
- [ ] BRANCH_PROTECTION_RULES.md reviewed
- [ ] CI_CD_CONFIGURATION.md reviewed
- [ ] WORKFLOW_DOCUMENTATION.md reviewed
- [ ] All runbooks and examples tested

---

## Cleanup After Testing

```bash
# Delete test tag
git tag -d v0.99.0-test

# Delete test branch (on GitHub or locally)
git branch -D test/branch-protection-validation
git push origin --delete test/branch-protection-validation

# Verify master clean
git checkout master
git status  # Should show "nothing to commit, working tree clean"
```

---

## Sign-Off

**Test Completed By**: [Your Name]  
**Date**: [Date]  
**Result**: ✅ PASS / ❌ FAIL  

**Notes**:
```
[Add any observations or issues found]
```

---

## Common Issues & Resolutions

### Issue: Status checks not appearing in branch protection

**Cause**: Workflow hasn't run yet on master

**Resolution**:
1. Create a test PR
2. Wait for CI to complete on master
3. GitHub learns the check exists
4. Refresh branch protection settings page
5. Checks now appear in dropdown

### Issue: "ci-status" check missing

**Cause**: This is a summary job that must exist in workflow

**Resolution**: Verify ci-enhanced.yml has a final `ci-status` job that depends on all others

### Issue: Merge button shows "Some required status checks are missing"

**Cause**: A required check in branch protection doesn't have a corresponding job in workflow

**Resolution**: 
1. Verify check name exactly matches workflow job name
2. Re-run workflow to populate GitHub's cache
3. Try again in 5-10 minutes

### Issue: Branch protection rule not saving

**Cause**: Missing required field or invalid pattern

**Resolution**:
1. Branch pattern must be `master` (not `main` if master is actual branch)
2. At least one status check must be required
3. Try again with simpler configuration first

