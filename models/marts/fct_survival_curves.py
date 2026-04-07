def _manual_kaplan_meier(frame, duration_col, event_col):
    """Fallback Kaplan-Meier estimator when lifelines is unavailable."""

    timeline = sorted(set(float(x) for x in frame[duration_col].fillna(0).tolist()))
    survival = []
    current_survival = 1.0

    for t_value in timeline:
        at_risk = frame[frame[duration_col] >= t_value]
        events = frame[(frame[duration_col] == t_value) & (frame[event_col] == 1)]
        n_at_risk = max(len(at_risk), 1)
        n_events = len(events)
        current_survival *= 1.0 - (n_events / n_at_risk)
        survival.append((t_value, current_survival))

    return survival


def model(dbt, session):
    dbt.config(materialized="table")

    import pandas as pd

    features = dbt.ref("fct_gold_customer_features").toPandas()
    if features.empty:
        return session.createDataFrame(
            pd.DataFrame(
                columns=[
                    "cohort_label",
                    "timeline_month",
                    "survival_probability",
                    "sample_size",
                    "event_count",
                ]
            )
        )

    features = features.copy()
    features["cohort_label"] = features["max_discount_percent"].apply(
        lambda x: "high_discount_gt20" if float(x) > 20 else "low_discount_lt5" if float(x) < 5 else "other"
    )
    features = features[features["cohort_label"].isin(["high_discount_gt20", "low_discount_lt5"])].copy()
    features["event_observed"] = features["is_churned"].astype(int)
    features["duration_months"] = features["customer_tenure_months"].fillna(0).clip(lower=0)

    outputs = []
    for cohort_label, cohort_frame in features.groupby("cohort_label"):
        sample_size = len(cohort_frame)
        event_count = int(cohort_frame["event_observed"].sum())

        try:
            from lifelines import KaplanMeierFitter

            kmf = KaplanMeierFitter()
            kmf.fit(
                durations=cohort_frame["duration_months"],
                event_observed=cohort_frame["event_observed"],
                label=cohort_label,
            )
            curve = kmf.survival_function_.reset_index()
            curve.columns = ["timeline_month", "survival_probability"]
            curve["timeline_month"] = curve["timeline_month"].astype(float)
            curve["survival_probability"] = curve["survival_probability"].astype(float)
        except Exception:
            curve = pd.DataFrame(
                _manual_kaplan_meier(cohort_frame, "duration_months", "event_observed"),
                columns=["timeline_month", "survival_probability"],
            )

        curve["cohort_label"] = cohort_label
        curve["sample_size"] = sample_size
        curve["event_count"] = event_count
        outputs.append(curve)

    result = pd.concat(outputs, ignore_index=True)
    result = result[["cohort_label", "timeline_month", "survival_probability", "sample_size", "event_count"]]
    return session.createDataFrame(result)
