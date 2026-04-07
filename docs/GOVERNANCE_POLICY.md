# Governance Policy & Compliance Framework

## Overview

This document defines the governance policies, compliance requirements, and data management rules that apply across all layers of the predictive-ltv-survival-pipeline platform.

**Governance Principles**:
- **Transparency**: All data movements and transformations audited
- **Accountability**: Every action has an owner and timestamp
- **Control**: Access and modifications governed by role-based rules
- **Compliance**: Adherence to regulatory and business requirements
- **Stewardship**: Data treated as critical asset with documented ownership

---

## Data Classification Framework

### Classification Levels

**Level 1: Public**
- No sensitive information
- Can be shared externally
- Example: Product catalog, public analytics

**Level 2: Internal**
- Shared within organization
- Not for external distribution
- Example: Internal metrics, operational dashboards

**Level 3: Sensitive**
- Contains PII (Personally Identifiable Information)
- Restricted access required
- Example: Customer data, billing records

**Level 4: Confidential**
- Customer proprietary or regulatory-restricted
- Executive and specialist access only
- Example: Customer churn predictions (strategic decisions)

### Classification Rules by Layer

| Layer | Default | Rules | Examples |
|-------|---------|-------|----------|
| Bronze | Level 3 | All raw data assumed sensitive (PII likely) | raw_customers, raw_billing |
| Silver | Level 2-3 | Depends on content; mostly internal | trusted_customers (L3), trusted_billing (L3) |
| Gold | Level 2-1 | Aggregated/anonymized; lower sensitivity | fact_ltv (L2), agg_by_segment (L1) |
| Presentation | Level 1-2 | Dashboards generally public/internal | dashboards, reports |

### Implementation

**Each table tagged with classification**:
```yaml
# dbt model configuration
{{ config(
  meta={
    'data_classification': 'Level 3',
    'pii_columns': ['email', 'phone_number', 'address'],
    'retention_days': 365,
    'access_groups': ['data_analytics_team', 'cto_office']
  }
) }}

SELECT
  customer_id,
  email,           -- PII: email address
  phone_number,    -- PII: phone contact
  signup_date,
  -- ... other columns
FROM {{ source('bronze', 'raw_customers') }}
```

---

## Access Control Policy

### Role-Based Access Control (RBAC)

**Roles Defined**:

| Role | Bronze | Silver | Gold | Presentation | Abilities |
|------|--------|--------|------|--------------|-----------|
| **Data Engineer** | R/W | R/W | R | R | Ingest, transform, maintain pipelines |
| **Data Analyst** | - | R | R | R | Query, analyze, create reports |
| **Analytics Engineer** | R | R/W | R/W | R | Build metrics, maintain dbt |
| **BI Specialist** | - | - | R | R/W | Create dashboards, publish reports |
| **Data Scientist** | R | R | R/W | R | Build models, experiment |
| **Manager** | - | - | R | R | View reports, access insights |
| **Executive** | - | - | - | R | View dashboards only |
| **CTO/Chief Data** | R | R | R | R | Override access, audits |

**Legend**: R = Read, W = Write, - = No access

### Layer-Specific Access Rules

**Bronze Layer**:
```
✅ Read-Write: Data Engineers, CTO
⚠️  Read-Only: Analytics Engineers, Data Scientists
❌ No access: Analysts, BI, Managers (PII exposure risk)
```

**Silver Layer**:
```
✅ Read-Write: Data Engineers, Analytics Engineers
✅ Read-Only: Data Analysts, Data Scientists, BI
⚠️  Limited: Managers (approved tables only)
❌ No access: Executives (raw business model exposure)
```

**Gold Layer**:
```
✅ Read-Write: Analytics Engineers, Data Scientists
✅ Read-Only: Data Analysts, BI, Managers, Executives
❌ No access: (All needed access roles included)
```

**Presentation Layer**:
```
✅ Read: Everyone (based on dashboard access)
✅ Edit: BI Specialists
✅ Publish: BI Specialists + Analytics Managers
```

### Access Provisioning Process

```
1. Request
   └─ Employee: Request access via ITHelp ticket

2. Approval
   └─ Manager + Data Owner: Review need-to-know basis
              └─ Approve or deny with reason

3. Provisioning
   └─ Data Admin: Add to appropriate group
              └─ Verify access within 24 hours

4. Onboarding
   └─ Data Owner: Brief employee on data sensitivity
              └─ Document training completion

5. Audit
   └─ Monthly: List all access holders
              └─ Manager confirms each person still needs it

6. Revocation
   └─ Off-boarding: Remove access immediately
              └─ Record in audit log
```

### Access Request Template

```
SUBJECT: Access Request - [Employee Name] to [Table/Layer]

NAME: John Smith
ROLE: Data Analyst
TEAM: Growth Analytics
MANAGER: Alice Chen

REQUESTING ACCESS TO:
  - Silver layer: trusted_customers table
  - Gold layer: agg_ltv_by_segment table

BUSINESS JUSTIFICATION:
  Need to analyze customer LTV trends for Q2 planning

DATA CLASSIFICATION:
  - trusted_customers: Level 3 (PII)
  - agg_ltv_by_segment: Level 2 (Internal)

TIME FRAME:
  From: 2026-04-15
  To: 2026-12-31 (or indefinite)

MANAGER APPROVAL:
  Alice Chen: ✅ Approved (2026-04-10)

DATA OWNER APPROVAL:
  Analytics Lead: ✅ Approved (2026-04-10)

ACCESS GRANTED:
  2026-04-11 by: data-admin-team
  Added to: data_analysts_group
```

---

## Audit Trail & Compliance

### Audit Log Schema

**Every data access logged**:

```sql
CREATE TABLE governance.audit_log (
  audit_id BIGINT,
  timestamp TIMESTAMP,
  
  -- Who
  principal_id VARCHAR,      -- User/service account
  principal_type VARCHAR,    -- 'user', 'service', 'system'
  
  -- What
  action VARCHAR,            -- 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP'
  object_type VARCHAR,       -- 'table', 'schema', 'catalog'
  object_name VARCHAR,       -- e.g., 'gold.fact_customer_ltv'
  
  -- How
  query_hash VARCHAR,        -- SHA256(query) for uniqueness
  ip_address VARCHAR,
  connection_type VARCHAR,   -- 'jupyter', 'sql_editor', 'app', 'api'
  
  -- Why
  reason VARCHAR,            -- Job name, manually provided reason
  request_id VARCHAR,        -- Trace to request
  
  -- Result
  row_count BIGINT,          -- Rows returned/affected
  success BOOLEAN,
  error_message VARCHAR,
  execution_time_ms INT
);
```

### Audit Retention

```
Access logs: 90 days hot, 2 years archive
  └─ Quick queries on recent activity
  └─ Compliance snapshot available 2 years back

DDL (schema changes): 3 years permanent
  └─ Regulatory requirement (SOX, GDPR)
  └─ Track all model changes for compliance

Failed authentication: 1 year
  └─ Security incident investigation
```

### Compliance Reports

**Automated Monthly Report**:

```
PREDICTIVE-LTV COMPLIANCE REPORT
Month: March 2026
Generated: 2026-04-01

1. ACCESS SUMMARY
   ├─ Total unique users: 42
   ├─ New access provisioned: 5
   └─ Access revoked: 2

2. AUDIT LOG STATISTICS
   ├─ Total queries: 125,432
   ├─ Failed authentications: 3
   ├─ Unauthorized access attempts: 0
   └─ Admin overrides: 1 (CTO emergency access)

3. DATA QUALITY EVENTS
   ├─ SLA breaches: 0
   ├─ Data quality failures: 2
   │  ├─ Null percentage spike in raw_customers
   │  └─ Table join failure in silver transformation
   └─ All resolved with RCA + fix

4. SCHEMA CHANGES
   ├─ Tables added: 1 (gold.agg_ltv_by_segment)
   ├─ Tables modified: 3
   └─ Tables dropped: 0

5. COMPLIANCE STATUS
   ├─ GDPR: ✅ All data classified, access controlled
   ├─ SOX: ✅ All transforms audited, lineage traced
   ├─ Internal policy: ✅ All access approved
   └─ Overall: ✅ COMPLIANT
```

---

## Data Retention & Archival

### Retention Policy by Layer

**Bronze Layer** (Raw ingestion):
```
Retention: 12 months (rolling window)
Archival: Move to cold storage after 180 days
Deletion: Automatic after 12 months
Rationale: Raw data rarely needed, expensive to store
```

**Silver Layer** (Trusted transforms):
```
Retention: 24 months (full history)
Archival: No archival (frequently accessed)
Deletion: Manual only (with business justification)
Rationale: May need to re-query historical transformations
```

**Gold Layer** (Metrics):
```
Retention: Indefinite (critical business data)
Archival: Copy to cold storage after 3 years
Deletion: Never automatic (executive decision required)
Rationale: Metrics are immutable source of truth for business
```

**Audit/Governance Logs**:
```
Retention: 3 years (regulatory requirement)
Deletion: Automatic after 3 years
Compliance: SOX, GDPR, internal policy
```

### PII Handling & Retention

**For all tables with PII marked**:

```
Definitions:
  - PII: email, phone, address, SSN, name, ID numbers
  - sensitive_pii: SSN, full credit card, passport

Rules:
  1. Encryption: All PII encrypted at rest (AES-256)
  2. Masking: PII masked in dev/test environments
  3. Access: Only authorized roles can see unmasked PII
  4. Retention: Delete per regulatory timeline:
      - GDPR (EU data): 30 days after account deletion
      - CCPA (CA data): 45 days after deletion request
      - Default: 12 months after last activity
```

**Example: Customer Data Deletion Request**

```
REQUEST: Customer John Doe (ID: 12345) requests data deletion

PROCESS:
1. Verify identity (confirm email + phone match)
2. Log deletion request with timestamp
3. Flag customer record as deleted
4. Schedule deletion for 30 days (GDPR grace period)
5. During grace period:
   - Queries still return deleted records (soft delete)
   - Email alerts: "Deletion scheduled for 2026-05-15"
6. After 30 days:
   - Hard delete: Remove all PII from all layers
     DELETE FROM bronze.raw_customers WHERE customer_id = 12345
     DELETE FROM silver.trusted_customers WHERE customer_id = 12345
     (cascades to all dependent tables)
   - Audit log: Record permanent deletion
7. Verify deletion:
   SELECT * FROM bronze.raw_customers WHERE customer_id = 12345
   Result: (no rows) ✅
```

---

## Change Control Process

### Change Categories

**Category A: Low-Risk** (Fast-track)
- Time to approve: ≤1 hour
- Example: Bug fix query in dbt model

**Category B: Medium-Risk** (Standard)
- Time to approve: ≤1 business day
- Example: New metric in Gold layer

**Category C: High-Risk** (Review)
- Time to approve: ≤3 business days
- Example: Schema change to Silver table

**Category D: Critical** (Executive)
- Time to approve: ≤1 week
- Example: Access policy change, retention policy update

### Category Decision Tree

```
┌─ Is this changing schema or structure?
│  ├─ YES → Category B or C (depends on impact)
│  └─ NO → Continue
│
├─ Affects >100K rows?
│  ├─ YES → Category B (medium caution)
│  └─ NO → Continue
│
├─ Changes retention/compliance rules?
│  ├─ YES → Category D (executive review)
│  └─ NO → Continue
│
├─ Is this a bug fix?
│  ├─ YES → Category A (fast-track)
│  └─ NO → Category B (standard)
```

### Change Request Template

```
TITLE: Fix null value handling in churn_probability column

CATEGORY: A (Low-risk bug fix)

DESCRIPTION:
  Model `gold.fact_churn_predictions` has null values for 0.3% of rows.
  Root cause: missing left join condition in silver model.
  Fix: Add `AND churn_data.customer_id IS NOT NULL`.

IMPACT ANALYSIS:
  ├─ Upstream changes: None (silver model unchanged)
  ├─ Downstream changes: None
  ├─ SLA impact: None (still computed by 10am)
  └─ Data quality: Improved (removes nulls)

RISKS:
  ├─ Low: Bug fix only, no schema changes
  ├─ Rollback plan: Simple revert to previous version
  └─ Testing: All existing unit tests pass

TESTING:
  ✅ Local: dbt test gold.fact_churn_predictions (all pass)
  ✅ Staging: Ran against 1M rows (5sec, no errors)
  ✅ SQL: SELECT COUNT(*) FROM gold.fact_churn_predictions
         WHERE churn_probability IS NULL
         Result: 0 (previously 3,000)

APPROVALS:
  ├─ Author: Sarah (Analytics Eng) → Submitted 2026-04-10
  ├─ Reviewer: James (Analytics Eng Lead) → ✅ 2026-04-10
  └─ Auto-approved in 1 hour (Category A)

DEPLOYMENT:
  ├─ Target: master branch
  ├─ Deployment time: 2026-04-10 09:00 UTC
  ├─ Who: CI/CD pipeline (GitHub Actions)
  └─ Validation: dbt test gold.fact_churn_predictions + data quality checks
```

### Change Review Checklist

**For Category B+ changes**:

```
☑ Code Review
  └─ SQL logic reviewed by peer
  └─ No performance regressions detected

☑ Testing
  └─ All unit tests passing
  └─ Integration tests on sample data pass
  └─ Rollback procedure tested

☑ Documentation
  └─ Model description updated
  └─ Assumptions documented
  └─ Breaking changes (if any) highlighted

☑ Impact Analysis
  └─ Downstream models identified
  └─ SLA impact assessed
  └─ Schema changes (if any) reviewed

☑ Security & Access
  └─ No new access grants required?
  └─ Or approved by data owner?
  └─ PII handling correct?

☑ Approval
  └─ Domain owner approved
  └─ On-call engineer notified
  └─ Scheduled deployment time confirmed
```

---

## Compliance Standards

### Regulatory Compliance

**GDPR (General Data Protection Regulation)** - EU customers

```
Requirements:
  1. Right to be forgotten: Customer can request data deletion
     ✅ Implemented: Deletion process in this policy
  
  2. Data portability: Customer can request export of their data
     ✅ Implemented: Query bronze.raw_customers WHERE customer_id = ?
  
  3. Privacy by design: Minimize data collection
     ✅ Implemented: Keep only necessary fields in Silver/Gold
  
  4. Consent management: Track data usage consent
     ✅ To implement: governance.consent_log table
  
  5. Encryption: All PII encrypted
     ✅ Implemented: AES-256 at rest
```

**CCPA (California Consumer Privacy Act)** - CA customers

```
Requirements:
  1. Disclosure: Tell customers what data collected
     ✅ Implemented: Data dictionary in dbt docs
  
  2. Deletion: Customer can request deletion within 45 days
     ✅ Implemented: Same process as GDPR (more lenient)
  
  3. Opt-out: Customer can opt-out of data sale
     ✅ To implement: governance.opt_out_customers table
  
  4. Non-discrimination: Don't penalize users for exercising rights
     ✅ Audit: Check for differential pricing post-deletion
```

**SOX (Sarbanes-Oxley Act)** - Public company financial reporting

```
Requirements:
  1. Audit trails: All financial data access logged
     ✅ Implemented: audit_log table (3-year retention)
  
  2. Change control: All changes approved + logged
     ✅ Implemented: Change control process above
  
  3. Segregation of duties: Different roles for different actions
     ✅ Implemented: RBAC policy above
  
  4. Documentation: All processes documented
     ✅ Implemented: This policy document
  
  5. Testing: Controls tested regularly
     ✅ Quarterly: Governance audit procedure (see below)
```

### Internal Policy Compliance

**Data Stewardship**:
```
✅ Every table has documented owner
✅ Owner is accountable for data quality
✅ Owner must approve access requests
✅ Owner escalates SLA breaches
```

**Security**:
```
✅ All access logged
✅ Failed authentication attempts logged
✅ Quarterly access review
✅ Immediate revocation on termination
```

**Performance**:
```
✅ Query resource limits enforced
✅ No individual can consume >50% cluster
✅ Long-running queries auto-cancelled
✅ Resource throttling documented
```

---

## Governance Audit Procedure

### Quarterly Audit (Every 90 Days)

**Step 1: Access Review** (1 week before quarter end)
```bash
# Export all active access
SELECT 
  user_id, role, tables_accessible, last_access_date
FROM governance.user_access
WHERE is_active = TRUE
ORDER BY role, user_id

# Send to each manager:
"Please review access for your team. Confirm each person still needs it.
Respond by EOD Friday."

# Follow up on non-responders (emergency removal after 2 weeks)
```

**Step 2: Audit Log Review** (Following week)
```sql
-- Anomalies: Unusual access patterns
SELECT 
  user_id, action, object_name, COUNT(*) as frequency
FROM governance.audit_log
WHERE DATE(timestamp) >= '2026-01-01'
  AND action IN ('DELETE', 'UPDATE')
GROUP BY user_id, action, object_name
HAVING COUNT(*) > 100  -- Threshold
ORDER BY frequency DESC
```

**Step 3: Compliance Verification** (Week 3)
```
Checklist:
  ☑ All Bronze tables have retention policy
  ☑ All sensitive tables encrypted
  ☑ No access to Bronze for business users
  ☑ Change log has approval for all changes
  ☑ No failed authentication spikes
  ☑ All PII handled per policy
  ☑ Schema changes documented
  ☑ SLA tracking operational
```

**Step 4: Report & Remediation** (Week 4)
```
Governance Audit Report
Quarter: Q1 2026
Date: 2026-03-31

Issues Found:
  1. ⚠️  Medium: User X has access to Bronze (not authorized)
     → Action: Revoke access immediately
  
  2. ⚠️  Low: Schema change Y not documented
     → Action: Add documentation retroactively

  3. ✅ No high-severity issues

Remediation Due: 2026-04-14
```

---

## Governance Enforcement

### Automated Enforcement

```python
# scripts/governance_enforcement.py

def enforce_governance_policies():
    """Run hourly to ensure compliance"""
    
    issues = []
    
    # 1. Check unauthorized access
    unauthorized = get_audit_log_errors(
        'Failed authentication attempts > 5 in 1 hour', 
        hours=1
    )
    if len(unauthorized) > 0:
        issues.append('unauthorized_access', unauthorized)
    
    # 2. Check access violations
    bronze_access = get_audit_log(
        "action='SELECT' AND object LIKE 'bronze.%' AND user_role != 'data_engineer'",
        hours=1
    )
    if len(bronze_access) > 0:
        issues.append('rbac_violation', bronze_access)
    
    # 3. Check query resource limits
    large_queries = get_slow_queries(threshold_seconds=300)
    if len(large_queries) > 0:
        issues.append('resource_limit', large_queries)
    
    # 4. Check data retention
    old_bronze = check_table_age('bronze.*', days_threshold=365)
    if len(old_bronze) > 0:
        issues.append('retention_violation', old_bronze)
    
    # Alert on any issues
    for issue_type, details in issues:
        send_alert(
            severity='P1' if issue_type.startswith('unauthorized') else 'P2',
            message=f'Governance violation: {issue_type}',
            details=details
        )
```

### Manual Enforcement (Governance Review)

```
Bi-weekly governance sync (Wednesdays 10am):

Attendees:
  - Data Owner
  - Engineering Lead
  - Security/Compliance
  - CTO (monthly)

Agenda:
  1. Review audit alerts (5 min)
  2. Discuss access requests pending (10 min)
  3. Review upcoming changes (10 min)
  4. Escalate any issues (10 min)

Decisions:
  - Access approvals/denials
  - Policy exceptions (rare)
  - Urgent security issues
```

---

## Success Criteria

✅ Data classification framework defined  
✅ Role-based access control implemented  
✅ Audit logging and compliance tracking operational  
✅ Change control process established  
✅ Retention policies defined per layer  
✅ Regulatory compliance mapped (GDPR, CCPA, SOX)  
✅ Governance enforcement automated  
✅ Ready for operational deployment

