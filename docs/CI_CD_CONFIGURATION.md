# CI/CD Configuration Guide

## GitHub Actions Setup

### 1. Repository Settings (Required)

Navigate to your repository settings at: `https://github.com/theo-lyd/predictive-ltv-survival-pipeline/settings`

#### Branch Protection Rules

Set up protected branch rules for `master`:

1. Go to **Settings → Branches → Branch protection rules**
2. Add rule for `master` branch

**Configuration:**
```
✓ Require a pull request before merging
  └─ Require approvals: 1
✓ Require status checks to pass before merging
  └─ Following checks required:
     - "ci: Code Quality & Testing"
     - "ci: dbt Lint & Parse"
     - "ci: dbt Tests (Slim CI)"
     - "ci: Enforce merge"
✓ Require branches to be up to date before merging
✓ Require code reviews before merging
  └─ Dismiss stale pull request approvals: checked
✓ Restrict who can push to matching branches
```

#### Workflow Permissions

1. Go to **Settings → Actions → General**
2. Set permissions:
   ```
   ✓ Read repository contents permission
   ✓ Allow GitHub Actions to create and approve pull requests
   ```

### 2. Secrets & Variables

Some workflows may need secrets. Configure at: **Settings → Secrets and variables → Actions**

**Currently required secrets:** None (can add later for external integrations)

**Environment variables to add:**
```
CODECOV_TOKEN=<from codecov.io if using>
```

### 3. Dependabot Configuration

Dependabot is configured via `.github/dependabot.yml`:
- Checks for pip dependency updates weekly
- Creates pull requests automatically
- Runs CI/CD on dependency PRs

**Enable Dependabot alerts:**
1. Go to **Settings → Code security and analysis**
2. Enable:
   - ✓ Dependabot alerts
   - ✓ Dependabot security updates

---

## Semantic Versioning & Release Tags

### Version Format
```
v{MAJOR}.{MINOR}.{PATCH}[-{PRERELEASE}][+{BUILD}]

Examples:
v0.1.0          # Initial release
v1.0.0          # Major release
v1.2.3          # Patch (bug fix)
v2.0.0-alpha.1  # Pre-release (not production-ready)
```

### Creating a Release

#### Step 1: Create & Push Tag Locally
```bash
# Create annotated tag (recommended)
git tag -a v1.2.3 -m "Release v1.2.3: Add SLA monitoring"

# Or lightweight tag
git tag v1.2.3

# Push tag to GitHub
git push origin v1.2.3
```

#### Step 2: GitHub Actions Auto-Executes
- Release workflow starts automatically
- GitHub release created with changelog
- SBOM generated
- Documentation updated
- Email notification sent to watcher

#### Step 3: Verify Release
1. Navigate to GitHub **Releases** page
2. Verify new release appeared with changelog
3. Artifacts available for download

### Automatic Version Bumping (Future)

For automated versioning, use conventional commits:

```
feat: Add SLA monitoring          → version bump (MINOR)
fix: Fix SLA calculation           → version bump (PATCH)
BREAKING CHANGE: Redesign API     → version bump (MAJOR)
```

Then use tool like `bump2version` or `python-semantic-release` to auto-increment versions.

---

## Required Installations for Local CI

Before running local CI checks, ensure dev dependencies are installed:

```bash
make install-dev
```

This installs:
- Testing: `pytest`, `pytest-cov`
- Linting: `pylint`, `flake8`, `black`, `isort`
- Security: `bandit`, `pip-audit`
- Formatting: `yamllint`
- Analysis: `radon`
- Data validation: `great_expectations`
- dbt: `dbt-core`

---

## Continuous Integration Checklist

Run before pushing your PR:

```bash
# 1. Format code
make format

# 2. Run linting
make lint

# 3. Run tests
make test

# 4. Security check
make sec-audit

# 5. dbt validation
make dbt-parse
make dbt-test

# 6. Data quality
make ge-validate

# Or run all at once:
make ci-local
```

**Expected output:**
```
✅ All local CI checks passed!
```

If any check fails, fix before pushing.

---

## GitHub Actions Dashboard

### Viewing Workflow Runs

Navigate to: **Actions** tab → Select workflow → View run

**Run details show:**
- ✅ Passed jobs (green)
- ❌ Failed jobs (red)
- ⏭ Skipped jobs (gray)
- ⏱ Duration per job
- 📊 Job logs and artifacts

### Monitoring Performance

Each workflow run shows:
- **Total duration**: Aim for <5min (slim CI) or <12min (full)
- **Cache hit ratio**: Aim for >50% after first run
- **Artifact sizes**: Each <100MB

### Re-running Jobs

If a job fails due to transient error (network, timeouts):
1. Go to **Actions → Run details**
2. Click **Re-run jobs**
3. Select failed job(s)
4. GitHub re-executes

---

## Security Best Practices

### 1. Secrets Management
- ❌ Never commit credentials to git
- ✅ Use GitHub Secrets for sensitive values
- ✅ Use environment-specific values
- ✅ Rotate secrets quarterly

### 2. Dependency Security
- Dependabot auto-checks for vulnerable packages
- `pip-audit` runs in CI to catch issues early
- Review dependency changes in PRs

### 3. Code Security
- `bandit` scans for common vulnerabilities
- `pylint` catches security anti-patterns
- Manual code review required for sensitive changes

### 4. Workflow Permissions
- Workflows use minimal required permissions
- `GITHUB_TOKEN` auto-scoped per job
- No long-lived personal tokens needed

---

## Troubleshooting

### Workflow Doesn't Trigger

**Problem:** Push a commit but workflow doesn't start

**Solutions:**
1. Check branch protection rules aren't blocking
2. Verify file changes match workflow `on:` conditions
3. Check **Actions → All workflows → (select workflow)** for recent runs
4. Look for `[skip ci]` in commit message (if present, CI is skipped)

### Job Timeout (>1 hour)

**Problem:** Job runs for >60 minutes and auto-cancels

**Solutions:**
1. Check for infinite loops in tests/queries
2. Break large jobs into parallel jobs
3. Enable caching if not already enabled
4. Profile slow steps with `time` prefix

### Artifact Upload Fails

**Problem:** Artifacts don't appear in GitHub

**Solutions:**
1. Check artifact path exists
2. Verify artifact size < 100MB
3. Check GitHub storage quota not exceeded
4. Verify job didn't fail before artifact upload step

### Cache Not Working

**Problem:** Dependencies re-download on every run

**Solutions:**
1. Verify cache action correctly configured
2. Check cache key includes dependency file hash
3. Clear cache manually in **Settings → Actions → General**
4. Note: Cache size limited to 5GB per repo

---

## Next Steps (Roadmap)

Integration improvements planned for future phases:

- [ ] Slack notifications for build status
- [ ] Integration with Jira for failed test tracking
- [ ] Container image building and ECR push
- [ ] dbt Cloud job orchestration
- [ ] Performance regression detection
- [ ] Automated rollback on production failures
- [ ] Multi-region deployment automation

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
