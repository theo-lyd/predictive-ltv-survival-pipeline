# Data Ownership & Responsibility Matrix

## Overview

This document defines data ownership, SLA responsibilities, and escalation paths for the predictive-ltv-survival-pipeline project. Clear ownership ensures accountability and enables rapid incident response.

---

## Ownership Pyramid

```
                    Project Owner
                  (Strategic decisions)
                         ▲
                         │
                    System Owners
              (ArchitectureLayout decisions)
                    ▲         ▲
                    │         │
          Layer Owners    Tool Owners
      (Data quality,      (CI/CD,
       correctness)     infrastructure)
             │                 │
             ▼                 ▼
        Data Engineers    DevOps / SRE
```

---

## Primary Ownership Assignments

### Project Level

| Role | Name | Responsibilities | Escalation |
|------|------|-----------------|------------|
| Project Owner | `@theo-lyd` | Overall strategy, roadmap, approval gates | CEO/VP |
| Analytics Owner | `@analytics-lead` | KPI definitions, metric correctness, stakeholder alignment | Project Owner |
| Platform Owner | `@platform-owner` | Infrastructure, CI/CD, security, compliance | Project Owner |

### Layer Ownership (Medallion Architecture)

#### Bronze Layer (Raw Data)
| Component | Owner | On-Call | Alternate |
|-----------|-------|---------|-----------|
| Churn ingestion | Data Engineer (Bronze) | 24h rotation | Senior engineer |
| Billing ingestion | Data Engineer (Bronze) | 24h rotation | Senior engineer |
| Promotions ingestion | Data Engineer (Bronze) | 24h rotation | Senior engineer |
| **SLA**: Data available by 8am UTC daily | — | — | — |
| **Escalation**: If delayed 1h → page on-call | — | — | — |

**Responsibilities**:
- ✅ Validate source data freshness
- ✅ Monitor ingestion for errors/gaps
- ✅ Document schema changes
- ✅ Respond to upstream connector issues
- ✅ Coordinate with source systems team for outages

---

#### Silver Layer (Trusted Data)
| Component | Owner | On-Call | Alternate |
|-----------|-------|---------|-----------|
| Quality checks (GE) | Data Quality Engineer | Weekdays 9-5 | Data Manager |
| Schema enforcement | Data Quality Engineer | Weekdays 9-5 | Data Manager |
| Data reconciliation | Data Manager | Weekdays 9-5 | Senior analyst |
| **SLA**: Issues resolved within 24h | — | — | — |
| **Escalation**: If lasting >4h during business hours → escalate | — | — | — |

**Responsibilities**:
- ✅ Run Great Expectations checkpoints
- ✅ Investigate quality failures
- ✅ Document schema and lineage
- ✅ Coordinate fixes with source layer
- ✅ Report freshness metrics

---

#### Gold Layer (Semantic Layer)
| Component | Owner | On-Call | Alternate |
|-----------|-------|---------|-----------|
| LTV metrics | Analytics Engineer (Premium) | 24h rotation | Senior analyst |
| Churn metrics | Analytics Engineer (Premium) | 24h rotation | Senior analyst |
| NRR metrics | Analytics Engineer (Premium) | 24h rotation | Senior analyst |
| Discount impact models | Economist / Analyst | Weekdays 9-5 | Senior analyst |
| **SLA**: Metrics correct by 10am UTC daily | — | — | — |
| **Escalation**: If metric wrong >2h → alert stakeholders, fix immediately | — | — | — |

**Responsibilities**:
- ✅ Ensure metric accuracy (test coverage >90%)
- ✅ Document business logic clearly
- ✅ Validate against external benchmarks
- ✅ Respond to metric discrepancy reports
- ✅ Own metric version history

---

#### Presentation Layer (Dashboards)
| Component | Owner | On-Call | Alternate |
|-----------|-------|---------|-----------|
| Executive Dashboard | Analytics Lead | Weekdays 9-5 | Business Analyst |
| Role-specific views | Analytics Lead | Weekdays 9-5 | Business Analyst |
| AI Narratives | AI/ML Engineer | Weekdays 9-5 | Data Scientist |
| **SLA**: Dashboards load correctly by 10:30am UTC | — | — | — |
| **Escalation**: If dashboard broken >30min → page whoever is available | — | — | — |

**Responsibilities**:
- ✅ Dashboard accessibility and styling
- ✅ Narrative artifact generation
- ✅ Streamlit app stability
- ✅ Respond to user feedback
- ✅ Document features for users

---

### Tool/Infrastructure Ownership

#### CI/CD Pipeline
| Component | Owner | Escalation | SLA |
|-----------|-------|-----------|-----|
| GitHub Actions | Platform/DevOps Engineer | If workflow broken: within 30min | <0.5% failure rate |
| dbt execution | Data Engineer | If parse fails: within 1h | All models valid |
| Test suite | QA/Data Engineer | If coverage drops: within sprint | ≥80% coverage |
| Artiwork deployment | Platform/DevOps | If artifact missing: within 1h | 100% artifact generation |

**Responsibilities**:
- ✅ Maintain workflow reliability
- ✅ Monitor job performance
- ✅ Fix flaky tests
- ✅ Update dependencies (Dependabot PRs)
- ✅ Document CI/CD decisions

---

#### Data Quality & Validation
| Component | Owner | Escalation | SLA |
|-----------|-------|-----------|-----|
| Great Expectations | Data Quality Engineer | If checkpoint fails unexpectedly: within 2h | 0 false negatives |
| dbt tests | Analytics Engineer | If test coverage drops: within sprint | Comprehensive coverage |
| Schema validation | Data Architect | If schema change missed: within 4h | 100% schema validation |

---

#### Dependencies & Security
| Component | Owner | Escalation | SLA |
|-----------|-------|-----------|-----|
| Python packages | Platform/DevOps | If vulnerability found: within 24h | <24h response to CVEs |
| dbt packages | Data Engineer | If breaking change: coordinate release | Stable versions locked |
| GitHub Actions actions | Platform/DevOps | If action broken: within 24h | Active action maintenance |

---

## Incident Response & Escalation

### Incident Severity Levels

#### P1: Critical (Metric Wrong or Unavailable)
**Examples**:
- NRR metrics showing incorrect values
- Dashboard completely broken
- Data freshness SLA missed by >2 hours

**Response**:
```
1. Page on-call owner (5 min max response)
2. Declare incident in #data-urgency Slack
3. Form war room: owner + stakeholders
4. Establish root cause within 15 min
5. Deploy fix or rollback within 30 min
6. Post-mortem within 24h
```

**Escalation Path**:
```
Data Engineer
    ↓
Analytics Lead (if metric)
    ↓
Platform Owner (if infrastructure)
    ↓
Project Owner (if strategic impact)
```

#### P2: High (Data Quality Issue)
**Examples**:
- Great Expectations check failing
- Test coverage dropped below 80%
- Dependency vulnerability found

**Response**:
```
1. Alert owner within 24 hours
2. Create ticket with details
3. Schedule fix for next sprint
4. Communicate timeline to users
```

**Escalation Path**:
```
Data Quality Engineer
    ↓
Analytics Lead (if impact to metrics)
    ↓
Platform Owner (if system-wide issue)
```

#### P3: Medium (Documentation or Style)
**Examples**:
- Outdated docstring
- Missing lineage documentation
- Code style issues

**Response**:
```
1. Document in backlog
2. Include in next batch
3. No urgent action needed
```

---

## Ownership Rotation & Backups

### On-Call Rotation (24h shifts)

**Bronze Layer**:
- Weekly rotation Sun-Sat
- 9am-9am timezone
- Paid on-call for critical incidents

**Gold Layer (Metrics)**:
- Weekly rotation Sun-Sat
- 8am-5pm local time (overlaps with business hours)
- Escalate to backup after hours

**Presentation Layer**:
- Business hours only (9am-5pm local)
- No formal rotation, respond to urgent tickets

### Backup Assignments

| Primary Owner | Backup 1 | Backup 2 |
|---------------|----------|----------|
| Data Engineer (Bronze) | Senior Engineer | Analytics Lead |
| Data Quality Engineer | Data Manager | Data Architect |
| Analytics Engineer | Senior Analyst | Analytics Lead |
| AI/ML Engineer | Data Scientist | Analytics Lead |
| DevOps Engineer | Platform Owner | Senior DevOps |

### Escalation to Backup

**Trigger**: Primary owner unavailable for >15 minutes on P1 incident

**Process**:
1. Incident commander pages Backup 1
2. If no response after 5 min → pages Backup 2
3. If no response → pages Project Owner

---

## Data Lineage Responsibility

### Lineage Documentation

Each data asset owner responsible for documenting lineage:

```
Raw Churn Data (Bronze)
    ↓ (owned by: Bronze Data Engineer)
Churn Quality Check (Silver)
    ↓ (owned by: Data Quality Engineer)
Survival Tables (Gold)
    ↓ (owned by: Analytics Engineer)
Churn Dashboard (Presentation)
    ↓ (owned by: Analytics Lead)
Executive Dashboard Panel
```

### Lineage Tracking Tooling

**Current**: Manual documentation (this file)

**Future** (Phase 6 B3): Unity Catalog + dbt exposures for automated lineage

```yaml
# dbt_project.yml
exposures:
  - name: Executive Dashboard
    type: dashboard
    owner: @analytics-lead
    depends_on:
      - ref('fct_customer_ltv')
      - ref('fct_churn_prediction')
    url: https://streamlit.internal.company.com
    maturity: production
```

---

## Metric Ownership & Correctness

### KPI Definitions

| Metric | Definition | Owner | Expected Range | Refresh |
|--------|-----------|-------|-----------------|---------|
| **NRR** | (MRR_end - Churn + Expansion) / MRR_start | @analytics-engineer | 100-130% | Daily 8am |
| **LTV** | Avg(10-year customer value) | @analytics-engineer | $10k-$50k | Daily 8am |
| **CAC** | Sales spend / New customers | @finance-analyst | $1k-$5k | Daily 10am |
| **Churn Rate** | (Churned / Active customers) | @analytics-engineer | 2-8% | Daily 8am |
| **Discount Efficiency** | Impact per $ spent | @economist | >1.2x | Weekly |

### Correctness Validation

**Owner responsibility**:
- ✅ Unit tests for business logic (>90% coverage)
- ✅ Integration tests against known data samples
- ✅ Monthly manual validation against external sources
- ✅ Document edge cases and exclusions
- ✅ Track metric version history

**Example - NRR Metric**:
```python
def test_nrr_calculation():
    """NRR owned by @analytics-engineer - must pass"""
    sample_data = load_known_good_sample()
    result = compute_nrr(sample_data)
    
    assert result == 1.15  # Expected 15% NRR
    assert result > 1.0    # Always positive (by definition)
    assert math.isfinite(result)  # No NaN/Inf
    
    # Edge cases:
    assert compute_nrr(empty_data) == 0  # No customers
    assert compute_nrr(no_churn_data) > 1  # Pure expansion
```

---

## SLA Definitions by Owner

### Bronze Layer SLA

**Owner**: Data Engineer (Bronze)

| Metric | Target | Impact if Missed |
|--------|--------|-----------------|
| Data available by | 8:00 AM UTC | Manual re-ingest, delay downstream |
| Data freshness | <24h old | Stale metrics |
| Ingestion accuracy | 100% | Data corruption, audit trail gap |
| Response time to alert | <1h | Cascading failures downstream |

---

### Silver Layer SLA

**Owner**: Data Quality Engineer

| Metric | Target | Impact if Missed |
|--------|--------|-----------------|
| All checks passed by | 9:00 AM UTC | Silver metrics not available |
| Investigation time (P1) | <1h | Gold layer blocked |
| Response to schema change | <4h | Silent data corruption |
| Coverage (Great Expectations) | 100% of columns | Undetected quality issues |

---

### Gold Layer SLA

**Owner**: Analytics Engineer

| Metric | Target | Impact if Missed |
|--------|--------|-----------------|
| Metrics available by | 10:00 AM UTC | Dashboards show stale data |
| Correctness (test passing) | 100% tests | Stakeholders see wrong numbers |
| Metric accuracy (vs manual check) | 100% | Loss of trust in data |
| Response time to error report | <30min | Error compounds through day |

---

### Presentation Layer SLA

**Owner**: Analytics Lead

| Metric | Target | Impact if Missed |
|--------|--------|-----------------|
| Dashboard load time | <5s | Users abandon page |
| Dashboard uptime | 99.5% | Stakeholders can't access metrics |
| Narrative freshness | <2h old | Insights outdated |
| Response to bug report | <1h during business hours | User frustration, lost trust |

---

## Responsibility Transfer & Onboarding

### When Ownership Changes

**Trigger**: Employee departure, role change, team restructuring

**Process** (2-week transition):
```
Week 1:
  - New owner shadows current owner
  - Review all documentation
  - Understand on-call schedule and escalation
  - Test incident response procedures

Week 2:
  - New owner takes all tickets
  - Current owner available for questions
  - Dry-run on-call shift with backup
  - Sign-off on readiness

Week 3+:
  - New owner officially on-call
  - Previous owner remains backup for first month
```

### Onboarding Checklist

- [ ] Access to all necessary systems (GitHub, Databricks, Slack)
- [ ] Added to on-call rotation
- [ ] Trained on incident response procedures
- [ ] Copy of runbooks and escalation paths
- [ ] Introduced to team Slack channels
- [ ] Knows who to ask for help (backup owners)

---

## Accountability Metrics

### Monthly Review (Last Friday of month)

**Reviewed by**: Project Owner + affected team leads

**Metrics**:
- Incident count (P1, P2, P3)
- MTTR (Mean Time To Resolve) by owner
- SLA compliance % by layer
- Coverage (test, documentation, monitoring)
- On-call satisfaction (survey)

**Actions**:
- Escalation if SLA consistently missed
- Training if skill gaps identified
- Rotation change if on-call burnout detected
- Process improvement if systemic issues found

---

## Next Steps & Timeline

| Phase | Actions | Status |
|-------|---------|--------|
| **Phase 6 B2** | Document data ownership (this file) | ✅ Now |
| **Phase 6 B3** | Populate with actual team members | ⏳ Next |
| **Phase 6 B3** | Implement Unity Catalog lineage | ⏳ Next |
| **Phase 6 B4** | Set up SLA monitoring & alerts | ⏳ Next |
| **Phase 7** | Add automated incident escalation | 📋 Future |

---

## References

- [RACI Matrix](https://en.wikipedia.org/wiki/Responsibility_assignment_matrix) - Responsible/Accountable/Consulted/Informed
- [Site Reliability Engineering](https://sre.google/books/) - Google SRE best practices
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices) - Model ownership
- [Data Mesh Pattern](https://martinfowler.com/articles/data-mesh.html) - Domain ownership concepts
