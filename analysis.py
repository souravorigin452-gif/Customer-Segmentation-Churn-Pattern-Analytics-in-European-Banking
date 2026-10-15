"""Reusable preparation and KPI functions for the bank churn project."""
from __future__ import annotations

import pandas as pd

REQUIRED = {
    "CreditScore", "Geography", "Gender", "Age", "Tenure", "Balance",
    "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary", "Exited",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize expected headers while preserving unrelated columns."""
    out = df.copy()
    out.columns = [str(c).strip().replace(" ", "") for c in out.columns]
    aliases = {"Exited": ["Exited", "Churn", "Churned", "Exit"],
               "Geography": ["Geography", "Country", "Region"],
               "IsActiveMember": ["IsActiveMember", "ActiveMember", "IsActive"],
               "NumOfProducts": ["NumOfProducts", "Products", "ProductCount"]}
    for target, choices in aliases.items():
        if target not in out:
            found = next((c for c in choices if c in out), None)
            if found:
                out = out.rename(columns={found: target})
    return out


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate input and add the project's documented segmentation fields."""
    out = normalize_columns(df)
    missing = sorted(REQUIRED - set(out.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    for col in ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts", "EstimatedSalary"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in ["HasCrCard", "IsActiveMember", "Exited"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=list(REQUIRED)).copy()
    out = out[out["Exited"].isin([0, 1])]
    out["Exited"] = out["Exited"].astype(int)
    out["AgeGroup"] = pd.cut(out["Age"], [-1, 29, 45, 60, float("inf")],
                              labels=["Under 30", "30-45", "46-60", "61+"])
    out["CreditScoreBand"] = pd.cut(out["CreditScore"], [-float("inf"), 579, 669, float("inf")],
                                    labels=["Low (<580)", "Medium (580-669)", "High (670+)"])
    out["TenureGroup"] = pd.cut(out["Tenure"], [-1, 2, 6, 10],
                                labels=["New (0-2y)", "Mid-term (3-6y)", "Long-term (7-10y)"])
    positive = out.loc[out["Balance"] > 0, "Balance"]
    median_positive = positive.median() if not positive.empty else 0
    out["BalanceSegment"] = "Zero balance"
    out.loc[(out["Balance"] > 0) & (out["Balance"] <= median_positive), "BalanceSegment"] = "Lower positive balance"
    out.loc[out["Balance"] > median_positive, "BalanceSegment"] = "Higher positive balance"
    out["CustomerStatus"] = out["Exited"].map({0: "Retained", 1: "Churned"})
    return out


def overall_kpis(df: pd.DataFrame) -> dict:
    n = len(df)
    churners = int(df["Exited"].sum())
    high_balance_cutoff = df.loc[df["Balance"] > 0, "Balance"].quantile(.75)
    high_balance = df[df["Balance"] >= high_balance_cutoff] if pd.notna(high_balance_cutoff) else df.iloc[0:0]
    hb_churn_rate = float(high_balance["Exited"].mean()) if len(high_balance) else 0.0
    overall_rate = churners / n if n else 0.0
    inactive_rate = float(df.loc[df["IsActiveMember"] == 0, "Exited"].mean()) if (df["IsActiveMember"] == 0).any() else 0.0
    active_rate = float(df.loc[df["IsActiveMember"] == 1, "Exited"].mean()) if (df["IsActiveMember"] == 1).any() else 0.0
    return {
        "customers": n, "churners": churners, "retained": n - churners,
        "churn_rate": overall_rate, "high_balance_churn_rate": hb_churn_rate,
        "balance_exposure": float(df.loc[df["Exited"] == 1, "Balance"].sum()),
        "inactive_churn_rate": inactive_rate, "active_churn_rate": active_rate,
        "engagement_ratio": (inactive_rate / active_rate) if active_rate > 0 else None,
        "high_balance_cutoff": float(high_balance_cutoff) if pd.notna(high_balance_cutoff) else None,
    }


def segment_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in df:
        raise ValueError(f"Unknown segment: {dimension}")
    result = (df.groupby(dimension, observed=False)
              .agg(Customers=("Exited", "size"), Churners=("Exited", "sum"),
                   ChurnRate=("Exited", "mean"), MeanBalance=("Balance", "mean"),
                   ChurnedBalance=("Balance", lambda x: x[df.loc[x.index, "Exited"] == 1].sum()))
              .reset_index())
    result["ChurnShare"] = result["Churners"] / max(int(df["Exited"].sum()), 1)
    return result


def geography_risk(df: pd.DataFrame) -> pd.DataFrame:
    overall = float(df["Exited"].mean())
    result = segment_summary(df, "Geography")
    result["GeographicRiskIndex"] = result["ChurnRate"] / overall if overall else 0.0
    return result.sort_values("ChurnRate", ascending=False)

