"""Generate a clearly synthetic dataset for demonstrating the app offline."""
import numpy as np
import pandas as pd

SEED = 20261013


def main():
    rng = np.random.default_rng(SEED)
    n = 10_000
    geography = rng.choice(["France", "Germany", "Spain"], n, p=[.50, .25, .25])
    gender = rng.choice(["Female", "Male"], n, p=[.46, .54])
    age = np.clip(np.rint(rng.normal(39, 10, n)), 18, 92).astype(int)
    tenure = rng.integers(0, 11, n)
    score = np.clip(np.rint(rng.normal(650, 95, n)), 350, 850).astype(int)
    balance = np.where(rng.random(n) < .36, 0, np.maximum(0, rng.normal(105_000, 60_000, n))).round(2)
    products = rng.choice([1, 2, 3, 4], n, p=[.51, .46, .025, .005])
    active = rng.binomial(1, .52, n)
    has_card = rng.binomial(1, .70, n)
    salary = np.round(rng.uniform(12_000, 200_000, n), 2)
    geo_effect = np.select([geography == "Germany", geography == "Spain"], [.48, -.15], default=0)
    logit = -2.25 + .045 * (age - 40) + geo_effect + .62 * (active == 0) \
            + .70 * (products == 1) + 1.35 * (products >= 3) \
            + .45 * (balance == 0) + .12 * (tenure <= 1) \
            + .16 * (score < 550) + .08 * (gender == "Female")
    probability = 1 / (1 + np.exp(-logit))
    exited = rng.binomial(1, probability)
    df = pd.DataFrame({
        "RowNumber": np.arange(1, n + 1), "CustomerId": np.arange(100000, 100000 + n),
        "Surname": [f"Demo{i:05d}" for i in range(n)], "CreditScore": score,
        "Geography": geography, "Gender": gender, "Age": age, "Tenure": tenure,
        "Balance": balance, "NumOfProducts": products, "HasCrCard": has_card,
        "IsActiveMember": active, "EstimatedSalary": salary, "Exited": exited,
    })
    df.to_csv("data/demo_bank_churn_synthetic.csv", index=False)
    print(f"Wrote {len(df):,} synthetic demo rows; churn rate={df.Exited.mean():.3%}")


if __name__ == "__main__":
    main()
