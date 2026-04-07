select *
from {{ ref('fct_model_drift_baseline') }}
where drift_status <> 'within_baseline'
