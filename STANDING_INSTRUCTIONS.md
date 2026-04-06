# Standing Instructions for Capstone Project Execution

**Repository**: predictive-ltv-survival-pipeline  
**Purpose**: Governance framework for all phases of development  
**Enforced By**: All batch deliverables and phase checkpoints  
**Last Updated**: Phase 0 documentation complete + "Why" rationale added

---

## Core Governance Requirements

### 1. Batch Execution Protocol

**Every batch shall:**
1. Be announced with clear scope and objectives
2. Request user approval before proceeding
3. Include atomic git commits (single logical change per commit)
4. Be published with `git commit && git push`
5. Include batch-specific documentation

**Batch Size Guidelines:**
- Target: 1-3 hours per batch to prevent container crashes
- Max changes: 5-10 files per batch (reduces integration risk)
- If phase work grows large, split into 2-4 smaller batches

---

### 2. Documentation Requirements

Every phase deliverable must include:

#### A. Batch Documentation Report
- **What was built**: Clear list of all files created/modified
- **Why each tool/methodology was chosen**: Explicit rationale (see Section 3)
- **Issues encountered**: Problems discovered, root causes, resolutions
- **Acceptance criteria met**: Verification that batch objectives complete
- **Time taken**: Estimate for planning future phases
- **Dependencies introduced**: New packages, configurations, infrastructure changes

#### B. Command Log
- **Git commands**: All commits, branches, push operations
- **Bash/shell commands**: Setup, validation, build, test commands
- **dbt commands**: Parse, debug, test, run operations
- **Python commands**: Test execution, validation, package verification
- **Make commands**: Developer convenience command usage
- **Expected outputs**: What success looks like for each command

#### C. Deliverables Index
- Update README.md with links to phase documentation
- Organize by phase and batch for easy navigation
- Include quick-start commands

---

### 3. **"Why" Documentation Standard** ✨ [NEW]

For every significant tool, package, methodology, or architectural choice, document:

#### Required "Why" Documentation Elements

1. **The Choice**: What was selected (e.g., "dbt-databricks" vs alternative)
2. **Alternatives Considered**: What other options were available and why they weren't chosen
3. **Decision Rationale**: Business/technical reasons for the choice
4. **Trade-offs**: What's gained and what's sacrificed
5. **When to Reconsider**: Under what conditions would this choice change

#### Implementation: Where to Document "Why"

**In Batch Documentation Reports:**
```markdown
## Tool/Methodology Justifications

### Choice: dbt + Databricks (vs. Spark jobs only)
- **Why**: Enables version control, testing, lineage tracking, documentation
- **Alternatives**: Direct Spark jobs (simpler), Databricks workflows (limited versioning)
- **Trade-offs**: Additional dbt learning curve, but gains YAML-based governance
- **When to reconsider**: If organization mandates Python-only tooling or Spark native workflows

### Choice: Medallion Architecture (vs. Star schema)
- **Why**: Separates concerns (raw → trusted → semantic), enables data quality gates
- **Alternatives**: Star schema directly on raw data, Dimensional modeling
- **Trade-offs**: Requires 3 transformation layers, but enables data lineage and quality auditing
```

**In code/configuration comments:**
```python
# DECISION: Using lifelines (Kaplan-Meier) instead of SQL window functions
# Why: Survival analysis library provides censoring handling, confidence intervals
# Trade-off: External dependency, ~2min per execution (vs <10sec SQL)
# When reconsider: If monthly runs become too frequent for latency budget
```

**In Phase Documentation:**
```markdown
## Technology Stack Justification

### Python 3.10
- Chosen for: Stability, long-term support (until Oct 2026), package maturity
- Alternatives: Python 3.11, Python 3.12
- Trade-off: Not latest features, but proven stability in production

### Databricks + Delta Lake
- Chosen for: Unity Catalog governance, auto-scaling, ACID transactions
- Alternatives: Snowflake, BigQuery, Redshift
- Trade-off: Costs higher, but data lakehouse architecture enables both analytics and AI
```

**In Final Phase Report (adds to existing requirements):**

Include new section:
```markdown
## Technology & Methodology Decisions

[Table showing each decision, rationale, alternatives, trade-offs]

This section ensures future developers understand the reasoning behind 
current architecture and can make informed decisions about evolution.
```

---

### 4. Final Phase Deliverables

Each phase completion requires:

1. **Phase Batch Completion Summary** (750+ lines)
   - All batch details, issues resolved, lessons learned
   - "Why" rationale for all key decisions in this phase

2. **Phase Command Log** (500+ lines)
   - All commands executed with examples
   - Troubleshooting section referencing "why" choices

3. **Master Thesis Report** (academic format)
   - Methodology section explains "why" architecture chosen
   - Trade-offs section documents alternatives

4. **Executive Report** (non-technical)
   - Business rationale for "why" tools were selected
   - ROI and risk considerations

5. **Seminar/Defense Brief** (presentation outline)
   - Key "why" decisions as talking points
   - Anticipated questions about tool choices

6. **Interview Q&A Prep**
   - "Why did you choose dbt?" type questions anticipated
   - Sample answers referencing trade-offs

---

### 5. Implementation in Phase 1

**For Phase 1 (Bronze Layer Ingestion), apply "Why" documentation:**

**Example - Synthetic Data Generation:**
```markdown
## Phase 1 Batch 1: Synthetic Data Generator

### Choice: Using Faker for data generation
- **Why**: Realistic data distributions, low maintenance cost
- **Alternatives**: Hand-coded datasets (tedious), real production data (compliance risk)
- **Trade-off**: Not 100% realistic churn patterns, but 80/20 rule applies
- **When reconsider**: If we move to real production data after prototyping

### Choice: Intentional data quality defects
- **Why**: Validates data quality pipeline catches real-world issues
- **Alternatives**: Perfect synthetic data only (doesn't test quality checks)
- **Trade-off**: More complex data generation logic, but essential for validation
- **When reconsider**: Won't change - always need quality defects for testing
```

---

### 6. Git Commit Message Standard

Every commit must include "why" in the message:

```bash
# Good pattern:
git commit -m "Batch 3: Add dbt schema routing macro

DECISION RATIONALE:
- Using macro instead of explicit schemas: enables convention-based routing
- Routes stg_* → silver (trusted zone where data quality validated)
- Routes mart_* → gold (semantic layer ready for BI consumption)

TRADE-OFF: Requires macro understanding, but enables automatic layer separation
without hardcoding schemas in YAML"

# Avoid (insufficient rationale):
git commit -m "Add dbt macro"  # ❌ No "why"
```

---

### 7. Code Review Checklist

When reviewing pull requests, verify:
- [ ] Batch announcement included scope and objectives
- [ ] All git commits have descriptive messages with reasoning
- [ ] Tool/package choices documented with rationale
- [ ] Alternatives considered documented
- [ ] Trade-offs explicitly listed
- [ ] Batch completion report includes "why" justifications
- [ ] Command log includes examples with expected outputs
- [ ] README updated with phase/batch links
- [ ] Acceptance criteria verified with checkmarks

---

### 8. Error Recovery Protocol

If a batch fails:

1. **Diagnose**: Root cause analysis (not band-aid fixes)
2. **Document**: Create incident report showing:
   - What failed and why
   - What decision led to this failure
   - Whether "why" rationale was wrong
   - How to prevent recurrence
3. **Remediate**: Fix and re-test
4. **Learn**: Update standing instructions if pattern recurring

*Example: Recovery mode container failure analyzed root cause (Yarn GPG source) and updated Dockerfile pattern, preventing future similar issues.*

---

### 9. Phase Checkpoints

Before moving to next phase:

✅ Acceptance criteria 100% complete  
✅ All "why" justifications documented  
✅ Command log fully populated  
✅ Batch completion summary written  
✅ README updated  
✅ All commits pushed  
✅ No blocking issues in backlog  

---

## Current Standing Instructions Summary

| Requirement | Details | Status |
|-------------|---------|--------|
| Batch execution | Atomic commits, user approval, git push after each batch | Standard |
| Documentation per batch | Batch report + command log + deliverables index | Standard |
| **"Why" justification** | Rationale for all tool/methodology/package choices | **NEW - Phase 1+** |
| Final phase reports | Thesis, executive, beginner, seminar, interview Q&A | Standard |
| Problem resolution | Root cause analysis, not band-aids | Standard |
| Git commit messages | Descriptive with reasoning | Enhanced |

---

## Application Timeline

- **Phase 0**: Applied to Dockerfile hardening, dbt configuration, bootstrap scripts
- **Phase 1+**: Mandatory "why" documentation in all batch reports and code comments
- **All Future Phases**: Every tool selection, package addition, methodology choice requires documented rationale

---

**Next Phase**: [Phase 1: Bronze Layer Ingestion](docs/02_phase_by_phase_implementation_plan.md#phase-1-bronze-layer-ingestion)

Apply "Why" standard to all batch decisions starting with Batch 1 of Phase 1.
