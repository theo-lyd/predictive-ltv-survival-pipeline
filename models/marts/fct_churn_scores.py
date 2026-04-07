def model(dbt, session):
    dbt.config(materialized="table")

    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    features = dbt.ref("fct_gold_customer_features").toPandas()
    if features.empty:
        return session.createDataFrame(
            pd.DataFrame(
                columns=[
                    "customer_id",
                    "churn_probability",
                    "risk_bucket",
                    "is_active_customer",
                    "model_version",
                    "model_run_at",
                ]
            )
        )

    features = features.copy()
    features["target_churned"] = features["state_transition"].isin(
        ["active_to_churn", "discounted_to_churn"]
    ).astype(int)
    features["is_active_customer"] = (~features["is_churned"]).astype(int)

    model_columns = [
        "customer_tenure_months",
        "monthly_recurring_revenue",
        "discount_intensity_index",
        "contributed_margin_monthly",
        "invoice_count",
        "avg_invoice_amount",
        "max_discount_percent",
    ]

    train_frame = features[model_columns].fillna(0)
    target = features["target_churned"]

    classifier = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        min_samples_leaf=5,
        class_weight="balanced",
    )
    classifier.fit(train_frame, target)

    features["churn_probability"] = classifier.predict_proba(train_frame)[:, 1]
    features["risk_bucket"] = pd.cut(
        features["churn_probability"],
        bins=[-1, 0.33, 0.66, 1.0],
        labels=["low", "medium", "high"],
    ).astype(str)

    result = features[["customer_id", "churn_probability", "risk_bucket", "is_active_customer"]].copy()
    result["model_version"] = "rf_v1"
    result["model_run_at"] = pd.Timestamp.utcnow().isoformat()

    return session.createDataFrame(result)
