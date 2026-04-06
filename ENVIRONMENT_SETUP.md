# Environment Setup Guide

## Quick Start (One Session Bootstrap)

For a new contributor to get started in one session:

```bash
# 1. Clone the repository
git clone https://github.com/theo-lyd/predictive-ltv-survival-pipeline.git
cd predictive-ltv-survival-pipeline

# 2. Run bootstrap script
bash scripts/bootstrap.sh

# 3. Set up Databricks credentials
bash scripts/setup_secrets.sh
source .env.local

# 4. Test dbt connection
dbt debug

# 5. Run project validation
make validate
```

## Prerequisites

- Python 3.10+
- Java 17 (for local Spark; not required if using Databricks SQL only)
- Git
- GitHub account with repository access

## Step-by-Step Setup

### 1. Clone Repository

```bash
git clone https://github.com/theo-lyd/predictive-ltv-survival-pipeline.git
cd predictive-ltv-survival-pipeline
```

### 2. Install Dependencies

#### Option A: Using bootstrap script (Recommended)

```bash
bash scripts/bootstrap.sh
```

#### Option B: Manual installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional: install development tools
pip install -r requirements-dev.txt
```

### 3. Configure Databricks Credentials

#### Using setup script (Recommended)

```bash
bash scripts/setup_secrets.sh
source .env.local
```

#### Manual setup

Create a `.env.local` file in the project root:

```bash
export DATABRICKS_HOST="your-instance.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_TOKEN="dbapinnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn"
```

Tip: you can bootstrap from template:

```bash
cp .env.example .env.local
```

Then source it:

```bash
source .env.local
```

### 4. Configure dbt Profile

Copy the example profile:

```bash
cp profiles.yml.example ~/.dbt/profiles.yml
```

Edit `~/.dbt/profiles.yml` to match your environment:

```yaml
predictive_ltv_survival_pipeline:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: main
      schema: predictive_ltv_dev
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      threads: 4
    prod:
      type: databricks
      catalog: main
      schema: predictive_ltv_prod
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      threads: 8
```

### 5. Validate Setup

```bash
# Test dbt connection
dbt debug

# Run project validation
make validate

# List available make commands
make help
```

## Common Commands

```bash
# Development workflow
make install              # Install core dependencies
make install-dev         # Install with dev tools
make lint                # Run code quality checks
make format              # Auto-format code
make test                # Run unit tests
make clean               # Clean build artifacts

# dbt specific
dbt debug                # Test Databricks connection
dbt parse                # Parse project
dbt run                  # Run transformations
dbt test                 # Run data quality tests
dbt docs generate        # Generate documentation

# Project operations
make bootstrap           # Bootstrap project
make validate            # Validate environment
```

## Troubleshooting

### "dbt debug" fails with connection error

**Issue**: Cannot connect to Databricks
**Solution**:
1. Verify `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, and `DATABRICKS_TOKEN` are set
2. Test with: `echo $DATABRICKS_HOST`
3. Ensure credentials are sourced: `source .env.local`

### Python import errors

**Issue**: `ModuleNotFoundError: No module named 'dbt_databricks'`
**Solution**:
```bash
pip install --upgrade dbt-databricks
python -m pip show dbt-databricks
```

### Permission denied on bootstrap.sh

**Issue**: `Permission denied: scripts/bootstrap.sh`
**Solution**:
```bash
chmod +x scripts/bootstrap.sh
bash scripts/bootstrap.sh
```

### VS Code dbt extension shows "dbt not found" or "profile not found"

**Issue**: dbt Power User diagnostics show one or more of:
- `dbt configuration is invalid : dbt not found`
- `Could not find profile named 'predictive_ltv_survival_pipeline'`
- `Env var required but not provided: 'DATABRICKS_HOST'`

**Root cause**: VS Code extension process is not using the same Python/dbt/profile context as your terminal.

**Fix checklist**:
1. Ensure the interpreter is the repo venv:
   - Command Palette -> `Python: Select Interpreter`
   - Select `/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python`
2. Ensure workspace settings exist in `.vscode/settings.json`:
```json
{
  "dbt.dbtIntegration": "core",
  "dbt.dbtPythonPathOverride": "/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python",
  "terminal.integrated.env.linux": {
    "DBT_PROFILES_DIR": "${workspaceFolder}"
  }
}
```
3. Ensure a profile file exists in the project root:
```bash
cp profiles.yml.example profiles.yml
```
4. Reload VS Code window:
   - Command Palette -> `Developer: Reload Window`
5. If warnings persist, clear extension cache:
   - Command Palette -> `dbt Power User: Clear Manifest Cache`

**Verification**:
```bash
DBT_PROFILES_DIR=/workspaces/predictive-ltv-survival-pipeline \
  /workspaces/predictive-ltv-survival-pipeline/.venv/bin/dbt parse --project-dir .
```
Expected: parse succeeds (warnings are acceptable), no profile/binary errors.

## Environment Variables

The following environment variables are required:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Databricks instance hostname | `abc123.cloud.databricks.com` |
| `DATABRICKS_HTTP_PATH` | Path to SQL Warehouse or All-Purpose Cluster | `/sql/1.0/warehouses/abc123` |
| `DATABRICKS_TOKEN` | Personal access token for authentication | `dbapin1234567890abcdef...` |

Optional:

| Variable | Description | Default |
|----------|-------------|---------|
| `DBT_PROFILES_DIR` | Path to dbt profiles directory | `~/.dbt` |
| `PYTHONPATH` | Python module search path | (auto-set by scripts) |

## Security Notes

- **Never** commit `.env` or `.env.local` files containing credentials
- **Never** commit `~/.dbt/profiles.yml` with actual tokens
- Use GitHub Secrets for CI/CD pipelines
- Rotate tokens regularly
- Use principle of least privilege for service accounts

## Directory Structure After Setup

```
predictive-ltv-survival-pipeline/
├── .devcontainer/          # Codespaces configuration
├── .dbt/                   # (local only, not in repo)
├── .env.local              # (local only, not in repo)
├── scripts/
│   ├── bootstrap.sh        # One-session setup
│   └── setup_secrets.sh    # Credential helper
├── data/
│   ├── bronze/             # Raw ingestion
│   ├── silver/             # Cleaned data
│   └── gold/               # Analytics outputs
├── models/
│   ├── staging/            # stg_* models
│   ├── marts/              # fct_* and dim_* models
│   └── sources.yml
├── dbt_project.yml
├── profiles.yml.example    # Template for profiles
├── requirements.txt        # Core dependencies
└── requirements-dev.txt    # Optional dev tools
```

## Next Steps

After completing setup:

1. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. Check [docs/01_project_brief.md](docs/01_project_brief.md) for project context
3. Run `dbt docs generate && dbt docs serve` to view data lineage
4. Create your first feature branch following naming conventions
