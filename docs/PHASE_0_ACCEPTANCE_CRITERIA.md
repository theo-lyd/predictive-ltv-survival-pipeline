# Phase 0: Acceptance Criteria & Validation Checklist

## Objective
Establish a reproducible, secure, cloud-native platform for analytics engineering.

## Deliverables Checklist

### ✓ 1. Reproducible Codespace Startup

- [ ] `.devcontainer/devcontainer.json` configured with Python 3.10, Java, dbt, Databricks CLI
- [ ] `.devcontainer/post-create.sh` validates dependencies and provides helpful errors
- [ ] New contributor can run `bash scripts/bootstrap.sh` successfully in one session
- [ ] Bootstrap script validates:
  - [ ] Python 3.10+ installed
  - [ ] Required packages installed (dbt, pandas, pyspark, etc.)
  - [ ] Databricks environment variables configured
  - [ ] dbt profile file created or instructions provided
  - [ ] Directory structure initialized (Bronze/Silver/Gold)

### ✓ 2. Working dbt Connection

- [ ] `dbt debug` executes successfully
- [ ] dbt connects to target Databricks workspace
- [ ] dbt can parse all models without errors
- [ ] dbt profile configured in `~/.dbt/profiles.yml` with Databricks credentials
- [ ] dbt schema naming aligns with Medallion architecture:
  - [ ] Staging models route to `stg` schema
  - [ ] Mart models route to `marts` schema

### ✓ 3. Medallion Directory Structure

- [ ] Bronze layer logical schema defined:
  - [ ] Path: `/mnt/bronze/` (documented, Azure/AWS specific)
  - [ ] Delta Lake format
  - [ ] Append-only configuration
  
- [ ] Silver layer logical schema defined:
  - [ ] Path: `/mnt/silver/` (documented)
  - [ ] Schema name: `stg` (for staging models)
  - [ ] dbt models in `models/staging/` directory
  
- [ ] Gold layer logical schema defined:
  - [ ] Path: `/mnt/gold/` (documented)
  - [ ] Schema name: `marts` (for business metrics)
  - [ ] dbt models in `models/marts/` directory

- [ ] Directory structure on disk matches Medallion organization:
  ```
  models/
  ├── staging/         # Silver layer models
  ├── marts/           # Gold layer models
  ├── sources.yml      # Bronze source definitions
  ├── schema.yml       # Data contracts
  └── README.md        # Layer documentation
  ```

### ✓ 4. Access Patterns for SQL Warehouse

- [ ] Databricks credentials securely stored (not in git):
  - [ ] `~/.dbt/profiles.yml` excluded from version control
  - [ ] `.env.local` in `.gitignore`
  - [ ] GitHub Secrets configured for CI/CD
  
- [ ] Access patterns documented:
  - [ ] SQL Warehouse endpoint configured in dbt profile
  - [ ] All-Purpose cluster option documented as alternative
  - [ ] Connection timeout and retry settings configured
  
- [ ] Test access:
  - [ ] `dbt debug` succeeds
  - [ ] `dbt parse` runs without errors
  - [ ] `dbt run --select stg_*` executes sample query

### ✓ 5. Repository Standards & Governance

- [ ] `.gitignore` configured to exclude:
  - [ ] Python cache (`__pycache__/`, `*.pyc`)
  - [ ] Virtual environments (`venv/`, `.venv`)
  - [ ] IDE files (`.vscode/`, `.idea/`)
  - [ ] dbt build artifacts (`target/`, `logs/`)
  - [ ] Data files (`data/`, `*.parquet`, `*.csv`)
  - [ ] Secrets files (`.env`, `profiles.yml`)
  
- [ ] `.editorconfig` standardizes:
  - [ ] Python indentation (4 spaces)
  - [ ] Line endings (LF)
  - [ ] Encoding (UTF-8)
  
- [ ] `Makefile` provides convenient shortcuts:
  - [ ] `make install` - Install dependencies
  - [ ] `make lint` - Run style checks
  - [ ] `make format` - Auto-format code
  - [ ] `make test` - Run tests
  - [ ] `make bootstrap` - Initialize project
  - [ ] `make validate` - Validate environment
  
- [ ] GitHub PR template includes:
  - [ ] Description and related issue link
  - [ ] Type of change (bug, feature, docs, etc.)
  - [ ] Testing details
  - [ ] Checklist for code quality and tests

### ✓ 6. Documentation & Runbooks

- [ ] `ENVIRONMENT_SETUP.md` covers:
  - [ ] Quick-start one-session bootstrap
  - [ ] Step-by-step manual setup
  - [ ] Databricks credential configuration
  - [ ] dbt profile setup
  - [ ] Common troubleshooting
  
- [ ] `ARCHITECTURE.md` covers:
  - [ ] High-level data flow diagram
  - [ ] Medallion layer architecture with SQL examples
  - [ ] Technology stack overview
  - [ ] Lineage and governance strategy
  - [ ] Deployment environments (dev/prod)
  - [ ] Scaling and optimization strategies
  - [ ] Incident runbooks
  
- [ ] `models/README.md` documents:
  - [ ] Medallion layer definitions
  - [ ] Directory structure
  - [ ] Naming conventions
  - [ ] Testing and validation approach

### ✓ 7. Bootstrap & Automation

- [ ] `scripts/bootstrap.sh` provides one-session setup:
  - [ ] Validates Python and Java
  - [ ] Installs all dependencies
  - [ ] Initializes directory structure
  - [ ] Provides next-step instructions
  
- [ ] `scripts/setup_secrets.sh` simplifies credential setup:
  - [ ] Securely prompts for Databricks credentials
  - [ ] Creates `.env.local` file
  - [ ] Provides sourcing instructions

### ✓ 8. Testing & Validation

- [ ] `tests/test_environment.py` validates:
  - [ ] Python 3.10+ installed
  - [ ] Required packages available
  - [ ] Databricks env vars configured
  - [ ] dbt connection working
  - [ ] Directory structure complete
  - [ ] Configuration files present
  
- [ ] `make validate` runs environment tests
- [ ] Validation succeeds with `dbt debug` passing

## Acceptance Criteria For Phase 0

### For Individual Contributor

**Criterion**: New contributor can bootstrap in one session

Test procedure:
```bash
# Start from clean repository
git clone <repo>
cd predictive-ltv-survival-pipeline
bash scripts/bootstrap.sh
bash scripts/setup_secrets.sh
source .env.local
dbt debug
make validate
```

**Expected Result**: All commands succeed, no manual file edits needed beyond `.env.local`

### For Environment Parity

**Criterion**: Environment reproducible across two clean rebuilds

Test procedure:
1. Rebuild Codespaces container
2. Run `bash scripts/bootstrap.sh`
3. Run `dbt debug` and `make validate`
4. Rebuild again and repeat

**Expected Result**: Consistent success across rebuilds, no Docker build failures

### For Data Platform Access

**Criterion**: dbt can parse and run all models

Test procedure:
```bash
dbt parse                     # Parse all models
dbt test --select stg_*      # Run staging model tests
dbt run --select stg_*       # Run staging models
dbt docs generate            # Generate lineage
```

**Expected Result**: All commands succeed, lineage visible in docs

## Sign-Off Checklist

- [ ] All deliverables implemented
- [ ] All acceptance criteria validated
- [ ] Documentation reviewed and accurate
- [ ] Bootstrap script tested by new contributor
- [ ] dbt connection verified in dev and prod environments
- [ ] No Docker build failures on rebuild
- [ ] Repository secrets properly excluded
- [ ] Phase 0 complete and ready for Phase 1

## Related Tests

Run these commands to verify Phase 0 completion:

```bash
# Full validation
make validate

# dbt specific
dbt debug
dbt parse
dbt docs generate

# Repository standards
make lint
make format

# Directory check
ls -la models/staging models/marts
ls -la data/bronze data/silver data/gold
```
